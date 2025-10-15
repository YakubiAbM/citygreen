import aiosqlite
from config import DATABASE_NAME
from typing import List, Tuple, Dict, Any

async def init_db():
    """Инициализация базы данных и создание таблиц."""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        # Таблица пользователей (users)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                role TEXT DEFAULT 'client'
            )
        """)

        # ➡️ ОБНОВЛЕННАЯ ТАБЛИЦА MASTERS: ДОБАВЛЕНО ПОЛЕ 'city'
        await db.execute("""
            CREATE TABLE IF NOT EXISTS masters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                name TEXT NOT NULL,
                city TEXT,                 
                price TEXT,
                contact TEXT NOT NULL,
                photos TEXT
            )
        """)

        await db.commit()

async def get_user_role(user_id: int) -> str:
    """Получает роль пользователя (admin/client)."""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        cursor = await db.execute("SELECT role FROM users WHERE user_id = ?", (user_id,))
        result = await cursor.fetchone()
        return result[0] if result else 'client'

async def register_user(user_id: int, username: str, role: str = 'client'):
    """Регистрирует нового пользователя или обновляет существующего."""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        await db.execute("""
            INSERT INTO users (user_id, username, role)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET username = ?, role = ?
        """, (user_id, username, role, username, role))
        await db.commit()

# --- Функции для Администратора ---

async def add_master(category: str, name: str, city: str, price: str, contact: str, photos: List[str]):
    """Добавляет нового мастера в базу данных с указанием города."""
    photo_str = ",".join(photos)
    async with aiosqlite.connect(DATABASE_NAME) as db:
        await db.execute(
            "INSERT INTO masters (category, name, city, price, contact, photos) VALUES (?, ?, ?, ?, ?, ?)",
            (category, name, city, price, contact, photo_str)
        )
        await db.commit()

async def get_all_masters() -> List[Dict[str, Any]]:
    """Возвращает список всех мастеров."""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM masters ORDER BY category, name")
        results = await cursor.fetchall()
        return [dict(row) for row in results]

async def delete_master_by_id(master_id: int) -> bool:
    """Удаляет мастера по его ID и возвращает True, если удаление успешно."""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        cursor = await db.execute("DELETE FROM masters WHERE id = ?", (master_id,))
        await db.commit()
        return cursor.rowcount > 0 

async def add_master_batch(data: List[Dict[str, Any]]):
    """Добавляет несколько мастеров из списка словарей (теперь с городом)."""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        # Подготовка данных: category, name, city, price, contact, photos (пустая строка)
        values = [(item['category'], item['name'], item.get('city', ''), item['price'], item['contact'], '') for item in data]
        
        await db.executemany(
            "INSERT INTO masters (category, name, city, price, contact, photos) VALUES (?, ?, ?, ?, ?, ?)",
            values
        )
        await db.commit()
        return len(values)

async def get_all_clients() -> List[int]:
    """Возвращает список ID всех пользователей с ролью 'client'."""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        cursor = await db.execute("SELECT user_id FROM users WHERE role = 'client'")
        results = await cursor.fetchall()
        return [row[0] for row in results]

# --- Функции для Клиента ---

async def get_all_categories() -> List[str]:
    """Возвращает список всех уникальных категорий мастеров."""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        cursor = await db.execute("SELECT DISTINCT category FROM masters")
        results = await cursor.fetchall()
        return [row[0] for row in results]

# ➡️ НОВАЯ ФУНКЦИЯ ДЛЯ КЛИЕНТА: Поиск мастеров по категории И городу
async def get_masters_by_city_and_category(city: str, category: str) -> List[Dict[str, Any]]:
    """Возвращает список мастеров по заданной категории и городу."""
    city_like = f"%{city}%" # Ищем частичное совпадение
    async with aiosqlite.connect(DATABASE_NAME) as db:
        db.row_factory = aiosqlite.Row 
        cursor = await db.execute(
            "SELECT * FROM masters WHERE category = ? AND city LIKE ?", 
            (category, city_like)
        )
        results = await cursor.fetchall()
        return [dict(row) for row in results]