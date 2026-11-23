"""Bot for stopots.com: joins a room and fills every round with answers from dictionary.json."""

import asyncio
import json
import logging
import sys
import time
from argparse import ArgumentParser, ArgumentTypeError
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from random import choice
from urllib.parse import urlsplit

from faker import Faker
from playwright.async_api import BrowserContext, Page, Request, Response, Route, WebSocket, async_playwright
from playwright.async_api import Error as PlaywrightError
from unidecode import unidecode


class StopotsError(Exception):
    """Base error of the bot."""


class RoomPasswordRequiredError(StopotsError):
    """The room asked for a password, which the bot does not support."""


class TooManyDisconnectsError(StopotsError):
    """The site sent the bot back to the entrance page too many times in a row."""


class GamePageUnresponsiveError(StopotsError):
    """Every action on the game page kept failing, so the page is treated as dead."""


class StopotsURL(str, Enum):
    BASE = "https://stopots.com/pt/"


class Selector(str, Enum):
    """CSS selectors read from the live site on 2026-11-22."""

    # .screen-exit is the screen that is leaving: it stays in the DOM for about 1.5 s after the next one mounts
    LANDING_USERNAME = ".screen:not(.screen-exit) .start .input input"
    LANDING_PLAY = ".start .action button:has-text('JOGAR')"
    JOIN_USERNAME = ".screen:not(.screen-exit) .join-content .user .input input"
    JOIN_PLAY = ".join-content .user .button button"
    PASSWORD_POPUP = ".popupPassword"
    GAME = ".game"
    LETTER = ".headerGame .letter p"
    ANSWER_ROW = ".answers .answer"
    # .page-exit holds the button of the screen that is leaving; STOP! shares this slot and is filtered by label
    CONFIRM_BUTTON = ".game > .bottom > div:not(.page-exit) button:not([disabled])"
    POPUP_BUTTON = ".popupSystem .btPopup"


class ButtonLabel(str, Enum):
    VALIDATE = "avaliar"
    READY = "estou pronto"


class WebSocketEvent(str, Enum):
    CLOSE = "close"
    FRAME_SENT = "framesent"
    FRAME_RECEIVED = "framereceived"


@dataclass(frozen=True)
class Entrance:
    """Page the bot uses to get into a room: the landing page or the join page of one room."""

    url: str
    username_input: str
    play_button: str

    @classmethod
    def public(cls) -> "Entrance":
        return cls(StopotsURL.BASE.value, Selector.LANDING_USERNAME.value, Selector.LANDING_PLAY.value)

    @classmethod
    def for_room(cls, room_id: str) -> "Entrance":
        return cls(StopotsURL.BASE.value + room_id, Selector.JOIN_USERNAME.value, Selector.JOIN_PLAY.value)


@dataclass(frozen=True)
class BotSettings:
    username: str
    headless: bool
    log_file: str
    entrance: Entrance


@dataclass(frozen=True)
class CategoryField:
    label: str
    input_id: str


@dataclass(frozen=True)
class FeedLine:
    text: str
    level: int


class CommandLine:
    USERNAME_MAX_LENGTH = 15  # maxlength of the username input on the site

    def __init__(self, faker: Faker) -> None:
        self._faker = faker

    def parse(self, argv: list[str]) -> BotSettings:
        parser = ArgumentParser(description="Plays stopots.com with answers from dictionary.json")
        parser.add_argument("--headless", action="store_true", help="Run in headless mode")
        parser.add_argument("--username", type=str, default="", help="Username to use in the game")
        parser.add_argument("--log-file", type=str, default="stopots.log", help="Log file path")
        parser.add_argument("--room", type=self._room_id, default="", help="Room id to join (default: a random public room)")
        args = parser.parse_args(argv)
        username = (args.username or self._faker.user_name().replace("-", ""))[: self.USERNAME_MAX_LENGTH]
        return BotSettings(username, args.headless, args.log_file, self._entrance(args.room))

    def _room_id(self, value: str) -> str:
        # argparse also runs this on the "" default, which means "no room"
        if value and not value.isdigit():
            raise ArgumentTypeError(f"room id must be digits only, got {value!r}")
        return value

    def _entrance(self, room_id: str) -> Entrance:
        if room_id:
            return Entrance.for_room(room_id)
        return Entrance.public()


