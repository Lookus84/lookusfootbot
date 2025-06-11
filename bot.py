from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler

# База данных
players_db = {
    "playing": [],
    "not_playing": [],
    "maybe": [],
    "ignored": set(),
    "last_notification": 0  # Чтобы не дублировать уведомления
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

    if action == 'play':
        players_db["playing"] = [u for u in players_db["playing"] if u.id != user.id]
        players_db["playing"].append(user)
        players_db["not_playing"] = [u for u in players_db["not_playing"] if u.id != user.id]
        players_db["maybe"] = [u for u in players_db["maybe"] if u.id != user.id]
        query.answer("Ты в игре! ✅")
    elif action == 'cancel':
        players_db["not_playing"] = [u for u in players_db["not_playing"] if u.id != user.id]
        players_db["not_playing"].append(user)
        players_db["playing"] = [u for u in players_db["playing"] if
