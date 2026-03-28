from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ConversationHandler
)
import os
import json
import asyncio
from datetime import time
import pytz
from pathlib import Path
from dotenv import load_dotenv

from reader import finder
from Service import getting

# Load environment variables
load_dotenv()
TOKEN = os.environ.get('Telegram_Token')
if not TOKEN:
    raise ValueError("No Telegram token found in environment variables")

# Set project root and data directory
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
USERS_FILE = DATA_DIR / "users.json"

# Conversation states
AWAITING_CODE, AWAITING_GROUP, SELECTING_ACCOMMODATION = range(3)

def read_sync():
    try:
        if not USERS_FILE.exists():
            return {}
        with USERS_FILE.open("r", encoding="utf-8") as infile:
            return json.load(infile)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def write_sync(users):
    with USERS_FILE.open("w", encoding="utf-8") as outfile:
        json.dump(users, outfile, indent=2)

async def read_users():
    return await asyncio.to_thread(read_sync)

async def write_users(users):
    await asyncio.to_thread(write_sync, users)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Welcome to the Schedule Bot! 🚌📚\n\n"
        "Use /register to start receiving your daily schedule and bus timings.\n"
        "Use /delete if you wish to unregister."
    )

async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = str(update.effective_user.id)
    users = await read_users()
    if user_id in users:
        await update.message.reply_text("You are already registered! Use /delete first if you want to re-register.")
        return ConversationHandler.END
    
    await update.message.reply_text("Please enter your intake code (e.g., APD1F2309SE):")
    return AWAITING_CODE

async def get_intake_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['code'] = update.message.text.strip().upper()
    await update.message.reply_text("Now enter your Group code (e.g., G1 or G2):")
    return AWAITING_GROUP

async def get_group_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['group'] = update.message.text.strip().upper()
    
    keyboard = [
        [InlineKeyboardButton("City Of Green", callback_data='City Of Green')],
        [InlineKeyboardButton("M Vertica", callback_data='M Vertica')],
        [InlineKeyboardButton("Fortune Park", callback_data='Fortune Park')],
        [InlineKeyboardButton("Bloomsvale", callback_data='Bloomsvale')],
        [InlineKeyboardButton("LRT - Bukit Jalil", callback_data='LRT - Bukit Jalil')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Please choose your accommodation:", reply_markup=reply_markup)
    return SELECTING_ACCOMMODATION

async def select_accommodation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user_id = str(update.effective_user.id)
    accommodation = query.data
    
    await query.answer()
    await query.edit_message_text(text=f"Selected accommodation: {accommodation}")

    # Save user data
    user_info = {
        'code': context.user_data['code'],
        'group': context.user_data['group'],
        'accommodation': accommodation
    }
    
    users = await read_users()
    users[user_id] = user_info
    await write_users(users)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            "✅ Registration complete!\n\n"
            f"📍 Intake: {user_info['code']}\n"
            f"👥 Group: {user_info['group']}\n"
            f"🏠 Accommodation: {user_info['accommodation']}\n\n"
            "You will now receive your schedule every morning at 7:00 AM."
        )
    )
    
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Registration cancelled.")
    context.user_data.clear()
    return ConversationHandler.END

async def delete_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    users = await read_users()
    if user_id in users:
        del users[user_id]
        await write_users(users)
        await update.message.reply_text("Your registration has been deleted.")
    else:
        await update.message.reply_text("You are not registered.")

async def send_schedules_now(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("🔄 Fetching and sending schedules...")
    # Refresh data first
    await getting()
    results = await run_daily_job(context)
    
    summary = (
        f"✅ Sent: {len(results['sent'])}\n"
        f"❌ Failed: {len(results['failed'])}\n"
        f"⏭ Skipped: {len(results['skipped'])}"
    )
    await update.message.reply_text(f"Schedule distribution complete!\n\n{summary}")

async def run_daily_job(context: ContextTypes.DEFAULT_TYPE) -> dict:
    users = await read_users()
    if not users:
        return {"sent": [], "failed": [], "skipped": []}

    sent, failed, skipped = [], [], []

    for user_id, details in users.items():
        try:
            code = details.get('code')
            group = details.get('group')
            acc = details.get('accommodation')
            
            # finder handles the logic of finding the schedule
            schedule_text = finder(code, group, acc)
            
            if not schedule_text or "No physical classes" in schedule_text:
                # Still send "No classes" message or skip? 
                # According to reader.py, it returns a message anyway.
                pass
                
            await context.bot.send_message(chat_id=user_id, text=schedule_text)
            sent.append(user_id)
        except Exception as e:
            print(f"Error sending to {user_id}: {e}")
            failed.append(user_id)

    return {"sent": sent, "failed": failed, "skipped": skipped}

async def scheduled_morning_task(context: ContextTypes.DEFAULT_TYPE):
    """Refreshes data and sends schedules every morning."""
    await getting() # Refresh schedules from S3
    await run_daily_job(context)

def main() -> None:
    print("Bot starting...")
    app = ApplicationBuilder().token(TOKEN).build()

    # Conversation handler for registration
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("register", register_start)],
        states={
            AWAITING_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_intake_code)],
            AWAITING_GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_group_code)],
            SELECTING_ACCOMMODATION: [CallbackQueryHandler(select_accommodation)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("send", send_schedules_now))
    app.add_handler(CommandHandler("delete", delete_user))
    
    # Schedule the daily job at 7:00 AM (MYT)
    # Note: Ensure the server time is correct or handle timezone
    job_queue = app.job_queue
    job_queue.run_daily(
        scheduled_morning_task, 
        time=time(hour=7, minute=0, tzinfo=pytz.timezone('Asia/Kuala_Lumpur'))
    )

    print("Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()