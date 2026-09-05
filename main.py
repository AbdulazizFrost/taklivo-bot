"""
Главный модуль запуска Telegram-бота TAKLIVO.
Поддерживает как локальный запуск, так и бесплатный облачный хостинг (Render, Koyeb, Railway).
"""
import asyncio
import logging
import os
import sys

# Настройка UTF-8 для консоли Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    BotCommand,
    BotCommandScopeDefault,
    BotCommandScopeChat,
    ErrorEvent,
)

from bot.database import db
from bot.handlers import client_router, order_router, admin_router
from bot.middlewares import UserTrackerMiddleware
from bot.services import reminder
from config import config

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("taklivo_bot")


async def health_check(request: web.Request) -> web.Response:
    """Эндпоинт проверки здоровья для бесплатных облачных хостингов (Render/Koyeb)."""
    return web.json_response({"status": "ok", "service": "TAKLIVO Wedding Bot", "database": "connected"})


async def start_web_server() -> web.AppRunner | None:
    """Запуск легковесного HTTP сервера для облачных платформ и REST API для сайтов."""
    port = int(os.getenv("PORT", "8080"))
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)
    
    # Регистрация REST API для сайтов-приглашений (HTML / Next.js / Astro)
    from bot.api import setup_api_routes
    setup_api_routes(app)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    try:
        await site.start()
        logger.info(f"HTTP Health-сервер и REST API запущены на порту {port}")
        return runner
    except Exception as e:
        logger.warning(f"HTTP Health-сервер не запущен (некритично для локального запуска): {e}")
        return None


async def run_keep_alive_loop() -> None:
    """Периодический опрос собственного сервера для предотвращения спящего режима на бесплатных тарифах."""
    url = os.getenv("RENDER_EXTERNAL_URL")
    if not url:
        return
    health_url = f"{url.rstrip('/')}/health"
    logger.info(f"Keep-alive сервис активирован: {health_url}")
    await asyncio.sleep(60)
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(health_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    logger.debug(f"Keep-alive ping status: {resp.status}")
        except Exception as e:
            logger.debug(f"Keep-alive ping warning: {e}")
        await asyncio.sleep(600)


async def set_bot_commands(bot: Bot) -> None:
    """
    Установка команд в меню:
    - Обычные пользователи видят ТОЛЬКО /start.
    - Администраторы видят /start и /admin.
    """
    user_commands = [
        BotCommand(command="start", description="Главное меню / Asosiy menyu"),
    ]
    admin_commands = [
        BotCommand(command="start", description="Главное меню / Asosiy menyu"),
        BotCommand(command="admin", description="👑 Панель администратора"),
    ]

    try:
        await bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())
        for admin_id in config.ADMIN_IDS:
            try:
                await bot.set_my_commands(
                    admin_commands,
                    scope=BotCommandScopeChat(chat_id=admin_id),
                )
            except Exception as e:
                logger.warning(f"Не удалось установить меню для админа {admin_id}: {e}")
    except Exception as e:
        logger.warning(f"Не удалось установить команды меню: {e}")


async def global_error_handler(event: ErrorEvent) -> None:
    """Глобальный обработчик непредвиденных ошибок."""
    logger.error(f"Ошибка в обработчике: {event.exception}", exc_info=True)


async def main() -> None:
    """Точка входа и инициализация приложения."""
    logger.info("Запуск Telegram-бота TAKLIVO...")

    # Проверка переменных окружения
    config.validate()

    # Инициализация базы данных
    await db.init()
    if config.DATABASE_URL and config.DATABASE_URL.startswith(("postgres://", "postgresql://")):
        logger.info("База данных успешно подключена (Облачный PostgreSQL / Supabase).")
    else:
        logger.info(f"База данных успешно подключена ({config.DATABASE_PATH}).")

    # Инициализация HTTP сервера для бесплатного хостинга (Render / Koyeb)
    web_runner = await start_web_server()

    # Инициализация бота и диспетчера
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Регистрация обработчиков
    dp.errors.register(global_error_handler)
    dp.message.middleware(UserTrackerMiddleware())
    dp.callback_query.middleware(UserTrackerMiddleware())
    dp.include_router(admin_router)
    dp.include_router(order_router)
    dp.include_router(client_router)

    # Настройка персонального меню
    await set_bot_commands(bot)

    # Фоновые периодические задачи
    reminder_task = asyncio.create_task(reminder.run_reminder_loop(bot))
    keep_alive_task = asyncio.create_task(run_keep_alive_loop())

    logger.info(f"Бот TAKLIVO успешно запущен. ID администраторов: {config.ADMIN_IDS}")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        reminder_task.cancel()
        keep_alive_task.cancel()
        if web_runner:
            await web_runner.cleanup()
        await bot.session.close()
        logger.info("Бот TAKLIVO остановлен.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот завершил работу.")
