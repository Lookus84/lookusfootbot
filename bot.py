import os
import pickle
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    CallbackQueryHandler,
    ContextTypes
)

class BotDatabase:
    def __init__(self):
        self.data_file = 'football_bot_data.pkl'
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
    user = update.effective_user
    
    await query.answer()
    
    if not user:
        return

    # Очищаем предыдущий статус
    for status in ['playing', 'not_playing', 'maybe']:
        if user.id in db.data[status]:
            db.data[status].remove(user.id)
    
    # Обрабатываем действие
    if query.data == 'play':
        db.data['playing'].add(user.id)
        await query.answer("Вы записаны на игру! ✅")
    elif query.data == 'cancel':
        db.data['not_playing'].add(user.id)
        await query.answer("Вы отказались от игры ❌")
    elif query.data == 'maybe':
        db.data['maybe'].add(user.id)
        await query.answer("Вы под вопросом 🤔")
    elif query.data == 'stats':
        await query.message.reply_text(
            get_stats_text(),
            parse_mode='Markdown'
        )
        db.save_data()
        return
    
    db.save_data()
    await check_notifications(update, context)
    
    # Обновляем сообщение с кнопками
    keyboard = [
        [InlineKeyboardButton("✅ Играю!", callback_data='play')],
        [InlineKeyboardButton("❌ Не играю", callback_data='cancel')],
        [InlineKeyboardButton("❓ Под вопросом", callback_data='maybe')],
        [InlineKeyboardButton("📊 Статистика", callback_data='stats')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await query.edit_message_text(
            "⚽ *Футбольный бот* ⚽\nВыбери действие:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    except:
        pass

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
        db.save_data()
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
    TOKEN = os.getenv('TOKEN', '7994041571:AAF-hoI9hyTIj__S7Ac5_PIpOq9BfC3SUqk')
    
    application = Updater(TOKEN).build_application()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback))

    print("Бот запускается...")
    application.run_polling()
    print("Бот успешно запущен!")

if __name__ == "__main__":
    main()
