from pyexpat.errors import messages

from aiogram.enums import ContentType
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiohttp.hdrs import CONTENT_TYPE
from asgiref.sync import sync_to_async
from dateutil.relativedelta import relativedelta
from django.core.exceptions import ObjectDoesNotExist
from icecream import ic
from pydantic.types import AnyType

from bot.models import User, Installment, Sms, Category
from dispatcher import dp
from sms import SayqalSms
from tg_bot.buttons.inline import  accept
from tg_bot.buttons.reply import menu_btn, skip, back, admin_btn, months, category
from tg_bot.buttons.text import *
from tg_bot.state.main import *
from datetime import datetime
import calendar

from tg_bot.test import format_phone_number, extract_payment_amount


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

    try:
        phone = format_phone_number(msg.text)
    except Exception as e:
        await msg.answer("Raqam uzunligi notugri kiritildi iltimos tekshirib qaytadan kiriting!")
        await state.clear()
        await state.set_state(Add_order.phone)
        return

    data = await state.get_data()

    data["phone"] = phone
    ic(data["phone"])

    # Update the state with the corrected phone number
    await state.set_data(data)


    user = await sync_to_async(User.objects.filter(phone=phone).first)()
    if user:
        await state.set_state(Add_order.product_category)
        await msg.answer("Mahsulotlar guruhini kiriting:", reply_markup=category())
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
    ic(data["phone"])
    data['user_name'] = message.text
    await state.set_data(data)
    await state.set_state(Add_order.product_category)
    await message.answer("Mahsulotlar Guruhini tanlang:", reply_markup=category())




# Handle product name input
@dp.message(Add_order.product_category)
async def product_name_handler(message: Message, state: FSMContext) -> None:
    if message.text == ortga:
        await state.set_state(Add_order.phone)
        await message.answer("Mijoz raqamini qaytadan kiriting:", reply_markup=back())
        await state.clear()
        return

    data = await state.get_data()
    data['product_category'] = message.text
    await state.set_data(data)

    try:
        # Check if the category exists in the database
        category = Category.objects.get(name=data['product_category'])
    except Category.DoesNotExist:
        # Handle the case where the category does not exist
        await message.answer("Buyurtmalar guruhini faqat mavjud bo'lgan ro'yxatdan tanlang!")
        await state.set_state(Add_order.product_category)
        return

    await state.set_state(Add_order.product_name)
    await message.answer("Buyurtmalarning nomini kiriting:", reply_markup=back())



@dp.message(Add_order.product_name)
async def product_name_handler(message: Message, state: FSMContext) -> None:
    if message.text == ortga:
        await state.set_state(Add_order.user_name)
        await message.answer("Buyurtmalarning guruhini kiriting:", reply_markup=category())
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
    if not message.text.isdigit():
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

    if message.text.isdigit() :
        data = await state.get_data()
        data['avans'] = message.text
        await state.set_data(data)
        await state.set_state(Add_order.rasrochka_vaqti)
        await message.answer('Nasiya savdo oylarini kiriting:', reply_markup=months())

    elif message.text == "O'tkazib yuborish ➡️":
        data = await state.get_data()
        data['avans'] = message.text if message.text != "O'tkazib yuborish ➡️" else '0'
        await state.set_data(data)

        await state.set_state(Add_order.rasrochka_vaqti)
        await message.answer('Nasiya savdo oylarini kiriting:', reply_markup=months())
    else:
        await message.answer("Boshlang'ich to'lovni faqat raqamlar bilan $ hisobida kiriting!")
        await state.set_state(Add_order.avans)
        return

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
    ustama = extract_payment_amount(message.text)
    data['ustama'] = ustama
    await state.set_data(data)

    if not ustama % 1 == 0:
        await message.answer("Bo'lib to'lash ustama foizini to'g'ri faqat raqam orqali kiriting:")
        await state.set_state(Add_order.ustama)
        return

    ic(data.values())
    mijoz = ""

    if data.get("user_name") is None:
        user = User.objects.filter(phone=data.get("phone")).first()
        if user:
            mijoz = user.full_name
    else:
        mijoz = data.get("user_name")

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
        ic(overall_payment)

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
            payment_year = start_day.year + year_adjustment

            # Get the last day of the target month
            last_day_of_month = calendar.monthrange(payment_year, month_num)[1]

            # Use the minimum of today's day or the last day of the target month
            payment_day = min(today.day, last_day_of_month)

            payment_date = start_day.replace(year=payment_year, month=month_num, day=payment_day)

            if month == rasrochka_months - 1:
                payment_schedule.append(f"{payment_date.strftime('%d %B %Y')}: {last_month_payment:.2f}$")
            else:
                payment_schedule.append(f"{payment_date.strftime('%d %B %Y')}: {rounded_monthly_payment:.2f}$")

        foiz_miqdori= (price-avans)*(ustama/100)

        ic(mijoz,overall_payment, last_month_payment, payment_schedule,base_monthly_payment, foiz_miqdori,rounded_monthly_payment)

        datas = [
            f"<b>Mijoz ismi:</b> {mijoz}",
            f"<b>Telefon raqami:</b> {data.get('phone', '')}",
            f"<b>Buyurtma guruhi:</b> {data.get('product_category', '')}",
            f"<b>Mahsulotlar:</b> {data.get('product_name', '')}",
            f"<b>Mahsulot tan narxi:</b> {data.get('product_price', '')} $",
            f"<b>Boshlang'ich to'lov:</b> {data.get('avans', '')} $",
            f"<b>Nasiya savdo muddati:</b> {data.get('rasrochka_muddati', '')} oy",
            f"<b>Qo'shilgan foiz:</b> {data.get('ustama', '')} %",
            f"<b>To'lov qilish sanasi har oyning:</b> {today.strftime('%d')} chi sanasida\n",
            f"<b>Mahsulot tan narxi :</b>  {price:.2f} $\n"
            f"<b>Qo'shilgan foiz miqdori:</b>  {foiz_miqdori:.2f} $\n\n",
            f"<b>Jami ustama bilan hisoblangan narx:</b> {(price + foiz_miqdori):.2f}$\n\n",
            "\n".join(payment_schedule),
        ]

        ic(datas)

        # Send the confirmation message with payment schedule
        await message.answer("\n".join(datas), reply_markup=accept())
    except Exception as e:
        ic(e)
        await message.answer("Buyurtma qo'shishda xatolik, iltimos sintaksis qoidalariga amal qiling!",
                             reply_markup=admin_btn())
        await state.clear()
        return