class LoggerFactory:
    NAME = "stopots"
    FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

    def build(self, log_file: str) -> logging.Logger:
        logger = logging.getLogger(self.NAME)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        # the terminal shows the game; the file also keeps HTTP, WebSocket and per screen detail
        self._add_handler(logger, logging.StreamHandler(), logging.INFO)
        self._add_handler(logger, logging.FileHandler(log_file, mode="w", encoding="utf-8"), logging.DEBUG)
        return logger

    def _add_handler(self, logger: logging.Logger, handler: logging.Handler, level: int) -> None:
        handler.setLevel(level)
        handler.setFormatter(logging.Formatter(self.FORMAT))
        logger.addHandler(handler)


class HTTPRequestLogger:
    SITE_HOST = "stopots.com"
    IGNORED_URL_PARTS = (
        "/_next/static/",
        ".woff",
        ".ttf",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".svg",
        ".webp",
        ".css",
        ".js",
        ".mp3",
        ".mp4",
    )

    def __init__(self, context: BrowserContext, logger: logging.Logger) -> None:
        self._context = context
        self._logger = logger

    def attach(self) -> None:
        self._context.on("request", self._on_request)
        self._context.on("response", self._on_response)

    def _is_noise(self, url: str) -> bool:
        # a substring test would let through tracker URLs that carry the site in a query parameter
        if not (urlsplit(url).hostname or "").endswith(self.SITE_HOST):
            return True
        return any(part in url for part in self.IGNORED_URL_PARTS)

    def _on_request(self, request: Request) -> None:
        if self._is_noise(request.url):
            return
        self._logger.debug("REQ %s %s (type: %s)", request.method, request.url, request.resource_type)

    def _on_response(self, response: Response) -> None:
        if self._is_noise(response.url):
            return
        self._logger.debug("RES [%s] %s", response.status, response.url)


class WebSocketLogger:
    MAX_FRAME_CHARS = 500

    def __init__(self, page: Page, logger: logging.Logger) -> None:
        self._page = page
        self._logger = logger

    def attach(self) -> None:
        # "websocket" is a Page event; a BrowserContext never emits it
        self._page.on("websocket", self._on_websocket)

    def _on_websocket(self, ws: WebSocket) -> None:
        # must stay a plain def: an async handler runs as a task and attaches the frame listeners too late
        self._logger.debug("WS CONNECT %s", ws.url)
        ws.on(WebSocketEvent.FRAME_SENT.value, lambda payload: self._log_frame("->", payload))
        ws.on(WebSocketEvent.FRAME_RECEIVED.value, lambda payload: self._log_frame("<-", payload))
        ws.on(WebSocketEvent.CLOSE.value, lambda _: self._logger.debug("WS CLOSED %s", ws.url))

    def _log_frame(self, direction: str, payload: object) -> None:
        self._logger.debug("WS %s %s", direction, str(payload)[: self.MAX_FRAME_CHARS])


