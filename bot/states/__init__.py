"""
Пакет состояний FSM.
"""
from bot.states.order import OrderStates, ClientStates
from bot.states.admin import AdminStates

__all__ = ["OrderStates", "ClientStates", "AdminStates"]
