# handlers/admin.py

from aiogram import Router, types, F
from aiogram.filters import StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from config import ADMIN_IDS
from db import get_all_clients, get_all_masters, delete_master_by_id, add_master_batch # ⬅️ ИМПОРТЫ
from keyboards import get_contact_manager_kb, get_delete_master_kb, get_back_to_admin_kb, get_admin_menu_kb # ⬅️ ИМПОРТЫ
from aiogram.enums import ParseMode
import logging
import csv
import io

# Инициализация роутера
router = Router()
# Добавляем фильтр: все хэндлеры в этом роутере будут работать только для админов
router.message.filter(F.from_user.id.in_(ADMIN_IDS))
router.callback_query.filter(F.from_user.id.in_(ADMIN_IDS))

# Определение состояний для рассылки
class Mailing(StatesGroup):
    message_text = State()

# ➡️ НОВЫЙ КЛАСС СОСТОЯНИЙ ДЛЯ ИМПОРТА
class ImportMaster(StatesGroup):
    wait_for_file = State()

# --- Логика Рассылки (Остается прежней) ---

@router.message(F.text == "📢 Сделать рассылку")
async def cmd_start_mailing(message: types.Message, state: FSMContext):
    """Начинает процесс рассылки."""
    await message.answer("✍️ Введите **текст сообщения** для рассылки всем клиентам.")
    await state.set_state(Mailing.message_text)

@router.message(Mailing.message_text)
async def cmd_execute_mailing(message: types.Message, state: FSMContext):
    """Выполняет рассылку."""
    await state.clear() 
    
    text_to_send = message.text
    client_ids = await get_all_clients()
    
    success_count = 0
    kb = get_contact_manager_kb() 
    
    await message.answer(f"⏳ Начинаю рассылку для {len(client_ids)} клиентов...")
    
    for client_id in client_ids:
        try:
            await message.bot.send_message(
                chat_id=client_id, 
                text=text_to_send, 
                reply_markup=kb
            )
            success_count += 1
        except Exception as e:
            logging.error(f"Не удалось отправить сообщение пользователю {client_id}: {e}")

    await message.answer(
        f"✅ **Рассылка завершена!**\n"
        f"Успешно доставлено: {success_count} из {len(client_ids)}."
    )


# --- Логика Удаления Мастера (НОВЫЕ ХЭНДЛЕРЫ) ---

