from datetime import datetime, timedelta, date
from celery import shared_task
from django.utils.timezone import now
from bot.models import Payment, User, Installment
from asgiref.sync import sync_to_async



from aiogram import Bot

async def send_notification(bot: Bot, user_id: int, message: str):
    await bot.send_message(user_id, message)


@shared_task
def send_payment_reminders():
    today = now().date()
    reminders = [10, 3, 1]  # Days before payment due date
    users_to_notify = []

    @sync_to_async
    def get_upcoming_payments(end_date):
        return Installment.objects.filter(
            next_payment_dates__gte=date.today(),  # Payments due today or later
            next_payment_dates__lte=end_date,  # Payments due on or before the 10th day
            status="ACTIVE"
        )

    for reminder in reminders:
        # Calculate the reminder date
        reminder_date = today + timedelta(days=reminder)

        # Find payments due on the reminder date
        due_payments = get_upcoming_payments(reminder)

        for payment in due_payments:
            users_to_notify.append({
                "Mijoz ismi": payment.user.full_name,
                "Telefon raqami": payment.user.phone,
                "To'lov sanasi": payment.next_payment_dates,
                "Miqdor": payment.amount,
                "To'lovgacha qolgan kun": reminder,
            })

    # Send notifications to users
    for user_data in users_to_notify:
        send_notification_to_user(user_data)


def send_notification_to_user(user_data):
    message = (f"Assalomu alaykum! Sizning keyingi {user_data['Miqdor']} $ to'lovingiz {user_data["To'lov sanasi"]} kunida bo'lishi kerak."
               f" {user_data["To'lovgacha qolgan kun"]} kun qoldi!")
    send_notification(user_id=user_data['user_id'], message=message)  # Replace this with your notification logic
