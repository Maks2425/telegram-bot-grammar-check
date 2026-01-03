import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# Завантаження змінних оточення
load_dotenv()

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Отримання токенів зі змінних оточення
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Перевірка наявності токенів
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не знайдено в змінних оточення")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY не знайдено в змінних оточення")

# Ініціалізація клієнта OpenAI
openai_client = OpenAI(api_key=OPENAI_API_KEY)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обробник команди /start"""
    welcome_message = (
        "Привіт! Я бот для перевірки граматики.\n\n"
        "Просто надішліть мені текст, і я перевірю його граматику за допомогою OpenAI."
    )
    await update.message.reply_text(welcome_message)
    logger.info(f"Користувач {update.effective_user.id} виконав команду /start")


async def check_grammar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обробник текстових повідомлень для перевірки граматики"""
    user_text = update.message.text
    user_id = update.effective_user.id
    
    logger.info(f"Користувач {user_id} надіслав текст для перевірки: {user_text[:50]}...")
    
    try:
        # Відправка індикатора "печатає..."
        await update.message.chat.send_action(action="typing")
        
        # Формування запиту до OpenAI
        system_instruction = "Перевір граматику, не роби дуже сильних змін у тексті, а лише виправляй помилки"
        
        response = openai_client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_text}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        # Отримання відповіді від OpenAI
        corrected_text = response.choices[0].message.content
        
        # Відправка результату користувачу
        await update.message.reply_text(corrected_text)
        logger.info(f"Успішно перевірено граматику для користувача {user_id}")
        
    except Exception as e:
        logger.error(f"Помилка при перевірці граматики: {str(e)}", exc_info=True)
        error_message = "Вибачте, сталася помилка при перевірці граматики. Спробуйте пізніше."
        await update.message.reply_text(error_message)


def main() -> None:
    """Головна функція для запуску бота"""
    # Створення додатку
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Додавання обробників
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_grammar))
    
    # Запуск бота
    logger.info("Бот запущено...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()

