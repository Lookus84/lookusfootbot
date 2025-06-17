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
                'playing': set(),
                'not_playing': set(),
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

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    if not user:
        return

    action = query.data
    if action in ['play', 'cancel', 'maybe']:
        # Очищаем предыдущий статус
        for status in ['playing', 'not_playing', 'maybe']:
            if user.id in db.data[status]:
                db.data[status].remove(user.id)
        
        # Устанавливаем новый статус
        db.data[action].add(user.id)
        await query.answer(f"Статус обновлен: {'✅ Играю' if action == 'play' else '❌ Не играю' if action == 'cancel' else '❓ Под вопросом'}")
    elif action == 'stats':
        await query.edit_message_text(
            text=get_stats_text(),
            parse_mode='Markdown'
        )
    
    db.save_data()
    await check_notifications(update, context)
    await start(update, context)  # Обновляем интерфейс

async def check_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    playing_count = len(db.data['playing'])
    chat_id = update.effective_chat.id

    if playing_count >= 15 and db.data['last_notification'] != 15:
        await context.bot.send_message(
            chat_id=chat_id,
            text="🔥 *15 человек!!! Играем в три команды по 5!*",
            parse_mode='Markdown'
        )
        db.data['last_notification'] = 15
    elif playing_count >= 12 and db.data['last_notification'] not in (12, 15):
        await context.bot.send_message(
            chat_id=chat_id,
            text="⚡ *Набралось 12 человек! Играем в две команды по 6!*",
            parse_mode='Markdown'
        )
        db.data['last_notification'] = 12
    
    db.save_data()

def get_stats_text():
    playing = len(db.data['playing'])
    not_playing = len(db.data['not_playing'])
    maybe = len(db.data['maybe'])
    ignored = len(db.data['all_users']) - playing - not_playing - maybe
    
    return (
        "📊 *Статистика:*\n\n"
        f"✅ Играют: *{playing}*\n"
        f"❌ Отказались: *{not_playing}*\n"
        f"❓ Под вопросом: *{maybe}*\n"
        f"🤷 Не ответили: *{ignored if ignored > 0 else 0}*"
    )

def main():
    TOKEN = os.getenv('TELEGRAM_TOKEN')
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))

    print("Бот запускается...")
    application.run_polling()
    print("Бот успешно запущен!")

if __name__ == "__main__":
    main()