@router.message(F.text == "🗑️ Удалить мастера")
async def cmd_show_masters_to_delete(message: types.Message):
    """Показывает список всех мастеров с кнопками для их удаления."""
    masters = await get_all_masters()
    
    if not masters:
        await message.answer("❌ В базе данных нет ни одного мастера для удаления.")
        return
        
    await message.answer(f"🛠️ **Найдено мастеров:** {len(masters)}. Нажмите на кнопку '🗑️ Удалить безвозвратно' под нужным мастером:", 
                         parse_mode=ParseMode.MARKDOWN)

    # Отправляем карточки мастеров
    for master in masters:
        caption = (
            f"ID: **{master['id']}**\n"
            f"👤 **Имя:** {master['name']}\n"
            f"🛠️ **Категория:** {master['category']}\n"
            f"💰 **Цена:** {master['price']}"
        )
        
        photos_str = master.get('photos')
        photo_ids = photos_str.split(',') if photos_str else []
        
        try:
            if photo_ids and photo_ids[0]:
                await message.bot.send_photo(
                    chat_id=message.chat.id,
                    photo=photo_ids[0],
                    caption=caption,
                    reply_markup=get_delete_master_kb(master['id']),
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await message.bot.send_message(
                    chat_id=message.chat.id,
                    text=f"Карточка мастера:\n{caption}",
                    reply_markup=get_delete_master_kb(master['id']),
                    parse_mode=ParseMode.MARKDOWN
                )
        except Exception as e:
            logging.error(f"Ошибка при отправке карточки мастера {master['id']} для удаления: {e}")
            await message.bot.send_message(
                 chat_id=message.chat.id,
                 text=f"❌ Ошибка загрузки (ID: {master['id']}): {caption}",
                 reply_markup=get_delete_master_kb(master['id']),
                 parse_mode=ParseMode.MARKDOWN
            )

@router.callback_query(F.data.startswith("del_confirm_"))
async def cb_confirm_delete_master(callback: types.CallbackQuery):
    """Обрабатывает нажатие кнопки "Удалить безвозвратно"."""
    await callback.answer("Подтверждаю удаление...", show_alert=True)
    
    master_id = int(callback.data.split("del_confirm_")[1])
    success = await delete_master_by_id(master_id)
    
    if success:
        await callback.message.edit_text(
            f"✅ **Мастер ID: {master_id} успешно удален!**",
            reply_markup=get_back_to_admin_kb(),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await callback.message.edit_text(
            f"❌ **Ошибка:** Мастер ID: {master_id} не найден в базе данных.",
            reply_markup=get_back_to_admin_kb(),
            parse_mode=ParseMode.MARKDOWN
        )

@router.callback_query(F.data == "back_to_admin_menu")
async def cb_back_to_admin_menu(callback: types.CallbackQuery):
    """Обрабатывает кнопку 'Назад в меню админа'."""
    await callback.answer()
    try:
        await callback.message.delete()
    except Exception:
        # Если сообщение нельзя удалить, редактируем его
        await callback.message.edit_text(
            "↩️ Возврат в панель Администратора.",
            reply_markup=get_admin_menu_kb()
        )
    
    # Отправляем сообщение с клавиатурой, чтобы обновить ее
    await callback.message.answer(
        "↩️ Возврат в панель Администратора.",
        reply_markup=get_admin_menu_kb()
    )


# --- Логика Массового Добавления (НОВЫЕ FSM ХЭНДЛЕРЫ) ---

@router.message(F.text == "📄 Массовое добавление (CSV)")
async def cmd_start_import(message: types.Message, state: FSMContext):
    """Начинает процесс массового импорта мастеров."""
    await message.answer(
        "📂 **Массовое добавление мастеров (CSV)**\n\n"
        "Отправьте файл в формате **CSV** со следующими столбцами (в этой последовательности):\n\n"
        "`category`, `name`, `price`, `contact`\n\n"
        "**Пример строки:** `Сантехник,Иван Петров,от 1500 руб/час,+79001234567`\n"
        "Для отмены используйте /menu.",
        parse_mode=ParseMode.MARKDOWN
    )
    await state.set_state(ImportMaster.wait_for_file)

@router.message(ImportMaster.wait_for_file, F.document)
async def cmd_process_import_file(message: types.Message, state: FSMContext):
    """Обрабатывает отправленный CSV-файл."""
    await state.clear() # Сбрасываем FSM
    
    if not message.document.file_name.lower().endswith('.csv'):
        await message.answer("⚠️ Ожидается файл в формате **CSV**. Пожалуйста, повторите.")
        return

    file_id = message.document.file_id
    file_info = await message.bot.get_file(file_id)
    file_path = file_info.file_path
    
    await message.answer("⏳ Файл получен, обрабатываю данные...")
    
    try:
        # Скачиваем файл
        file_content_bytes = await message.bot.download_file(file_path)
        
        # Декодируем содержимое (важно выбрать правильную кодировку, часто это 'utf-8')
        file_content = io.StringIO(file_content_bytes.read().decode('utf-8'))
        
        reader = csv.reader(file_content)
        masters_to_add = []
        errors = []
        
        for i, row in enumerate(reader):
            # Пропускаем пустые строки
            if not any(row):
                continue

            # Проверяем, что строка содержит 4 элемента
            if len(row) >= 4:
                masters_to_add.append({
                    'category': row[0].strip(),
                    'name': row[1].strip(),
                    'price': row[2].strip(),
                    'contact': row[3].strip()
                })
            else:
                errors.append(f"Строка {i+1}: Недостаточно данных.")

        if masters_to_add:
            added_count = await add_master_batch(masters_to_add)
            
            error_report = "\n".join(errors) if errors else "Ошибок не обнаружено."
            
            await message.answer(
                f"🎉 **Массовое добавление завершено!**\n"
                f"Успешно добавлено мастеров: **{added_count}**.\n"
                f"Отчет по ошибкам:\n`{error_report}`",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await message.answer(f"❌ **Импорт завершен:** Не найдено ни одной корректной записи для добавления.\n"
                                f"Отчет по ошибкам:\n`{'\n'.join(errors)}`",
                                parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        await message.answer(f"❌ **Критическая ошибка при чтении файла:** {e}. Убедитесь, что файл имеет кодировку UTF-8.")
        logging.error(f"Критическая ошибка при импорте CSV: {e}")
        
    finally:
        # Убеждаемся, что FSM сброшен, даже если была ошибка
        await state.clear()


# Если пользователь отправляет текст вместо файла
@router.message(ImportMaster.wait_for_file)
async def cmd_import_unexpected_text(message: types.Message):
    await message.answer("⚠️ Пожалуйста, отправьте файл в формате **CSV**. Для отмены используйте /menu.")