from aiogram import Bot, Dispatcher, F
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command

from asgiref.sync import sync_to_async
from icecream import ic
from bot.models import Payment, User
from dispatcher import dp
from tg_bot.buttons.reply import admin_btn
from tg_bot.state.main import PaymentState
from tg_bot.buttons.text import *


@dp.message(lambda msg : msg.text == "add_payments")
async def start_payment(message: Message, state: FSMContext):
    await state.set_state(PaymentState.inline_search)
    await message.answer("Ismi yoki raqami bo'yicha qidiring:")


@dp.inline_query()
async def inline_search_handler(inline_query: InlineQuery):
    query = inline_query.query.strip()  # Get user input
    results = []

    # Search users in the database by name or phone number
    users = User.objects.filter(full_name__icontains=query) | User.objects.filter(phone__icontains=query)

    # Build inline query results
    for user in users:
        results.append(
            InlineQueryResultArticle(
                id=str(user.id),
                title=f"{user.full_name} - {user.phone}",
                input_message_content=InputTextMessageContent(
                    message_text=f"User: {user.full_name}\n Phone: {user.phone} \n ID: {user.id}"  # Pass the user_id here
                ),
            )
        )

    await inline_query.answer(results, cache_time=0, is_personal=True)


@dp.message(PaymentState.inline_search)
async def handle_user_selection(message: Message, state: FSMContext):

    user_id = message.text.split("ID:")[1].strip()  # Extract the ID from the message
    await state.update_data(user_id=user_id)
    await state.set_state(PaymentState.enter_amount)
    await message.answer("To'lov miqdorini kiriting $ hisobida:")



# Handle payment amount
@dp.message(PaymentState.enter_amount)
async def handle_payment_amount(message: Message, state: FSMContext):
    amount = message.text.strip()
    data = await state.get_data()
    user_id = data.get("user_id")
    ic(user_id)

    try:
        # Validate that amount is a valid number
        amount = float(amount)  # Ensuring that the amount is numeric

        # Save payment to the database
        user = User.objects.get(id=user_id)
        query = Payment.objects.create(user_id=user.id, amount=amount)  # Provide payment_date

        await message.answer(f"To'lov qo'shildi: {amount} $.", reply_markup=admin_btn())

        await state.clear()
    except ValueError:
        await state.set_state(PaymentState.enter_amount)
        await message.answer("To'lov miqdori noto'g'ri formatda. Iltimos, raqam kiriting.")
    except Exception as e:
        ic(e)
        await message.answer("To'lov qo'shishda xatolik yuz berdi. Qaytadan urinib ko'ring.", reply_markup=admin_btn())

