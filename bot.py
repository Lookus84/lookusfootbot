from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler, PersistenceInput
import os
import pickle
from datetime import datetime

# Настройки persistence (сохранение состояния)
class FilePersistence:
    def __init__(self, filename='bot_data.pkl'):
        self.filename = filename
        try:
            with open(filename, 'rb') as f:
                self.data = pickle.load(f)
        except (FileNotFoundError, EOFError):
            self.data = {
                'user_data': {},
                'chat_data': {},
                'bot_data': {
                    'playing': [],
                    'not_playing': [],
                    'maybe': [],
                    'last_notification': 0
                }
            }

    def flush(self):
        with open(self.filename, 'wb') as f:
            pickle.dump(self.data, f)

persistence = FilePersistence()

def get_players():
    return persistence.data['bot_data']

def save_players():
    persistence.flush()

def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("✅ Играю!", callback_data='play')],
        [InlineKeyboardButton("❌ Не играю", callback_data='cancel')],
        [InlineKeyboardButton("❓ Под вопросом", callback_data='maybe')],
        [InlineKeyboardButton("📊 Статистика", callback_data='stats')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "⚽ *Футбольный бот* ⚽\nВыбери действие:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

def button_click(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user = query.from_user
    action = query.data
    players = get_players()

    # Удаляем пользователя из всех списков
    for status in ['playing', 'not_playing', 'maybe']:
        players[status] = [u for u in players[status] if u['id'] != user.id]

    if action == 'play':
        players['playing'].append({'id': user.id, 'name': user.first_name})
        query.answer("Ты в игре! ✅")
    elif action == 'cancel':
        players['not_playing'].append({'id': user.id, 'name': user.first_name})
        query.answer("Жаль, но ты выбыл ❌")
    elif action == 'maybe':
        players['maybe'].append({'id': user.id, 'name': user.first_name})
        query.answer("Ждём решения 🤔")
    elif action == 'stats':
        query.message.reply_text(
            get_stats_text(),
            parse_mode='Markdown'
        )
        save_players()
        return

    save_players()
    check_notifications(update, context)

    # Обновляем меню
    keyboard = [
        [InlineKeyboardButton("✅ Играю!", callback_data='play')],
        [InlineKeyboardButton("❌ Не играю", callback_data='cancel')],
        [InlineKeyboardButton("❓ Под вопросом", callback_data='maybe')],
        [InlineKeyboardButton("📊 Статистика", callback_data='stats')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        "⚽ *Футбольный бот* ⚽\nВыбери действие:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

def check_notifications(update: Update, context: CallbackContext):
    players = get_players()
    playing_count = len(players['playing'])
    chat_id = update.effective_chat.id

    if playing_count >= 15 and players['last_notification'] != 15:
        context.bot.send_message(
            chat_id=chat_id,
            text="🔥 *15 человек!!! Играем в три команды по 5!*",
            parse_mode='Markdown'
        )
        players['last_notification'] = 15
        save_players()
    elif playing_count >= 12 and players['last_notification'] not in (12, 15):
        context.bot.send_message(
            chat_id=chat_id,
            text="⚡ *Набралось 12 человек! Играем в две команды по 6!*",
            parse_mode='Markdown'
        )
        players['last_notification'] = 12
        save_players()

def get_stats_text():
    players = get_players()
    playing = len(players['playing'])
    not_playing = len(players['not_playing'])
    maybe = len(players['maybe'])
    
    # Подсчет "игнорирующих" (все кто писал /start но не выбрал статус)
    all_users = set(u['id'] for u in players['playing'] + players['not_playing'] + players['maybe'])
    ignored = len(persistence.data['user_data']) - len(all_users) if persistence.data['user_data'] else 0

    return (
        "📊 *Статистика:*\n\n"
        f"✅ Играют: *{playing}*\n"
        f"❌ Отказались: *{not_playing}*\n"
        f"❓ Под вопросом: *{maybe}*\n"
        f"🤷 Не ответили: *{ignored if ignored > 0 else 0}*"
    )

def main():
    TOKEN = os.getenv('TOKEN', '7994041571:AAF-hoI9hyTIj__S7Ac5_PIpOq9BfC3SUqk')
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(button_click))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