class RoomEventTranslator:
    """Turns one socket.io frame of the room into one readable line.

    The codes were mapped by watching live rooms on 2026-11-22; a code not listed here is shown raw.
    """

    EVENT_PREFIX = "42"
    ROOM_STATE = "10"
    ROOM_EVENT = "9"
    REMOVED = "8"
    PER_PLAYER_NOISE = ("4",)  # one frame per player per validation screen, about 100 per round
    MAX_RAW_CHARS = 200
    UNKNOWN_PLAYER = "someone"
    EVENT_PAYLOAD = 2  # ["9", code, payload]
    ROOM_PLAYERS = 3  # [room id, settings, round, players, ...]
    RANKING_POINTS = 3  # [player id, name, avatar, points]
    NOTHING = FeedLine("", logging.DEBUG)

    def __init__(self, names: dict[str, str]) -> None:
        self._names = names

    def translate(self, frame: str) -> FeedLine:
        if not frame.startswith(self.EVENT_PREFIX):
            return self.NOTHING
        event = json.loads(frame[len(self.EVENT_PREFIX) :])
        handlers = {self.ROOM_STATE: self._room_state, self.ROOM_EVENT: self._room_event, self.REMOVED: self._removed}
        handler = handlers.get(str(event[0]))
        if handler is None:
            return self.NOTHING
        return handler(event)

    def _room_state(self, event: list) -> FeedLine:
        room_id, players = event[1][0], event[1][self.ROOM_PLAYERS]
        self._names.clear()
        self._names.update({str(player[0]): str(player[1]) for player in players})
        return FeedLine(f"Room {room_id} has {len(players)} players: {', '.join(self._names.values())}", logging.INFO)

    def _removed(self, event: list) -> FeedLine:
        return FeedLine(f"The server removed the bot from the room (code {event[1]})", logging.WARNING)

    def _room_event(self, event: list) -> FeedLine:
        code, payload = str(event[1]), event[self.EVENT_PAYLOAD] or []
        level = logging.DEBUG if code in self.PER_PLAYER_NOISE else logging.INFO
        describe = self._describers().get(code)
        if describe is None:
            return FeedLine(f"Room event {code}: {json.dumps(payload, ensure_ascii=False)[: self.MAX_RAW_CHARS]}", level)
        return FeedLine(describe(payload), level)

    def _describers(self) -> dict[str, Callable[[list], str]]:
        return {
            "3": self._answer_time_over,
            "4": self._confirmed_validation,
            "6": self._ready,
            "7": self._emoji,
            "8": self._letter,
            "9": self._categories,
            "10": self._validation,
            "11": self._ranking,
            "14": self._joined,
            "15": self._left,
        }

    def _name(self, player_id: object) -> str:
        return self._names.get(str(player_id), self.UNKNOWN_PLAYER)

    def _answer_time_over(self, payload: list) -> str:
        return "Answer time is over"

    def _confirmed_validation(self, payload: list) -> str:
        return f"{self._name(payload[0])} confirmed the validation"

    def _ready(self, payload: list) -> str:
        return f"{self._name(payload[0])} {'is ready' if payload[1] else 'is no longer ready'}"

    def _emoji(self, payload: list) -> str:
        return f"{self._name(payload[0])} sent emoji {payload[1]}"

    def _letter(self, payload: list) -> str:
        return f"Next letter drawn: {payload[0]}"

    def _categories(self, payload: list) -> str:
        return "Round categories: " + ", ".join(str(label).split("|")[0] for label in payload[0])

    def _validation(self, payload: list) -> str:
        return f"Validation {payload[0] + 1}: {', '.join(payload[1])}"

    def _ranking(self, payload: list) -> str:
        return "Ranking: " + ", ".join(f"{row[1]} {row[self.RANKING_POINTS]}" for row in payload[0])

    def _joined(self, payload: list) -> str:
        self._names.update({str(player[0]): str(player[1]) for player in payload})
        return f"{', '.join(str(player[1]) for player in payload)} joined the room"

    def _left(self, payload: list) -> str:
        return f"{self._names.pop(str(payload[0]), self.UNKNOWN_PLAYER)} left the room"


