import os
import pickle
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

class BotDatabase:
    def __init__(self):
        self.data_file = '/tmp/football_bot_data.pkl'
        self.data = self.load_data()
    
    def load_data(self):
        try:
            with open(self.data_file, 'rb') as f:
                return pickle.load(f)
        except (FileNotFoundError, EOFError):
            return {
                'play': set(),
                'cancel': set(),
                'maybe': set(),
                'last_notification': 0,
                'all_users': set()
            }
    
    def save_data(self):
        with open(self.data_file, 'wb') as f:
            pickle.dump(self.data, f)

db = BotDatabase()

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(f"Ошибка: {context.error}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # ... (остальной код start без изменений) ...

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # ... (остальной код handle_callback без изменений) ...

async def check_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (остальной код check_notifications без изменений) ...

def get_stats_text():
    # ... (остальной код get_stats_text без изменений) ...

def main():
    TOKEN = os.getenv('TELEGRAM_TOKEN')
    if not TOKEN:
        print("❌ Ошибка: Не задан TELEGRAM_TOKEN!")
        exit(1)

    # Создаем Application с параметром exclusive=True
    application = (
        Application.builder()
        .token(TOKEN)
        .updater(None)  # Явно отключаем updater
        .build()
    )

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))
    
    # Правильно регистрируем обработчик ошибок
    application.add_error_handler(error_handler)

    # Удаляем возможные предыдущие подключения
    await application.bot.delete_webhook(drop_pending_updates=True)
    
    print("🔄 Бот запускается с полным сбросом состояния...")
    
    try:
        await application.initialize()
        await application.start()
        await application.updater.start_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
            timeout=30,
            pool_timeout=30
        )
        print("🤖 Бот успешно запущен!")
        await application.updater.idle()
    except Exception as e:
        print(f"🚨 Фатальная ошибка: {e}")
        await application.stop()
        exit(1)
    finally:
        await application.stop()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
