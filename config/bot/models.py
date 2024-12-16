from datetime import date
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.db import models


class User(models.Model):
    chat_id = models.BigIntegerField(null=True, blank=True, default=0)
    full_name = models.CharField(max_length=255,null=True, blank=True)
    phone = models.CharField(max_length=255,null=True, blank=True)
    role = models.CharField(max_length=255,null=True,blank=True,
                            choices=[('ADMIN', 'admin'), ('USER', 'user')], default='USER')
    # client = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)




class Installment(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name="installments")
    product = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2,null=True)
    starter_payment = models.DecimalField(max_digits=10, decimal_places=2,null=True)
    payment_months = models.IntegerField()  # Total number of installment months
    additional_fee_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    start_date = models.DateField(null=True, blank=True)
    next_payment_dates = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=[('ACTIVE', 'Active'), ('COMPLETED', 'Completed')], default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product} ({self.user.full_name})"

    def calculate_overall_price(self):
        """
        Calculate the total price with the additional fee.
        """
        remaining_balance = self.price - self.starter_payment
        additional_fee = (remaining_balance * self.additional_fee_percentage) / 100
        return remaining_balance + additional_fee

    def calculate_monthly_payment(self):
        """
        Calculate the monthly payment amount.
        """
        overall_price = self.calculate_overall_price()
        if self.payment_months > 0:
            return overall_price / self.payment_months
        return Decimal(0)  # Return 0 if no payment months are provided

    def next_payment_date(self):
        """
        Calculate the next payment date based on the start date.
        """
        # Using payments.count() might cause issues, as it will not correctly count payments in the future installments.
        # Instead, we calculate based on the months passed.
        payments_made = self.payments.count()
        return self.start_date + relativedelta(months=payments_made + 1)

    def is_payment_overdue(self):
        """
        Check if a payment is overdue.
        """
        next_payment = self.next_payment_date()
        return date.today() > next_payment and self.status == "ACTIVE"

    def payment_history(self):
        """
        Returns a summary of the payment history for this installment.
        """
        payments = self.payments.all()
        total_paid = sum(payment.amount for payment in payments)
        remaining_balance = self.calculate_overall_price() - total_paid
        history = {
            "total_paid": total_paid,
            "remaining_balance": remaining_balance,
            "payments": [{"amount": payment.amount, "date": payment.payment_date} for payment in payments]
        }
        return history

    def update_status(self):
        """
        Check if the installment is fully paid and update the status to 'COMPLETED'.
        """
        total_paid = sum(payment.amount for payment in self.payments.all())
        overall_price = self.calculate_overall_price()
        if total_paid >= overall_price:
            self.status = "COMPLETED"
            self.save()



class Payment(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name="payments")
    installment = models.ForeignKey('Installment', on_delete=models.CASCADE, related_name="payments", null=True)
    payment_date = models.DateField(default=date.today())
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment of {self.amount} for {self.installment.product} on {self.payment_date}"

    def is_paid(self):
        """
        Determine if the payment is marked as paid.
        """
        # Example logic: Check if the payment is associated with an active installment
        return self.installment and self.installment.status == "COMPLETED"


