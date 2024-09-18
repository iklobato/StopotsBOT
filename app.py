import re
from argparse import ArgumentParser

from tabulate import tabulate
from unidecode import unidecode
import asyncio
import json
import logging
from random import choice, random

from playwright.async_api import async_playwright

from faker import Faker

fake = Faker('pt_BR')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

LABELS_MAP = {
    'CEPCidade, Estado ou Pais': 'cep',
    'GentilicoAdjetivo patrio (Ex: Brasileiro, Mineiro, Curitibano...)': 'gentilico',
    'FLVFruta, Legume ou Verdura': 'flv',
    'JLRJornal, Livro ou Revista': 'jlr',
    'PCHParte do Corpo Humano': 'pch',
    'PDAPersonagem de Desenho Animado': 'pda',
    'MSEMinha Sogra E...': 'mse',
}

STOPOTS_URL = "https://stopots.com/system/"
letters_answers_file = open("dictionary.json")
letters_answers_json = json.load(letters_answers_file)
letters_answers_file.close()


async def check_and_press_ok_button(page):
    button_xpath = '/html/body/div[1]/div[1]/div[2]/div/div/div/div[2]/button/strong'
    b = await page.query_selector(f'xpath={button_xpath}')
    if not b:
        return
    button_text = await page.text_content(f'xpath={button_xpath}')
    is_disable = await page.evaluate(f'el => el.disabled', f'xpath={button_xpath}')
    if not is_disable and button_text and button_text.strip().lower() in ['ok']:
        await page.click(f'xpath={button_xpath}')


async def get_word_answer(chosen_letter: str, category: str):
    category_parsed = unidecode(category)
    letter_info = letters_answers_json.get(chosen_letter, {})
    answer = letter_info.get(category_parsed)
    if not answer:
        return f"{chosen_letter}-NaoSei"
    answer = choice(answer)
    return answer


async def compare_score(page, current_points=None) -> dict:
    users_points = {}
    users = await page.locator('ul#users li').all()

    if not users:
        logging.warning("No users found.")
        return current_points

    for user in users:
        username = await user.locator('.nick').text_content()
        if 'Vazio' in username:
            continue

        span_count = await user.locator('span').count()
        if span_count > 0:
            points_text = await user.locator('span').text_content()
            points = int(points_text.replace(' pts', '').strip())
            users_points[unidecode(username.strip())] = points

    return users_points


async def print_score(users_points: dict, username=None) -> None:
    if username:
        for user in users_points:
            if user == username:
                users_points[f"> {user}"] = users_points[user]
                del users_points[user]
                break
    t = tabulate(
        sorted(users_points.items(), key=lambda x: x[1], reverse=True),
        headers=['user', 'points'],
        tablefmt='outline'
    )
    logging.info(f'\n{t}')


async def click_ready_if_exists(page):
    ready_button_xpath = '/html/body/div[1]/div[1]/div[1]/div/div/div[2]/div[2]/div/button/strong'
    button = await page.query_selector(f'xpath={ready_button_xpath}')
    if not button:
        return
    button_text = await page.text_content(f'xpath={ready_button_xpath}')
    is_disable = await page.evaluate(f'el => el.disabled', f'xpath={ready_button_xpath}')
    if not is_disable and button_text and button_text.strip().lower() in ['estou pronto', 'avaliar']:
        await page.click(f'xpath={ready_button_xpath}')
        await asyncio.sleep(1)


async def check_new_messages(page, last_message_count=0):
    chat_xpath = '//div[@id="chat"]//ul[@class="historic"]/li'

    try:
        # Get all message elements in the chat
        messages = await page.query_selector_all(f'xpath={chat_xpath}')
        current_message_count = len(messages)

        # If there are new messages, process and print them
        if current_message_count > last_message_count:
            new_messages = messages[last_message_count:current_message_count]
            for message in new_messages:
                message_class = await message.get_attribute("class")

                if message_class == "message":
                    username = await message.query_selector('strong')
                    text = await message.query_selector('span')
                    if username and text:
                        username_text = await username.text_content()
                        text_content = await text.text_content()
                        logging.info(f'Chat (Message): {username_text}: {text_content}')

                elif message_class == "system":
                    username = await message.query_selector('strong')
                    text = await message.query_selector('span')
                    if username and text:
                        username_text = await username.text_content()
                        text_content = await text.text_content()
                        logging.info(f'Chat (System): {username_text} {text_content}')

                # elif message_class == "votingKick":
                #     voter = await message.query_selector('strong')
                #     voted_user = await message.query_selector_all('strong')
                #     action_text = await message.query_selector('span')
                #     if voter and voted_user and action_text:
                #         voter_text = await voter.voter_text()
                #         voted_user_text = await voted_user.text_content()
                #         action_text_content = await action_text.text_content()
                #         logging.info(f'Chat (VotingKick): {voter_text} {action_text_content} {voted_user_text}')

                elif message_class == "actionStop":
                    username = await message.query_selector('strong')
                    action_text = await message.query_selector('span')
                    if username and action_text:
                        username_text = await username.text_content()
                        action_text_content = await action_text.text_content()
                        logging.info(f'Chat (ActionStop): {username_text} {action_text_content}')

            # Update the last message count
            last_message_count = current_message_count

    except Exception as e:
        logging.error(f"An error occurred while checking for new messages: {e}")

    return last_message_count


