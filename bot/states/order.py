"""
FSM-состояния для процесса оформления заказа клиентом.
"""
from aiogram.fsm.state import State, StatesGroup


class OrderStates(StatesGroup):
    # Выбор дизайна, тарифа и опций
    choosing_template = State()
    choosing_plan = State()
    choosing_options = State()

    # Данные свадьбы
    bride_name = State()
    groom_name = State()
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
    payment = State()
    waiting_receipt = State()

    # Правки по готовому сайту
    revising = State()

    # Алиасы для обратной совместимости
    SELECT_TEMPLATE = choosing_template
    SELECT_PLAN = choosing_plan
    SELECT_OPTIONS = choosing_options
    ENTER_BRIDE_NAME = bride_name
    ENTER_GROOM_NAME = groom_name
    ENTER_DATE = wedding_date
    ENTER_TIME = wedding_time
    ENTER_VENUE = venue
    ENTER_ADDRESS = address
    ENTER_PHONE = phone
    UPLOAD_GALLERY = gallery_upload
    UPLOAD_MUSIC = music_upload
    CONFIRM_ORDER = review
    UPLOAD_RECEIPT = waiting_receipt
    ENTER_REVISION = revising
