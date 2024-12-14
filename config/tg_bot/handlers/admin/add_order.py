from pyexpat.errors import messages

from aiogram.enums import ContentType
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiohttp.hdrs import CONTENT_TYPE
from asgiref.sync import sync_to_async
from dateutil.relativedelta import relativedelta
from icecream import ic
from pydantic.types import AnyType

from bot.models import User, Installment
from dispatcher import dp
from sms import SayqalSms
from tg_bot.buttons.inline import  accept
from tg_bot.buttons.reply import menu_btn, skip, back, admin_btn,months
from tg_bot.buttons.text import *
from tg_bot.state.main import *
from datetime import datetime
import calendar

from tg_bot.test import format_phone_number


# Start of adding an order
@dp.message(lambda msg: msg.text == add_order)
async def command_start_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(Add_order.phone)
    await message.answer(text="Mijoz raqamini yuboring +998123456789 formarida:",reply_markup=back())


@dp.message(Add_order.phone)
async def phone_handler(msg: Message, state: FSMContext) -> None:
    if msg.text == ortga:
        await state.clear()
        await msg.answer("Buyurtma qo'shish bekor qilindi.", reply_markup=admin_btn())
        return

    # Check if the message contains only letters (invalid phone input)
    if msg.text.isalpha():
        await msg.answer("Mijoz raqamini yuboring +998123456789 formarida:")
        await state.clear()
        await state.set_state(Add_order.phone)
        return

    # Check if the phone number has a valid length (13 digits or a valid international format

    # Format the phone number if it's valid
    phone = format_phone_number(msg.text)

    # Get the current state data and update the phone field
    data = await state.get_data()
    data["phone"] = phone

    # Update the state with the corrected phone number
    await state.set_data(data)


    user = await sync_to_async(User.objects.filter(phone=phone).first)()
    if user:
        await state.set_state(Add_order.product_name)
        await msg.answer("Mahsulotlar nomini kiriting:", reply_markup=back())
    else:
        await state.set_state(Add_order.user_name)
        await msg.answer("Mijoz ismini kiriting:", reply_markup=back())



@dp.message(Add_order.user_name)
async def user_name_handler(message: Message, state: FSMContext) -> None:
    if message.text == ortga:
        await state.set_state(Add_order.phone)
        await message.answer("Mijoz raqamini qaytadan yuboring:", reply_markup=back())
        return

    data = await state.get_data()
    data['user_name'] = message.text
    await state.set_data(data)
    User.objects.create(full_name=data['user_name'],
                            phone=data['phone'])
    await state.set_state(Add_order.product_name)
    await message.answer("Mahsulotlar ro'yxatini kiriting:", reply_markup=back())


# Handle product name input
@dp.message(Add_order.product_name)
async def product_name_handler(message: Message, state: FSMContext) -> None:
    if message.text == ortga:
        await state.set_state(Add_order.user_name)
        await message.answer("To'liq ismingizni qaytadan kiriting:", reply_markup=back())
        return

    data = await state.get_data()
    data['product_name'] = message.text
    await state.set_data(data)

    await state.set_state(Add_order.product_price)
    await message.answer("Buyurtmaning tan narxini kiriting $ hisobida:", reply_markup=back())


# Handle product price input
@dp.message(Add_order.product_price)
async def product_price_handler(message: Message, state: FSMContext) -> None:
    if message.text == ortga:
        await state.set_state(Add_order.product_name)
        await message.answer("Mahsulotlar ro'yxatini qaytadan kiriting:", reply_markup=back())
        return
    if message.text.isalpha() or message.text.endswith("$") or message.text.startswith("$"):
        await message.answer("Buyurtmaning tan narxini $ hisobida faqat sonlar bilan kiriting !")
        await state.set_state(Add_order.product_price)
        return

    data = await state.get_data()
    data["product_price"] = message.text
    await state.set_data(data)

    await state.set_state(Add_order.avans)
    await message.answer("Boshlang'ich to'lovni $ hisobida kiriting yoki o'tkazib yuborish tugmasini bosing:", reply_markup=skip())


