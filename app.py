import json
import logging
import asyncio
import traceback
from argparse import ArgumentParser
from enum import Enum
from random import choice, random

from playwright.async_api import async_playwright
from unidecode import unidecode
from faker import Faker

fake = Faker("pt_BR")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)


class XPath(str, Enum):
    OK_BUTTON = "/html/body/div/main/div[1]/div/div/div[2]/div[1]/section/span[2]/div[1]/button"
    READY_BUTTON = "/html/body/div/main/div[1]/div/div/div[3]/div/div/button/strong"
    LETTER = "/html/body/div/main/div[1]/div/div/div[1]/section/div[2]/div/span/p"
    USERNAME_INPUT = "/html/body/div/main/div[1]/div/div/div[2]/div[1]/section/span[1]/div[2]/input"
    HEADER_BUTTON = "/html/body/header/div[1]/div[2]/div[1]/form/button/strong"
    SUBMIT_BUTTON = "/html/body/div/main/div[1]/div/div/div[2]/div[1]/section/span[2]/div[1]/button"
    CATEGORY_LABEL = "/html/body/div/main/div[1]/div/div/div[2]/div[2]/div[1]/div/div/div[1]/section/div/div[{i}]/label/legend/p"
    CATEGORY_INPUT = "/html/body/div/main/div[1]/div/div/div[2]/div[2]/div[1]/div/div/div[1]/section/div/div[{i}]/label/input"
    VALIDATION_POPUP = "/html/body/div/main/div[1]/div/div/div[2]/div[2]/div[1]/div/div/div[1]"


class StopotsURL(str, Enum):
    BASE = "https://stopots.com/pt/"


class WebSocketEvent(str, Enum):
    CONNECT = "connect"
    CLOSE = "close"
    FRAME_SENT = "framesent"
    FRAME_RECEIVED = "framereceived"


class WebSocketLogger:
    def __init__(self, context):
        self._context = context
        self._ws_counter = 0
        self._current_ws_id: int | None = None

    def attach(self):
        self._context.on("websocket", self._on_websocket)

    async def _on_websocket(self, ws):
        self._ws_counter += 1
        self._current_ws_id = self._ws_counter
        logging.info(f"WS [{self._current_ws_id}] connected: {ws.url}")

        ws.on(WebSocketEvent.FRAME_SENT.value, self._on_frame_sent)
        ws.on(WebSocketEvent.FRAME_RECEIVED.value, self._on_frame_received)
        ws.on(WebSocketEvent.CLOSE.value, self._on_close)

    def _on_frame_sent(self, frame):
        logging.info(f"WS [{self._current_ws_id}] -> {frame.text[:100]}")

    def _on_frame_received(self, frame):
        logging.info(f"WS [{self._current_ws_id}] <- {frame.text[:100]}")

    def _on_close(self):
        logging.info(f"WS [{self._current_ws_id}] closed")
        self._current_ws_id = None


class DictionaryService:
    def __init__(self, filepath: str = "dictionary.json"):
        self._filepath = filepath
        self._data: dict | None = None

    def _load(self) -> None:
        if self._data is None:
            with open(self._filepath) as f:
                self._data = json.load(f)

    def get_answer(self, letter: str, category: str) -> str:
        self._load()
        category_key = unidecode(category.lower()).strip()
        letter_data = self._data.get(letter.lower(), {})
        answers = letter_data.get(category_key)
        if not answers:
            logging.warning(f"No answer for [{letter.upper()}] [{category}]")
            return f"{letter}-NaoSei"
        return choice(answers)


class BrowserHelper:
    def __init__(self, page):
        self.page = page

    async def click_if_enabled(self, xpath: XPath, *valid_texts: str) -> bool:
        try:
            await self.page.wait_for_selector(f"xpath={xpath.value}", state="visible", timeout=2000)
        except Exception:
            return False

        element = await self.page.query_selector(f"xpath={xpath.value}")
        if not element:
            return False

        is_disabled = await self.page.evaluate("el => el.disabled", element)
        if is_disabled:
            return False

        text = await self.page.text_content(f"xpath={xpath.value}")
        if not text:
            return False

        text_lower = text.strip().lower()

        if text_lower not in [t.lower() for t in valid_texts]:
            return False

        logging.info(f"Clicking: {text.strip()}")
        await self.page.evaluate(
            f"""
            document.evaluate('{xpath.value}', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click()
        """
        )
        await asyncio.sleep(0.2)
        return True

    async def safe_goto(self, url: str, retries: int = 5) -> None:
        for attempt in range(retries):
            try:
                await self.page.goto(url, wait_until="load")
                logging.info(f"Loaded: {url}")
                return
            except TimeoutError:
                logging.warning(f"Attempt {attempt + 1} failed, retrying...")
                if attempt + 1 == retries:
                    raise
                await asyncio.sleep(60 * (attempt + 1))

    async def type_letter_by_letter(self, xpath: str, text: str) -> None:
        await self.page.fill(f"xpath={xpath}", text)

    async def fill_all(self, inputs: list[tuple[str, str]]) -> None:
        for xpath, text in inputs:
            logging.info(f"Filling: {text}")
        tasks = [self.page.fill(f"xpath={xpath}", text) for xpath, text in inputs]
        await asyncio.gather(*tasks)

    async def log_validated_answers(self) -> None:
        popup = await self.page.query_selector(f"xpath={XPath.VALIDATION_POPUP.value}/div")
        if not popup:
            return

        title_el = await popup.query_selector("h2")
        title = await title_el.text_content() if title_el else None

        answer_els = await popup.query_selector_all("label p")
        answers = []
        for el in answer_els:
            text = await el.text_content()
            if text:
                answers.append(text)

        logging.info(f"Validated [{title}]: {answers}")


