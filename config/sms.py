import hashlib
import os
from random import randint
from sys import stderr
import time

from dotenv import load_dotenv
from icecream import ic
from requests import post

load_dotenv()

class SayqalSms:
    def __init__(self):
        self.username = os.getenv("SAYQAL_USERNAME")
        self.token = os.getenv("SAYQAL_TOKEN")

        assert (
            self.username is not None
        ), "Environment variable SAYQAL_USERNAME is not set"

        assert self.token is not None, "Environment variable SAYQAL_TOKEN is not set"

        self.url = "https://routee.sayqal.uz/sms/"

    def generateToken(self, method: str, utime: int):

        access = f"{method} {self.username} {self.token} {utime}"
        token = hashlib.md5(access.encode()).hexdigest()

        return token

    def fixNumber(self, number: str):
        if number.startswith("+"):
            return number[1:]

    def send_sms(self, number: str, message: str):

        utime = int(time.time())

        token = self.generateToken("TransmitSMS", utime)

        number = self.fixNumber(
            number,
        )
        print(number, file=stderr)

        url = self.url + "TransmitSMS"
        data = {
            "utime": utime,
            "username": self.username,
            "service": {"service": 1},
            "message": {
                "smsid": randint(111111, 999999),
                "phone": number,
                "text": message,
            },
        }

        response = post(url, json=data, headers={"X-Access-Token": token})

        ic(response)
        ic("Sms response", data, response.json())

        return response.json()


def send_sms1(phone_number, message):
    sms_service = SayqalSms()
    sms_service.send_sms(
        message=message,
        number=phone_number
    )

active = [
"998977007109",
"+998977130280",
"+998998958558",
"+998990307995",
"+998931023234",
"+998973431462",
"+998991481222",
"+998935697979",
"+998935976055",
"+998977830201",
"+998991990087",
"+998998826267",
"+998991747762",
"+998974505771",
"+998946068939",
"+998886330124"
]
active1 = ["+998948025101","+998886330124"]
for i in active:
    send_sms1(phone_number=i, message=f"Assalomu alaykum, xurmatli mijoz!\n"
"https://t.me/ab_nasiya_bot botini ishga tushirdik."
"Ushbu bot orqali to'lov va qarzlaringiz holatini real vaqtda nazorat qilishingiz mumkin. "
"To'liq ma'lumot uchun: +998901740280 (Alisher Sharabaev)")