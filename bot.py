from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# ====== CONFIG ======
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
STEAM_API_KEY = os.getenv("STEAM_API_KEY")
GROUP_INVITE_LINK = os.getenv("GROUP_INVITE_LINK")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # Telegram channel ID like @yourchannel

# ====== STEPS ======
NAME, SURNAME, SECTION, AUID, TELEGRAM_USERNAME, STEAM_ID = range(6)

# ====== BOT HANDLERS ======
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "👋 Welcome to the Acharya CS2 Registration Bot!\nPlease enter your *Name:*",
        parse_mode=ParseMode.MARKDOWN
    )
    return NAME

def get_name(update, context):
    context.user_data['name'] = update.message.text
    update.message.reply_text("Please enter your *Surname:*", parse_mode=ParseMode.MARKDOWN)
    return SURNAME

def get_surname(update, context):
    context.user_data['surname'] = update.message.text
    update.message.reply_text("Enter your *Section:* (e.g., CSE-A, IT-B)", parse_mode=ParseMode.MARKDOWN)
    return SECTION

def get_section(update, context):
    context.user_data['section'] = update.message.text
    update.message.reply_text("Enter your *AUID:*", parse_mode=ParseMode.MARKDOWN)
    return AUID

def get_auid(update, context):
    context.user_data['auid'] = update.message.text
    update.message.reply_text("Enter your *Telegram Username:* (without @)", parse_mode=ParseMode.MARKDOWN)
    return TELEGRAM_USERNAME

def get_telegram_username(update, context):
    context.user_data['telegram_username'] = update.message.text
    update.message.reply_text("Finally, enter your *Steam Account ID:* (numeric or custom profile ID)", parse_mode=ParseMode.MARKDOWN)
    return STEAM_ID

def check_steam_id(steam_id):
    # Check if it's a vanity URL
    vanity_url = f"https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/?key={STEAM_API_KEY}&vanityurl={steam_id}"
    resp = requests.get(vanity_url).json()
    if resp.get("response", {}).get("success") == 1:
        return True

    # Check if numeric Steam ID
    try:
        num = int(steam_id)
        if num < 76561197960265728:
            num += 76561197960265728
        url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={STEAM_API_KEY}&steamids={num}"
        resp = requests.get(url).json()
        return len(resp.get("response", {}).get("players", [])) > 0
    except ValueError:
        return False

def get_steam(update, context):
    steam_id = update.message.text.strip()
    update.message.reply_text("🔍 Checking your Steam ID, please wait...")

    if not check_steam_id(steam_id):
        update.message.reply_text("❌ Invalid Steam ID. Please try again.")
        return STEAM_ID

    context.user_data['steam_id'] = steam_id

    # Prepare message to send to channel
    message = (
        f"📝 *New Registration!*\n\n"
        f"*Name:* {context.user_data['name']}\n"
        f"*Surname:* {context.user_data['surname']}\n"
        f"*Section:* {context.user_data['section']}\n"
        f"*AUID:* {context.user_data['auid']}\n"
        f"*Telegram Username:* @{context.user_data['telegram_username']}\n"
        f"*Steam ID:* {context.user_data['steam_id']}"
    )

    # Send to channel
    context.bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode=ParseMode.MARKDOWN)

    update.message.reply_text(
        "✅ Registration complete!\n"
        "You have been successfully added to the Acharya CS2 Competition.\n\n"
        f"🎮 Join the official group here:\n{GROUP_INVITE_LINK}"
    )
    return ConversationHandler.END

def cancel(update, context):
    update.message.reply_text("❌ Registration cancelled. You can start again with /start.")
    return ConversationHandler.END

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(Filters.text & ~Filters.command, get_name)],
            SURNAME: [MessageHandler(Filters.text & ~Filters.command, get_surname)],
            SECTION: [MessageHandler(Filters.text & ~Filters.command, get_section)],
            AUID: [MessageHandler(Filters.text & ~Filters.command, get_auid)],
            TELEGRAM_USERNAME: [MessageHandler(Filters.text & ~Filters.command, get_telegram_username)],
            STEAM_ID: [MessageHandler(Filters.text & ~Filters.command, get_steam)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
