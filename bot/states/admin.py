"""
FSM-состояния для действий администратора TAKLIVO.
"""
from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    # Работа с заказом
    entering_website_url = State()
    entering_client_message = State()
    WAITING_WEBSITE_URL = entering_website_url
    WAITING_CLIENT_MESSAGE = entering_client_message

    # Рассылка
    entering_broadcast_message = State()
    entering_broadcast_button = State()
    confirming_broadcast = State()

    # Промокоды
    entering_promo_code = State()
    entering_promo_discount = State()
    entering_promo_limit = State()
