import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from openai import OpenAI


load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


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
        "Привіт ти в телеграм боті grammar check! Вибери категорію як ти хочеш провірити граматику!"
    )
    
    # Створення кнопок
    keyboard = [
        [InlineKeyboardButton("Просте перевірення без об'яснення", callback_data="mode_simple")],
        [InlineKeyboardButton("Перевірення та тільки об'яснення базових помилок", callback_data="mode_basic")],
        [InlineKeyboardButton("Перевірення та об'яснення базових помилок та граматичних", callback_data="mode_full")],
        [InlineKeyboardButton("мінігра", callback_data="minigame")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)
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


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обробник натискань на кнопки"""
    query = update.callback_query
    user_id = query.from_user.id
    
    if not is_user_authorized(user_id):
        await query.answer("У вас немає доступу до цього бота.")
        return
    
    callback_data = query.data
    
    # Обробка мінігри
    if callback_data == "minigame":
        keyboard = [
            [InlineKeyboardButton("Easy", callback_data="level_easy")],
            [InlineKeyboardButton("Normal", callback_data="level_normal")],
            [InlineKeyboardButton("Hard", callback_data="level_hard")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.answer()
        await query.edit_message_text(
            "Оберіть рівень складності:",
            reply_markup=reply_markup
        )
        logger.info(f"Користувач {user_id} обрав мінігру")
        return
    
    # Обробка рівнів складності мінігри
    if callback_data.startswith("level_"):
        level = callback_data.split("_")[1]  # easy, normal, hard
        await query.answer()
        await query.edit_message_text("🎮 Генерую завдання...")
        await start_minigame(update, context, level)
        return
    
    # Обробка режимів перевірки граматики
    mode = callback_data
    context.user_data['grammar_mode'] = mode
    context.user_data['in_minigame'] = False  # Скидаємо режим мінігри
    
    mode_names = {
        'mode_simple': 'Просте перевірення без об\'яснення',
        'mode_basic': 'Перевірення та тільки об\'яснення базових помилок',
        'mode_full': 'Перевірення та об\'яснення базових помилок та граматичних'
    }
    
    mode_name = mode_names.get(mode, 'Невідомий режим')
    
    await query.answer(f"Обрано: {mode_name}")
    await query.edit_message_text(
        f"✅ Режим вибрано: {mode_name}\n\n"
        f"Тепер надішліть текст для перевірки граматики."
    )
    logger.info(f"Користувач {user_id} вибрав режим: {mode_name}")


async def start_minigame(update: Update, context: ContextTypes.DEFAULT_TYPE, level: str) -> None:
    """Запуск мінігри з вибраним рівнем складності"""
    query = update.callback_query
    user_id = query.from_user.id
    
    # Встановлюємо режим мінігри
    context.user_data['in_minigame'] = True
    context.user_data['minigame_level'] = level
    
    level_names = {
        'easy': 'легкий',
        'normal': 'середній',
        'hard': 'важкий'
    }
    level_name = level_names.get(level, level)
    
    # Пояснення гри
    game_explanation = (
        f"🎮 Мінігра: Знайди помилки!\n\n"
        f"Рівень складності: {level_name.capitalize()}\n\n"
        f"Ти отримаєш речення з граматичними помилками. "
        f"Твоє завдання - написати правильну версію речення!"
    )
    
    await query.edit_message_text(game_explanation)
    
    # Генеруємо текст з помилками
    try:
        await query.message.chat.send_action(action="typing")
        
        # Визначаємо кількість помилок залежно від рівня
        error_counts = {
            'easy': '1 або 2 помилки',
            'normal': '4 або 5 помилок',
            'hard': '7 або 8 помилок'
        }
        error_count = error_counts.get(level, '4 або 5 помилок')
        
        # Генеруємо правильне речення через OpenAI
        difficulty_prompts = {
            'easy': 'Створи просте українське речення (5-8 слів). Речення має бути про щось звичайне (погода, їжа, навчання). Надай ТІЛЬКИ речення без помилок.',
            'normal': 'Створи середнє українське речення (8-12 слів). Речення має бути про щось цікаве (подорож, хобі, робота). Надай ТІЛЬКИ речення без помилок.',
            'hard': 'Створи складне українське речення (12-18 слів). Речення має бути про щось складне (наука, філософія, технології). Надай ТІЛЬКИ речення без помилок.'
        }
        
        prompt = difficulty_prompts.get(level, difficulty_prompts['normal'])
        
        # Генеруємо правильне речення
        correct_response = openai_client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": "Ти створюєш правильні українські речення. Надай ТІЛЬКИ речення без помилок, без пояснень."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=200
        )
        
        correct_text = correct_response.choices[0].message.content.strip()
        
        # Додаємо помилки до правильного речення
        error_prompt = (
            f"Візьми це правильне речення і додай до нього рівно {error_count} граматичних помилок "
            f"(орфографічні помилки, помилки в пунктуації, граматичні помилки). "
            f"Надай ТІЛЬКИ речення з помилками, без пояснень та без правильного варіанту."
        )
        
        error_response = openai_client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": "Ти додаєш граматичні помилки до правильного речення. Надай ТІЛЬКИ речення з помилками, без пояснень."},
                {"role": "user", "content": f"{error_prompt}\n\nПравильне речення: {correct_text}"}
            ],
            temperature=0.8,
            max_tokens=200
        )
        
        text_with_errors = error_response.choices[0].message.content.strip()
        
        # Зберігаємо правильну відповідь
        context.user_data['minigame_correct_answer'] = correct_text.lower().strip()
        context.user_data['minigame_original'] = text_with_errors
        
        # Відправляємо завдання
        task_message = (
            f"{text_with_errors}\n\n"
            f"Напиши правильну версію речення! Та я її перевірю."
        )
        
        await query.message.reply_text(task_message)
        logger.info(f"Користувач {user_id} отримав завдання мінігри (рівень: {level})")
        
    except Exception as e:
        logger.error(f"Помилка при генерації завдання мінігри: {str(e)}", exc_info=True)
        error_message = "Вибачте, сталася помилка при генерації завдання. Спробуйте пізніше."
        await query.message.reply_text(error_message)


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
    
    # Перевірка, чи це відповідь у мінігрі
    if context.user_data.get('in_minigame'):
        await check_minigame_answer(update, context)
        return
    
    # Перевірка, чи вибрано режим
    mode = context.user_data.get('grammar_mode', 'mode_simple')
    
    user_text = update.message.text
    logger.info(f"Користувач {user_id} надіслав текст для перевірки (режим: {mode}): {user_text[:50]}...")
    
    try:
        # Відправка індикатора "печатає..."
        await update.message.chat.send_action(action="typing")
        
        # Формування інструкцій залежно від режиму
        system_instructions = {
            'mode_simple': "Перевір граматику тексту. Надай тільки виправлений варіант тексту без жодних пояснень та коментарів. Не додавай зайвих пояснень, тільки виправлений текст.",
            'mode_basic': "Перевір граматику тексту. Надай виправлений варіант тексту та поясни тільки базові помилки (орфографічні помилки, помилки в пунктуації). Не пояснюй складні граматичні правила.",
            'mode_full': "Перевір граматику тексту. Надай виправлений варіант тексту та детально поясни всі знайдені помилки - як базові (орфографічні, пунктуаційні), так і граматичні (синтаксис, морфологія). Надай повне пояснення кожної помилки."
        }
        
        system_instruction = system_instructions.get(mode, system_instructions['mode_simple'])
        
        response = openai_client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_text}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        
        # Отримання відповіді від OpenAI
        corrected_text = response.choices[0].message.content
        
        # Відправка результату користувачу
        await update.message.reply_text(corrected_text)
        logger.info(f"Успішно перевірено граматику для користувача {user_id} (режим: {mode})")
        
    except Exception as e:
        logger.error(f"Помилка при перевірці граматики: {str(e)}", exc_info=True)
        error_message = "Вибачте, сталася помилка при перевірці граматики. Спробуйте пізніше."
        await update.message.reply_text(error_message)


async def check_minigame_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Перевірка відповіді в мінігрі"""
    user_id = update.effective_user.id
    user_answer = update.message.text.strip().lower()
    correct_answer = context.user_data.get('minigame_correct_answer', '').lower()
    
    try:
        await update.message.chat.send_action(action="typing")
        
        # Порівнюємо відповіді (з урахуванням варіантів написання)
        # Використовуємо OpenAI для більш гнучкої перевірки
        check_response = openai_client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": "Ти перевіряєш чи дві речення мають однаковий сенс та правильну граматику. Відповідай тільки 'ТАК' або 'НІ' без пояснень."},
                {"role": "user", "content": f"Правильна відповідь: {correct_answer}\nВідповідь гравця: {user_answer}\n\nЧи правильна відповідь гравця?"}
            ],
            temperature=0.1,
            max_tokens=10
        )
        
        is_correct = check_response.choices[0].message.content.strip().upper().startswith('ТАК')
        
        if is_correct:
            message = (
                "🎉 Відмінно! Ти правильно виправив помилки!\n\n"
                "Хочеш спробувати ще раз? Натисни /start та обери мінігру!"
            )
        else:
            original_text = context.user_data.get('minigame_original', '')
            message = (
                f"❌ Це не правильна відповідь.\n\n"
                f"Правильна відповідь:\n{correct_answer.capitalize()}\n\n"
                f"Спробуй ще раз! Натисни /start та обери мінігру!"
            )
        
        # Скидаємо режим мінігри
        context.user_data['in_minigame'] = False
        context.user_data.pop('minigame_correct_answer', None)
        context.user_data.pop('minigame_original', None)
        context.user_data.pop('minigame_level', None)
        
        await update.message.reply_text(message)
        logger.info(f"Користувач {user_id} відповів у мінігрі (правильно: {is_correct})")
        
    except Exception as e:
        logger.error(f"Помилка при перевірці відповіді мінігри: {str(e)}", exc_info=True)
        error_message = "Вибачте, сталася помилка при перевірці відповіді. Спробуйте ще раз."
        await update.message.reply_text(error_message)


def main() -> None:
    """Головна функція для запуску бота"""
    # Створення додатку
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Додавання обробників
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("myid", myid))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_grammar))
    
    # Запуск бота
    logger.info("Бот запущено...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()