@dp.message(Add_order.avans)
async def avans_handler(message: Message, state: FSMContext) -> None:
    if message.text == ortga:
        await state.set_state(Add_order.product_price)
        await message.answer("Buyurtma narxini qaytadan kiriting:", reply_markup=back())
        return

    if (message.text.isalpha() or message.text.startswith('$') or message.text.endswith("$")
            and (message.text != "O'tkazib yuborish ➡️" or message.text != ortga )):
        await message.answer("Boshlang'ich to'lovni faqat raqamlar bilan $ hisobida kiriting !")
        await state.set_state(Add_order.avans)
        return


    data = await state.get_data()
    data['avans'] = message.text if message.text != "O'tkazib yuborish ➡️" else '0'
    await state.set_data(data)

    await state.set_state(Add_order.rasrochka_vaqti)
    await message.answer('Rasrochka oylarini kiriting:', reply_markup=months())


@dp.message(Add_order.rasrochka_vaqti)
async def rasrochka_handler(msg: Message, state: FSMContext) -> None:
    if msg.text == ortga:
        await state.set_state(Add_order.avans)
        await msg.answer("Boshlang'ich to'lovni qaytadan kiriting $ hisobida yoki o'tkazib yuborish tugmasini bosing:", reply_markup=skip())
        return

    data = await state.get_data()
    data['rasrochka_muddati'] = msg.text
    await state.set_data(data)

    await state.set_state(Add_order.ustama)
    await msg.answer("Ustama foizini kiriting:", reply_markup=back())



from decimal import Decimal, ROUND_CEILING, ROUND_UP


@dp.message(Add_order.ustama)
async def ustama_handler(message: Message, state: FSMContext) -> None:
    if message.text == ortga:
        await state.set_state(Add_order.rasrochka_vaqti)
        await message.answer("Bo'lib to'lash muddatini qaytadan kiriting:",
                             reply_markup=months())
        return

    data = await state.get_data()
    data['ustama'] = message.text
    await state.set_data(data)

    if not message.text.isdigit():
        await message.answer("Bo'lib to'lash ustama foizini to'g'ri faqat raqam orqali kiriting:")
        await state.set_state(Add_order.ustama)
        return

    mijoz = ""
    if data.get("user_name") is None:
        user = User.objects.filter(phone=data.get("phone")).first()
        if user:
            mijoz += user.full_name
    else:
        mijoz += data.get("user_name")

    try:
        price = Decimal(data.get("product_price", 0))
        avans = Decimal(data.get("avans", 0))
        ustama = Decimal(data.get("ustama", 0))
        rasrochka_muddati_txt = data.get('rasrochka_muddati', '0').split(' ')[0]
        rasrochka_months = int(rasrochka_muddati_txt)

        if price <= 0 or rasrochka_months <= 0:
            await message.answer("To'lov ma'lumotlari to'g'ri kiritilmagan. Iltimos, qaytadan kiriting.",
                                 reply_markup=admin_btn())
            await state.clear()
            return

        # Calculate overall payment with the fee
        overall_payment = (price - avans) + ((price - avans) * ustama) / 100

        # Calculate monthly payments
        base_monthly_payment = overall_payment / rasrochka_months
        rounded_monthly_payment = base_monthly_payment.quantize(Decimal('1'), rounding=ROUND_CEILING)
        last_month_payment = overall_payment - rounded_monthly_payment * (rasrochka_months - 1)

        # Prepare payment schedule for each month
        payment_schedule = []
        today = datetime.today()
        start_day = today.replace(day=1) + relativedelta(months=1)

        for month in range(rasrochka_months):
            month_num = (start_day.month + month - 1) % 12 + 1
            year_adjustment = (start_day.month + month - 1) // 12
            payment_date = start_day.replace(year=start_day.year + year_adjustment, month=month_num, day=today.day)

            if month == rasrochka_months - 1:
                payment_schedule.append(f"{payment_date.strftime('%d %B %Y')}: {last_month_payment:.2f}$")
            else:
                payment_schedule.append(f"{payment_date.strftime('%d %B %Y')}: {rounded_monthly_payment:.2f}$")

        # Prepare confirmation message
        datas = [
            f"<b>Mijoz ismi:</b> {mijoz}",
            f"<b>Telefon raqami:</b> {data.get('phone', 'N/A')}",
            f"<b>Mahsulotlar:</b> {data.get('product_name', 'N/A')}",
            f"<b>Mahsulot tan narxi:</b> {data.get('product_price', 'N/A')} $",
            f"<b>Boshlang'ich to'lov:</b> {data.get('avans', 'N/A')} $",
            f"<b>Rasrochka muddati:</b> {data.get('rasrochka_muddati', 'N/A')}",
            f"<b>Qo'shilgan foiz:</b> {data.get('ustama', 'N/A')} %",
            f"<b>To'lov qilish sanasi har oyning:</b> {today.strftime('%d')} chi sanasida",
            f"<b>Jami ustama bilan hisoblangan narx:</b> {overall_payment:.2f}$\n\n",
            "\n".join(payment_schedule),
        ]

        # Send the confirmation message with payment schedule
        await message.answer("\n".join(datas), reply_markup=accept())
    except Exception as e:
        await message.answer("Buyurtma qo'shishda xatolik, iltimos sintaksis qoidalariga amal qiling!",
                             reply_markup=admin_btn())
        await state.clear()
        return

