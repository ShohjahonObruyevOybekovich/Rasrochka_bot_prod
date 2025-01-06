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

from bot.models import Installment, Sms, User
from sms import SayqalSms

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


async def send_async_message(chat_id, text, phone):
    """
    Sends a message to the specified chat_id asynchronously.
    """
    try:
        # Ensure you use an instance of Bot
        await bot.send_message(chat_id, text=text, parse_mode=ParseMode.HTML)
        logging.info(f"Message sent to chat_id {chat_id}.")
        sms_service = SayqalSms()
        sms_service.send_sms(
            message=text,
            number= phone
        )
        sms = Sms()
        sms.counter()
        logging.info(f"Message sent to phone {phone}.")
    except Exception as e:
        logging.error(f"Failed to send message to chat_id {chat_id}: {e}")


async def send_async_messages_to_admin(chat_id, text):
    try:
        await bot.send_message(chat_id,text=text, parse_mode=ParseMode.HTML)
        logging.info(f"Message sent to chat_id {chat_id}.")
        logging.info(f"Message sent to admin {text}.")
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
            f"Assalomu alaykum! Sizning nasiya savdo bo'yicha <b>{ payment.product }</b> xaridingizning  "
            f"keyingi to'lov sanasi {payment.next_payment_dates}. "
            f"To'lovni o'z vaqtida amalga oshiring."
        )
        asyncio.run(send_async_message(user_chat_id, message_text,payment.user.phone))

    logging.info("Celery task completed.")

from asgiref.sync import async_to_sync

@app.task
def send_daily_message_to_admin():
    """
    Celery task to send daily messages to admins regarding upcoming payments.
    """
    logging.info("Celery task started: Sending daily messages to admins...")

    # Get admin users
    admins = User.objects.filter(role="ADMIN").all()

    # Prepare date range
    today = date.today()
    five_days_later = today + timedelta(days=5)
    one_day_later = today + timedelta(days=1)

    # Fetch upcoming payments asynchronously
    upcoming_payments = async_to_sync(get_upcoming_payments)(one_day_later, five_days_later)

    for admin in admins:
        for payment in upcoming_payments:
            # Prepare the message for each admin
            user_chat_id = admin.chat_id  # Assuming `user` relation has a `chat_id` field
            message_text = (
                f"To'lov amalga oshirishi kerak bo'lgan mijoz: \n"
                f" <b>{payment.user.full_name}</b> - {payment.user.phone}\n "
                f"keyingi to'lov sanasi {payment.next_payment_dates}.\n "
                f"Maxsulot: <b>{payment.product}</b>."
            )

            # Send the message asynchronously
            try:
                async_to_sync(send_async_messages_to_admin)(user_chat_id, message_text)
                logging.info(f"Message successfully sent to admin chat_id {user_chat_id}.")
            except Exception as e:
                logging.error(f"Failed to send message to admin chat_id {user_chat_id}: {e}")

    logging.info("Celery task completed: Admin notifications sent.")


logging.info("Celery task completed.")
