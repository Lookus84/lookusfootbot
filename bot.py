from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler

# База данных
players_db = {
    "playing": [],
    "not_playing": [],
    "maybe": [],
    "ignored": set(),
    "last_notification": 0
}

def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if user.id not in [u.id for u in players_db["playing"] + players_db["not_playing"] + players_db["maybe"]]:
        players_db["ignored"].add(user.id)

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

    if user.id in players_db["ignored"]:
        players_db["ignored"].remove(user.id)

    # Очищаем пользователя из всех списков перед добавлением в новый
    for status in ["playing", "not_playing", "maybe"]:
        players_db[status] = [u for u in players_db[status] if u.id != user.id]

    if action == 'play':
        players_db["playing"].append(user)
        query.answer("Ты в игре! ✅")
    elif action == 'cancel':
        players_db["not_playing"].append(user)
        query.answer("Жаль, но ты выбыл ❌")
    elif action == 'maybe':
        players_db["maybe"].append(user)
        query.answer("Ждём решения 🤔")
    elif action == 'stats':
        query.message.reply_text(
            get_stats_text(),
            parse_mode='Markdown'
        )
        return

    check_notifications(update, context)

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

def check_notifications(update: Update, context: CallbackContext) -> None:
    playing_count = len(players_db["playing"])
    chat_id = update.effective_chat.id

    if playing_count >= 15 and players_db["last_notification"] != 15:
        context.bot.send_message(
            chat_id=chat_id,
            text="🔥 *15 человек!!! Играем в три команды по 5!*",
            parse_mode='Markdown'
        )
        players_db["last_notification"] = 15
    elif playing_count >= 12 and players_db["last_notification"] not in (12, 15):
        context.bot.send_message(
            chat_id=chat_id,
            text="⚡ *Набралось 12 человек! Играем в две команды по 6!*",
            parse_mode='Markdown'
        )
        players_db["last_notification"] = 12

def get_stats_text() -> str:
    playing = len(players_db["playing"])
    not_playing = len(players_db["not_playing"])
    maybe = len(players_db["maybe"])
    ignored = len(players_db["ignored"])

    return (
        "📊 *Статистика:*\n\n"
        f"✅ Играют: *{playing}*\n"
        f"❌ Отказались: *{not_playing}*\n"
        f"❓ Под вопросом: *{maybe}*\n"
        f"🤷 Не ответили: *{ignored}*"
    )

def main():
    TOKEN = "7994041571:AAF-hoI9hyTIj__S7Ac5_PIpOq9BfC3SUqk"
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(button_click))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
