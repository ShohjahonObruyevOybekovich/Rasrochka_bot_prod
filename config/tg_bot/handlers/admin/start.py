from datetime import datetime
from decimal import Decimal
from pyexpat.errors import messages

from aiogram.filters import CommandStart, StateFilter
from aiogram.types import Message, CallbackQuery
from dateutil.relativedelta import relativedelta
from icecream import ic
from tg_bot.handlers.admin import *
from bot.models import User
from dispatcher import dp
from tg_bot.buttons.inline import *
from tg_bot.buttons.reply import *
from tg_bot.buttons.text import *
from tg_bot.state.main import *
from aiogram import F
user_sessions = {}

@dp.message(lambda msg:msg.text == "/start")
async def command_start_handler(message: Message,state: FSMContext) -> None:

    user = User.objects.filter(chat_id=message.from_user.id)
    if not user:
        await state.set_state(Messeage.phone)
        await message.answer(
            text=f"Assalomu alaykum <b><i>{message.from_user.username}</i></b> "
                 f"\nBotdan foydalanish uchun raqamingizni yuboring 👇🏿",
            parse_mode="HTML",  # Enable HTML parsing
            reply_markup=phone_number_btn()
        )
    else:
        role = user.filter(role="ADMIN")
        if role:
            await message.answer("Admen menusi :",reply_markup=admin_btn())
        else:
            await message.answer(
                text=f"Assalomu alaykum <b><i>{message.from_user.username}</i></b> "
                     f"\nBuyruqlardan birini tanlang 👇🏿",

                parse_mode="HTML",  # Enable HTML parsing
                reply_markup=menu_btn()
            )
# @dp.message(F.text.regexp(r"^\+\d{9,13}$"))
# async def phone_number_handler(msg: Message):
#     phone = format_phone_number(msg.text)
#     await msg.answer(phone)

from aiogram.types import ContentType
import re

# @dp.message(StateFilter(Messeage.phone), content_types=[ContentType.TEXT, ContentType.CONTACT])
# async def handle_phone_number(msg: Message, state: FSMContext) -> None:
#     if msg.content_type == ContentType.CONTACT:  # When the user shares contact via button
#         phone_number = msg.contact.phone_number
#     elif msg.content_type == ContentType.TEXT:  # When the user manually types their phone number
#         if not re.match(r"^\+\d{9,13}$", msg.text):  # Validate manually entered phone number
#             await msg.answer("Telefon raqami noto'g'ri formatda. Iltimos, +998901234567 kabi yuboring.")
#             return
#         phone_number = msg.text
#     else:
#         await msg.answer("Iltimos, telefon raqamingizni to'g'ri formatda kiriting yoki yuboring.")
#         return
#
#     # Save the phone number to the database (example with Django ORM)
#     user, created = User.objects.get_or_create(chat_id=msg.chat.id)
#     user.phone_number = phone_number
#     user.save()
#
#     await state.clear()  # Clear the state as the phone number is now handled
#     await msg.answer("Raqamingiz qabul qilindi!", reply_markup=menu_btn())


@dp.message(StateFilter(Messeage.phone))
async def handle_phone_number(message: Message, state: FSMContext) -> None:
    # Check if the message contains a contact

    if message.contact:
        phone_number = format_phone_number(message.contact.phone_number)
        ic(message.text)
    elif message.text and message.text.isnumeric() and len(message.text) ==13:  # If the phone number is entered as plain text
        phone_number = format_phone_number(message.text)
    else:
        await message.answer("Telefon raqamingizni Raqamni yuborish 📞 tugmasi orqali yuboring \n"
                             "yoki +998900000000 formatida kiriting: !", reply_markup=phone_number_btn())

        await state.clear()
        await state.set_state(Messeage.phone)
        return

    # Save the phone number to the user object
    user = User.objects.create(chat_id=message.from_user.id, phone=phone_number,full_name=message.from_user.full_name)

    await state.clear()



    # Respond to the user based on their role
    if user.role == "ADMIN":
        await message.answer("Admin menusi:", reply_markup=admin_btn())
    else:
        await message.answer(
            text=f"Rahmat! Telefon raqamingiz muvaffaqiyatli saqlandi: 👇🏿 \n<b>{phone_number}</b>",
            parse_mode="HTML",
            reply_markup=menu_btn()
        )



@dp.message(lambda msg: msg.text == orders_list_txt)
async def paginate_orders(msg: Message, state: FSMContext) -> None:
    # Fetch active orders for the user
    orders = Installment.objects.filter(user__chat_id=msg.from_user.id, status="ACTIVE")

    # If no orders, notify the user
    if not orders.exists():
        await msg.answer("Buyurtmalar ro'yxati bo'sh.", reply_markup=menu_btn())
        return

    order_list = []  # To hold details for all orders
    for order in orders:
        # Extract order details
        price = Decimal(order.price)
        starter_payment = Decimal(order.starter_payment)
        interest_rate = Decimal(order.additional_fee_percentage)
        installment_period = order.payment_months
        total_paid = sum(payment.amount for payment in order.payments.all())

        # Calculate overall payment and monthly payments
        overall_payment = (price - starter_payment) + ((price - starter_payment) * interest_rate / 100)
        base_monthly_payment = overall_payment / installment_period
        rounded_monthly_payment = base_monthly_payment.quantize(Decimal('1'), rounding=ROUND_CEILING)
        last_month_payment = overall_payment - rounded_monthly_payment * (installment_period - 1)

        # Start building the payment schedule
        payment_schedule = []
        today = datetime.today()
        start_day = today.replace(day=15) + relativedelta(months=1)  # Assume payments are due on the 15th

        applied_payments = Decimal(0)  # To track payments applied across months
        for month in range(installment_period):
            payment_date = start_day + relativedelta(months=month)

            # Determine expected payment
            expected_payment = last_month_payment if month == installment_period - 1 else rounded_monthly_payment

            # Determine the status of payments for this month
            if applied_payments + expected_payment <= total_paid:
                # Fully paid month
                payment_schedule.append(f"{payment_date.strftime('%d %B %Y')}: {expected_payment:.2f}$ ✅")
                applied_payments += expected_payment
            elif applied_payments < total_paid:
                # Partially paid month
                paid_for_month = total_paid - applied_payments
                payment_schedule.append(
                    f"{payment_date.strftime('%d %B %Y')}: {expected_payment:.2f}$ 🟢 ({paid_for_month:.2f}$ paid)"
                )
                applied_payments += paid_for_month
            else:
                # Unpaid month
                payment_schedule.append(f"{payment_date.strftime('%d %B %Y')}: {expected_payment:.2f}$ ❗️")

        # Format order details
        order_details = [
            f"<b>Mijoz:</b> {order.user.full_name}",
            f"<b>Telefon raqami:</b> {order.user.phone}",
            f"<b>Mahsulot:</b> {order.product}",
            f"<b>Narxi:</b> {price:.2f}$",
            f"<b>Boshlang'ich to'lov:</b> {starter_payment:.2f}$",
            f"<b>To'lanishi lozim bo'lgan to'lov miqdori:</b> {overall_payment:.2f}$",
            f"<b>Qolgan to'lov:</b> {overall_payment - total_paid:.2f}$",
            "\n<b>To'lov jadvali:</b>\n" + "\n".join(payment_schedule),
            "\n"
        ]
        order_list.append("\n".join(order_details))

    # Paginate orders and send messages
    chunk_size = 10  # Number of orders per message
    for i in range(0, len(order_list), chunk_size):
        chunk = "\n".join(order_list[i:i + chunk_size])
        await msg.answer(chunk, parse_mode="HTML", reply_markup=menu_btn())


