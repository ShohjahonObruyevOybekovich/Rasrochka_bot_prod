from aiogram.client.context_controller import BotContextController
from celery import shared_task
from datetime import datetime, timedelta
from bot.models import User, Installment
from aiogram import Bot
from django.conf import settings


@shared_task
def send_next_payment_notifications():
    """
    Celery task to send notifications to users for upcoming payments 10, 3, or 1 day before the payment date.
    Runs daily at 8:00 AM.
    """
    # Get the current date and time
    now = datetime.now()
    today = now.date()

    # Define intervals for reminders (10, 3, 1 day before)
    intervals = [10, 3, 1]

    # Calculate the date ranges for reminders
    upcoming_dates = [today + timedelta(days=interval) for interval in intervals]

    # Fetch installments with upcoming payment dates matching the intervals
    installments = Installment.objects.filter(
        next_payment_date__in=upcoming_dates,
        status="ACTIVE"
    )

    for installment in installments:
        user = installment.user

        # Calculate days remaining for the payment
        days_left = (installment.next_payment_date - today).days

        # Format the reminder message
        reminder_message = (
            f"Salom {user.first_name},\n\n"
            f"Sizning keyingi to'lovingiz <b>{installment.next_payment_date.strftime('%d %B %Y')}</b> kuni "
            f"Qolgan kunlar: <b>{days_left}</b>\n\n"
            f"To'lovni o'z vaqtida amalga oshirishingizni so'raymiz. 😊"
        )

        # Send the notification using Aiogram
        try:
            BotContextController.bot.loop.create_task(BotContextController.bot.send_message(chat_id=user.chat_id, text=reminder_message, parse_mode="HTML"))
            print(f"Reminder sent to {user.first_name} ({user.chat_id}) for payment on {installment.next_payment_date}")
        except Exception as e:
            print(f"Error sending message to {user.chat_id}: {str(e)}")

    return f"Notifications sent for {len(installments)} installments."
