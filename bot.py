import os
import pickle
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, Filters

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

def start_bot():
    TOKEN = os.getenv('TELEGRAM_TOKEN')
    updater = Updater(TOKEN, use_context=True)
    
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(handle_callback))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, start))

    print("Бот запускается...")
    updater.start_polling()
    print("Бот успешно запущен!")
    updater.idle()

# ... (остальные функции start, handle_callback, check_notifications, get_stats_text остаются без изменений)

if __name__ == "__main__":
    # Запускаем HTTP-сервер в отдельном потоке
    health_thread = Thread(target=run_health_server)
    health_thread.daemon = True
    health_thread.start()

    # Запускаем бота в основном потоке
    start_bot()