class RoomFeed:
    """Prints what happens in the room in real time, from the frames the site sends."""

    def __init__(self, page: Page, translator: RoomEventTranslator, logger: logging.Logger) -> None:
        self._page = page
        self._translator = translator
        self._logger = logger

    def attach(self) -> None:
        self._page.on("websocket", self._on_websocket)

    def _on_websocket(self, ws: WebSocket) -> None:
        ws.on(WebSocketEvent.FRAME_RECEIVED.value, self._on_frame)

    def _on_frame(self, payload: object) -> None:
        try:
            line = self._translator.translate(str(payload))
        except (LookupError, TypeError, ValueError, RecursionError) as error:
            # the protocol is not documented: a frame with a new shape must not stop the bot
            self._logger.debug("Feed could not read a frame: %r", error)
            return
        if line.text:
            self._logger.log(line.level, "Feed | %s", line.text)


class ResourceBlocker:
    BLOCKED_PATTERNS = (
        "**/*.{png,jpg,jpeg,gif,svg,ico,woff,woff2,ttf,otf,eot}",
        "**/*.css",
        "**/*.mp4",
        "**/*.mp3",
        "**/analytics/**",
        "**/tracking/**",
    )

    def __init__(self, context: BrowserContext) -> None:
        self._context = context

    async def attach(self) -> None:
        for pattern in self.BLOCKED_PATTERNS:
            await self._context.route(pattern, self._abort)

    async def _abort(self, route: Route) -> None:
        await route.abort()


class MissedCategories:
    """Letter + category pairs the dictionary could not answer, reported when the bot stops."""

    def __init__(self, logger: logging.Logger, missed: set[tuple[str, str]]) -> None:
        self._logger = logger
        self._missed = missed

    def record(self, letter: str, category: str) -> None:
        self._missed.add((letter.upper(), category.strip()))

    def log_summary(self) -> None:
        self._logger.info("Left blank for lack of an answer in dictionary.json: %d", len(self._missed))
        for letter, category in sorted(self._missed):
            self._logger.info("  [%s] %s", letter, category)


class DictionaryService:
    def __init__(self, answers: dict[str, dict[str, list[str]]], missed: MissedCategories) -> None:
        self._answers = answers
        self._missed = missed

    @classmethod
    def from_file(cls, path: Path, missed: MissedCategories) -> "DictionaryService":
        with path.open(encoding="utf-8") as handle:
            return cls(json.load(handle), missed)

    def get_answer(self, letter: str, category: str) -> str:
        category_key = unidecode(category.lower()).strip()
        answers = self._answers.get(letter.lower(), {}).get(category_key, [])
        if not answers:
            self._missed.record(letter, category)
            return ""
        return choice(answers)


