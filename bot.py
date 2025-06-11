import os
import pickle
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler
from telegram.error import BadRequest

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
                'playing': [],
                'not_playing': [],
                'maybe': [],
                'last_notification': 0,
                'all_users': set()
            }
    
    def save_data(self):
        with open(self.data_file, 'wb') as f:
            pickle.dump(self.data, f)

db = BotDatabase()

def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
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
            update.message.reply_text(
                "⚽ *Футбольный бот* ⚽\nВыбери действие:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            update.callback_query.message.reply_text(
                "⚽ *Футбольный бот* ⚽\nВыбери действие:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    except Exception as e:
        print(f"Error in start: {e}")

def button_click(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user = update.effective_user
    action = query.data
    
    try:
        # Удаляем пользователя из всех списков
        for status in ['playing', 'not_playing', 'maybe']:
            if user.id in db.data[status]:
                db.data[status].remove(user.id)
        
        if action == 'play':
            db.data['playing'].append(user.id)
            query.answer("Ты в игре! ✅")
        elif action == 'cancel':
            db.data['not_playing'].append(user.id)
            query.answer("Жаль, но ты выбыл ❌")
        elif action == 'maybe':
            db.data['maybe'].append(user.id)
            query.answer("Ждём решения 🤔")
        elif action == 'stats':
            query.message.reply_text(
                get_stats_text(),
                parse_mode='Markdown'
            )
            db.save_data()
            return
        
        db.save_data()
        check_notifications(update, context)
        
        # Обновляем меню только если статус изменился
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
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise
    except Exception as e:
        print(f"Error in button_click: {e}")
        query.answer("Произошла ошибка, попробуйте ещё раз")

def check_notifications(update: Update, context: CallbackContext):
    try:
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
    except Exception as e:
        print(f"Error in check_notifications: {e}")

def get_stats_text():
    try:
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
    except Exception as e:
        print(f"Error in get_stats_text: {e}")
        return "Не удалось получить статистику"

def error_handler(update: Update, context: CallbackContext):
    print(f"Update {update} caused error {context.error}")
    if update.callback_query:
        update.callback_query.answer("Произошла ошибка, попробуйте ещё раз")

def main():
    TOKEN = os.getenv('TOKEN', '7994041571:AAF-hoI9hyTIj__S7Ac5_PIpOq9BfC3SUqk')
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(button_click))
    dispatcher.add_error_handler(error_handler)

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
