from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler

# База данных (пока просто словарь)
players_db = {
    "playing": [],
    "not_playing": [],
    "maybe": []
}

def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("✅ Играю!", callback_data='play')],
        [InlineKeyboardButton("❌ Не играю", callback_data='cancel')],
        [InlineKeyboardButton("❓ Под вопросом", callback_data='maybe')],
        [InlineKeyboardButton("📋 Список игроков", callback_data='list')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "⚽ *Футбольный бот* ⚽\n"
        "Выбери действие:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

def button_click(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user = query.from_user
    action = query.data

    if action == 'play':
        if user not in players_db["playing"]:
            players_db["playing"].append(user)
            query.answer(f"Ты в игре! ✅")
        else:
            query.answer("Ты уже записан!")
    elif action == 'cancel':
        if user in players_db["playing"]:
            players_db["playing"].remove(user)
        query.answer("Жаль, но ты выбыл ❌")
    elif action == 'maybe':
        if user not in players_db["maybe"]:
            players_db["maybe"].append(user)
            query.answer("Ждём решения 🤔")
        else:
            query.answer("Ты уже в «может быть»")
    elif action == 'list':
        players_list = format_players_list()
        query.message.reply_text(
            players_list,
            parse_mode='Markdown'
        )
        return

    # Обновляем сообщение с кнопками
    keyboard = [
        [InlineKeyboardButton("✅ Играю!", callback_data='play')],
        [InlineKeyboardButton("❌ Не играю", callback_data='cancel')],
        [InlineKeyboardButton("❓ Под вопросом", callback_data='maybe')],
        [InlineKeyboardButton("📋 Список игроков", callback_data='list')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        "⚽ *Футбольный бот* ⚽\n"
        "Выбери действие:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

def format_players_list() -> str:
    playing = "🔹 *Играют:*\n" + "\n".join([f"👉 {user.first_name}" for user in players_db["playing"]]) if players_db["playing"] else "🔹 *Играют:* пока никто 😢"
    maybe = "🔸 *Под вопросом:*\n" + "\n".join([f"👉 {user.first_name}" for user in players_db["maybe"]]) if players_db["maybe"] else "🔸 *Под вопросом:* пока никто"
    return f"{playing}\n\n{maybe}"

def main():
    TOKEN = "7994041571:AAF-hoI9hyTIj__S7Ac5_PIpOq9BfC3SUqk"  # Твой токен
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(button_click))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
