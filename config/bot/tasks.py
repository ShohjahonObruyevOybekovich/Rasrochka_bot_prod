import asyncio
from celery import Celery
from aiogram import Bot, Dispatcher
from dispatcher import TOKEN  # Assuming dispatcher.py provides TOKEN

# Initialize Celery app
celery_app = Celery('tasks', broker='redis://localhost:6379/0')

# Initialize Bot and Dispatcher
bot = Bot(TOKEN)
dp = Dispatcher()


import asyncio

def send_async_message(chat_id, text):
    asyncio.run(bot.send_message(chat_id, text))


# Wrapper to send async message
def send_async_message(chat_id, text):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot.send_message(chat_id, text))

# Celery task to send a message
import logging


@celery_app.task
def send_daily_message():
    logging.basicConfig(level=logging.INFO)
    logging.info("Celery task started: Sending daily message...")

    user_chat_id = "5995495508"
    message_text = "Good morning! This is your daily message."
    try:
        send_async_message(user_chat_id, message_text)
        logging.info("Message sent successfully.")
    except Exception as e:
        logging.error(f"Error sending message: {e}")