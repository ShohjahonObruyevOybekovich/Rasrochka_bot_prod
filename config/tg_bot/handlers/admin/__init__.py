from tg_bot.buttons.reply import admin_btn


#admin_handlers

from tg_bot.handlers.admin.add_order import *
# from tg_bot.handlers.admin.add_payment import *
from tg_bot.handlers.admin.next_payments import *
from tg_bot.handlers.admin.start import *
from tg_bot.handlers.admin.orders import *
from tg_bot.handlers.admin.order_history import *


@dp.message(lambda msg : msg.text == admin_txt )
async def check_admin(message: Message) -> None:
    user = User.objects.filter(chat_id=message.from_user.id, role="ADMIN").first()
    if user is None:
        user = User.objects.filter(chat_id=message.from_user.id, role="USER").update(role="ADMIN")
        await message.answer(
            text=f"Assalomu alaykum <b><i>{message.from_user.username}</i></b> "
                 f"\nadmin paneldan foydalanish uchun tugmalardan birini tanlang 👇🏿",
            parse_mode="HTML",  # Enable HTML parsing
            reply_markup=admin_btn()
        )
    else:
        await message.answer(
            text=f"Assalomu alaykum <b><i>{message.from_user.username}</i></b> "
                 f"\nadmin paneldan foydalanish uchun tugmalardan birini tanlang 👇🏿",
            parse_mode="HTML",  # Enable HTML parsing
            reply_markup=admin_btn()
        )

@dp.message(lambda msg : msg.text == back_to_user )
async def back_to_admin(message: Message) -> None:
    await message.answer("User menusi :", reply_markup=menu_btn())
    return