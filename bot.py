from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

players = []

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "Привет! Я бот для записи на футбол.\n"
        "Команды:\n"
        "/запись - записаться\n"
        "/список - список игроков\n"
        "/сброс - очистить список"
    )

def add_player(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if user not in players:
        players.append(user)
        update.message.reply_text(f"{user.first_name} записан! ⚽")
    else:
        update.message.reply_text("Ты уже в списке!")

def show_players(update: Update, context: CallbackContext) -> None:
    if not players:
        update.message.reply_text("Пока никого нет 😢")
    else:
        player_list = "\n".join([f"{i+1}. {user.first_name}" for i, user in enumerate(players)])
        update.message.reply_text(f"Игроки ({len(players)}):\n{player_list}")

def reset_players(update: Update, context: CallbackContext) -> None:
    global players
    players = []
    update.message.reply_text("Список очищен!")

def main():
    TOKEN = "7994041571:AAF-hoI9hyTIj__S7Ac5_PIpOq9BfC3SUqk"  # <- Твой токен
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("запись", add_player))
    dispatcher.add_handler(CommandHandler("список", show_players))
    dispatcher.add_handler(CommandHandler("сброс", reset_players))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()