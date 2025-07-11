from django.contrib import admin
from pandas import to_datetime

from bot.models import User, Installment, Payment, Sms, Category

# bot/admin.py

from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import User, Installment, Category, Payment
import pandas as pd
from datetime import datetime
from decimal import Decimal


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'phone', 'role', 'created_at']
    search_fields = ['full_name', 'phone']
    list_filter = ["full_name",'role', 'created_at']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'installment', 'payment_date', 'amount', 'created_at']
    search_fields = ['user__full_name', 'installment__product']
    list_filter = ['payment_date', 'installment__status']

@admin.register(Sms)
class SmsAdmin(admin.ModelAdmin):
    list_display = ["count","updated_at"]

@admin.register(Category)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["name"]



class ExcelUploadAdmin(admin.ModelAdmin):
    list_display = ["id",'user', 'product', 'price', 'starter_payment', 'payment_months', 'start_date', 'status', 'next_payment_dates']
    search_fields = ['product', 'user__full_name']
    list_filter = ['status', 'start_date']
    change_list_template = "admin/excel_upload.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("upload-excel/", self.admin_site.admin_view(self.upload_excel), name="upload_excel"),
        ]
        return custom_urls + urls

    def upload_excel(self, request):
        if request.method == "POST" and request.FILES.get("excel_file"):
            try:
                df = pd.read_excel(request.FILES["excel_file"])

                last_user = None
                last_installment = None
                last_start_date = None

                for _, row in df.iterrows():
                    phone = str(row.get('Telefon raqami')).strip() if pd.notna(row.get('Telefon raqami')) else None

                    name = str(row.get('Mijoz')).strip() if pd.notna(row.get('Mijoz')) else None

                    category_name = str(row.get('Mahsulotlar guruhi')).strip() if pd.notna(row.get('Mahsulotlar guruhi')) else None

                    product = str(row.get('Mahsulotlar')).strip() if pd.notna(row.get('Mahsulotlar')) else None

                    payment_month = str(row.get("To'lov oylari")).strip() if pd.notna(
                        row.get("To'lov oylari")) else None
                    payment_month = int(float(payment_month)) if payment_month is not None else None

                    print(row)

                    if phone and name and product:
                        user, _ = User.objects.get_or_create(phone=phone.split(".",)[0], defaults={"full_name": name})

                        category, _ = Category.objects.get_or_create(name=category_name)

                        # Handle first payment date logic - matching command logic
                        def try_parse_date(val):
                            try:
                                return to_datetime(str(val).strip(), dayfirst=True).to_pydatetime()
                            except Exception:
                                return None

                        first_payed_date = row.get("Payment Dates")
                        first_payed_date = try_parse_date(first_payed_date)

                        if not first_payed_date:
                            created_val = row.get("Yaratilgan vaqti")
                            first_payed_date = try_parse_date(created_val)

                        # Handle created date - matching command logic

                        def parse_flexible_date(date_str):
                            for fmt in ("%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%d/%m/%Y %H:%M", "%Y-%m-%d"):
                                try:
                                    return datetime.strptime(date_str, fmt)
                                except ValueError:
                                    continue
                            raise ValueError(f"Unsupported date format: {date_str}")

                        date_str = str(row.get("Yaratilgan vaqti")).strip() if pd.notna(
                            row.get("Yaratilgan vaqti")) else None
                        created_date = parse_flexible_date(date_str) if date_str else first_payed_date

                        status = 'COMPLETED' if str(row['Buyurtma statusi']).strip().upper() == 'COMPLETED' else 'ACTIVE'

                        try:
                            price = Decimal(str(row['Asil narxi']).replace("$", "").strip())
                            starter = Decimal(str(row['Avans']).replace("$", "").strip())
                            fee_percent = Decimal(str(row['Ustama foizi']).replace("%", "").strip())
                        except Exception as e:
                            messages.error(request, f"Decimal parse error: {e}")
                            continue

                        installment = Installment.objects.create(
                            user=user,
                            category=category,
                            product=product,
                            price=price,
                            starter_payment=starter,
                            payment_months=payment_month,
                            additional_fee_percentage=fee_percent,
                            start_date=first_payed_date,  # Use first_payed_date like command
                            next_payment_dates=None,
                            status=status,
                            created_at=created_date
                        )

                        last_user = user
                        last_installment = installment
                        last_start_date = first_payed_date


                    if pd.notna(row.get("To'lovlar")):
                        payment_text = str(row["To'lovlar"])

                        print("--------------")
                        print(payment_text)

                        if payment_text and ":" in payment_text:
                            entries = payment_text.split('\n')
                            UZBEK_MONTHS = {
                                "Yanvar": "January",
                                "Fevral": "February",
                                "Mart": "March",
                                "Aprel": "April",
                                "May": "May",
                                "Iyun": "June",
                                "Iyul": "July",
                                "Avgust": "August",
                                "Sentabr": "September",
                                "Oktabr": "October",
                                "Noyabr": "November",
                                "Dekabr": "December"
                            }
                            for entry in entries:
                                try:
                                    if ":" in entry:
                                        date_part, amount_part = entry.split(":")
                                        month_uz = date_part.strip().split("-")[1]

                                        if not month_uz:
                                            raise ValueError(f"Unknown Uzbek month: {month_uz}")

                                        day = date_part.strip().split("-")[0]
                                        date_str = f"{day}-{month_uz} {last_start_date.year}"
                                        payment_date = datetime.strptime(date_str, "%d-%B %Y").date()
                                        amount = Decimal(amount_part.replace("$", "").strip())

                                        Payment.objects.create(
                                            user=last_user,
                                            installment=last_installment,
                                            payment_date=payment_date,
                                            amount=amount
                                        )
                                except Exception as e:
                                    messages.error(request, f"Payment parse error for {last_user.full_name if last_user else 'Unknown'}: {e}")

                messages.success(request, "✅ Excel data imported successfully!")
                return redirect("..")

            except Exception as e:
                messages.error(request, f"❌ Error processing Excel: {e}")
                return redirect("..")

        return render(request, "admin/excel_upload_form.html")


# Optionally, register it on a model to make it visible
from django.contrib import admin
admin.site.register(Installment, ExcelUploadAdmin)


