from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from bot.models import Category
from tg_bot.buttons.text import *



def menu_btn():
    k2 = KeyboardButton(text = orders_list_txt)
    design = [
        [k2],
    ]
    return ReplyKeyboardMarkup(keyboard=design , resize_keyboard=True)

def phone_number_btn():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text = "Raqamni yuborish 📞",
                                                         request_contact=True) ]] ,
                               resize_keyboard=True)

def Login():
    keyboard1 = KeyboardButton(text = Login_txt)
    design = [[keyboard1]]
    return ReplyKeyboardMarkup(keyboard=design , resize_keyboard=True)



def admin_btn():
    keyboard1 = KeyboardButton(text = order_history_txt)
    keyboard2 = KeyboardButton(text = orders_txt)
    keyboard3 = KeyboardButton(text=add_order)
    keyboard4 = KeyboardButton(text=next_payments)
    keyboard6 = KeyboardButton(text=statistic_txt)
    keyboard5 = KeyboardButton(text=back_to_user)

    design = [[keyboard1, keyboard2],
              [keyboard3, keyboard4],
              [keyboard6,keyboard5]]
    return ReplyKeyboardMarkup(keyboard=design ,
                               resize_keyboard=True)


def skip():
    keyboard1 = KeyboardButton(text = "O'tkazib yuborish ➡️")
    keyboard2 = KeyboardButton(text = ortga)
    design = [[keyboard1],[keyboard2]]
    return ReplyKeyboardMarkup(keyboard=design , resize_keyboard=True)


def category():
    category = Category.objects.all()
    category_keyboard = [[KeyboardButton(text=ct.name)] for ct in category]
    back = [KeyboardButton(text=ortga)]
    category_keyboard.append(back)
    return ReplyKeyboardMarkup(keyboard=category_keyboard, resize_keyboard=True)



def back():
    keyboard1 = KeyboardButton(text = ortga)
    design = [[keyboard1]]
    return ReplyKeyboardMarkup(keyboard=design , resize_keyboard=True)

def months():
    uch_oy = KeyboardButton(text='3 oylik')
    olti_oy = KeyboardButton(text='6 oylik')
    toqqiz_oy  = KeyboardButton(text='12 oylik')
    yigirma_turt = KeyboardButton(text='24 oylik')
    back = KeyboardButton(text=ortga)
    design = [[uch_oy, olti_oy],[toqqiz_oy,yigirma_turt],[back]]
    return ReplyKeyboardMarkup(keyboard=design , resize_keyboard=True)

def start_btn():
    start = KeyboardButton(text = "start")
    return ReplyKeyboardMarkup(keyboard=[[start]] , resize_keyboard=True)

def back_admin():
    keyboard1 = KeyboardButton(text = "Admin menu:")
    design = [[keyboard1]]
    return ReplyKeyboardMarkup(keyboard=design , resize_keyboard=True)