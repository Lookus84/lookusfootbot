import os
import pickle
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, Filters

class BotDatabase:
    def __init__(self):
        self.data_file = '/tmp/football_bot_data.pkl'  # Изменили путь для Render
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

def start(update: Update, context: CallbackContext) -> None:
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
        update.message.reply_text(
            "⚽ *Футбольный бот* ⚽\nВыбери действие:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    elif update.callback_query:
        update.callback_query.edit_message_text(
            "⚽ *Футбольный бот* ⚽\nВыбери действие:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

def handle_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user = update.effective_user
    
    query.answer()
    
    if not user:
        return

    if query.data == 'play':
        db.data['not_playing'].discard(user.id)
        db.data['maybe'].discard(user.id)
        db.data['playing'].add(user.id)
        query.answer("Вы записаны на игру! ✅")
    elif query.data == 'cancel':
        db.data['playing'].discard(user.id)
        db.data['maybe'].discard(user.id)
        db.data['not_playing'].add(user.id)
        query.answer("Вы отказались от игры ❌")
    elif query.data == 'maybe':
        db.data['playing'].discard(user.id)
        db.data['not_playing'].discard(user.id)
        db.data['maybe'].add(user.id)
        query.answer("Вы под вопросом 🤔")
    elif query.data == 'stats':
        query.edit_message_text(
            get_stats_text(),
            parse_mode='Markdown'
        )
        db.save_data()
        return
    
    db.save_data()
    check_notifications(update, context)
    
    keyboard = [
        [InlineKeyboardButton("✅ Играю!", callback_data='play')],
        [InlineKeyboardButton("❌ Не играю", callback_data='cancel')],
        [InlineKeyboardButton("❓ Под вопросом", callback_data='maybe')],
        [InlineKeyboardButton("📊 Статистика", callback_data='stats')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        query.edit_message_text(
            "⚽ *Футбольный бот* ⚽\nВыбери действие:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"Error editing message: {e}")

def check_notifications(update: Update, context: CallbackContext):
    playing_count = len(db.data['playing'])
    chat_id = update.effective_chat.id

    if playing_count >= 15 and db.data['last_notification'] != 15:
        context.bot.send_message(
            chat_id=chat_id,
            text="🔥 *15 человек!!! Играем в три команды по 5!*",
            parse_mode='Markdown'
        )
        db.data['last_notification'] = 15
        db.save_data()
    elif playing_count >= 12 and db.data['last_notification'] not in (12, 15):
        context.bot.send_message(
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
    
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(handle_callback))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, start))

    print("Бот запускается...")
    updater.start_polling(
        drop_pending_updates=True,
        timeout=30,
        read_latency=5
    )
    print("Бот успешно запущен!")
    updater.idle()

if __name__ == "__main__":
    main()