class GamePage:
    """Reads and drives the game screen. No call here waits for an element that may never come."""

    ACTION_TIMEOUT_MS = 2_000  # same bound the old click helper used
    FIELDS_JS = """rows => rows.map(row => ({
        label: (row.querySelector('legend p')?.textContent ?? '').trim(),
        input_id: row.querySelector('input')?.id ?? '',
        value: row.querySelector('input')?.value ?? '',
    }))"""
    VALIDATION_JS = """() => {
        const screen = document.querySelector('.center > div:not(.page-exit) .validation');
        const title = screen?.querySelector('h2')?.childNodes[0]?.textContent ?? '';
        const answers = [...(screen?.querySelectorAll('.answer label p') ?? [])].map(p => p.textContent);
        return '[' + title + ']: ' + answers.join(', ');
    }"""
    PLAYERS_JS = """rows => rows.map(row =>
        (row.querySelector('.data > p')?.textContent ?? '') + ' (' + (row.querySelector('.data section p')?.textContent ?? '0') + ')'
        + (row.classList.contains('you') ? ' [you]' : '')).join(', ')"""

    STANDING_JS = """rows => {
        const index = rows.findIndex(row => row.classList.contains('you'));
        if (index < 0) return 'not in the player list';
        const points = rows[index].querySelector('.data section p')?.textContent ?? '0';
        return points + ' pts, position ' + (index + 1) + ' of ' + rows.length;
    }"""
    PLAYER_ROW = ".players .list .player"

    def __init__(self, page: Page) -> None:
        self._page = page

    async def read_letter(self) -> str:
        element = await self._page.query_selector(Selector.LETTER.value)
        if element is None:
            return ""
        return (await element.text_content() or "").strip()

    async def empty_fields(self) -> list[CategoryField]:
        rows = await self._page.eval_on_selector_all(Selector.ANSWER_ROW.value, self.FIELDS_JS)
        return [CategoryField(row["label"], row["input_id"]) for row in rows if row["input_id"] and not row["value"]]

    async def fill(self, field: CategoryField, answer: str) -> None:
        await self._page.fill(f"#{field.input_id}", answer, timeout=self.ACTION_TIMEOUT_MS)

    async def confirm_button_label(self) -> str:
        button = await self._page.query_selector(Selector.CONFIRM_BUTTON.value)
        if button is None:
            return ""
        return (await button.text_content() or "").strip().lower()

    async def click_confirm_button(self, label: ButtonLabel) -> None:
        # bound to the label that was just read: after a screen swap the slot may hold another button
        await self._page.click(f"{Selector.CONFIRM_BUTTON.value}:has-text('{label.value}')", timeout=self.ACTION_TIMEOUT_MS)

    async def dismiss_popup(self) -> bool:
        button = await self._page.query_selector(Selector.POPUP_BUTTON.value)
        if button is None:
            return False
        await button.click(timeout=self.ACTION_TIMEOUT_MS)
        return True

    async def validation_summary(self) -> str:
        return await self._page.evaluate(self.VALIDATION_JS)

    async def players_summary(self) -> str:
        return await self._page.eval_on_selector_all(self.PLAYER_ROW, self.PLAYERS_JS)

    async def standing(self) -> str:
        return await self._page.eval_on_selector_all(self.PLAYER_ROW, self.STANDING_JS)


class RoomEntrance:
    NAVIGATION_TIMEOUT_MS = 30_000  # the landing page loaded in 2 to 3 s in the measured runs
    GOTO_ATTEMPTS = 5
    RETRY_WAIT_SECONDS = 60

    def __init__(self, page: Page, settings: BotSettings, logger: logging.Logger) -> None:
        self._page = page
        self._settings = settings
        self._logger = logger

    async def is_outside_room(self) -> bool:
        """True when the entrance form is up, and also when no game screen exists at all (error page, site down)."""
        entrance_inputs = f"{Selector.LANDING_USERNAME.value}, {Selector.JOIN_USERNAME.value}"
        if await self._page.query_selector(entrance_inputs) is not None:
            return True
        return await self._page.query_selector(Selector.GAME.value) is None

    async def enter(self) -> None:
        entrance = self._settings.entrance
        await self._goto(entrance.url)
        await self._page.fill(entrance.username_input, self._settings.username, timeout=self.NAVIGATION_TIMEOUT_MS)
        await self._page.click(entrance.play_button, timeout=self.NAVIGATION_TIMEOUT_MS)
        joined_or_locked = f"{Selector.GAME.value}, {Selector.PASSWORD_POPUP.value}"
        await self._page.wait_for_selector(joined_or_locked, timeout=self.NAVIGATION_TIMEOUT_MS)
        if await self._page.query_selector(Selector.PASSWORD_POPUP.value):
            raise RoomPasswordRequiredError(f"{entrance.url} asks for a password, which the bot does not support")
        self._logger.info("Joined a room from %s as [%s]", entrance.url, self._settings.username)

    async def _goto(self, url: str) -> None:
        for attempt in range(1, self.GOTO_ATTEMPTS):
            try:
                await self._page.goto(url, wait_until="load", timeout=self.NAVIGATION_TIMEOUT_MS)
                return
            except PlaywrightError as error:
                self._logger.warning("Loading %s failed (attempt %d of %d): %s", url, attempt, self.GOTO_ATTEMPTS, error)
                await asyncio.sleep(self.RETRY_WAIT_SECONDS * attempt)
        await self._page.goto(url, wait_until="load", timeout=self.NAVIGATION_TIMEOUT_MS)


