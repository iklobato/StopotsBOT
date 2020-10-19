from unidecode import unidecode
import json
import random
from time import sleep
import sys
from selenium.common.exceptions import NoSuchElementException        
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

json_file = open('dictionary.json', 'r')
lines = json_file.readlines()
lines = ''.join(lines)
json_file.close()
dictionary = json.loads(lines)

# driver = webdriver.PhantomJS(executable_path='/home/ik/Downloads/phantomjs-2.1.1-linux-x86_64 (1)/phantomjs-2.1.1-linux-x86_64/bin/phantomjs')
driver = webdriver.Firefox()
if sys.argv[1] == '0':
    driver.get(f"https://stopots.com.br/login/anonimo")
    nome_usuario = driver.find_element(By.XPATH, '//*[@id="screenHome"]/div[2]/div[1]/div[2]/input')
    nome_usuario.clear()
else:
    driver.get(f"http://stopots.com.br/{sys.argv[1]}")
    botao_jogar = driver.find_element(By.XPATH, '/html/body/header/div/div[2]/div/form/button')
    botao_jogar.click()
    nome_usuario = driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[1]/div[2]/div[2]/input')
    nome_usuario.clear()

if sys.argv[2] == '':
    nome_usuario.send_keys('Amarildinho')
nome_usuario.send_keys(sys.argv[2])

response_msg = ''

while True:
    try:
        botao_jogar = driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[1]/div/div[2]/div[2]/div[2]/button[1]/strong')
        botao_jogar.click()
        break
    except Exception:
        pass
    try:
        botao_jogar = driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[1]/div[2]/div[2]/button')
        botao_jogar.click()
        break
    except Exception:
        continue

while True:

    try:
        botao_avaliar = driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[1]/div/div/div[2]/div[2]/div/button/strong')
        botao_avaliar_txt = botao_avaliar.text
        if botao_avaliar_txt.lower() in ['avaliar', 'estou pronto', 'iniciar']:
            botao_avaliar.click()
            sleep(1)
            continue
        letra = driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[1]/div/div/div[1]/div[2]/div[2]/div/ul/li[1]/span')
        letra = letra.text.lower()
        if letra == '':
            sleep(3)
            continue
        
        something_blank = False
        for i in range(1,13):
            location = f'/html/body/div[1]/div[1]/div[1]/div/div/div[2]/div[2]/div/div[1]'
            inp = driver.find_element(By.XPATH, f'{location}/label[{i}]/input')
            text = driver.find_element(By.XPATH, f'{location}/label[{i}]').text
            text = unidecode(text).lower()
            
            try:
                # value = dictionary[letra][text][0].title()
                lista_de_valores = dictionary[letra][text]
                value = random.choice(lista_de_valores)
                if value == '': raise KeyError
                inp.send_keys(value)
            except Exception as e:
                something_blank = True
                pass
            finally:
                response_msg += f'{value}, '

        stop = driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[1]/div/div/div[2]/div[2]/div/button/strong')
        
       
        while True:
            if something_blank:
                print(f'Espaços em branco, deixando alguem aberto stop antes...')
                sleep(45)
            stop.click()
        print('Stop!')

    except NoSuchElementException as nsee:
        sleep(3)
    except Exception as e:
        pass
    finally:
        if response_msg != '':
            print(response_msg)
            response_msg = ''

driver.close()

