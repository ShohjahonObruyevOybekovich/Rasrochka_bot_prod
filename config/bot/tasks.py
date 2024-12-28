import asyncio
from datetime import date, timedelta
import logging

from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from asgiref.sync import sync_to_async
from celery import Celery
from aiogram import Bot

from config.celery import app
from dispatcher import Dispatcher, TOKEN

from bot.models import Installment


bot = Bot(TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
# Logger setup
logging.basicConfig(level=logging.INFO)

@sync_to_async
def get_upcoming_payments(start_date, end_date):
    """
    Fetches upcoming payments within the given date range and with ACTIVE status.
    """
    return Installment.objects.filter(
        next_payment_dates__gte=start_date,
        next_payment_dates__lte=end_date,
        status="ACTIVE"
    )


async def send_async_message(chat_id, text):
    """
    Sends a message to the specified chat_id asynchronously.
    """
    try:
        # Ensure you use an instance of Bot
        await bot.send_message(chat_id, text=text, parse_mode="Markdown")
        logging.info(f"Message sent to chat_id {chat_id}.")
    except Exception as e:
        logging.error(f"Failed to send message to chat_id {chat_id}: {e}")

@app.task
def send_daily_message():
    """
    Celery task to send daily messages for upcoming payments.
    """
    logging.info("Celery task started: Sending daily messages...")

    today = date.today()
    five_days_later = today + timedelta(days=5)
    one_day_later = today + timedelta(days=1)

    # Fetch upcoming payments
    upcoming_payments = asyncio.run(get_upcoming_payments(one_day_later, five_days_later))

    # Iterate over each payment and send a message
    for payment in upcoming_payments:
        user_chat_id = payment.user.chat_id  # Assuming `user` relation has a `chat_id` field
        message_text = (
            f"Assalomu alaykum! Sizning nasiya savdo bo'yicha xaridingizning "
            f"keyingi to'lov muddati {payment.next_payment_dates}. "
            f"To'lovni o'z vaqtida amalga oshiring."
        )
        asyncio.run(send_async_message(user_chat_id, message_text))

    logging.info("Celery task completed.")
