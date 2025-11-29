from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, 
    CallbackContext, 
    CommandHandler, 
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler
)
import os
import json
from datetime import time
from enum import Enum
from reader import finder
from Service import getting
from datetime import time
from dotenv import load_dotenv
import pytz
from pathlib import Path


registering = False
code = ""
load_dotenv()
token = os.environ.get('Telegram_Token')
if not token:
    raise ValueError("No Telegram token found in environment variables")

# set project root and users file location
BASE_DIR = Path(__file__).resolve().parents[1]  # /Users/neehtham/Documents/code/sheduleBot
USERS_FILE = BASE_DIR / "users.json"

def write(result):
    try:
        if USERS_FILE.exists():
            with USERS_FILE.open("r", encoding="utf-8") as infile:
                users = json.load(infile)
        else:
            users = {}
    except (json.JSONDecodeError, FileNotFoundError):
        users = {}

    if not isinstance(users, dict):
        users = {}

    users.update(result)

    with USERS_FILE.open("w", encoding="utf-8") as outfile:
        json.dump(users, outfile, indent=2)

def read():
    try:
        if not USERS_FILE.exists():
            return {}
        with USERS_FILE.open("r", encoding="utf-8") as infile:
            users = json.load(infile)
            return users
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

async def welcome(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Welcome to the bot! Use /register to register.")

class RegistrationState(Enum):
    IDLE = 0
    AWAITING_CODE = 1
    AWAITING_GROUP = 2
    SELECTING_ACCOMMODATION = 3

# Replace global variables with user state dictionary
user_states = {}
user_data = {}

async def register(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    users = read()
    if user_id in users:
        await update.message.reply_text("You are already registered.")
        return
    else:
        user_states[user_id] = RegistrationState.AWAITING_CODE
        await update.message.reply_text("Enter your intake code")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    message = update.message.text
    
    if user_id not in user_states:
        return
        
    state = user_states[user_id]
    
    if state == RegistrationState.AWAITING_CODE:
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]['code'] = message
        user_states[user_id] = RegistrationState.AWAITING_GROUP
        await update.message.reply_text("enter your Group code ex:G1")
        
    elif state == RegistrationState.AWAITING_GROUP:
        user_data[user_id]['group'] = message
        user_states[user_id] = RegistrationState.SELECTING_ACCOMMODATION
        # Create keyboard directly here
        keyboard = [
            [InlineKeyboardButton("City Of Green", callback_data='COG')],
            [InlineKeyboardButton("M Vertica", callback_data='M Vertica')],
            [InlineKeyboardButton("Fortune Park", callback_data='Fortune Park')],
            [InlineKeyboardButton("Bloomsvale", callback_data='Bloomsvale')],
            [InlineKeyboardButton("LRT - Bukit Jalil", callback_data='LRT - Bukit Jalil')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Please choose your accommodation:", reply_markup=reply_markup)
    
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if user_id not in user_data:
        user_data[user_id] = {}

    await query.answer()

    await query.edit_message_text(text=f"Selected option: {query.data}")

    user_data[user_id]['accommodation'] = query.data

    result = user_data
    write(result)
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=f"Registration complete!\nCode: {result['user_id']['code']}\nGroup: {result['user_id']['group']}\nAccommodation: {result['user_id']['accommodation']}"
    )
    print("User registered:", user_data)
    user_data.pop(user_id, None)
    del user_states[user_id]

async def senddaily_job(context: ContextTypes.DEFAULT_TYPE) -> dict:
    users = read()
    if not users:
        print("senddaily_job: no users found")
        return {"sent": [], "failed": [], "skipped": []}

    sent = []
    failed = []
    skipped = []

    for user_id, details in users.items():
        code = details.get('code')
        group = details.get('group')
        accommodation = details.get('accommodation')

        schedule = finder(code, group, accommodation)
        print(f"DEBUG: user={user_id!r} code={code!r} group={group!r} accommodation={accommodation!r} schedule={schedule!r}")

        if not schedule:
            print(f"Skipping {user_id}: no schedule returned")
            skipped.append(user_id)
            continue

        try:
            await context.bot.send_message(chat_id=user_id, text=schedule)
            sent.append(user_id)
        except Exception as e:
            print(f"Failed to send message to {user_id}: {e}")
            failed.append((user_id, str(e)))

    return {"sent": sent, "failed": failed, "skipped": skipped}

async def senddaily_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Sending schedules now...")
    await senddaily_job(context)

async def delete_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    users = read()
    if user_id in users:
        del users[user_id]
        write(users)
        await update.message.reply_text("Your registration has been deleted.")
    else:
        await update.message.reply_text("You are not registered.")
     
#RED ZONE DO NOT DLELETE
def main() -> None:
    print("Bot started...")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("register", register))
    app.add_handler(CommandHandler("send", senddaily_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(CommandHandler("delete", delete_user))

    daily_queue = app.job_queue
    shedule_update = app.job_queue

    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    daily_queue.run_daily(
        senddaily_job,
        time=time(hour=7, minute=0, tzinfo=malaysia_tz),
        days=(0,1,2,3,4),  # Monday=0, Tuesday=1, Wednesday=2, Thursday=3, Friday=4
        name='daily_schedule'
    )

    
    shedule_update.run_daily(
        getting,
        time=time(hour=7, minute=0, tzinfo=malaysia_tz),
        days=(5,6),  # Saturday=5, Sunday=6
        name='shedule_update'
    )

    app.run_polling(allowed_updates=Update.ALL_TYPES)
if __name__ == "__main__":
    main()