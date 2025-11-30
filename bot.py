from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
import requests
import pandas as pd
from dotenv import load_dotenv
import os
load_dotenv()


# ====== CONFIG ======
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
STEAM_API_KEY = os.getenv("STEAM_API_KEY")
GROUP_INVITE_LINK = os.getenv("GROUP_INVITE_LINK")
DATA_FILE = os.getenv("DATA_FILE")


# ====== STEPS ======
NAME, SURNAME, SECTION, AUID, TELEGRAM_USERNAME, STEAM_ID = range(6)

def start(update: Update, context: CallbackContext):
    update.message.reply_text("👋 Welcome to the Acharya CS2 Registration Bot!\nPlease enter your *Name:*", parse_mode='Markdown')
    return NAME

def get_name(update, context):
    context.user_data['name'] = update.message.text
    update.message.reply_text("Please enter your *Surname:*", parse_mode='Markdown')
    return SURNAME

def get_surname(update, context):
    context.user_data['surname'] = update.message.text
    update.message.reply_text("Enter your *Section:* (e.g., CSE-A, IT-B)", parse_mode='Markdown')
    return SECTION

def get_section(update, context):
    context.user_data['section'] = update.message.text
    update.message.reply_text("Enter your *AUID:*", parse_mode='Markdown')
    return AUID

def get_auid(update, context):
    context.user_data['auid'] = update.message.text
    update.message.reply_text("Enter your *Telegram Username:* (without @)", parse_mode='Markdown')
    return TELEGRAM_USERNAME

def get_telegram_username(update, context):
    context.user_data['telegram_username'] = update.message.text
    update.message.reply_text("Finally, enter your *Steam Account ID:* (numeric or custom profile ID)", parse_mode='Markdown')
    return STEAM_ID

def check_steam_id(steam_id):
    # First, try as vanity (custom) ID
    vanity_url = f"https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/?key={STEAM_API_KEY}&vanityurl={steam_id}"
    resp = requests.get(vanity_url).json()
    if resp.get("response", {}).get("success") == 1:
        return True

    # Try numeric Steam ID (convert if short)
    try:
        num = int(steam_id)
        # Convert short Steam ID to full 64-bit SteamID if necessary
        if num < 76561197960265728:
            num += 76561197960265728

        url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={STEAM_API_KEY}&steamids={num}"
        resp = requests.get(url).json()
        players = resp.get("response", {}).get("players", [])
        return len(players) > 0
    except ValueError:
        return False



def get_steam(update, context):
    steam_id = update.message.text.strip()
    update.message.reply_text("🔍 Checking your Steam ID, please wait...")

    if not check_steam_id(steam_id):
        update.message.reply_text("❌ Invalid Steam ID. Please try again with your correct Steam ID or custom ID.")
        return STEAM_ID

    context.user_data['steam_id'] = steam_id

    # Save data
    data = {
        'Name': context.user_data['name'],
        'Surname': context.user_data['surname'],
        'Section': context.user_data['section'],
        'AUID': context.user_data['auid'],
        'Telegram Username': context.user_data['telegram_username'],
        'Steam ID': context.user_data['steam_id']
    }

    try:
        df = pd.read_csv(DATA_FILE)
    except FileNotFoundError:
        df = pd.DataFrame(columns=data.keys())

    df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)

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
