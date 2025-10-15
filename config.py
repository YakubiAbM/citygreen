import os
from typing import List
ADMIN_IDS: List[int] = [6318017185] # ID администратора(ов)
ADMIN_USERNAME = "username_admin"  # Юзернейм администратора для кнопки "Связаться"
DATABASE_NAME = "citygreen.db"
BOT_TOKEN = os.getenv("xVE8353786544:AAFimU0W-xKksDDnULatciYzi9EF0Ri7",) # Второй аргумент - резервный для локального запуска
# config.py
import os # <-- Убедитесь, что этот импорт есть!
from typing import List

# ➡️ Считываем BOT_TOKEN из переменных окружения.
# Если переменная не найдена (например, при локальном запуске), 
# используется резервное значение (второй аргумент)
# Но на Render переменная должна быть установлена!
BOT_TOKEN = os.getenv("xVE8353786544:AAFimU0W-xKksDDnULatciYzi9EF0Ri7",)
# ... (остальные переменные)
ADMIN_IDS: List[int] = [123456789] 
ADMIN_USERNAME = "username_admin"  
DATABASE_NAME = "citygreen.db"