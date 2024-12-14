from datetime import date, datetime
from decimal import Decimal, ROUND_CEILING
from pyexpat.errors import messages

from aiogram.fsm.context import FSMContext
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent, CallbackQuery, Message
from asgiref.sync import sync_to_async
from dateutil.relativedelta import relativedelta

from icecream import ic

from bot.models import User, Installment, Payment
from dispatcher import dp
from sms import SayqalSms
from tg_bot.buttons.inline import  reply_payment
from tg_bot.buttons.reply import admin_btn, back
from tg_bot.buttons.text import *
from tg_bot.handlers.admin.add_payment import start_payment, inline_search_handler
from tg_bot.state.main import *
from tg_bot.test import process_monthly_payment
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup


@dp.message(lambda message:message.text == orders_txt)
async def list_customers(message: Message, state: FSMContext):
    await state.set_state(PaymentFlow.customer_selection)

    # Create the button
    button = InlineKeyboardButton(
        text="Qidirish 🔍",  # Button text
        switch_inline_query_current_chat=""
        # This will be used to handle the button press
    )

    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[[button]])
    await message.answer("Mijozni tanlang yoki qidiring:",
                         reply_markup=inline_keyboard)


from django.db.models import Q
@dp.inline_query()
async def search_customers(inline_query: InlineQuery):
    query = inline_query.query.strip()
    results = []

    # Search for users based on query
    installments = await sync_to_async(Installment.objects.filter)(
        (Q(user__full_name__incontains=query) | Q(user__phone__icontains=query)) & Q(status="ACTIVE")
    )

    for user in installments:
        ic(user.id)
        results.append(
            InlineQueryResultArticle(
                id=str(user.id),
                title=f"{user.full_name} ({user.phone})",
                input_message_content=InputTextMessageContent(
                    message_text=f"Tanlangan mijoz:\nID: {user.id} \n{user.full_name} ({user.phone})"
                ),
                description="Mijoz haqida ma'lumotni ko'rish"
            )
        )
    await inline_query.answer(results, cache_time=0, is_personal=True)



@dp.message(PaymentFlow.customer_selection)
async def handle_customer_selection(message: Message, state: FSMContext):
    if message.text == ortga:
        await message.answer("Qidiruv bekor qilindi!", reply_markup=admin_btn())
        await state.clear()
        return
    # ic(message.text.split())
    # user_id = message.text.split()[3]
    # ic(user_id)
    parts = message.text.split()  # Split the text into a list

    # Find the index of "Phone:" and get the next value
    if "ID:" in parts:
        phone_index = parts.index("ID:")  # Find the index of "Phone:"
        user_id:int = parts[phone_index + 1]

    try:
        orders = Installment.objects.filter(user_id=user_id,status="ACTIVE")
        if not orders.exists():
            await message.answer("Buyurtmalar topilmadi.", reply_markup=admin_btn())
            await state.clear()
            return
        sorted_orders = sorted(orders, key=lambda x: x.product.lower())  # Sort by product name, case insensitive
    except Exception as e:
        await message.answer(str(e), reply_markup=admin_btn())
        await state.clear()
        return
    page_size = 10
    page = 1
    start = (page - 1) * page_size
    end = page * page_size
    orders_page = sorted_orders[start:end]

    order_details_list = []
    for order in orders_page:
        # Extract order details
        customer_name = order.user.full_name
        phone_number = order.user.phone
        products = order.product
        product_price = Decimal(order.price)
        starter_payment = Decimal(order.starter_payment)
        installment_period = order.payment_months
        interest_rate = Decimal(order.additional_fee_percentage)

        foiz_miqdori = product_price *(interest_rate/100)

        # Calculate overall payment
        overall_price = (product_price - starter_payment) + ((product_price - starter_payment) * interest_rate / 100)
        total_paid = sum(p.amount for p in order.payments.all())
        remaining_balance = overall_price - total_paid

        # Calculate monthly payments
        base_monthly_payment = overall_price / installment_period
        rounded_monthly_payment = base_monthly_payment.quantize(Decimal('1'), rounding=ROUND_CEILING)
        last_month_payment = overall_price - rounded_monthly_payment * (installment_period - 1)


        payment_schedule = []
        applied_payments = Decimal(0)
        start_day = order.start_date

        for month in range(installment_period):
            payment_date = start_day + relativedelta(months=month)

            # Determine the expected payment for this month
            expected_payment = last_month_payment if month == installment_period - 1 else rounded_monthly_payment

            if applied_payments + expected_payment <= total_paid:
                # Fully paid month
                payment_status = "✅"
                applied_payments += expected_payment
            elif applied_payments < total_paid:
                # Partially paid month
                remaining_for_month = total_paid - applied_payments
                payment_status = f"🟢 ({remaining_for_month:.2f} $ paid)"
                applied_payments += remaining_for_month
            else:
                # Unpaid month
                payment_status = "❗️"

            # Add to payment schedule
            payment_schedule.append(
                f"{payment_date.strftime('%d.%m.%Y')}: {expected_payment:.2f}$ {payment_status}"
            )
        # Append order details
        order_details = (
                f"<b>Mijoz ismi:</b>  {customer_name}\n"
                f"<b>Telefon raqami:</b>  {phone_number}\n"
                f"<b>Mahsulotlar:</b>  {products}\n"
                f"<b>Mahsulot tan narxi:</b>  {product_price:.2f} $\n"
                f"<b>Boshlang'ich to'lov:</b>  {starter_payment:.2f} $\n"
                f"<b>Rasrochka muddati:</b>  {installment_period} oylik\n"
                f"<b>Qo'shilgan foiz:</b>  {interest_rate:.2f} %\n"
                f"<b>To'lov qilish sanasi har oyning:</b>  {start_day.day} da\n\n"
                f"<b>To'liq summa :</b>  {product_price+starter_payment+foiz_miqdori:.2f} $\n"
                f"<b>Qo'shilgan foiz miqdori:</b>  {foiz_miqdori:.2f} $\n"
                f"<b>Jami ustama bilan hisoblangan narx:</b>  {overall_price:.2f}$\n"
                f"<b>Qolgan to'lov miqdori:</b>  {remaining_balance:.2f}$\n\n"
                f"<b>To'lov jadvali:</b>\n" + "\n".join(payment_schedule)
        )
        order_details_list.append(order_details)

    for order_details in order_details_list:
        await message.answer(order_details, parse_mode="HTML", reply_markup=reply_payment(order))
    await message.answer("Buyurtmalar ...", reply_markup=back())
    await state.update_data(user_id=user_id)
    await state.set_state(PaymentFlow.order_selection)

