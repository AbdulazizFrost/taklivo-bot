"""
Пакет клавиатур для бота TAKLIVO.
"""
from bot.keyboards.client import (
    get_language_keyboard,
    get_main_menu_keyboard,
    get_about_keyboard,
    get_pricing_keyboard,
    get_event_type_keyboard,
    get_template_selection_keyboard,
    get_options_toggle_keyboard,
    get_gallery_upload_keyboard,
    get_music_upload_keyboard,
    get_order_preview_keyboard,
    get_edit_fields_keyboard,
    get_payment_keyboard,
    get_my_orders_keyboard,
    get_order_card_keyboard,
    get_client_website_review_keyboard,
    get_cancel_keyboard,
    get_back_cancel_keyboard,
)
from bot.keyboards.admin import (
    get_admin_main_keyboard,
    get_admin_order_actions_keyboard,
    get_admin_status_selection_keyboard,
    get_admin_orders_list_keyboard,
    get_admin_back_keyboard,
)

__all__ = [
    "get_language_keyboard",
    "get_main_menu_keyboard",
    "get_about_keyboard",
    "get_pricing_keyboard",
    "get_event_type_keyboard",
    "get_template_selection_keyboard",
    "get_options_toggle_keyboard",
    "get_gallery_upload_keyboard",
    "get_music_upload_keyboard",
    "get_order_preview_keyboard",
    "get_edit_fields_keyboard",
    "get_payment_keyboard",
    "get_my_orders_keyboard",
    "get_order_card_keyboard",
    "get_client_website_review_keyboard",
    "get_cancel_keyboard",
    "get_back_cancel_keyboard",
    "get_admin_main_keyboard",
    "get_admin_order_actions_keyboard",
    "get_admin_status_selection_keyboard",
    "get_admin_orders_list_keyboard",
    "get_admin_back_keyboard",
]
