from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from config import ADMIN_USERNAME
from typing import List

# НОВЫЙ СПИСОК ФИКСИРОВАННЫХ КАТЕГОРИЙ
MASTER_CATEGORIES = ["Сантехник", "Электрик", "Молярщик", "Кафельщик"] 

# --- КЛАВИАТУРЫ ДЛЯ АДМИНИСТРАТОРА ---

def get_admin_menu_kb() -> ReplyKeyboardMarkup:
    """Клавиатура для главного меню администратора."""
    kb = [
        [KeyboardButton(text="➕ Добавить мастера"), KeyboardButton(text="🗑️ Удалить мастера")], # ⬅️ ДОБАВЛЕНА КНОПКА
        [KeyboardButton(text="📢 Сделать рассылку"), KeyboardButton(text="📄 Массовое добавление (CSV)")], # ⬅️ НОВАЯ КНОПКА
        [KeyboardButton(text="/help"), KeyboardButton(text="/menu")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=False)

def get_master_photo_kb() -> InlineKeyboardMarkup:
    """Кнопка для завершения отправки фотографий мастера."""
    kb = [
        [InlineKeyboardButton(text="➡️ Готово", callback_data="add_master_photo_done")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_master_category_kb() -> InlineKeyboardMarkup:
    """Создает Inline-клавиатуру с фиксированными категориями мастеров."""
    kb = []
    for category in MASTER_CATEGORIES:
        kb.append([InlineKeyboardButton(text=category, callback_data=f"select_cat_{category}")])
    
    kb.append([InlineKeyboardButton(text="❌ Отмена добавления", callback_data="cancel_master_add")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# ➡️ НОВАЯ ФУНКЦИЯ ДЛЯ КЛАВИАТУРЫ УДАЛЕНИЯ
def get_delete_master_kb(master_id: int) -> InlineKeyboardMarkup:
    """Кнопка подтверждения удаления для карточки мастера."""
    kb = [
        [InlineKeyboardButton(text="🗑️ Удалить безвозвратно", callback_data=f"del_confirm_{master_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)
    
# ➡️ НОВАЯ ФУНКЦИЯ ДЛЯ КНОПКИ НАЗАД
def get_back_to_admin_kb() -> InlineKeyboardMarkup:
    """Кнопка возврата в меню админа (для использования в Inline-сообщениях)."""
    kb = [
        [InlineKeyboardButton(text="⬅️ Назад в меню админа", callback_data="back_to_admin_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


# --- КЛАВИАТУРЫ ДЛЯ КЛИЕНТА ---

def get_client_menu_kb() -> ReplyKeyboardMarkup:
    """Клавиатура для главного меню клиента."""
    kb = [
        [KeyboardButton(text="📋 Список мастеров")],
        [KeyboardButton(text="🧱 Стройматериалы")],
        [KeyboardButton(text="💬 Связаться с менеджером")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=False)

def get_masters_categories_kb(categories: List[str]) -> InlineKeyboardMarkup:
    """
    Создает Inline-клавиатуру со списком категорий мастеров.
    :param categories: Список строк с названиями категорий.
    """
    kb = []
    for category in categories:
        kb.append([InlineKeyboardButton(text=category, callback_data=f"show_masters_{category}")])

    kb.append([InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_contact_manager_kb() -> InlineKeyboardMarkup:
    """Кнопка для связи с администратором."""
    kb = [
        [InlineKeyboardButton(text="Связаться с менеджером", url=f"t.me/{ADMIN_USERNAME}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)