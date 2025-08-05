from telegram import Update, MessageOriginUser
from telegram.ext import ApplicationBuilder, CallbackContext, CommandHandler, ContextTypes
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()
registering = False

token = os.getenv('Telegram_Token')
if not token:
    raise ValueError("No Telegram token found in environment variables")

def write (result):
    try:
        with open("users.json", "r") as infile:
            users = json.load(infile)
    except (json.JSONDecodeError, FileNotFoundError):
        users = []

    users.append(result)

    with open("users.json", "w") as outfile:
        json.dump(users, outfile, indent=2)

async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')

async def register(update: Update, context: CallbackContext) -> None:
    global registering
    registering = True
    await context.bot.send_message(
        chat_id=update.message.chat_id,
        text="Enter your intake code",
        entities=update.message.entities
    )

app = ApplicationBuilder().token(token).build()
app.add_handler(CommandHandler("hello", hello))
app.add_handler(CommandHandler("register", register))

if __name__ == '__main__':
    print("Bot started...")
    app.run_polling()