# Handle confirmation
@dp.callback_query(lambda call: call.data == 'accepted')
async def confirm_handler(call: CallbackQuery, state: FSMContext) -> None:
    await call.message.edit_reply_markup(reply_markup=None)
    data = await state.get_data()

    rasrochka_muddati_txt = data['rasrochka_muddati'].split(' ')[0]
    ic(rasrochka_muddati_txt)

    user = User.objects.filter(phone=data.get("phone")).first()
    ic(user)

    today = datetime.today()
    payment_schedule = []
    pay = []
    today = datetime.today()

    # Starting point (next month, not this month)
    start_day = today.replace(day=1) + relativedelta(months=1)

    for month in range(int(rasrochka_muddati_txt)):
        month_num = (start_day.month + month - 1) % 12 + 1
        year_adjustment = (start_day.month + month - 1) // 12
        payment_date = start_day.replace(year=start_day.year + year_adjustment,
                                         month=month_num, day=today.day)

        payment_schedule.append(payment_date.strftime('%Y %B %d'))
        pay.append(payment_date.date())
    ic(pay[0])

    Installment.objects.create(
        user=user ,
        product=data['product_name'],
        price=data['product_price'],
        starter_payment=data['avans'],
        payment_months=int(rasrochka_muddati_txt),
        additional_fee_percentage=data['ustama'],
        start_date=pay[0],
        next_payment_dates = pay[0],
    )
    # user.client = True
    # user.save()


    ic(user, user.chat_id)
    try:
        sms_service = SayqalSms()
        sms_service.send_sms(
            message=f"Xurmatli mijoz sizning nomingizga muddatli to'lov evaziga {data['product_name']}\n do'konimiz tomonidan rasmiylashtirildi!\n"
            f"To'liq ma'lumot olish uchun https://t.me/ecommerce_1_bot botimizdan ro'yxatdan o'ting!",
            number=data['phone'],
        )
        message = await call.bot.send_message(
            chat_id=user.chat_id,
            text=f"Xurmatli mijoz sizning nomingizga muddatli to'lov evaziga {data['product_name']}\n do'konimiz tomonidan rasmiylashtirildi!\n"
            f"Maxsulot nomi: {data['product_name']}\n"
            f"Boshlang'ich to'lov: {data['avans']}$\n"
            f"Bo'lib to'lash muddati: {rasrochka_muddati_txt} oy\n"
            f"Birinchi to'lov sanasi:{pay[0]}"
        )


        await call.message.answer(f"Yangi rasrochka saqlandi birinchi to'lov sanasi {pay[0]} ", reply_markup=admin_btn())
        await state.clear()

    except Exception as e:
        await call.message.answer("Mijoz hali botdan o'z raqami buyicha ro'yhatdan "
                                  "o'tmagan, habar sms orqali yuborildi !"
                                  ,reply_markup=admin_btn())
        await state.clear()
    await state.clear()



