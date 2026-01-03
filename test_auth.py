"""
Тестовий скрипт для перевірки налаштування авторизації
"""
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ALLOWED_USER_IDS = os.getenv('ALLOWED_USER_IDS', '')

print("=" * 60)
print("Перевірка налаштування авторизації")
print("=" * 60)
print()

print(f"TELEGRAM_BOT_TOKEN: {'✅ Встановлено' if TELEGRAM_BOT_TOKEN else '❌ Не встановлено'}")
print(f"OPENAI_API_KEY: {'✅ Встановлено' if OPENAI_API_KEY else '❌ Не встановлено'}")
print()

print(f"ALLOWED_USER_IDS (сирий рядок): '{ALLOWED_USER_IDS}'")
print(f"ALLOWED_USER_IDS (довжина): {len(ALLOWED_USER_IDS)}")
print()

# Парсинг списку
ALLOWED_USER_IDS_LIST = []
if ALLOWED_USER_IDS:
    try:
        ALLOWED_USER_IDS_LIST = [int(uid.strip()) for uid in ALLOWED_USER_IDS.split(',') if uid.strip()]
        print(f"✅ Успішно розпарсено {len(ALLOWED_USER_IDS_LIST)} ID:")
        for uid in ALLOWED_USER_IDS_LIST:
            print(f"   - {uid}")
    except ValueError as e:
        print(f"❌ Помилка при парсингу: {e}")
        print(f"   Перевірте формат у .env файлі. Має бути: ALLOWED_USER_IDS=123456789,987654321")
else:
    print("⚠️  ALLOWED_USER_IDS не встановлено або порожній")
    print("   Бот буде доступний ВСІМ користувачам!")

print()
print("=" * 60)
if ALLOWED_USER_IDS_LIST:
    print(f"✅ Авторизація активна: доступ мають {len(ALLOWED_USER_IDS_LIST)} користувачів")
else:
    print("⚠️  Авторизація НЕ активна: доступ мають ВСІ користувачі")
print("=" * 60)

