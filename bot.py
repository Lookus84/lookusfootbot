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
            # Инициализируем все возможные статусы
            return {
                'play': set(),       # Изменили 'playing' на 'play'
                'cancel': set(),     # Изменили 'not_playing' на 'cancel'
                'maybe': set(),
                'last_notification': 0,
                'all_users': set()
            }
    
    def save_data(self):
        with open(self.data_file, 'wb') as f:
            pickle.dump(self.data, f)

db = BotDatabase()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user:
        db.data['all_users'].add(user.id)
        db.save_data()
    
    keyboard = [
        [InlineKeyboardButton("✅ Играю!", callback_data='play')],
        [InlineKeyboardButton("❌ Не играю", callback_data='cancel')],
        [InlineKeyboardButton("❓ Под вопросом", callback_data='maybe')],
        [InlineKeyboardButton("📊 Статистика", callback_data='stats')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        if update.message:
            await update.message.reply_text(
                "⚽ *Футбольный бот* ⚽\nВыбери действие:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        elif update.callback_query:
            await update.callback_query.edit_message_text(
                "⚽ *Футбольный бот* ⚽\nВыбери действие:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    except Exception as e:
        print(f"Ошибка в start: {e}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    if not user:
        return

    action = query.data
    
    try:
        if action in ['play', 'cancel', 'maybe']:
            # Очищаем предыдущий статус
            for status in ['play', 'cancel', 'maybe']:
                db.data[status].discard(user.id)
            
            # Устанавливаем новый статус
            db.data[action].add(user.id)
            db.save_data()
            
            # Ответ пользователю
            responses = {
                'play': "✅ Вы записаны на игру!",
                'cancel': "❌ Вы отказались от игры",
                'maybe': "❓ Вы под вопросом"
            }
            await query.answer(responses[action])
            
            # Проверка уведомлений
            await check_notifications(update, context)
            
            # Обновляем интерфейс
            await start(update, context)
            
        elif action == 'stats':
            await query.edit_message_text(
                text=get_stats_text(),
                parse_mode='Markdown'
            )
    except Exception as e:
        print(f"Ошибка в handle_callback: {e}")
        await query.answer("⚠️ Произошла ошибка, попробуйте позже")

async def check_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        playing_count = len(db.data['play'])
        chat_id = update.effective_chat.id

        if playing_count >= 15 and db.data['last_notification'] != 15:
            await context.bot.send_message(
                chat_id=chat_id,
                text="🔥 *15 человек!!! Играем в три команды по 5!*",
                parse_mode='Markdown'
            )
            db.data['last_notification'] = 15
            db.save_data()
        elif playing_count >= 12 and db.data['last_notification'] not in (12, 15):
            await context.bot.send_message(
                chat_id=chat_id,
                text="⚡ *Набралось 12 человек! Играем в две команды по 6!*",
                parse_mode='Markdown'
            )
            db.data['last_notification'] = 12
            db.save_data()
    except Exception as e:
        print(f"Ошибка в check_notifications: {e}")

def get_stats_text():
    try:
        playing = len(db.data['play'])
        not_playing = len(db.data['cancel'])
        maybe = len(db.data['maybe'])
        ignored = len(db.data['all_users']) - playing - not_playing - maybe
        
        return (
            "📊 *Статистика:*\n\n"
            f"✅ Играют: *{playing}*\n"
            f"❌ Отказались: *{not_playing}*\n"
            f"❓ Под вопросом: *{maybe}*\n"
            f"🤷 Не ответили: *{ignored if ignored > 0 else 0}*"
        )
    except Exception as e:
        print(f"Ошибка в get_stats_text: {e}")
        return "⚠️ Не удалось получить статистику"

def main():
    TOKEN = os.getenv('TELEGRAM_TOKEN')
    if not TOKEN:
        print("❌ Ошибка: Не задан TELEGRAM_TOKEN!")
        exit(1)

    application = Application.builder().token(TOKEN).build()

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))

    # Обработка ошибок
    application.add_error_handler(lambda update, context: print(f"Ошибка: {context.error}"))

    print("Бот запускается...")
    
    try:
        # Указываем параметры polling для избежания конфликтов
        application.run_polling(
            close_loop=False,
            stop_signals=None,
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
    except Exception as e:
        print(f"Фатальная ошибка: {e}")
        # Принудительно завершаем процесс при конфликте
        os._exit(1)

if __name__ == "__main__":
    main()