# Handle confirmation
@dp.callback_query(lambda call: call.data == 'accepted')
async def confirm_handler(call: CallbackQuery, state: FSMContext) -> None:
    await call.message.edit_reply_markup(reply_markup=None)
    data = await state.get_data()

    rasrochka_muddati_txt = data.get('rasrochka_muddati').split(' ')[0]
    ic(rasrochka_muddati_txt)
    user1 = User.objects.filter(phone=data.get("phone")).first()
    if user1 is None:
        user1 = User.objects.create(full_name=data.get('user_name'),
                               phone=data.get('phone'))

    today = datetime.today()
    payment_schedule = []
    pay = []
    today = datetime.today()

    # Starting point (next month, not this month)
    start_day = today.replace(day=1) + relativedelta(months=1)

    for month in range(int(rasrochka_muddati_txt)):
        # Calculate the target month and year
        month_num = (start_day.month + month - 1) % 12 + 1
        year_adjustment = (start_day.month + month - 1) // 12
        payment_year = start_day.year + year_adjustment

        # Get the last valid day of the target month
        last_day_of_month = calendar.monthrange(payment_year, month_num)[1]

        # Use the smaller of today's day or the last day of the month
        payment_day = min(today.day, last_day_of_month)

        # Create the payment date
        payment_date = start_day.replace(year=payment_year, month=month_num, day=payment_day)

        # Append the formatted date to the schedule
        payment_schedule.append(payment_date.strftime('%Y %B %d'))
        pay.append(payment_date.date())
        ic(pay[0])
    try:
        # Retrieve the Category instance
        category_instance = Category.objects.get(name=data['product_category'])
    except ObjectDoesNotExist:
        raise ValueError(f"Category '{data['product_category']}' does not exist. Please ensure the category is valid.")


    Installment.objects.create(
        user=user1 ,
        product=data['product_name'],
        category=category_instance,
        price=data['product_price'],
        starter_payment=data['avans'],
        payment_months=int(rasrochka_muddati_txt),
        additional_fee_percentage=data['ustama'],
        start_date=pay[0],
        next_payment_dates = pay[0],
    )
    user1.role = "CLIENT"
    user1.save()
    # user.client = True
    # user.save()
    price = Decimal(data.get("product_price", 0))
    avans = Decimal(data.get("avans", 0))
    ustama = Decimal(data.get("ustama", 0))
    rasrochka_muddati_txt = data.get('rasrochka_muddati', '0').split(' ')[0]
    rasrochka_months = int(rasrochka_muddati_txt)


    overall_payment = (price - avans) + ((price - avans) * ustama) / 100
    base_monthly_payment = overall_payment / rasrochka_months
    rounded_monthly_payment = base_monthly_payment.quantize(Decimal('1'), rounding=ROUND_CEILING)
    last_month_payment = overall_payment - rounded_monthly_payment * (rasrochka_months - 1)

    # ic(user, user.chat_id)
    try:
        sms_service = SayqalSms()
        sms_service.send_sms(
            message=f"Buyurtma rasmiylashtirildi\n"
                    f"Buyurtma nomi:{data.get('product_name')}\n"
                    f"Oylik to'lovingiz: {rounded_monthly_payment}$\n"
                    f"To'liq malumot olish uchun botimizdan ro'yxatdan o'ting:"
                    f"https://t.me/ab_nasiya_bot",
            number=data['phone'],
        )
        sms = Sms()
        sms.counter()

        message = await call.bot.send_message(
            chat_id=user1.chat_id,
            text=f"Xurmatli mijoz sizning nomingizga muddatli to'lov evaziga  {data['product_name']}\n do'konimiz tomonidan rasmiylashtirildi!\n"
            f"<b>Maxsulot nomi:</b> {data['product_name']}\n"
            f"<b>Har oylik to'lov miqdori:</b> {rounded_monthly_payment}$\n"
            f"<b>Bo'lib to'lash muddati:</b> {rasrochka_muddati_txt} oy\n"
            f"<b>Birinchi to'lov sanasi:</b> {pay[0]}"
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

    # Validate that the date is a digit and between 1-31
    if not (1 <= int(edited_date) <= 31):
        await msg.answer(
            "To'lov sanasini to'g'ri kiriting. Sana ikki xonali son ko'rinishida va faqat 1 dan 31 gacha bo'lishi shart!"
        )
        return
    edited_date = extract_payment_amount(edited_date)
    mijoz = ''
    if data.get("user_name") is None:
        user = User.objects.filter(phone=data.get("phone")).first()
        if user:
            mijoz = user.full_name
    else:
        mijoz = data.get("user_name")
    edited_date = int(edited_date)  # Convert to integer
    data["edited_date"] = edited_date
    day = edited_date

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

            # Adjust day for months with fewer than 31 days
            if payment_date.month in [4, 6, 9, 11] and day > 30:
                adjusted_day = 30
            elif payment_date.month == 2:
                # Handle February
                if (payment_date.year % 4 == 0 and payment_date.year % 100 != 0) or (payment_date.year % 400 == 0):
                    # Leap year
                    adjusted_day = min(day, 29)
                else:
                    # Non-leap year
                    adjusted_day = min(day, 28)
            else:
                adjusted_day = day

            payment_date = payment_date.replace(day=adjusted_day)

            # Determine payment amount for the current month
            payment_amount = base_monthly_payment if month < rasrochka_months - 1 else last_month_payment
            payment_schedule.append(f"{payment_date.strftime('%d %B %Y')}: {payment_amount:.2f}$")

    except Exception as e:
        await msg.answer(f"Xatolik yuz berdi: {str(e)}. Iltimos, qaytadan urinib ko'ring.")
        return

    foiz_miqdori= (price-avans)*(ustama/100)
    details = [
        f"<b>Mijoz ismi:</b> {mijoz}",
        f"<b>Telefon raqami:</b> {data.get('phone', '')}",
        f"<b>Buyurtma guruhi:</b> {data.get('product_category', '')}",
        f"<b>Mahsulotlar:</b> {data.get('product_name', '')}",
        f"<b>Mahsulot tan narxi:</b> {data.get('product_price', '')} $",
        f"<b>Boshlang'ich to'lov:</b> {data.get('avans', '')} $",
        f"<b>Nasiya savdo muddati:</b> {data.get('rasrochka_muddati', '')} oy",
        f"<b>Qo'shilgan foiz:</b> {data.get('ustama', '')} %",
        f"<b>To'lov qilish sanasi har oyning:</b> {edited_date}-chi sanasida",
        f"<b>To'liq summa :</b>  {price:.2f} $\n"
        f"<b>Qo'shilgan foiz miqdori:</b>  {foiz_miqdori:.2f} $\n"
        f"<b>Jami ustama bilan hisoblangan narx:</b> {(price + foiz_miqdori):.2f} $",
        f"\n\n<b>To'lov jadvali:</b>\n" + "\n".join(payment_schedule),
    ]

    await msg.answer("\n".join(details), reply_markup=accept())

@dp.callback_query(lambda call: call.data == "cancelled")
async def confirm_handler(call: CallbackQuery, state: FSMContext) -> None:
    await call.message.edit_reply_markup()
    await call.message.answer("Buyurtma bekor qilindi !", reply_markup=admin_btn())
    await state.clear()