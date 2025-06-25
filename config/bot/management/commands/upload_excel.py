from django.core.management.base import BaseCommand
from bot.models import User, Installment, Category, Payment
from datetime import datetime
from decimal import Decimal
import pandas as pd

class Command(BaseCommand):
    help = 'Upload users, installments, and payments from Excel'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the Excel file')

    def handle(self, *args, **options):
        file_path = options['file_path']

        try:
            df = pd.read_excel(file_path)

            last_user = None
            last_installment = None
            last_start_date = None

            for _, row in df.iterrows():
                phone = str(row.get('Telefon raqami')).strip() if pd.notna(row.get('Telefon raqami')) else None
                name = str(row.get('Mijoz')).strip() if pd.notna(row.get('Mijoz')) else None
                category_name = str(row.get('Mahsulotlar guruhi')).strip() if pd.notna(row.get('Mahsulotlar guruhi')) else None
                product = str(row.get('Mahsulotlar')).strip() if pd.notna(row.get('Mahsulotlar')) else None
                payment_month=str(row.get("To'lov oylari")).strip() if pd.notna(row.get("To'lov oylari")) else None
                # If row has a user and installment info
                if phone and name and product:
                    user, _ = User.objects.get_or_create(phone=phone.split(".",)[0], defaults={"full_name": name})
                    category, _ = Category.objects.get_or_create(name=category_name)

                    first_payed_date = row.get("Payment Dates")
                    if pd.notna(first_payed_date):
                        try:
                            first_payed_date = datetime.strptime(str(first_payed_date).strip(), "%d %B %Y")
                        except ValueError:
                            print(f"❌ Invalid date format: {first_payed_date}")
                            first_payed_date = None
                    else:
                        created_val = row.get("Yaratilgan vaqti")
                        if pd.notna(created_val):
                            first_payed_date = datetime.strptime(str(created_val).strip(), "%d %B %Y")
                        else:
                            first_payed_date = None

                    date = str(row.get("Yaratilgan vaqti")).strip() if pd.notna(row.get("Yaratilgan vaqti")) else None
                    created_date = datetime.strptime(date, "%d-%B-%Y").date() if date else first_payed_date

                    status = 'COMPLETED' if str(row['Buyurtma statusi']).strip().upper() == 'COMPLETED' else 'ACTIVE'

                    try:
                        price = Decimal(str(row['Asil narxi']).replace("$", "").strip())
                        starter = Decimal(str(row['Avans']).replace("$", "").strip())
                        fee_percent = Decimal(str(row['Ustama foizi']).replace("%", "").strip())
                    except Exception as e:
                        self.stderr.write(self.style.ERROR(f"❌ Decimal parse error: {e}"))
                        continue

                    installment = Installment.objects.create(
                        user=user,
                        category=category,
                        product=product,
                        price=price,
                        starter_payment=starter,
                        payment_months=payment_month,
                        additional_fee_percentage=fee_percent,
                        start_date=first_payed_date,
                        next_payment_dates=None,
                        status=status,
                        created_at=created_date
                    )

                    last_user = user
                    last_installment = installment
                    last_start_date = first_payed_date

                # Handle To‘lovlar even if it's a continuation row
                if pd.notna(row.get("To‘lovlar")):
                    payment_text = str(row["To‘lovlar"])
                    if payment_text and ":" in payment_text:
                        entries = payment_text.split('\n')
                        for entry in entries:
                            try:
                                if ":" in entry:
                                    date_part, amount_part = entry.split(":")
                                    date_str = date_part.strip() + f" {last_start_date.year}"
                                    payment_date = datetime.strptime(date_str, "%d-%B %Y").date()
                                    amount = Decimal(amount_part.replace("$", "").strip())

                                    Payment.objects.create(
                                        user=last_user,
                                        installment=last_installment,
                                        payment_date=payment_date,
                                        amount=amount
                                    )
                            except Exception as e:
                                self.stderr.write(self.style.ERROR(f"❌ Payment parse error for {last_user.full_name if last_user else 'Unknown'}: {e}"))

            self.stdout.write(self.style.SUCCESS('✅ Data uploaded successfully'))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'❌ Error uploading data: {e}'))