@dp.message(PaymentFlow.order_selection)
async def handle_order_message(msg: Message, state: FSMContext):
    # Process the reply message (e.g., user sends a text)
    if msg.text == ortga:
        await msg.answer(f"Admin menu: ",reply_markup=admin_btn())
        await state.clear()
        return

@dp.callback_query(PaymentFlow.order_selection)
async def handle_order_selection(callback_query: CallbackQuery, state: FSMContext):
    ic(callback_query.data)
    if callback_query.data == ortga:
        data = await state.get_data()
        user_id = data.get("user_id")
        ic(user_id)

        await callback_query.message.edit_reply_markup(reply_markup=None)
        await callback_query.answer(text="admin menu:",reply_markup=admin_btn())
        await state.clear()
        return


    await callback_query.message.edit_reply_markup(reply_markup=None)
    ic(callback_query.data.split(":"))
    order_id = int(callback_query.data.split(":")[1])

    await state.update_data(order_id=order_id)

    await callback_query.message.answer("To'lov miqdorini kiriting $ qiymatida:")
    await state.set_state(PaymentFlow.enter_amount)



@dp.message(PaymentFlow.enter_amount)
async def handle_payment_amount(message: Message, state: FSMContext):
    if message.text == ortga:
        await state.set_state(PaymentFlow.enter_amount)
        await message.answer("To'lov miqdorini qayta kiriting $ qiymatida:", reply_markup=back())
        return

    amount = message.text.strip()
    data = await state.get_data()
    order_id = data.get("order_id")

    try:
        amount = float(amount)
        installment = await sync_to_async(Installment.objects.get)(id=order_id)
        payment = await sync_to_async(Payment.objects.create)(
            user=installment.user,
            installment=installment,
            payment_date=date.today(),
            amount=amount,
        )

        total_paid = sum(p.amount for p in installment.payments.all())
        remaining_balance = installment.calculate_overall_price() - total_paid
        remaining_balance = round(remaining_balance,1)

        if remaining_balance <= 0:
            installment.update_status()
            await message.answer(f"Mijoz qarizdorligi yakunlandi")
            user_chat_id = installment.user.chat_id
            if user_chat_id:
                await message.bot.send_message(
                    chat_id=installment.user.chat_id,
                    text=f"Qarizdorlik yakunlandi!"
                )
            else:
                await message.answer("BU mijoz hali botdan foydalangani yo'q habarnoma sms orqali yuborildi!", reply_markup=admin_btn())
            # sms_service = SayqalSms()
            # sms_service.send_sms(
            #     message="Qarizdorlik yakunlandi",
            #     number=installment.user.phone
            # )


        process_monthly_payment(
            user=installment.user,
            order_id=order_id,
            amount=amount,
        )
        user_chat_id = installment.user.chat_id
        ic(user_chat_id)
        if user_chat_id:
            await message.answer(
                f"To'lov qo'shildi: {amount} dollar.\nQolgan to'lov miqdori: {remaining_balance} dollar.",
                reply_markup=admin_btn()
            )
            message = await message.bot.send_message(
                chat_id=installment.user.chat_id,
                text=f"To'lov qo'shildi: {amount} dollar."
                     f"\nQolgan to'lov miqdori: "
                     f"{remaining_balance} dollar."
            )
        else:
            await message.answer(
                f"To'lov qo'shildi: {amount} dollar.\nQolgan to'lov miqdori: {remaining_balance} dollar.",
                reply_markup=admin_btn()
            )
            await message.answer("BU mijoz hali botdan foydalangani yo'q", reply_markup=admin_btn())

        # sms_service=SayqalSms()
        # sms_service.send_sms(
        #     message=f"To'lov qo'shildi: {amount} dollar.\n"
        #             f"Qolgan to'lov miqdori: {remaining_balance} dollar.",
        #     number="+998908175047"
        # )

        await state.clear()
    except ValueError:
        await message.answer("To'lov miqdori noto'g'ri formatda. Iltimos, raqam kiriting.")
    except Exception as e:
        print(
            f"Xatolik yuz berdi. Qaytadan urinib ko'ring.\n {str(e)}"
        )