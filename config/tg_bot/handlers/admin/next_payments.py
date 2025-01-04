from datetime import  date
from decimal import Decimal

from aiogram.types import Message
from asgiref.sync import sync_to_async
from icecream import ic

from dispatcher import dp
from tg_bot.buttons.text import next_payments
from bot.models import Installment, Payment
from tg_bot.state.sent_notification import *
# from bot.tasks import send_payment_reminders
@dp.message(lambda msg: msg.text == next_payments)
async def payments_summary(message: Message):
    """
    Display overdue payments and payments due within the next 10 days.
    """
    global datetime
    now = date.today()
    ten_days_later = now + timedelta(days=10)
    today = date.today()

    # Get overdue unpaid installments
    @sync_to_async
    def get_overdue_installments():

        return Installment.objects.filter(
            next_payment_dates__lt=date.today(),
            status="ACTIVE"
        ).all()




    @sync_to_async
    def get_upcoming_payments(end_date):
        return Installment.objects.filter(
            next_payment_dates__gte=date.today(),
            next_payment_dates__lte=end_date,
            status="ACTIVE"
        )

    overdue_installments = await get_overdue_installments()
    upcoming_payments = await get_upcoming_payments(ten_days_later)

#########------  send notification 10 days before ------- ###########

    for payment in upcoming_payments:
        payment_date = payment.next_payment_dates
        user_id = payment.user_id

        # reminder_time = payment_date - timedelta(minutes=1)
        datetime = datetime.now() + timedelta(minutes=1)
        ic(datetime.now())
        reminder_message = (f"Salom! Siz qarizdorligingiz bo'yicha to'lovingizni "
                            f"{payment_date.strftime('%d %B %Y')}da amalga oshirilishi kerak. "
                            f"Iltimos, to'lovni o'z vaqtida bajaring!")
    datetime = datetime.now() + timedelta(seconds=5)
    # res = send_payment_reminders.apply_async(
    #     args=[datetime.strftime('%Y-%m-%d %H:%M:%S')],
    #     kwargs={},
    #     eta=datetime
    # )
    # ic(res)

    from html import escape

    # Construct response safely
    response = ""

    if overdue_installments:
        response += "Muddat o'tgan qarzdorliklar:\n"
        for installment in overdue_installments:
            first_unpaid_payment = installment.is_payment_overdue()
            overdue_date = installment.next_payment_dates
            paymanet_amount = installment.calculate_monthly_payment()
            paymanet_amount = round(paymanet_amount, 2)

            # Escape user data
            full_name = escape(installment.user.full_name)
            phone = escape(installment.user.phone) if installment.user.phone else ""
            product = escape(installment.product)

            response += (
                f"\n<b>Mijoz:</b> {full_name}\n"
                f"<b>Mijoz raqami:</b> {phone}\n"
                f"<b>Mahsulot:</b> {product}\n"
                f"<b>To'lov miqdori:</b> {paymanet_amount} $\n"
                f"<b>Kechikkan sana:</b> {overdue_date}\n"
            )
    else:
        response += "Muddat o'tgan qarzdorliklar mavjud emas.\n"

    response += "\n" + "-" * 30 + "\n"

    if upcoming_payments:
        response += "Keyingi 10 kunda tushadigan to'lovlar:\n\n"
        for payment in upcoming_payments:
            paymanet_amount = payment.calculate_monthly_payment()
            paymanet_amount = round(paymanet_amount, 2)

            # Escape user data
            full_name = escape(payment.user.full_name)
            phone = escape(payment.user.phone) if payment.user.phone else ""
            product = escape(payment.product)

            response += (
                f"<b>Mijoz:</b> {full_name}\n"
                f"<b>Mijoz raqami:</b> {phone}\n"
                f"<b>Mahsulot:</b> {product}\n"
                f"<b>Miqdor:</b> {paymanet_amount} $\n"
                f"<b>To'lov sanasi:</b> {payment.next_payment_dates}\n\n"
            )
    else:
        response += "Keyingi 10 kunda tushadigan to'lovlar mavjud emas.\n"

    # Send the response with HTML parse_mode
    await message.answer(response, parse_mode="HTML")



