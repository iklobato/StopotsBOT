import re
import json
import logging
import asyncio
from argparse import ArgumentParser
from enum import Enum
from random import choice, random

from playwright.async_api import async_playwright
from tabulate import tabulate
from unidecode import unidecode
from faker import Faker

fake = Faker("pt_BR")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)


class XPath(str, Enum):
    OK_BUTTON = "/html/body/div[1]/div[1]/div[2]/div/div/div/div[2]/button/strong"
    READY_BUTTON = "/html/body/div[1]/div[1]/div[1]/div/div/div[2]/div[2]/div/button/strong"
    LETTER = "/html/body/div[1]/div[1]/div[1]/div/div/div[1]/div[2]/div[2]/div/ul/li[1]/span"
    USERNAME_INPUT = "/html/body/div[1]/div[1]/div[1]/div/div[2]/div[2]/div[1]/div[2]/input"
    HEADER_BUTTON = "/html/body/header/div[1]/div[2]/div[1]/form/button/strong"
    SUBMIT_BUTTON = "/html/body/div[1]/div[1]/div[1]/div/div[2]/div[2]/div[2]/button[1]"
    USERS_LIST = "ul#users li"
    CHAT_MESSAGES = '//div[@id="chat"]//ul[@class="historic"]/li'
    CATEGORY_LABEL = "/html/body/div[1]/div[1]/div[1]/div/div/div[2]/div[2]/div/div[1]/label[{i}]/span"
    CATEGORY_INPUT = "/html/body/div[1]/div[1]/div[1]/div/div/div[2]/div[2]/div/div[1]/label[{i}]/input"


class Label(str, Enum):
    CEP = "CEPCidade, Estado ou Pais"
    GENTILICO = "GentilicoAdjetivo patrio"
    FLV = "FLVFruta, Legume ou Verdura"
    JLR = "JLRJornal, Livro ou Revista"
    PCH = "PCHParte do Corpo Humano"
    PDA = "PDAPersonagem de Desenho Animado"
    MSE = "MSEMinha Sogra E..."

    @classmethod
    def to_key(cls, value: str) -> str:
        unidecoded = unidecode(value)
        for member in cls:
            if unidecode(member.value).startswith(unidecoded):
                return unidecode(member.name.lower())
        return unidecoded


class StopotsURL(str, Enum):
    BASE = "https://stopots.com/pt/"


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
        category_key = Label.to_key(category)
        letter_data = self._data.get(letter.lower(), {})
        answers = letter_data.get(category_key)
        if not answers:
            return f"{letter}-NaoSei"
        return choice(answers)


class BrowserHelper:
    def __init__(self, page):
        self.page = page

    async def click_if_enabled(self, xpath: XPath, *valid_texts: str) -> bool:
        element = await self.page.query_selector(f"xpath={xpath.value}")
        if not element:
            return False

        text = await self.page.text_content(f"xpath={xpath.value}")
        is_disabled = await self.page.evaluate("el => el.disabled", element)

        if is_disabled or not text:
            return False

        if text.strip().lower() not in [t.lower() for t in valid_texts]:
            return False

        await self.page.click(f"xpath={xpath.value}")
        return True

    async def safe_goto(self, url: str, retries: int = 5) -> None:
        for attempt in range(retries):
            try:
                await self.page.goto(url, wait_until="load")
                return
            except TimeoutError:
                logging.warning(f"Attempt {attempt + 1} failed, retrying...")
                if attempt + 1 == retries:
                    raise
                wait_time = 60 * (attempt + 1)
                logging.info(f"Waiting {wait_time} seconds before retrying...")
                await asyncio.sleep(wait_time)

    async def type_letter_by_letter(self, xpath: str, text: str) -> None:
        await self.page.click(f"xpath={xpath}")
        await self.page.keyboard.press("End")
        for char in text:
            await self.page.keyboard.type(char)


class ChatHandler:
    def __init__(self, browser: BrowserHelper):
        self._browser = browser
        self._last_count = 0

    async def check_new_messages(self) -> int:
        messages = await self._browser.page.query_selector_all(f"xpath={XPath.CHAT_MESSAGES.value}")
        current_count = len(messages)

        if current_count <= self._last_count:
            return self._last_count

        new_messages = messages[self._last_count : current_count]

        for msg in new_messages:
            msg_class = await msg.get_attribute("class")
            username = await msg.query_selector("strong")
            text = await msg.query_selector("span")

            if not (username and text):
                continue

            username_text = await username.text_content()
            text_content = await text.text_content()

            if msg_class == "message":
                logging.info(f"Chat (Message): {username_text}: {text_content}")
            elif msg_class == "system":
                logging.info(f"Chat (System): {username_text} {text_content}")
            elif msg_class == "actionStop":
                logging.info(f"Chat (ActionStop): {username_text} {text_content}")

        self._last_count = current_count
        return current_count


