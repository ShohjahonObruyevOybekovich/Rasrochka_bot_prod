from django.contrib import admin
from bot.models import User, Installment, Payment

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'phone', 'role', 'created_at']
    search_fields = ['full_name', 'phone']
    list_filter = ["full_name",'role', 'created_at']

@admin.register(Installment)
class InstallmentAdmin(admin.ModelAdmin):
    list_display = ["id",'user', 'product', 'price', 'starter_payment', 'payment_months', 'start_date', 'status', 'next_payment_dates']
    search_fields = ['product', 'user__full_name']
    list_filter = ['status', 'start_date']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'installment', 'payment_date', 'amount', 'created_at']
    search_fields = ['user__full_name', 'installment__product']
    list_filter = ['payment_date', 'installment__status']
