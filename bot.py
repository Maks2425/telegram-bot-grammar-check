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
ALLOWED_USER_IDS = os.getenv('ALLOWED_USER_IDS', '')

# Перевірка наявності токенів
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не знайдено в змінних оточення")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY не знайдено в змінних оточення")

# Парсинг списку дозволених користувачів
ALLOWED_USER_IDS_LIST = []
if ALLOWED_USER_IDS:
    try:
        ALLOWED_USER_IDS_LIST = [int(uid.strip()) for uid in ALLOWED_USER_IDS.split(',') if uid.strip()]
        logger.info(f"Завантажено {len(ALLOWED_USER_IDS_LIST)} дозволених користувачів: {ALLOWED_USER_IDS_LIST}")
    except ValueError as e:
        logger.error(f"Помилка при парсингу ALLOWED_USER_IDS: {e}. Перевірте формат у .env файлі.")
else:
    logger.warning("ALLOWED_USER_IDS не встановлено. Бот буде доступний всім користувачам.")

# Ініціалізація клієнта OpenAI
openai_client = OpenAI(api_key=OPENAI_API_KEY)


def is_user_authorized(user_id: int) -> bool:
    """Перевіряє, чи користувач має доступ до бота"""
    if not ALLOWED_USER_IDS_LIST:
        # Якщо список порожній, доступ мають всі
        logger.debug(f"ALLOWED_USER_IDS_LIST порожній, доступ дозволено для {user_id}")
        return True
    is_authorized = user_id in ALLOWED_USER_IDS_LIST
    if not is_authorized:
        logger.warning(f"Користувач {user_id} не знайдено в списку дозволених: {ALLOWED_USER_IDS_LIST}")
    else:
        logger.debug(f"Користувач {user_id} авторизований")
    return is_authorized


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обробник команди /start"""
    user_id = update.effective_user.id
    
    if not is_user_authorized(user_id):
        await update.message.reply_text(
            "Вибачте, у вас немає доступу до цього бота.\n"
            "Зверніться до адміністратора для отримання доступу."
        )
        logger.warning(f"Неавторизований користувач {user_id} спробував використати бота")
        return
    
    welcome_message = (
        "Привіт! Я бот для перевірки граматики.\n\n"
        "Просто надішліть мені текст, і я перевірю його граматику за допомогою OpenAI."
    )
    await update.message.reply_text(welcome_message)
    logger.info(f"Користувач {user_id} виконав команду /start")


async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обробник команди /myid - показує User ID користувача"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "не вказано"
    
    # Перевірка авторизації для команди /myid (завжди доступна, але показує статус)
    is_auth = is_user_authorized(user_id)
    auth_status = "✅ Авторизований" if is_auth else "❌ Не авторизований"
    
    message = (
        f"Ваш Telegram User ID: `{user_id}`\n"
        f"Username: @{username}\n"
        f"Статус: {auth_status}\n\n"
    )
    
    if not is_auth:
        message += f"Надайте цей ID адміністратору для отримання доступу до бота.\n"
        message += f"Дозволені користувачі: {ALLOWED_USER_IDS_LIST if ALLOWED_USER_IDS_LIST else 'не встановлено (доступ мають всі)'}"
    else:
        message += f"Ви маєте доступ до бота."
    
    await update.message.reply_text(message, parse_mode='Markdown')
    logger.info(f"Користувач {user_id} запросив свій ID (авторизований: {is_auth})")


async def check_grammar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обробник текстових повідомлень для перевірки граматики"""
    user_id = update.effective_user.id
    
    if not is_user_authorized(user_id):
        await update.message.reply_text(
            "Вибачте, у вас немає доступу до цього бота.\n"
            "Зверніться до адміністратора для отримання доступу."
        )
        logger.warning(f"Неавторизований користувач {user_id} спробував використати бота")
        return
    
    user_text = update.message.text
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
    application.add_handler(CommandHandler("myid", myid))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_grammar))
    
    # Запуск бота
    logger.info("Бот запущено...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()

