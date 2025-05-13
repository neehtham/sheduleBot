import logging
from reader import *
from Service import *
from telegram import Update, ForceReply, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext, CallbackQueryHandler,Filters
from apscheduler.schedulers.background import BackgroundScheduler
import os
import json
from pytz import timezone

logger = logging.getLogger(__name__)

# Store bot finding status
registering = False
whispering = False
code = ''
group = ''
accomodation = ''
# Pre-assign menu text
FIRST_MENU = "<b>Menu 1</b>\n\nA beautiful menu with a shiny inline button."
SECOND_MENU = "<b>Menu 2</b>\n\nA better menu with even more shiny inline buttons."

# Pre-assign button text
NEXT_BUTTON = "Next"
BACK_BUTTON = "Back"
TUTORIAL_BUTTON = "Tutorial"

# Build keyboards
FIRST_MENU_MARKUP = InlineKeyboardMarkup([[
    InlineKeyboardButton(NEXT_BUTTON, callback_data=NEXT_BUTTON)
]])
SECOND_MENU_MARKUP = InlineKeyboardMarkup([
    [InlineKeyboardButton(BACK_BUTTON, callback_data=BACK_BUTTON)],
    [InlineKeyboardButton(TUTORIAL_BUTTON, url="https://core.telegram.org/bots/api")]
])


def echo(update: Update, context: CallbackContext) -> None:
    print(f'{update.message.from_user.first_name} wrote {update.message.text}')
    global code, group, finding, accomodation
    if not code:
        code = update.message.text
        context.bot.send_message(
            update.message.chat_id,
            "enter your Group code ex:G1",
            entities=update.message.entities
        )
    elif not group:
        group = update.message.text
    if group and code and not accomodation:
        keyboard = [
            [InlineKeyboardButton("City of Green", callback_data="City of Green")],
            [InlineKeyboardButton("LRT - Bukit Jalil", callback_data="LRT - Bukit Jalil")],
            [InlineKeyboardButton("M Vertica", callback_data="M Vertica")],
            [InlineKeyboardButton("Fortune Park", callback_data="Fortune Park")],
            [InlineKeyboardButton("Bloomsvale", callback_data="Bloomsvale")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="Select your accommodation:",
            reply_markup=reply_markup
        )
        return


def write (result):
    try:
        with open("users.json", "r") as infile:
            users = json.load(infile)
    except (json.JSONDecodeError, FileNotFoundError):
        users = []

    users.append(result)

    with open("users.json", "w") as outfile:
        json.dump(users, outfile, indent=2)
def button_tap(update: Update, context: CallbackContext) -> None:
    global accomodation, code, group
    accomodation = update.callback_query.data
    result = {
        'code': code,
        'group': group,
        'accomodation': accomodation,
        'id': update.callback_query.from_user.id
    }
    write(result)
    context.bot.send_message(
        chat_id=update.callback_query.from_user.id,
        text=f"{code}: {group} is registered to Accommodation '{accomodation}' registered!"
    )
    code = ""
    group = ""
    accomodation = ""

def register(update: Update, context: CallbackContext) -> None:
    global registering
    registering = True
    context.bot.send_message(
        update.message.chat_id,
        "enter your intake code",
        entities=update.message.entities
    )

def send(update, context):
    with open("users.json", "r") as openfile:
        json_object = json.load(openfile)
    for obj in json_object:
        message = finder(obj["code"], obj["group"],obj["accomodation"])
        if message:
            context.bot.send_message(
                chat_id=obj["id"],
                text=message
            )


def main() -> None:
    token = os.getenv('Telegram_Token')
    updater = Updater(token=token, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("register", register))
    dispatcher.add_handler(CommandHandler("send", send))
    dispatcher.add_handler(CallbackQueryHandler(button_tap))
    dispatcher.add_handler(MessageHandler(~Filters.command, echo))

    # Scheduler setup
    scheduler = BackgroundScheduler()

    scheduler.add_job(send, 'cron', hour=6, minute=00, args=[None, dispatcher], timezone=timezone('Asia/Kuala_Lumpur'))
    scheduler.add_job(getting, 'cron', day_of_week='sun', hour=0, minute=00, timezone=timezone('Asia/Kuala_Lumpur'))
    scheduler.start()

    updater.start_polling()
    updater.idle()
    try:
        import time
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == '__main__':
    main()