async def run(_playwright, args):
    logging.info("Launching browser...")
    browser = await _playwright.chromium.launch(headless=args.headless)
    context = await browser.new_context(
        locale="pt-BR",
    )
    page = await context.new_page()
    page.set_default_timeout(180_000)

    logging.info(f"Navigating to {STOPOTS_URL}")

    async def safe_goto(_page, url, retries=5):
        for attempt in range(retries):
            try:
                await _page.goto(url, wait_until='load')
                return
            except TimeoutError:
                logging.warning(f"Attempt {attempt + 1} failed, retrying...")
                if attempt + 1 == retries:
                    raise
                logging.info(f"Waiting {60 * retries ** (attempt + 1)} seconds before retrying...")
                await asyncio.sleep(60 * retries ** (attempt + 1))  # Exponential backoff

    await safe_goto(page, STOPOTS_URL)

    username_input_xpath = '/html/body/div[1]/div[1]/div[1]/div/div[2]/div[2]/div[1]/div[2]/input'
    header_button_xpath = '/html/body/header/div[1]/div[2]/div[1]/form/button/strong'
    submit_button_xpath = '/html/body/div[1]/div[1]/div[1]/div/div[2]/div[2]/div[2]/button[1]'

    if await page.query_selector(f'xpath={username_input_xpath}') is None:
        await page.click(f'xpath={header_button_xpath}')

    await page.fill(f'xpath={username_input_xpath}', args.username)
    await page.click(f'xpath={submit_button_xpath}')

    last_letter = None
    current_users_points = None
    last_message_count = 0
    while True:
        try:

            await check_and_press_ok_button(page)  # anti ban
            await click_ready_if_exists(page)  # ready button
            last_message_count = await check_new_messages(page, last_message_count)  # chat

            letter_xpath = '/html/body/div[1]/div[1]/div[1]/div/div/div[1]/div[2]/div[2]/div/ul/li[1]/span'
            letter = await page.text_content(f'xpath={letter_xpath}')
            if letter in [last_letter, '?']:
                continue

            updated_score = await compare_score(page, current_users_points)
            if updated_score != current_users_points:
                await print_score(updated_score, args.username)
                current_users_points = updated_score

            if updated_score:
                ik_user_pattern = re.compile(r'ik/\d{1,2}')
                if any(ik_user_pattern.match(username) for username in updated_score.keys()):
                    if not any(username == args.username for username in updated_score.keys()):
                        logging.info("'ik/#' found in the room, searching for another room.")
                        await page.close()

                        page = await context.new_page()
                        await safe_goto(page, STOPOTS_URL)
                        continue

            last_letter = letter
            logging.info(f"Current letter: {letter.upper()}")

            for i in range(1, 13):
                label_xpath = f'/html/body/div[1]/div[1]/div[1]/div/div/div[2]/div[2]/div/div[1]/label[{i}]/span'
                input_xpath = f'/html/body/div[1]/div[1]/div[1]/div/div/div[2]/div[2]/div/div[1]/label[{i}]/input'

                if await page.query_selector(f'xpath={label_xpath}') is None:
                    break

                input_text = await page.input_value(f'xpath={input_xpath}')  # Await input_value()
                if input_text and input_text != "":
                    continue

                label_text = await page.text_content(f'xpath={label_xpath}')  # Await text_content()
                label_text = unidecode(label_text)
                label_text = LABELS_MAP.get(label_text, label_text)
                answer_text = await get_word_answer(letter.lower(), label_text.lower())
                logging.info(f"[{letter.upper()} {i}] {label_text.title()}: {answer_text.title()}")
                for _l in answer_text:
                    await page.click(f'xpath={input_xpath}')
                    await page.keyboard.press('End')
                    await page.keyboard.type(_l)
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            await page.screenshot(path=f"error_{random()}.png")
            break


async def main():
    parameters = ArgumentParser()
    parameters.add_argument('--headless', action='store_true', help='Run in headless mode')
    parameters.add_argument('--username', type=str, help='Username to use in the game')
    parameters.add_argument('--task', type=str, help='Task to run', default='stopots')
    args = parameters.parse_args()
    if not args.username:
        args.username = fake.profile(fields=['username'])['username']
        logging.info(f"Generated username: {args.username}")
    async with async_playwright() as _playwright:
        await run(_playwright, args)


if __name__ == "__main__":
    asyncio.run(main())
