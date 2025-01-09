import re

from aiogram.filters import StateFilter
from aiogram.types import Message, FSInputFile

from bot.models import User
from dispatcher import dp
from tg_bot.buttons.inline import *
from tg_bot.buttons.reply import *
from tg_bot.buttons.text import *
from tg_bot.handlers.admin import *
from tg_bot.state.main import *

user_sessions = {}


@dp.message(lambda msg: msg.text == "/start")
async def command_start_handler(message: Message, state: FSMContext) -> None:
    # Check if the user exists in the database by chat_id
    user = User.objects.filter(chat_id=message.from_user.id).first()

    if not user:
        # Ask for the phone number if the user is not found
        await state.set_state(Messeage.phone)
        video = FSInputFile('tg_bot/handlers/admin/bot_vedio.mp4')
        await message.answer_video_note(
            video_note=video,
            file_id="DQACAgIAAxkBAAIIb2eAFB0AARTLyjeNmCtzx1NOIG5buAACY2kAAktnAAFIvyPCUuU1USw2BA",
            caption=f"Assalomu alaykum "
                    f"\nBotdan foydalanish uchun raqamingizni yuboring 👇🏿",
            parse_mode="HTML",
            duration=51,
            length=384,
            reply_markup=phone_number_btn(),
        )
    else:
        # If the user exists, check their role
        if user.role == "ADMIN":
            await message.answer("Admin menusi:", reply_markup=admin_btn())
        else:
            await message.answer(
                text=f"Assalomu alaykum "
                     f"\nBuyruqlardan birini tanlang 👇🏿",
                parse_mode="HTML",
                reply_markup=menu_btn()
            )


@dp.message(StateFilter(Messeage.phone))
async def handle_phone_number(message: Message, state: FSMContext) -> None:
    # Extract the phone number
    if message.contact:
        phone_number = message.contact.phone_number
        phone_number = format_phone_number(phone_number)
    elif message.text and re.match(r"^\+\d{9,13}$", message.text):
        phone_number = message.text
    else:
        await message.answer(
            "Telefon raqamingizni Raqamni yuborish 📞 tugmasi orqali yuboring \n"
            "yoki +998900000000 formatida kiriting: !",
            reply_markup=phone_number_btn()
        )
        return

    try:
        # Check if the phone number already exists in the database
        user = User.objects.filter(phone=phone_number).first()
        if user:
            # Update the user's chat_id
            user.chat_id = message.from_user.id
            user.save()
        else:
            # Create a new user with the provided phone number
            User.objects.create(
                chat_id=message.from_user.id,
                phone=phone_number,
                full_name=message.from_user.full_name
            )

        # Clear the state and show the menu based on the user's role
        await state.clear()

        user = User.objects.get(chat_id=message.from_user.id)  # Get the updated user
        if user.role == "ADMIN":
            await message.answer("Admin menusi:", reply_markup=admin_btn())
        else:
            await message.answer(
                text=f"Rahmat! Telefon raqamingiz muvaffaqiyatli saqlandi: 👇🏿 \n<b>{phone_number}</b>",
                parse_mode="HTML",
                reply_markup=menu_btn()
            )
    except Exception as e:
        print(f"Error: {e}")
        await message.answer("Xatolik yuz berdi. Iltimos qayta urinib ko'ring.")


@dp.message(lambda msg: msg.text == orders_list_txt)
async def paginate_orders(msg: Message, state: FSMContext) -> None:
    try:
        # Fetch the user by chat_id
        user = User.objects.filter(chat_id=msg.from_user.id).first()
        if not user:
            await msg.answer("Telefon raqamingiz aniqlanmadi. Iltimos, qaytadan ro'yxatdan o'ting.",
                             reply_markup=start_btn())
            return

        # Fetch active orders for the user
        orders = Installment.objects.filter(user=user, status="ACTIVE")

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
            today = order.next_payment_dates
            start_day = today.replace(day=1) + relativedelta(months=1)

            applied_payments = Decimal(0)
            for month in range(installment_period):
                payment_date = start_day + relativedelta(months=month)
                expected_payment = last_month_payment if month == installment_period - 1 else rounded_monthly_payment

                # Determine payment status
                if applied_payments + expected_payment <= total_paid:
                    payment_schedule.append(f"{payment_date.strftime('%d %B %Y')}: {expected_payment:.2f}$ ✅")
                    applied_payments += expected_payment
                elif applied_payments < total_paid:
                    paid_for_month = total_paid - applied_payments
                    payment_schedule.append(
                        f"{payment_date.strftime('%d %B %Y')}: {expected_payment:.2f}$ 🟢 ({paid_for_month:.2f}$ paid)"
                    )
                    applied_payments += paid_for_month
                else:
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
        chunk_size = 10
        for i in range(0, len(order_list), chunk_size):
            chunk = "\n".join(order_list[i:i + chunk_size])
            await msg.answer(chunk, parse_mode="HTML", reply_markup=menu_btn())
    except Exception as e:
        print(f"Error: {e}")
        await msg.answer("Xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.", reply_markup=menu_btn())
