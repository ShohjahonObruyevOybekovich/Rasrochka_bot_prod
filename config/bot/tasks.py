import os
import logging
from requests import post
from datetime import date, timedelta
from bot.models import Installment, User
from dotenv import load_dotenv
from config.celery import app
load_dotenv()
# Celery setup
# app = Celery('tasks', broker='redis://localhost:6379/0')

# Logger setup
logging.basicConfig(level=logging.INFO)


class TelegramBot:
    HOST = "https://api.telegram.org/bot"

    def __init__(self):
        # Get token from environment variables


        token = os.getenv("BOT_TOKEN")
        if not token:
            raise ValueError("Telegram bot TOKEN is missing! Set the TOKEN environment variable.")
        self.base_url = self.HOST + token

    def send_message(
        self,
        chat_id,
        text,
        reply_markup=None,
        parse_mode="HTML",
    ):
        """
        Sends a message via Telegram Bot API.
        """
        url = self.base_url + "/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
        }

        # Add reply markup if provided
        if reply_markup:
            data["reply_markup"] = reply_markup.to_json()

        # Send the request
        try:
            res = post(url, json=data)
            res.raise_for_status()  # Raise HTTP errors if they occur
            logging.info(f"Message sent to chat_id {chat_id}: {text}")
            return res.json()
        except Exception as e:
            logging.error(f"Failed to send message to chat_id {chat_id}: {e}")
            return None


# Instantiate the Telegram bot
bot = TelegramBot()


@app.task
def send_daily_message():
    """
    Celery task to send daily messages for upcoming payments.
    """
    logging.info("Celery task started: Sending daily user notifications...")

    # Define date range
    today = date.today()
    one_day_later = today + timedelta(days=1)
    five_days_later = today + timedelta(days=5)

    # Fetch upcoming payments
    upcoming_payments = Installment.objects.filter(
        next_payment_dates__gte=one_day_later,
        next_payment_dates__lte=five_days_later,
        status="ACTIVE"
    )

    for payment in upcoming_payments:
        user_chat_id = payment.user.chat_id
        print(user_chat_id)
        user_phone = payment.user.phone
        message_text = (
            f"Assalomu alaykum! Sizning nasiya savdo bo'yicha <b>{payment.product}</b> xaridingizning "
            f"keyingi to'lov sanasi {payment.next_payment_dates}. "
            f"To'lovni o'z vaqtida amalga oshiring."
        )

        # Send the notification
        bot.send_message(user_chat_id, message_text)

    logging.info("Celery task completed: User notifications sent.")


@app.task
def send_daily_message_to_admin():
    """
    Celery task to send daily messages to admins about upcoming payments.
    """
    logging.info("Celery task started: Sending admin notifications...")

    # Fetch admins
    admins = User.objects.filter(role="ADMIN")

    # Define date range
    today = date.today()
    one_day_later = today + timedelta(days=1)
    five_days_later = today + timedelta(days=5)

    # Fetch upcoming payments
    upcoming_payments = Installment.objects.filter(
        next_payment_dates__gte=one_day_later,
        next_payment_dates__lte=five_days_later,
        status="ACTIVE"
    )

    for admin in admins:
        admin_chat_id = admin.chat_id
        print(admin_chat_id)


        for payment in upcoming_payments:
            user_full_name = payment.user.full_name
            user_phone = payment.user.phone
            message_text = (
                f"To'lov amalga oshirishi kerak bo'lgan mijoz: \n"
                f"<b>{user_full_name}</b> - {user_phone}\n"
                f"Keyingi to'lov sanasi: {payment.next_payment_dates}.\n"
                f"Maxsulot: <b>{payment.product}</b>."
            )

            # Send the admin notification
            bot.send_message(admin_chat_id, message_text)

    logging.info("Celery task completed: Admin notifications sent.")