class GameEngine:
    def __init__(self, page, args):
        self._page = page
        self._args = args
        self._browser = BrowserHelper(page)
        self._dictionary = DictionaryService()
        self._last_letter: str | None = None

    async def setup(self) -> None:
        logging.info("Navigating to game URL...")
        await self._browser.safe_goto(StopotsURL.BASE.value)

        username_input = XPath.USERNAME_INPUT.value
        if await self._page.query_selector(f"xpath={username_input}") is None:
            logging.info("Clicking header button...")
            await self._browser.page.click(f"xpath={XPath.HEADER_BUTTON.value}")

        logging.info(f"Entering username: {self._args.username}")
        await self._page.fill(f"xpath={username_input}", self._args.username)
        logging.info("Clicking submit button...")
        await self._browser.page.click(f"xpath={XPath.SUBMIT_BUTTON.value}")
        logging.info("Joined game room")

    async def run(self) -> None:
        await self.setup()
        logging.info("Game loop started")

        while True:
            try:
                game_started = await self._browser.click_if_enabled(XPath.OK_BUTTON, "jogar")
                if game_started:
                    logging.info("Clicked JOGAR")
                    await asyncio.sleep(1)

                ready_clicked = await self._browser.click_if_enabled(XPath.READY_BUTTON, "estou pronto", "avaliar")
                if ready_clicked:
                    logging.info("Clicked AVALIAR - waiting for new round...")
                    await self._browser.log_validated_answers()
                    await asyncio.sleep(3)
                    continue

                letter = await self._browser.page.text_content(f"xpath={XPath.LETTER.value}")

                if letter in (self._last_letter, "?"):
                    await asyncio.sleep(0.5)
                    continue

                self._last_letter = letter
                logging.info(f"New round: [{letter.upper()}]")
                await self._fill_categories(letter)

            except Exception as e:
                logging.error(f"An error occurred: {e}\n{traceback.format_exc()}")
                await self._page.screenshot(path=f"error_{random()}.png")
                break

    async def _fill_categories(self, letter: str) -> None:
        inputs_to_fill = []

        for i in range(1, 13):
            label_xpath = XPath.CATEGORY_LABEL.value.format(i=i)
            input_xpath = XPath.CATEGORY_INPUT.value.format(i=i)

            label_element = await self._page.query_selector(f"xpath={label_xpath}")
            if label_element is None:
                break

            input_text = await self._page.input_value(f"xpath={input_xpath}")
            if input_text:
                continue

            label_text = await self._browser.page.text_content(f"xpath={label_xpath}")
            answer = self._dictionary.get_answer(letter.lower(), label_text)
            inputs_to_fill.append((input_xpath, answer))

        if inputs_to_fill:
            await self._browser.fill_all(inputs_to_fill)

        logging.info(f"Round [{letter.upper()}] done - {len(inputs_to_fill)} filled")


async def main():
    parser = ArgumentParser()
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--username", type=str, help="Username to use in the game")
    args = parser.parse_args()

    if not args.username:
        args.username = fake.profile(fields=["username"])["username"].replace("-", "")

    logging.info(f"Bot started as [{args.username}]")
    logging.info(f"Headless mode: {args.headless}")

    async with async_playwright() as p:
        logging.info("Launching browser...")
        browser = await p.chromium.launch(
            headless=args.headless,
            args=[
                "--mute-audio",
                "--disable-extensions",
                "--disable-plugins",
                "--disable-background-networking",
                "--disable-default-apps",
                "--disable-sync",
                "--disable-translate",
                "--metrics-recording-only",
                "--no-first-run",
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--no-experiments",
                "--no-crash-upload",
                "--disable-low-res-tiling",
                "--log-level=3",
                "--disable-logging",
            ],
        )
        logging.info("Creating context...")
        context = await browser.new_context(
            locale="pt-BR",
            viewport={"width": 1280, "height": 720},
            ignore_https_errors=True,
        )
        context.route(
            "**/*.{png,jpg,jpeg,gif,svg,ico,woff,woff2,ttf,otf,eot}",
            lambda route: route.abort(),
        )

        logging.info("Attaching WebSocket logger...")
        ws_logger = WebSocketLogger(context)
        ws_logger.attach()

        logging.info("Creating page...")
        page = await context.new_page()
        page.set_default_timeout(180_000)

        engine = GameEngine(page, args)
        await engine.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