class RoundPlayer:
    """Plays whatever screen the room shows: confirms validations, marks ready, fills a new round."""

    NO_ROUND_LETTERS = ("", "?")

    def __init__(self, game: GamePage, dictionary: DictionaryService, logger: logging.Logger) -> None:
        self._game = game
        self._dictionary = dictionary
        self._logger = logger
        self._last_letter = ""
        self._ready_sent = False
        self._rounds = 0

    def forget_room(self) -> None:
        """What was seen in the room the bot left says nothing about the room it joins next."""
        self._last_letter = ""
        self._ready_sent = False

    async def play_screen(self) -> bool:
        """Returns True when this call filled a new round."""
        if await self._game.dismiss_popup():
            self._logger.info("Dismissed a popup")
        await self._confirm_screen()
        return await self._fill_new_round()

    async def _confirm_screen(self) -> None:
        label = await self._game.confirm_button_label()
        if label != ButtonLabel.READY.value:
            self._ready_sent = False
        if label == ButtonLabel.VALIDATE.value:
            self._logger.debug("Confirming validation %s", await self._game.validation_summary())
            await self._game.click_confirm_button(ButtonLabel.VALIDATE)
            return
        if label == ButtonLabel.READY.value and not self._ready_sent:
            # ESTOU PRONTO is a toggle on the site: a second click would undo the first
            await self._game.click_confirm_button(ButtonLabel.READY)
            self._ready_sent = True
            self._logger.info("Ranking after round %d: %s", self._rounds, await self._game.standing())

    async def _fill_new_round(self) -> bool:
        letter = await self._game.read_letter()
        if letter in self.NO_ROUND_LETTERS:
            self._last_letter = ""
            return False
        if letter == self._last_letter:
            return False
        fields = await self._game.empty_fields()
        if not fields:
            return False
        self._last_letter = letter
        self._rounds += 1
        await self._play_round(letter.upper(), fields)
        return True

    async def _play_round(self, letter: str, fields: list[CategoryField]) -> None:
        self._logger.debug("Round %d [%s] players: %s", self._rounds, letter, await self._game.players_summary())
        answers = {field: self._dictionary.get_answer(letter, field.label) for field in fields}
        typed = await self._type_answers(answers)
        self._logger.info("Round %d [%s] %d/%d filled: %s", self._rounds, letter, len(typed), len(fields), " | ".join(typed))
        blank = [field.label for field, answer in answers.items() if not answer]
        if blank:
            self._logger.warning("Round %d [%s] left blank, no answer in dictionary.json: %s", self._rounds, letter, ", ".join(blank))

    async def _type_answers(self, answers: dict[CategoryField, str]) -> list[str]:
        typed: list[str] = []
        try:
            for field, answer in [(field, answer) for field, answer in answers.items() if answer]:
                await self._game.fill(field, answer)
                typed.append(f"{field.label}={answer}")
        except PlaywrightError as error:
            self._logger.warning("Round %d ended while filling: %s", self._rounds, str(error).splitlines()[0])
        return typed


