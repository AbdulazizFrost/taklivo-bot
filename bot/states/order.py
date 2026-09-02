"""
FSM-состояния для процесса оформления заказа клиентом TAKLIVO.
"""
from aiogram.fsm.state import State, StatesGroup


class OrderStates(StatesGroup):
    # Выбор типа события
    choosing_event_type = State()

    # Выбор дизайна, тарифа и опций
    choosing_template = State()
    choosing_plan = State()
    choosing_options = State()

    # Данные свадьбы
    bride_name = State()
    groom_name = State()

    # Данные Дня рождения / Юбилея
    birthday_name = State()
    birthday_age = State()

    # Данные Суннат туя
    sunnat_child_name = State()
    sunnat_parents_name = State()

    # Общие данные
    wedding_date = State()
    wedding_time = State()
    venue = State()
    address = State()
    phone = State()

    # Медиа
    gallery_upload = State()
    music_upload = State()

    # Проверка, оплата и чек
    review = State()
    entering_promocode = State()
    payment = State()
    waiting_receipt = State()

    # Правки по готовому сайту
    revising = State()

    # Именные ссылки для гостей
    entering_guest_names = State()
