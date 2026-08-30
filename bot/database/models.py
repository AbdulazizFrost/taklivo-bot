"""
Модели данных и перечисления статусов для бота TAKLIVO.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class OrderStatus(str, Enum):
    NEW = "NEW"
    WAITING_PAYMENT = "WAITING_PAYMENT"
    PAYMENT_REVIEW = "PAYMENT_REVIEW"
    PAID = "PAID"
    IN_PROGRESS = "IN_PROGRESS"
    PREVIEW = "PREVIEW"
    REVISION = "REVISION"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

    @classmethod
    def all_statuses(cls) -> list[str]:
        return [status.value for status in cls]


class PaymentStatus(str, Enum):
    UNPAID = "UNPAID"
    REVIEW = "REVIEW"
    PAID = "PAID"
    REJECTED = "REJECTED"


@dataclass
class User:
    id: int
    telegram_id: int
    username: Optional[str]
    first_name: Optional[str]
    language: str
    created_at: str


@dataclass
class Order:
    id: int
    user_id: int
    telegram_id: int
    status: str
    template_id: str
    template_name: str
    plan: str
    bride_name: str
    groom_name: str
    wedding_date: str
    wedding_time: str
    venue: str
    address: str
    phone: str
    rsvp_enabled: bool
    map_enabled: bool
    music_enabled: bool
    gallery_enabled: bool
    dresscode_enabled: bool
    schedule_enabled: bool
    second_language_enabled: bool
    total_price: int
    payment_status: str
    payment_receipt_file_id: Optional[str]
    website_url: Optional[str]
    revision_text: Optional[str]
    created_at: str
    updated_at: str


@dataclass
class OrderPhoto:
    id: int
    order_id: int
    file_id: str
    file_unique_id: Optional[str]
    created_at: str


@dataclass
class OrderMusic:
    id: int
    order_id: int
    file_id: str
    file_name: Optional[str]
    created_at: str