@dp.callback_query(lambda call: call.data == "Sanani o'zgartirish")
async def confirm_handler(call: CallbackQuery, state: FSMContext) -> None:
    await call.message.edit_reply_markup(reply_markup=None)
    await state.set_state(Add_order.payment_date)
    await call.message.answer(
        "Kunni belgilang va mijoz har oyning shu sanasida to'lov uchun belgilanadi!"
    )

@dp.message(Add_order.payment_date)
async def edit_date_handler(msg: Message, state: FSMContext) -> None:
    data = await state.get_data()
    edited_date = msg.text

    if not edited_date.isdigit() or not (1 <= int(edited_date) <= 31):
        await msg.answer(
            "To'lov sanasini to'g'ri kiriting. Sana ikki xonali son ko'rinishida va faqat 1 dan 31 gacha bo'lishi shart!"
        )
        return

    data["edited_date"] = edited_date
    day = int(edited_date)

    # Extract and validate payment data
    price = Decimal(data.get("product_price", 0))
    avans = Decimal(data.get("avans", 0))
    ustama = Decimal(data.get("ustama", 0))
    rasrochka_muddati_txt = data.get('rasrochka_muddati', '0').split(' ')[0]
    rasrochka_months = int(rasrochka_muddati_txt)

    if price <= 0 or rasrochka_months <= 0:
        await msg.answer("To'lov ma'lumotlari to'g'ri kiritilmagan. Iltimos, qaytadan kiriting.")
        return

    # Calculate the overall payment
    remaining_balance = price - avans
    total_with_interest = remaining_balance + (remaining_balance * ustama / 100)

    # Calculate the monthly payment amounts
    base_monthly_payment = (total_with_interest / rasrochka_months).quantize(Decimal('1'), rounding=ROUND_UP)
    last_month_payment = total_with_interest - (base_monthly_payment * (rasrochka_months - 1))

    # Generate the payment schedule
    try:
        today = datetime.now()
        start_date = today.replace(day=1) + relativedelta(months=1)
        payment_schedule = []

        for month in range(rasrochka_months):
            payment_date = start_date + relativedelta(months=month)
            if day <= 28 or (payment_date.month in [4, 6, 9, 11] and day <= 30) or (payment_date.month == 2 and day <= 28):
                payment_date = payment_date.replace(day=day)
            else:
                payment_date = payment_date.replace(day=min(day, 30))

            # Determine payment amount for the current month
            payment_amount = base_monthly_payment if month < rasrochka_months - 1 else last_month_payment
            payment_schedule.append(f"{payment_date.strftime('%d %B %Y')}: {payment_amount:.2f}$")

    except Exception as e:
        await msg.answer(f"Xatolik yuz berdi: {str(e)}. Iltimos, qaytadan urinib ko'ring.")
        return

    # Prepare the confirmation message
    details = [
        f"<b>Mijoz ismi:</b> {data.get('full_name')}",
        f"<b>Telefon raqami:</b> {data.get('phone', 'N/A')}",
        f"<b>Mahsulotlar:</b> {data.get('product_name', 'N/A')}",
        f"<b>Mahsulot tan narxi:</b> {data.get('product_price', 'N/A')} $",
        f"<b>Boshlang'ich to'lov:</b> {data.get('avans', 'N/A')} $",
        f"<b>Rasrochka muddati:</b> {data.get('rasrochka_muddati', 'N/A')}",
        f"<b>Qo'shilgan foiz:</b> {data.get('ustama', 'N/A')} %",
        f"<b>To'lov qilish sanasi har oyning:</b> {edited_date}-chi sanasida",
        f"<b>Jami ustama bilan hisoblangan narx:</b> {total_with_interest:.2f} $",
        f"\n\n<b>To'lov jadvali:</b>\n" + "\n".join(payment_schedule),
    ]

    await msg.answer("\n".join(details), reply_markup=accept())


@dp.callback_query(lambda call: call.data == "cancelled")
async def confirm_handler(call: CallbackQuery, state: FSMContext) -> None:
    await call.message.edit_reply_markup()
    await call.message.answer("Buyurtma bekor qilindi !", reply_markup=admin_btn())
    await state.clear()