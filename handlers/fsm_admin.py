# handlers/fsm_admin.py

from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram import Router, types, F
from db import add_master
from keyboards import get_master_photo_kb, get_master_category_kb, get_admin_menu_kb 
from config import ADMIN_IDS 
from typing import List

# Инициализация роутера и фильтр админа
router = Router()
router.message.filter(F.from_user.id.in_(ADMIN_IDS))
router.callback_query.filter(F.from_user.id.in_(ADMIN_IDS))

# Определение состояний
class AddMaster(StatesGroup):
    """Класс состояний для пошагового добавления нового мастера."""
    category = State()
    name = State()
    city = State()             
    price = State()
    contact = State()
    photos = State() 

# --- Обработка начала диалога ---

@router.message(F.text == "➕ Добавить мастера")
async def cmd_add_master_start(message: types.Message, state: FSMContext):
    """Начинает процесс добавления мастера, предлагая выбор категории кнопками."""
    await message.answer(
        "🛠️ Выберите **категорию мастера** из списка:",
        reply_markup=get_master_category_kb(), 
        parse_mode="Markdown"
    )
    await state.set_state(AddMaster.category)

# --- Обработка выбора категории кнопкой ---

@router.callback_query(F.data.startswith("select_cat_"), AddMaster.category)
async def process_category_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обрабатывает нажатие кнопки категории."""
    await callback.answer() 
    
    category = callback.data.split("select_cat_")[1]
    
    await state.update_data(category=category)
    
    await callback.message.edit_text(
        f"✅ Выбрана категория: **{category}**.\n\n"
        "✍️ Теперь введите **имя** мастера (например, Иван Иванов).",
        parse_mode="Markdown",
        reply_markup=None 
    )
    await state.set_state(AddMaster.name)

# --- Обработка отмены (ИСПРАВЛЕНО) ---

@router.callback_query(F.data == "cancel_master_add")
async def cancel_add_master(callback: types.CallbackQuery, state: FSMContext):
    """Отменяет процесс добавления мастера и сбрасывает состояние."""
    await callback.answer("Процесс добавления мастера отменен.")
    
    await state.clear() 
    
    # 1. Редактируем сообщение, чтобы убрать Inline-клавиатуру и показать статус
    await callback.message.edit_text(
        "❌ **Добавление мастера отменено.**",
        reply_markup=None, # Убираем Inline-клавиатуру
        parse_mode="Markdown"
    )
    
    # 2. Отправляем НОВОЕ сообщение с Reply-клавиатурой
    await callback.message.answer(
        "↩️ Возврат в панель Администратора.",
        reply_markup=get_admin_menu_kb()
    )

# --- Обработка неожиданного текста в состоянии категории ---

@router.message(AddMaster.category)
async def process_category_unexpected_text(message: types.Message):
    """Ловит неверный ввод (текст вместо нажатия кнопки) и просит выбрать категорию."""
    await message.answer(
        "⚠️ Пожалуйста, **выберите категорию, используя кнопки** ниже. Не вводите текст вручную.",
        reply_markup=get_master_category_kb()
    )


# --- Состояние: Ввод имени ---

@router.message(AddMaster.name)
async def process_name(message: types.Message, state: FSMContext):
    """Обрабатывает введенное имя и просит ввести город."""
    await state.update_data(name=message.text.strip())
    
    await message.answer("🏙️ Введите **город**, в котором работает мастер.")
    await state.set_state(AddMaster.city)

# --- Состояние: Ввод города ---
@router.message(AddMaster.city)
async def process_city(message: types.Message, state: FSMContext):
    """Обрабатывает введенный город и просит ввести цену."""
    await state.update_data(city=message.text.strip())
    
    await message.answer("💰 Введите **цену услуг** (например, от 1000 руб/час или Договорная).")
    await state.set_state(AddMaster.price)

# --- Состояние: Ввод цены ---

@router.message(AddMaster.price)
async def process_price(message: types.Message, state: FSMContext):
    """Обрабатывает введенную цену."""
    await state.update_data(price=message.text.strip())
    await message.answer("📞 Введите **контакт** мастера (телефон или @username Telegram).")
    await state.set_state(AddMaster.contact)

# --- Состояние: Ввод контакта ---

@router.message(AddMaster.contact)
async def process_contact(message: types.Message, state: FSMContext):
    """Обрабатывает введенный контакт и переходит к фото."""
    await state.update_data(contact=message.text.strip())
    
    await state.update_data(photos=[]) 
    
    await message.answer(
        "🖼️ Отправьте **фотографии** мастера (или его работ). "
        "Вы можете отправить несколько фото подряд. \n\n"
        "Когда закончите, нажмите кнопку **'➡️ Готово'**.",
        reply_markup=get_master_photo_kb(),
        parse_mode="Markdown"
    )
    await state.set_state(AddMaster.photos)

# --- Состояние: Сбор фотографий ---

@router.message(AddMaster.photos, F.photo)
async def process_photos(message: types.Message, state: FSMContext):
    """Обрабатывает отправленное фото и сохраняет его file_id."""
    file_id = message.photo[-1].file_id
    
    data = await state.get_data()
    photos: List[str] = data.get('photos', [])
    photos.append(file_id)
    
    await state.update_data(photos=photos)
    
    await message.reply("✅ Фотография принята. Отправьте ещё или нажмите '➡️ Готово'.")

@router.callback_query(F.data == "add_master_photo_done", AddMaster.photos)
async def process_photos_done(callback: types.CallbackQuery, state: FSMContext):
    """Завершает процесс добавления мастера, сохраняет данные и выходит из FSM."""
    await callback.answer() 
    
    data = await state.get_data()
    category = data.get('category')
    name = data.get('name')
    city = data.get('city')
    price = data.get('price')
    contact = data.get('contact')
    photos: List[str] = data.get('photos', [])

    if not photos:
        # Если фото нет, просим отправить или нажать "Готово" еще раз для выхода
        try:
             await callback.message.edit_text(
                "⚠️ Вы не отправили ни одного фото. Пожалуйста, отправьте хотя бы одно. "
                "Или нажмите '➡️ Готово' еще раз, чтобы выйти из режима добавления.",
                reply_markup=get_master_photo_kb()
            )
        except:
             await callback.message.answer(
                "⚠️ Вы не отправили ни одного фото. Пожалуйста, отправьте хотя бы одно. "
                "Или нажмите '➡️ Готово' еще раз, чтобы выйти из режима добавления.",
                reply_markup=get_master_photo_kb()
            )
        return

    await add_master(category, name, city, price, contact, photos) 
    
    await state.clear()
    
    await callback.message.edit_text(
        f"🎉 **Мастер добавлен!**\n\n"
        f"Категория: {category}\n"
        f"🏙️ Город: {city}\n"
        f"Имя: {name}\n"
        f"Цена: {price}\n"
        f"Контакт: {contact}\n"
        f"Фото: {len(photos)} шт.",
        parse_mode="Markdown",
        reply_markup=None 
    )