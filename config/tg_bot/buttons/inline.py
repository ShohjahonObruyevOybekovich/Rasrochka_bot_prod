from aiofiles.os import access

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from asgiref.sync import sync_to_async
from bot.models import Installment



def accept():
    payment_date = InlineKeyboardButton(text="✏️ Sanani o'zgartirish", callback_data="Sanani o'zgartirish")
    accept = InlineKeyboardButton(text="✅ Buyurtmani tasdiqlash", callback_data="accepted")
    cancel = InlineKeyboardButton(text = "🗑 Buyurtmani bekor qilish", callback_data="cancelled")
    return InlineKeyboardMarkup(inline_keyboard=[[accept], [payment_date],[cancel]])



def excel():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Excel",callback_data="Excel")]
    ])
    return keyboard

# def reply_payment(order):
#     callback_data = f"payment_adding:{order.id}"
#     keyboard = InlineKeyboardMarkup(inline_keyboard=[
#         [InlineKeyboardButton(text="To'lov qo'shish",callback_data=callback_data)]])
#     return keyboard

def reply_payment(order):
    keyboard = InlineKeyboardButton(text="To'lov qo'shish",callback_data=f"payment_adding:{order.id}")
    keyboard2 = InlineKeyboardButton(text="Foizini o'zgartirish",callback_data=f"edit_fee:{order.id}")
    keyboard3 = InlineKeyboardButton(text="Buyurtmani bekor qilish",callback_data=f"cancelled:{order.id}")
    return InlineKeyboardMarkup(inline_keyboard=[[keyboard],[keyboard2],[keyboard3]])