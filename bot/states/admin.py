"""
FSM-состояния для действий администратора.
"""
from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    entering_website_url = State()
    entering_client_message = State()
    WAITING_WEBSITE_URL = entering_website_url
    WAITING_CLIENT_MESSAGE = entering_client_message
