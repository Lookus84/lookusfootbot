import os
import pickle
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
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

class HealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot is alive!')

def run_health_server():
    server = HTTPServer(('0.0.0.0', 8080), HealthServer)
    server.serve_forever()

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

    if query.data == 'play':
        db.data['not_playing'].discard(user.id)
        db.data['maybe'].discard(user.id)
        db.data['playing'].add(user.id)
        await query.answer("Вы записаны на игру! ✅")
    elif query.data == 'cancel':
        db.data['playing'].discard(user.id)
        db.data['maybe'].discard(user.id)
        db.data['not_playing'].add(user.id)
        await query.answer("Вы отказались от игры ❌")
    elif query.data == 'maybe':
        db.data['playing'].discard(user.id)
        db.data['not_playing'].discard(user.id)
        db.data['maybe'].add(user.id)
        await query.answer("Вы под вопросом 🤔")
    elif query.data == 'stats':
        await query.edit_message_text(
            get_stats_text(),
            parse_mode='Markdown'
        )
        db.save_data()
        return
    
    db.save_data()
    await check_notifications(update, context)
    
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
    except Exception as e:
        print(f"Error editing message: {e}")

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
    # Запускаем HTTP-сервер в отдельном потоке
    health_thread = Thread(target=run_health_server)
    health_thread.daemon = True
    health_thread.start()

    # Запускаем бота
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
