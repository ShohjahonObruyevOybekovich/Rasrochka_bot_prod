from io import BytesIO
from aiogram.types import BufferedInputFile, Message
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
from asgiref.sync import sync_to_async
from bot.models import Installment
from tg_bot.buttons.text import order_history_txt
from dispatcher import dp

@dp.message(lambda msg: msg.text == order_history_txt)
async def command_start_handler(message: Message) -> None:
    # Retrieve all installments
    installments = Installment.objects.all()

    if not installments:
        await message.answer("Buyurtmalar mavjud emas!.")
        return

    # Prepare the data for Excel
    excel_data = []

    for installment in installments:
        # Update status and calculate details
        installment.update_status()
        overall_price = installment.calculate_overall_price()
        total_paid = sum(payment.amount for payment in installment.payments.all())

        # Gather payment history (stacked format)
        payment_history = []
        for payment in installment.payments.order_by("payment_date").all():
            payment_date = payment.payment_date.strftime("%d-%B")  # Format the date
            payment_entry = f"{payment_date}: {payment.amount}$"
            payment_history.append(payment_entry)

        # Join the payment history with newline for vertical stacking
        payment_history_str = "\n".join(payment_history)

        # Collect all payment dates
        payment_dates = [payment.payment_date.strftime("%d %B %Y") for payment in installment.payments.order_by("payment_date").all()]
        payment_dates_str = "\n".join(payment_dates)  # Join dates with a newline for vertical stacking

        # Calculate the payment schedule based on `starter_date` and `rasrochka_months`
        rasrochka_months = int(installment.payment_months)  # Assuming `starter_payment` is the number of months
        payment_schedule = []

        today = datetime.today()

        # Assuming the `starter_date` is the date the installment starts
        starter_date = installment.start_date or today  # Use the installment's starter date, or fallback to today
        day_of_month = starter_date.day  # This is the day of the month we want to use for all payments

        # Generate the payment schedule for each month
        for month in range(rasrochka_months):
            # Calculate the payment date by adding months to the starter date
            payment_date = starter_date + relativedelta(months=month)

            # Ensure the day of the payment date matches the starter date's day
            try:
                payment_date = payment_date.replace(day=day_of_month)
            except ValueError:
                # If the month has fewer days, set the payment date to the last valid day of the month
                payment_date = payment_date.replace(day=28)  # Use the 28th if the day exceeds the month's days

            payment_schedule.append(payment_date.strftime("%d %B %Y"))

        # Prepare the data for Excel, including payment dates and schedule
        excel_data.append({
            "ID": installment.id,
            "Mijoz": installment.user.full_name,
            "Telefon raqami": installment.user.phone,
            "Mahsulotlar guruhi": installment.category.name,
            "Mahsulotlar": "\n".join(
                [f"{product.strip()} " for product in set(installment.product.split(","))]
            ),
            "Buyurtma statusi": installment.status,
            "Avans": f"{installment.starter_payment}$",
            "Ustama foizi" : f"{installment.additional_fee_percentage} %",
            "Ustama miqdori" : f"{installment.price* (installment.additional_fee_percentage/100):.2f} $",
            "Asil narxi": f"{installment.price}$",
            "Ustama bilan xisoblangan narxi": f"{(overall_price + installment.starter_payment):.2f}$",
            "To'liq so'mma " : f"{(installment.price + installment.price
                                  * (installment.additional_fee_percentage/100)+installment.starter_payment):.2f}",
            "Jami to'langan so'mma": f"{total_paid}$",
            "To'lovlar": payment_history_str,
            "Payment Dates": "\n".join(payment_schedule),  # Add the generated payment dates to the Excel data
            "Yaratilgan sana": installment.created_at.strftime("%d %B %Y"),
        })

    # Convert the list of dictionaries into a DataFrame
    df = pd.DataFrame(excel_data)

    # Save the DataFrame to an in-memory BytesIO object as an Excel file
    res = BytesIO()
    df.to_excel(res, index=False)
    res.seek(0)

    # Send the Excel file to the user
    await message.answer_document(
        BufferedInputFile(res.read(), filename="Buyurtmalar.xlsx"),
        caption="Buyurtmalar bilan Excel fayli."
    )
