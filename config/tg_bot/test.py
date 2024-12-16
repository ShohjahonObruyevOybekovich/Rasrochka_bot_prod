from datetime import datetime

from dateutil.relativedelta import relativedelta
from icecream import ic

from bot.models import Payment, Installment


def process_monthly_payment(user, order_id, amount):
    try:
        # Get all payments for the current month for the specific user
        current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_month_start = current_month_start + relativedelta(months=1)

        # Filter payments for the user and the month
        one_month_payments = Payment.objects.filter(
            installment__payment_months__gt=current_month_start,
            installment__payment_months__lt=next_month_start,
        )

        # Sum up payments for the month
        total_monthly_payments = sum(payment.amount for payment in one_month_payments)
        ic(total_monthly_payments)

        # Fetch the installment object
        installment = Installment.objects.get(id=order_id, user=user)

        # Check payment conditions
        if amount >= installment.calculate_monthly_payment() or total_monthly_payments:
            new_payment_date = installment.next_payment_dates.replace(day=1) + relativedelta(months=1)
            installment.next_payment_dates = new_payment_date
            installment.save()

            print(f"Installment updated: Next payment date is now {new_payment_date}.")
        else:
            print("Payment amount is insufficient or already covered.")

    except Installment.DoesNotExist:
        print("Installment with the given ID does not exist.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

def format_phone_number(phone_number: str) -> str:

    phone_number = ''.join(c for c in phone_number if c.isdigit())

    # Prepend +998 if missing
    if phone_number.startswith('998'):
        phone_number = '+' + phone_number
    elif not phone_number.startswith('+998'):
        phone_number = '+998' + phone_number

    # Check final phone number length
    if len(phone_number) == 13:
        return phone_number
    else:
        raise ValueError("Invalid phone number length")


import re

def extract_payment_amount(text):
    """
    Extracts the first numeric value from a given string and returns it as a number.
    Handles cases where numbers are embedded within words or surrounded by text.

    Args:
        text (str): The input string.

    Returns:
        float: The extracted number or None if no number is found.
    """
    # Find the first match for a number in the string
    match = re.search(r'\d+(\.\d+)?', text)  # Matches integers or decimals
    if match:
        return float(match.group())  # Convert the matched string to a float
    return None  # Return None if no numbers are found
