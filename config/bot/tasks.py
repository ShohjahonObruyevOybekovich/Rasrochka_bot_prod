from datetime import datetime, timedelta

from aiogram.client import bot
from asgiref.sync import async_to_sync
from celery import shared_task
from django.utils.timezone import now
from aiogram import Bot
from bot.models import Installment
#
# # Replace with your bot's token
# BOT_TOKEN = "your_bot_token"
# bot = Bot(token=BOT_TOKEN)

async def send_notification(bot: Bot, user_id: int, message: str):
    """
    Sends a notification to a user using Telegram bot.
    """
    try:
        await bot.send_message(chat_id=user_id, text=message)
    except Exception as e:
        print(f"Failed to send message to {user_id}: {e}")


@shared_task
def send_payment_reminders():
    """
    Celery task to send reminders to users about upcoming payments.
    """
    today = now().date()
    reminders = [5, 1]  # Days before the payment due date
    users_to_notify = []

    # Query installments with upcoming payments
    for reminder in reminders:
        reminder_date = today + timedelta(days=reminder)

        due_installments = Installment.objects.filter(
            next_payment_dates=reminder_date,
            status="ACTIVE",
        )

        for installment in due_installments:
            # Prepare data for notification
            users_to_notify.append({
                "user_id": installment.user.chat_id,  # Replace with correct field for Telegram ID
                "full_name": installment.user.full_name,
                "phone": installment.user.phone,
                "due_date": installment.next_payment_dates,
                "amount": installment.price,
                "days_left": reminder,
            })

    # Send notifications
    for user_data in users_to_notify:
        message = (
            f"Assalomu alaykum! Sizning keyingi {user_data['amount']} $ to'lovingiz "
            f"{user_data['due_date']} kuni bo'lishi kerak. "
            f"{user_data['days_left']} kun qoldi!"
        )

        # Use async_to_sync to call async function in Celery
        async_to_sync(send_notification)(bot, user_data["user_id"], message)


# Schedule this task daily at 8 AM
@shared_task
def schedule_reminders_daily():
    """
    Schedules reminders daily at 8 AM.
    """
    send_payment_reminders.apply_async(
        eta=datetime.combine(now().date() + timedelta(days=1), datetime.min.time()).replace(minute=50,hour=1)
    )
