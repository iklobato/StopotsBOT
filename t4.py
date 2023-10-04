from threading import Thread
from selenium.webdriver.common.keys import Keys
from unidecode import unidecode
import json
import random
from time import sleep
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
from selenium.webdriver.common.by import By


def load_dictionary(file_path):
    with open(file_path, 'r') as json_file:
        return json.load(json_file)


def find_and_click_element(d, xpath):
    try:
        element = d.find_element(By.XPATH, xpath)
        element.click()
        return True
    except NoSuchElementException:
        return False


def login(d, u):
    d.get("https://stopots.com.br/login/anonimo")
    nome_usuario = d.find_element(By.XPATH, '//*[@id="screenHome"]/div[2]/div[1]/div[2]/input')
    nome_usuario.clear()
    nome_usuario.send_keys(u)


def check_chat_file_content(c_file_pointer):
    with open(c_file_pointer, 'r') as f:
        content = f.read()
        if content != '':
            return content
        else:
            return False


def main_game_loop(drv, response_dict, c_file):
    response_msg = ''
    last_chat_comment = ''
    clicked = False

    while True:
        try:
            if find_and_click_element(
                    drv,
                    '/html/body/div[1]/div[1]/div[1]/div/div[2]/div[2]/div[2]/button[1]/strong'
            ):
                break
            if find_and_click_element(drv, '/html/body/div[1]/div[1]/div[1]/div[2]/div[2]/button'):
                break
        except Exception:
            pass

    while True:

        try:

            botao_stop = drv.find_element(
                By.XPATH,
                '/html/body/div[1]/div[1]/div[1]/div/div/div[2]/div[2]/div/button/strong'
            )
            botao_avaliar = drv.find_element(
                By.XPATH,
                '/html/body/div[1]/div[1]/div[1]/div/div/div[2]/div[2]/div/button/strong'
            )
            botao_avaliar_txt = botao_avaliar.text.lower()
            if botao_avaliar_txt in ['avaliar', 'iniciar']:
                botao_avaliar.click()
                sleep(1)
                continue
            elif botao_avaliar_txt == 'estou pronto' and not clicked:
                botao_avaliar.click()
                clicked = True
                continue
            avaliar_title = drv.find_element(
                By.XPATH,
                '/html/body/div[1]/div[1]/div[1]/div/div/div[2]/div[2]/div/div[1]/h4[1]'
            )
            if avaliar_title.text.lower() == 'avaliar':
                botao_stop.click()
                sleep(3)
                continue

        except NoSuchElementException:
            pass
        except Exception:
            continue

        try:
            letra_element = drv.find_element(
                By.XPATH,
                '/html/body/div[1]/div[1]/div[1]/div/div/div[1]/div[2]/div[2]/div/ul/li[1]/span'
            )
            letra = letra_element.text.lower()
            if letra == '':
                sleep(3)
                continue
            else:
                clicked = False

            for i in range(1, 13):
                location = f'/html/body/div[1]/div[1]/div[1]/div/div/div[2]/div[2]/div/div[1]'
                inp = drv.find_element(By.XPATH, f'{location}/label[{i}]/input')
                text = drv.find_element(By.XPATH, f'{location}/label[{i}]').text
                text = unidecode(text).lower()

                if inp.get_attribute('value') != '':
                    continue

                try:
                    lista_de_valores = response_dict[letra][text]
                    value = random.choice(lista_de_valores)
                    inp.send_keys(value)
                except Exception:
                    continue

        except NoSuchElementException:
            sleep(3)
        except Exception as e:
            pass
        finally:
            if response_msg != '':
                response_msg = ''
            try:
                file_content = check_chat_file_content(c_file)
                if not file_content == last_chat_comment:
                    chat_input = drv.find_element(
                        By.XPATH,
                        '/html/body/div[1]/div[1]/div[1]/div/div/div[2]/div[3]/form/input'
                    )
                    chat_input.send_keys(file_content)
                    chat_input.send_keys(Keys.ENTER)
                    last_chat_comment = file_content
            except Exception:
                pass


if __name__ == "__main__":
    username = 'ike'
    dictionary = load_dictionary('dictionary.json')
    chat_file = 'chat.txt'

    for i in range(5):
        d = webdriver.Firefox()
        d.set_window_size(800, 600)
        d.execute_script("document.body.style.zoom='80%'")
        login(d, f'{username}{i+1}')
        Thread(target=main_game_loop, args=(d, dictionary, chat_file)).start()
        print(f'Iniciando thread {i}')