class GameEngine:
    POLL_SECONDS = 0.2
    MAX_CONSECUTIVE_DROPS = 5  # same count as the page load attempts
    MAX_CONSECUTIVE_FAILED_TICKS = 10  # a screen swap fails 1 or 2 ticks; 10 in a row means the page is dead

    def __init__(self, entrance: RoomEntrance, player: RoundPlayer, logger: logging.Logger) -> None:
        self._entrance = entrance
        self._player = player
        self._logger = logger
        self._drops = 0
        self._failed_ticks = 0

    async def run(self) -> None:
        await self._entrance.enter()
        self._logger.info("Game loop started")
        while True:
            await self._tick()
            await asyncio.sleep(self.POLL_SECONDS)

    async def _tick(self) -> None:
        try:
            await self._play_or_rejoin()
            self._failed_ticks = 0
        except PlaywrightError as error:
            # the site swaps screens under the bot (STOP, end of a validation); the next tick reads the new screen
            self._failed_ticks += 1
            self._logger.debug("Tick failed (%d in a row): %s", self._failed_ticks, str(error).splitlines()[0])
            if self._failed_ticks >= self.MAX_CONSECUTIVE_FAILED_TICKS:
                raise GamePageUnresponsiveError(f"{self._failed_ticks} ticks failed in a row") from error

    async def _play_or_rejoin(self) -> None:
        if not await self._entrance.is_outside_room():
            if await self._player.play_screen():
                self._drops = 0
            return
        self._drops += 1
        if self._drops >= self.MAX_CONSECUTIVE_DROPS:
            raise TooManyDisconnectsError(f"out of the room {self._drops} times in a row")
        self._logger.warning("Out of the room (drop %d of %d) - rejoining", self._drops, self.MAX_CONSECUTIVE_DROPS)
        self._player.forget_room()
        await self._entrance.enter()


class BotApplication:
    DICTIONARY_PATH = Path(__file__).with_name("dictionary.json")
    LOCALE = "pt-BR"
    VIEWPORT = {"width": 1024, "height": 768}
    CHROMIUM_ARGS = (
        "--mute-audio",
        "--disable-extensions",
        "--disable-background-networking",
        "--disable-default-apps",
        "--disable-sync",
        "--no-first-run",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--disable-features=TranslateUI",
        "--disable-popup-blocking",
    )

    def __init__(self, settings: BotSettings, logger: logging.Logger) -> None:
        self._settings = settings
        self._logger = logger

    @classmethod
    def main(cls) -> None:
        settings = CommandLine(Faker("pt_BR")).parse(sys.argv[1:])
        logger = LoggerFactory().build(settings.log_file)
        try:
            asyncio.run(cls(settings, logger).play_until_stopped())
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except (StopotsError, PlaywrightError, OSError, ValueError, AttributeError, RuntimeError) as error:
            # ValueError and AttributeError cover a broken dictionary.json; the traceback goes to the log file
            logger.exception("Bot crashed: %s", error)
            raise SystemExit(1) from error

    async def play_until_stopped(self) -> None:
        self._logger.info("Bot started as [%s] (headless: %s)", self._settings.username, self._settings.headless)
        missed = MissedCategories(self._logger, set())
        dictionary = DictionaryService.from_file(self.DICTIONARY_PATH, missed)
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=self._settings.headless, args=list(self.CHROMIUM_ARGS))
            context = await browser.new_context(locale=self.LOCALE, viewport=self.VIEWPORT)
            try:
                await self._play(context, dictionary)
            finally:
                missed.log_summary()

    async def _play(self, context: BrowserContext, dictionary: DictionaryService) -> None:
        await ResourceBlocker(context).attach()
        HTTPRequestLogger(context, self._logger).attach()
        page = await context.new_page()
        WebSocketLogger(page, self._logger).attach()
        RoomFeed(page, RoomEventTranslator({}), self._logger).attach()
        player = RoundPlayer(GamePage(page), dictionary, self._logger)
        engine = GameEngine(RoomEntrance(page, self._settings, self._logger), player, self._logger)
        try:
            await engine.run()
        except (StopotsError, PlaywrightError):
            await self._save_crash_screenshot(page)
            raise

    async def _save_crash_screenshot(self, page: Page) -> None:
        try:
            await page.screenshot(path=f"error_{int(time.time())}.png")
        except (PlaywrightError, OSError) as error:
            # the crash that brought the bot here is the one worth reporting, not this
            self._logger.warning("Could not save the crash screenshot: %s", str(error).splitlines()[0])


if __name__ == "__main__":
    BotApplication.main()
