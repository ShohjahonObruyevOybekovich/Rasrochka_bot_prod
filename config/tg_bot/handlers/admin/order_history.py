import pandas as pd
from io import BytesIO
from datetime import datetime
from dateutil.relativedelta import relativedelta
from aiogram.types import Message, BufferedInputFile

from bot.models import User,Installment
from dispatcher import dp
from tg_bot.buttons.text import order_history_txt


@dp.message(lambda msg: msg.text == order_history_txt)
async def command_start_handler(message: Message) -> None:
    # Retrieve all installments
    installments = Installment.objects.all()

    if not installments:
        await message.answer("Buyurtmalar mavjud emas!.")
        return

    # Prepare the data for Excel
    excel_data = []

    for user in User.objects.all():
        user_installments = Installment.objects.filter(user=user)

        for installment in user_installments:
            installment.update_status()
            overall_price = installment.calculate_overall_price()
            total_paid = sum(payment.amount for payment in installment.payments.all())

            # Gather payment history (each payment will be a new row)
            payment_history = [
                f"{payment.payment_date.strftime('%d-%B')}: {payment.amount}$"
                for payment in installment.payments.order_by("payment_date").all()
            ]

            # If no payments, we still need one row for the installment
            max_payments = max(len(payment_history), 1)

            for j in range(max_payments):
                # First row should contain installment details
                installment_data = {
                    "ID": installment.id if j == 0 else "",
                    "Mijoz": installment.user.full_name if j == 0 else "",
                    "Telefon raqami": installment.user.phone if j == 0 else "",
                    "Mahsulotlar guruhi": installment.category.name if j == 0 else "",
                    "Mahsulotlar": "\n".join(
                        [f"{product.strip()} " for product in set(installment.product.split(","))]
                    ) if j == 0 else "",
                    "Buyurtma statusi": installment.status if j == 0 else "",
                    "Avans": f"{installment.starter_payment}$" if j == 0 else "",
                    "Ustama foizi": f"{installment.additional_fee_percentage} %" if j == 0 else "",
                    "Ustama miqdori": f"{installment.price * (installment.additional_fee_percentage / 100):.2f} $" if j == 0 else "",
                    "Asil narxi": f"{installment.price}$" if j == 0 else "",
                    "Ustama bilan xisoblangan narxi": f"{(overall_price + installment.starter_payment):.2f}$" if j == 0 else "",
                    "To'liq so'mma": f"{(installment.price + installment.price * (installment.additional_fee_percentage / 100) + installment.starter_payment):.2f}" if j == 0 else "",
                    "Jami to'langan so'mma": f"{total_paid}$" if j == 0 else "",
                    "To‘lovlar": payment_history[j] if j < len(payment_history) else "",
                    "Payment Dates": installment.created_at.strftime("%d %B %Y") if j == 0 else "",
                }

                excel_data.append(installment_data)  # Add row

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
