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

user_sessions = {}

@dp.message(lambda msg:msg.text == "/start")
async def command_start_handler(message: Message,state: FSMContext) -> None:

    user = User.objects.filter(chat_id=message.chat.id)
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

@dp.message(StateFilter(Messeage.phone))
async def handle_phone_number(message: Message, state: FSMContext) -> None:
    # Check if the message contains a contact
    if message.contact:
        phone_number = message.contact.phone_number
    elif message.text and message.text.isnumeric() and len(message.text) ==13:  # If the phone number is entered as plain text
        phone_number = message.text
    else:
        await message.answer("Telefon raqamingizni Raqamni yuborish 📞 tugmasi orqali yuboring \n"
                             "yoki +998900000000 formatida kiriting: !", reply_markup=phone_number_btn())

        await state.clear()
        await state.set_state(Messeage.phone)
        return

    # Save the phone number to the user object
    user, created = User.objects.get_or_create(chat_id=message.chat.id)
    user.phone = phone_number
    user.save()

    # Clear the state
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
    orders = Installment.objects.filter(user__chat_id=msg.from_user.id, status="ACTIVE")
    ic(orders)

    # If no orders, notify the user
    if not orders.exists():
        await msg.answer("Buyurtmalar ro'yxati bo'sh.", reply_markup=menu_btn())
        return

    order_list = []
    for order in orders:
        # Extract data for each order
        price = Decimal(order.price)
        avans = Decimal(order.starter_payment)
        ustama = Decimal(order.additional_fee_percentage)
        rasrochka = order.payment_months  # Assume this field stores the number of months

        # Calculate overall and monthly payment
        overall_payment = (price - avans) + ((price - avans) * ustama / 100)
        months_payment = overall_payment / rasrochka

        # Prepare payment schedule
        payment_schedule = []
        today = datetime.today()

        # Starting point (next month, not this month)
        start_day = today.replace(day=1) + relativedelta(months=1)

        total_paid_up_to_now = Decimal(0)  # To track total payments up to the current month
        for month in range(rasrochka):
            # Calculate the payment date
            payment_date = start_day + relativedelta(months=month)

            # Total payment for the month
            monthly_payment = months_payment

            # Check if payments for this date exist
            payments_for_month = order.payments.filter(payment_date=payment_date)

            if payments_for_month.exists():
                # Sum up all payments made for this month
                total_paid = sum(payment.amount for payment in payments_for_month)
                total_paid_up_to_now += total_paid  # Accumulate payments made so far

                if total_paid >= monthly_payment:
                    # If fully paid or overpaid, use strikethrough formatting
                    payment_schedule.append(f"<s>{payment_date.strftime('%d %B %Y')}: {total_paid:.2f}$</s>")
                else:
                    # If partially paid, show the paid and unpaid amounts
                    unpaid_amount = monthly_payment - total_paid
                    payment_schedule.append(
                        f"{payment_date.strftime('%d %B %Y')}: paid - {total_paid:.2f}$, not paid - {unpaid_amount:.2f}$"
                    )
            else:
                # If no payment made, show the full amount as unpaid
                payment_schedule.append(f"{payment_date.strftime('%d %B %Y')}: {monthly_payment:.2f}$")

            # Check if payments for previous months should be fully covered
            if total_paid_up_to_now >= months_payment * (month + 1):
                # If total payments up to this month exceed or match the total required for the months before
                payment_schedule[month] = f"<s>{payment_schedule[month]}</s>"

        # Format order details
        order_details = [
            f"<b>Mijoz:</b> {order.user.full_name}",
            f"<b>Telefon raqami:</b> {order.user.phone}",
            f"<b>Mahsulot:</b> {order.product}",
            f"<b>Narxi:</b> {order.price} $",
            "\nTo'lov jadvali:\n" + "\n".join(payment_schedule),
            "\n"  # Blank line between orders
        ]
        order_list.append("\n".join(order_details))

    # Paginate orders and send messages
    chunk_size = 10  # Number of orders per message
    for i in range(0, len(order_list), chunk_size):
        chunk = "\n".join(order_list[i:i + chunk_size])
        ic(f"Sending chunk: {chunk}")  # Debugging: Log the chunk being sent
        await msg.answer(chunk, parse_mode="HTML", reply_markup=menu_btn())
