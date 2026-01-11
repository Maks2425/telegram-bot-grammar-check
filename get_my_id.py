

import os
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not TELEGRAM_BOT_TOKEN:
    print("Помилка: TELEGRAM_BOT_TOKEN не знайдено в .env файлі")
    exit(1)


async def get_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показує User ID користувача"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "не вказано"
    first_name = update.effective_user.first_name or ""
    
    message = (
        f"👤 Ваш Telegram User ID: `{user_id}`\n"
        f"📝 Username: @{username}\n"
        f"👋 Ім'я: {first_name}\n\n"
        f"Скопіюйте цей ID та додайте його до ALLOWED_USER_IDS у .env файлі."
    )
    
    await update.message.reply_text(message, parse_mode='Markdown')
    print(f"\n✅ User ID отримано: {user_id}")
    print("Тепер ви можете зупинити скрипт (Ctrl+C) та додати цей ID до .env файлу\n")


def main():
    """Запуск бота для отримання User ID"""
    print("=" * 50)
    print("Скрипт для отримання Telegram User ID")
    print("=" * 50)
    print(f"\n1. Знайдіть вашого бота в Telegram")
    print(f"2. Надішліть йому будь-яке повідомлення")
    print(f"3. Бот надішле вам ваш User ID")
    print(f"4. Натисніть Ctrl+C для зупинки\n")
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.ALL, get_user_id))
    
    print("Бот запущено. Очікую повідомлення...\n")
    application.run_polling()


if __name__ == '__main__':
    main()

