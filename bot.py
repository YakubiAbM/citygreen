import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import BOT_TOKEN, ADMIN_IDS
from db import init_db, register_user, get_user_role
from keyboards import get_admin_menu_kb, get_client_menu_kb
from aiogram.fsm.storage.memory import MemoryStorage

# ⚠️ Импортируем роутеры из созданных модулей
from handlers import client, admin
from handlers.fsm_admin import router as fsm_admin_router 

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# --- ХЭНДЛЕРЫ (НАЧАЛЬНЫЕ) ---

@dp.message(Command("start"))
async def command_start_handler(message: types.Message) -> None:
    """Обработка команды /start."""
    user_id = message.from_user.id
    username = message.from_user.username or f"id_{user_id}"
    
    # Определяем роль пользователя
    role = 'admin' if user_id in ADMIN_IDS else 'client'
    
    # Регистрируем/обновляем пользователя в базе данных
    await register_user(user_id, username, role)
    
    if role == 'admin':
        text = "👋 Добро пожаловать, Администратор! Вы в панели управления."
        kb = get_admin_menu_kb()
    else:
        text = "👋 Добро пожаловать в CityGreen! Выберите интересующий вас раздел."
        kb = get_client_menu_kb()
        
    await message.answer(text, reply_markup=kb)

# ... (остальные команды /menu и /help остаются без изменений) ...
@dp.message(Command("menu"))
async def command_menu_handler(message: types.Message) -> None:
    """Обработка команды /menu (возврат в основное меню)."""
    user_id = message.from_user.id
    role = await get_user_role(user_id)
    
    if role == 'admin':
        text = "↩️ Возврат в панель Администратора."
        kb = get_admin_menu_kb()
    else:
        text = "↩️ Возврат в главное меню клиента."
        kb = get_client_menu_kb()
        
    await message.answer(text, reply_markup=kb)

@dp.message(Command("help"))
async def command_help_handler(message: types.Message) -> None:
    """Обработка команды /help."""
    user_id = message.from_user.id
    role = await get_user_role(user_id)
    
    if role == 'admin':
        help_text = (
            "ℹ️ Справка по панели администратора:\n"
            "➕ **Добавить мастера**: Запускает диалог для внесения нового мастера с его контактами, ценой и фото.\n"
            "📢 **Сделать рассылку**: Отправляет ваше сообщение всем зарегистрированным клиентам.\n"
            "/start, /menu, /help: Основные команды."
        )
    else:
        help_text = (
            "ℹ️ Справка по CityGreen:\n"
            "📋 **Список мастеров**: Откроет категории (сантехник, электрик и т.д.), чтобы вы могли выбрать нужного специалиста.\n"
            "💬 **Связаться с менеджером**: Прямая ссылка для связи с нашим администратором.\n"
            "🧱 **Стройматериалы**: Раздел в разработке.\n"
            "/start, /menu, /help: Основные команды."
        )
        
    await message.answer(help_text)
# --- КОНЕЦ ОБЩИХ ХЭНДЛЕРОВ ---


async def main() -> None:
    """Основная функция запуска бота."""
    logging.info("Инициализация базы данных...")
    await init_db()
    logging.info("База данных готова.")

    # 🚀 Подключаем роутеры:
    # 1. Сначала FSM для админа (для '➕ Добавить мастера')
    dp.include_router(fsm_admin_router)
    # 2. Затем другие хэндлеры админа (для '📢 Сделать рассылку')
    dp.include_router(admin.router)
    # 3. И хэндлеры клиента
    dp.include_router(client.router)

    # Запуск процесса поллинга (получения новых сообщений)
    logging.info("Запуск бота...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен вручную.")
# bot.py (добавьте это в main())

async def main() -> None:
    # ...
    # ➡️ ДОБАВЬТЕ ЭТУ СТРОКУ, ЗАПУСТИТЕ ОДИН РАЗ И УДАЛИТЕ ЕЕ!
    await bot.delete_webhook(drop_pending_updates=True) 
    # ...
    logging.info("Запуск бота...")
    await dp.start_polling(bot)