"""
Сервис расчета стоимости свадебного приглашения TAKLIVO.
Работает по принципу чистого конструктора: Базовая цена + выбранные функции.
"""
from dataclasses import dataclass
from typing import Any
from config import config
from bot.locales import get_text


@dataclass(frozen=True)
class CalculationResult:
    base_price: int
    selected_options: dict[str, bool]
    extra_options_cost: list[tuple[str, int]]  # Список (название, цена)
    extra_options_total: int
    total_price: int


class PriceCalculator:
    @staticmethod
    def calculate(
        options: dict[str, bool],
        lang: str = "ru",
        plan_id: str | None = None,
    ) -> CalculationResult:
        """
        Рассчитывает итоговую стоимость: Базовая цена + выбранные функции.
        """
        base_price = config.BASE_PRICE
        extra_prices = config.get_extra_options_prices()
        extra_costs: list[tuple[str, int]] = []
        extra_total = 0

        option_keys = [
            "timer",
            "rsvp",
            "map",
            "gallery",
            "music",
            "dresscode",
            "schedule",
            "second_language",
        ]

        for key in option_keys:
            if options.get(key, False):
                price = extra_prices.get(key, 0)
                opt_name = get_text(lang, f"option_{key}")
                extra_costs.append((opt_name, price))
                extra_total += price

        total_price = base_price + extra_total

        return CalculationResult(
            base_price=base_price,
            selected_options=options,
            extra_options_cost=extra_costs,
            extra_options_total=extra_total,
            total_price=total_price,
        )


calculator = PriceCalculator()


def calculate_total(options: dict[str, bool], lang: str = "ru", plan_id: str | None = None) -> CalculationResult:
    """
    Удобная функция расчета итоговой стоимости заказа.
    """
    return calculator.calculate(options=options, lang=lang, plan_id=plan_id)
