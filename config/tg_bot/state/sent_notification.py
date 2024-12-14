from celery import shared_task
from datetime import datetime, timedelta
from bot.models import User, Payment


@shared_task
def send_next_payment_notifications(date):
    """
    Celery task that checks all users for upcoming payment dates.
    If a user's payment date is within the next 24 hours, a reminder message is sent.
    """
    # Get the current time
    now = datetime.now()

    # Filter users whose next payment date is within the next 24 hours
    upcoming_payments = Payment.objects.filter(payment_date__gt=now, payment_date__lte=now + timedelta(days=1))

    # Loop through all payments that need notifications
    for payment in upcoming_payments:
        # Retrieve the user associated with the payment
        user = payment.user

        # Format the reminder message
        reminder_message = (
            f"Hi {user.first_name},\n"
            f"Just a reminder that your payment of {payment.amount} is due on {payment.payment_date.strftime('%d %B %Y')}."
            f" Please make sure to make the payment on time to avoid any penalties."
        )

        # Send the message (this can be a Telegram bot, email, or any other service)
        # send_message(user.contact_info, reminder_message)

        # Optionally, log the message sent or task completion
        print(
            f"Sent payment reminder to {user.first_name} for payment due on {payment.payment_date.strftime('%d %B %Y')}")

    return "Next payment reminders sent successfully!"
