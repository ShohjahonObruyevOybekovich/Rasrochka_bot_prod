from datetime import datetime
from asgiref.sync import sync_to_async
from dateutil.relativedelta import relativedelta
from icecream import ic

from bot.models import Installment
from dispatcher import dp
from tg_bot.buttons.text import statistic_txt
from aiogram.types import Message
from html import escape

@dp.message(lambda msg: msg.text == statistic_txt)
async def command_start_handler(message: Message) -> None:
    # Retrieve all active installments
    installments = await sync_to_async(list)(
        Installment.objects.filter(status="ACTIVE").prefetch_related("payments")
    )

    total_remaining_price = 0  # Total remaining payments
    current_month = datetime.today().month
    current_year = datetime.today().year
    payments_this_month = 0  # Payments due this month
    projected_profit = 0  # Profit for this month

    payments_this_month_details = []  # To store details of payments for this month

    for installment in installments:
        # Calculate the remaining balance after the advance payment
        remaining_balance = installment.price - installment.starter_payment

        # Apply the additional fee to the remaining balance
        additional_fee = remaining_balance * (installment.additional_fee_percentage / 100)
        total_with_fee = remaining_balance + additional_fee

        # Calculate the remaining balance after payments
        total_paid = sum(payment.amount for payment in installment.payments.all())
        installment_balance = total_with_fee - total_paid
        total_remaining_price += installment_balance

        # Generate payment schedule
        rasrochka_months = installment.payment_months
        starter_date = installment.next_payment_dates or datetime.today()
        day_of_month = starter_date.day

        # Track the months already paid
        prepayments_covered = int(total_paid // (total_with_fee / rasrochka_months))
        remaining_months = rasrochka_months - prepayments_covered

        # Distribute remaining balance over unpaid months
        monthly_payment = installment_balance / max(remaining_months, 1)

        # Check payments for this month
        for month in range(rasrochka_months):
            payment_date = starter_date + relativedelta(months=month)
            try:
                payment_date = payment_date.replace(day=day_of_month)
            except ValueError:
                payment_date = payment_date.replace(day=28)

            if payment_date.month == current_month and payment_date.year == current_year:
                payments_this_month += monthly_payment

                # Add profit for this month's payment
                projected_profit += additional_fee / rasrochka_months

                # Add this month's payment details
                payments_this_month_details.append({
                    "user": installment.user,
                    "product": installment.product,
                    "amount": round(monthly_payment, 2),
                    "payment_date": payment_date.strftime('%Y-%m-%d'),
                })

    # Generate summary report
    summary_report = (
        f"<b>Jami qolgan to'lovlar:</b> {total_remaining_price:.2f} $\n"
        # f"<b>Bu oyda keladigan to'lovlar:</b> {payments_this_month:.2f} $\n"
        f"<b>Jami foyda:</b> {projected_profit:.2f} $"
    )

    # # Add details for this month's payments
    # if payments_this_month_details:
    #     summary_report += "<b>Bu oyda keladigan to'lovlar tafsilotlari:</b>\n\n"
    #     for payment in payments_this_month_details:
    #         full_name = escape(payment["user"].full_name)
    #         phone = escape(payment["user"].phone)
    #         product = escape(payment["product"])
    #         amount = payment["amount"]
    #         payment_date = payment["payment_date"]
    #
    #         summary_report += (
    #             f"<b>Mijoz:</b> {full_name}\n"
    #             f"<b>Telefon:</b> {phone}\n"
    #             f"<b>Mahsulot:</b> {product}\n"
    #             f"<b>Miqdor:</b> {amount} $\n"
    #             f"<b>To'lov sanasi:</b> {payment_date}\n\n"
    #         )
    # else:
    #     summary_report += "Bu oyda keladigan to'lovlar mavjud emas.\n"
    #
    # # Send the report to the user
    await message.answer(summary_report, parse_mode="HTML")

