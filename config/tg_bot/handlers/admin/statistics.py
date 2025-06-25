from datetime import datetime
from asgiref.sync import sync_to_async
from icecream import ic
from bot.models import Installment
from dispatcher import dp
from tg_bot.buttons.text import statistic_txt
from aiogram.types import Message

@dp.message(lambda msg: msg.text == statistic_txt)
async def command_start_handler(message: Message) -> None:
    # Retrieve all active installments
    installments = await sync_to_async(list)(
        Installment.objects.filter(status="ACTIVE").prefetch_related("payments")
    )

    total_remaining_price = 0  # Total remaining payments
    total_profit = 0  # Total unpaid profit from active installments

    for installment in installments:
        # Calculate the remaining balance after starter payment
        remaining_balance = installment.price - installment.starter_payment

        # Calculate the total added interest
        interest_amount = remaining_balance * (installment.additional_fee_percentage / 100)

        # Calculate the total price including interest
        total_price = remaining_balance + interest_amount

        # Calculate the total paid so far
        total_paid = sum(payment.amount for payment in installment.payments.all())

        # Update the remaining balance (with interest)
        remaining_balance_with_interest = total_paid

        # Calculate unpaid profit (interest on the remaining balance)
        unpaid_profit = interest_amount * (remaining_balance_with_interest / total_price)

        # Add to totals
        total_remaining_price += max(remaining_balance_with_interest, 0)  # Ensure no negative values
        total_profit += max(unpaid_profit, 0)  # Ensure no negative values

    # Generate summary report
    summary_report = (
        f"<b>Jami qolgan to'lovlar:</b> {total_remaining_price:.2f} $\n"
        # f"<b>Jami foyda:</b> {total_profit:.2f} $"
    )

    # Send the report to the user
    await message.answer(summary_report, parse_mode="HTML")
