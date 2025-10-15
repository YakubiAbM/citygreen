# handlers/client.py

from aiogram import Router, types, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from db import get_all_categories, get_masters_by_city_and_category 
from keyboards import (
    get_client_menu_kb, 
    get_masters_categories_kb, 
    get_contact_manager_kb,
    ADMIN_USERNAME 
)
from aiogram.enums import ParseMode
import asyncio

router = Router()

# ➡️ НОВЫЙ КЛАСС СОСТОЯНИЙ ДЛЯ ПОИСКА КЛИЕНТА
class ClientSearch(StatesGroup):
    wait_for_city = State()
    wait_for_category = State()

# --- Обработка меню клиента ---

@router.message(F.text == "💬 Связаться с менеджером")
async def cmd_contact_manager(message: types.Message):
    """Обработка кнопки 'Связаться с менеджером'."""
    await message.answer(
        f"Нажмите кнопку ниже, чтобы начать чат с администратором:\n"
        f"@{ADMIN_USERNAME}",
        reply_markup=get_contact_manager_kb()
    )

@router.message(F.text == "🧱 Стройматериалы")
async def cmd_materials_placeholder(message: types.Message):
    """Заглушка для будущей функции."""
    await message.answer("🚧 Раздел **'Стройматериалы'** находится в разработке. Скоро будет доступен!", parse_mode="Markdown")

# --- Просмотр списка мастеров (Начало поиска по городу) ---

@router.message(F.text == "📋 Список мастеров")
async def cmd_start_search_by_city(message: types.Message, state: FSMContext):
    """Начинает поиск, запрашивая город."""
    await message.answer(
        "🏙️ Введите **город**, в котором вам нужен мастер.\n"
        "*(Например, Москва, Санкт-Петербург, или часть названия)*"
    )
    await state.set_state(ClientSearch.wait_for_city)

# ➡️ ХЭНДЛЕР: Ожидание города
@router.message(ClientSearch.wait_for_city)
async def cmd_get_city_and_show_categories(message: types.Message, state: FSMContext):
    """Получает город и показывает категории."""
    city_name = message.text.strip()
    await state.update_data(city=city_name)
    
    categories = await get_all_categories()
    
    if not categories:
        await state.clear()
        await message.answer("❌ В базе данных пока нет ни одного мастера.")
        return
        
    kb = get_masters_categories_kb(categories)
    await message.answer(
        f"✅ Город **{city_name}** принят.\n\n"
        "Выберите интересующую вас **категорию** мастера:", 
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await state.set_state(ClientSearch.wait_for_category)

# ➡️ ХЭНДЛЕР: Обработка выбора категории и вывод результатов
@router.callback_query(F.data.startswith("show_masters_"), ClientSearch.wait_for_category)
async def cb_show_masters_by_city_and_category(callback: types.CallbackQuery, state: FSMContext):
    """Обрабатывает выбор категории, ищет мастеров по городу+категории и выводит результат."""
    await callback.answer("Ищу мастеров в выбранной категории...")
    
    data = await state.get_data()
    city = data.get('city', 'Неизвестный город')
    
    # Сразу очищаем FSM
    await state.clear() 
    
    category = callback.data.split("show_masters_")[1]
    
    masters = await get_masters_by_city_and_category(city, category) 
    
    if not masters:
        await callback.message.edit_text(
            f"❌ В городе **{city}** нет мастеров в категории **'{category}'**.", 
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # Редактируем сообщение с кнопками категорий
    await callback.message.edit_text(f"🛠️ **Найдено мастеров в городе {city} (Категория '{category}')**:", parse_mode=ParseMode.MARKDOWN)
    
    # Отправляем карточки мастеров
    for master in masters:
        photos_str = master['photos']
        photo_ids = photos_str.split(',') if photos_str else []
        
        caption = (
            f"👤 **Имя:** {master['name']}\n"
            f"🏙️ **Город:** {master['city']}\n"
            f"💰 **Цена:** {master['price']}\n"
            f"📞 **Контакт:** `{master['contact']}`"
        )
        
        try:
            if photo_ids and photo_ids[0]:
                await callback.message.bot.send_photo(
                    chat_id=callback.message.chat.id,
                    photo=photo_ids[0], 
                    caption=caption,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await callback.message.bot.send_message(
                    chat_id=callback.message.chat.id,
                    text=f"Карточка мастера:\n{caption}",
                    parse_mode=ParseMode.MARKDOWN
                )
        except Exception as e:
            await callback.message.bot.send_message(
                chat_id=callback.message.chat.id,
                text=f"❌ Ошибка загрузки карточки мастера {master['name']}. Попробуйте позже.",
                parse_mode=ParseMode.MARKDOWN
            )
            await asyncio.sleep(0.5)

# --- ХЭНДЛЕР: Обработка кнопки "Назад в меню" ---
@router.callback_query(F.data == "back_to_menu")
async def cb_back_to_menu(callback: types.CallbackQuery, state: FSMContext):
    """Обрабатывает кнопку 'Назад в меню' и сбрасывает FSM."""
    await callback.answer()
    await state.clear() 
    
    try:
        await callback.message.delete() 
    except:
        pass
        
    await callback.message.answer(
        "↩️ Вы вернулись в главное меню клиента.",
        reply_markup=get_client_menu_kb()
    )