class ScoreManager:
    def __init__(self, browser: BrowserHelper):
        self._browser = browser

    async def get_scores(self) -> dict[str, int]:
        users = await self._browser.page.locator(XPath.USERS_LIST.value).all()
        scores: dict[str, int] = {}

        for user in users:
            username = await user.locator(".nick").text_content()
            if "Vazio" in username:
                continue

            spans = await user.locator("span").count()
            if spans > 0:
                points_text = await user.locator("span").text_content()
                points = int(points_text.replace(" pts", "").strip())
                scores[unidecode(username.strip())] = points

        return scores

    async def print_scores(self, scores: dict[str, int], current_user: str | None = None) -> None:
        if current_user and current_user in scores:
            scores[f"> {current_user}"] = scores.pop(current_user)

        table = tabulate(
            sorted(scores.items(), key=lambda x: x[1], reverse=True),
            headers=["user", "points"],
            tablefmt="outline",
        )
        logging.info(f"\n{table}")


class GameEngine:
    def __init__(self, page, args):
        self._page = page
        self._args = args
        self._browser = BrowserHelper(page)
        self._dictionary = DictionaryService()
        self._chat = ChatHandler(self._browser)
        self._scores = ScoreManager(self._browser)
        self._last_letter: str | None = None

    async def setup(self) -> None:
        await self._browser.safe_goto(StopotsURL.BASE.value)

        username_input = XPath.USERNAME_INPUT.value
        if await self._page.query_selector(f"xpath={username_input}") is None:
            await self._browser.page.click(f"xpath={XPath.HEADER_BUTTON.value}")

        await self._page.fill(f"xpath={username_input}", self._args.username)
        await self._browser.page.click(f"xpath={XPath.SUBMIT_BUTTON.value}")

    async def run(self) -> None:
        await self.setup()

        while True:
            try:
                await self._browser.click_if_enabled(XPath.OK_BUTTON, "ok")
                await self._browser.click_if_enabled(XPath.READY_BUTTON, "estou pronto", "avaliar")
                await self._chat.check_new_messages()

                letter = await self._browser.page.text_content(f"xpath={XPath.LETTER.value}")

                if letter in (self._last_letter, "?"):
                    continue

                await self._update_and_print_scores()

                if await self._should_switch_room():
                    await self._switch_room()
                    continue

                self._last_letter = letter
                logging.info(f"Current letter: {letter.upper()}")
                await self._fill_categories(letter)

            except Exception as e:
                logging.error(f"An error occurred: {e}")
                await self._page.screenshot(path=f"error_{random()}.png")
                break

    async def _update_and_print_scores(self) -> None:
        current_scores = await self._scores.get_scores()
        await self._scores.print_scores(current_scores, self._args.username)

    async def _should_switch_room(self) -> bool:
        scores = await self._scores.get_scores()
        ik_pattern = re.compile(r"ik/\d{1,2}")

        has_ik_user = any(ik_pattern.match(u) for u in scores.keys())
        has_my_user = any(u == self._args.username for u in scores.keys())

        return has_ik_user and not has_my_user

    async def _switch_room(self) -> None:
        logging.info("'ik/#' found in the room, searching for another room.")
        await self._page.close()
        self._page = await self._page.context.new_page()
        self._browser = BrowserHelper(self._page)
        self._chat = ChatHandler(self._browser)
        self._scores = ScoreManager(self._browser)
        await self._browser.safe_goto(StopotsURL.BASE.value)

    async def _fill_categories(self, letter: str) -> None:
        for i in range(1, 13):
            label_xpath = XPath.CATEGORY_LABEL.value.format(i=i)
            input_xpath = XPath.CATEGORY_INPUT.value.format(i=i)

            if await self._page.query_selector(f"xpath={label_xpath}") is None:
                break

            input_text = await self._page.input_value(f"xpath={input_xpath}")
            if input_text:
                continue

            label_text = await self._browser.page.text_content(f"xpath={label_xpath}")
            answer = self._dictionary.get_answer(letter.lower(), label_text)

            logging.info(f"[{letter.upper()} {i}] {label_text.title()}: {answer.title()}")
            await self._browser.type_letter_by_letter(input_xpath, answer)


async def main():
    parser = ArgumentParser()
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--username", type=str, help="Username to use in the game")
    parser.add_argument("--task", type=str, default="stopots")
    args = parser.parse_args()

    if not args.username:
        args.username = fake.profile(fields=["username"])["username"]
        logging.info(f"Generated username: {args.username}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=args.headless)
        context = await browser.new_context(locale="pt-BR")
        page = await context.new_page()
        page.set_default_timeout(180_000)

        engine = GameEngine(page, args)
        await engine.run()


if __name__ == "__main__":
    asyncio.run(main())
