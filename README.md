# Telegram Grammar Check Bot

Telegram бот для перевірки граматики текстів за допомогою OpenAI API.

## Опис

Цей бот приймає текстові повідомлення від користувачів та відправляє їх до OpenAI API з інструкцією перевірити граматику. Результат перевірки повертається користувачу.

## Вимоги

- Python 3.8 або вище
- Telegram Bot Token (отримати у [@BotFather](https://t.me/BotFather))
- OpenAI API Key (отримати на [platform.openai.com](https://platform.openai.com))

## Встановлення

1. Клонуйте репозиторій або завантажте файли проекту

2. Створіть віртуальне середовище:
```bash
python -m venv venv
```

3. Активуйте віртуальне середовище:

**Windows (PowerShell):**
```bash
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```bash
venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

4. Встановіть залежності:
```bash
pip install -r requirements.txt
```

5. Створіть файл `.env` в корені проекту:
```bash
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
```

Замініть `your_telegram_bot_token_here` та `your_openai_api_key_here` на ваші реальні ключі.

## Запуск

**Важливо:** Переконайтеся, що віртуальне середовище активовано перед запуском!

Запустіть бота командою:
```bash
python bot.py
```

Після запуску бот буде готовий до роботи. Знайдіть свого бота в Telegram та надішліть йому команду `/start` для початку роботи.

## Використання

1. Надішліть боту команду `/start` для привітання
2. Надішліть будь-який текст для перевірки граматики
3. Бот поверне виправлений варіант тексту з поясненнями

## Структура проекту

```
telegram-bot-grammar-check/
├── bot.py                 # Основний файл бота
├── requirements.txt       # Залежності Python
├── .env.example          # Приклад файлу змінних оточення
├── .gitignore            # Git ignore файл
├── venv/                 # Віртуальне середовище (створюється після встановлення)
└── README.md             # Цей файл
```

## Технології

- `python-telegram-bot` - бібліотека для роботи з Telegram Bot API
- `openai` - офіційна бібліотека OpenAI
- `python-dotenv` - для завантаження змінних оточення

## Примітки

- Бот використовує модель `gpt-3.5-turbo` від OpenAI
- Всі помилки логуються в консоль для відстеження
- Переконайтеся, що у вас є достатньо кредитів на OpenAI акаунті

