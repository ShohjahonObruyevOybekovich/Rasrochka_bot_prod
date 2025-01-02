from aiogram.fsm.state import StatesGroup, State


class Add_order(StatesGroup):
    phone = State()
    user_name = State()
    product_category = State()
    product_name = State()
    product_price = State()
    avans = State()
    rasrochka_vaqti = State()
    ustama = State()
    payment_date = State()

class Order_history(StatesGroup):
    phone = State()

class PaymentState(StatesGroup):
    inline_search = State()
    enter_amount = State()
    phone = State()

class PaymentFlow(StatesGroup):
    customer_selection = State()
    order_selection = State()
    change_monthes = State()
    add_payment = State()
    enter_amount = State()
    edit_fee = State()

class NextPayment(StatesGroup):
    next_10_days = State()
    overdue = State()


class Messeage(StatesGroup):
    phone = State()
