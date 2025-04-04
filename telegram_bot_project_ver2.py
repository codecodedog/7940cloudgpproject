import os
import logging
import requests
import db_connect
import datetime
import json
from db_connect import get_connection
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from typing import Optional, Dict, List
from dotenv import load_dotenv
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters, 
    CallbackContext, ConversationHandler, CallbackQueryHandler
)

from command.general import *
from command.register import *
from command.property import *

# Load environment variables from .env file
load_dotenv()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# Conversation states - User Registration
user_telegram_id = 1
user_username = 2
user_condition = 3
user_district = 4
user_confirm = 5

# Conversation states - Property Registration
prop_type_choice = 10  # Leasing or Purchasing
prop_district = 11
prop_address = 12
prop_condition = 13
prop_price_min = 14
prop_price_max = 15
prop_duration = 16
prop_confirm = 17

# Group assignment state
group_assignment = 20

# Normal conversation state
question_asked = 30


def main() -> None:
    # Start the bot
    updater = Updater(token=os.environ.get("TELEGRAM_KEY"))
    dispatcher = updater.dispatcher
    
    # Main conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            # User registration states
            user_telegram_id: [
                MessageHandler(Filters.regex('^Register Now$'), register_telegram_id),
                MessageHandler(Filters.regex('^Use my Telegram ID$'), register_telegram_id)
            ],
            user_username: [
                MessageHandler(Filters.text & ~Filters.command, register_username)
            ],
            user_condition: [
                MessageHandler(Filters.text & ~Filters.command, register_condition)
            ],
            user_district: [
                MessageHandler(Filters.text & ~Filters.command, register_district)
            ],
            user_confirm: [
                MessageHandler(Filters.regex('^(Yes|No)$'), register_confirm)
            ],
            
            # Property registration states
            prop_type_choice: [
                MessageHandler(Filters.regex('^Register a Property$'), property_type_choice),
                MessageHandler(Filters.regex('^Register Another Property$'), property_type_choice),
                MessageHandler(Filters.regex('^Search for Properties$'), property_type_choice),
                MessageHandler(Filters.regex('^Ask a Question$'), property_type_choice),
                MessageHandler(Filters.regex('^Ask Another Question$'), property_type_choice)
            ],
            prop_district: [
                MessageHandler(Filters.regex('^(Leasing|Selling)$'), property_district)
            ],
            prop_address: [
                MessageHandler(Filters.text & ~Filters.command, property_address)
            ],
            prop_condition: [
                MessageHandler(Filters.text & ~Filters.command, property_conditions_selection)
            ],
            prop_price_min: [
                MessageHandler(Filters.text & ~Filters.command, property_price_min)
            ],
            prop_price_max: [
                MessageHandler(Filters.text & ~Filters.command, property_price_max)
            ],
            prop_duration: [
                MessageHandler(Filters.text & ~Filters.command, property_duration)
            ],
            prop_confirm: [
                MessageHandler(Filters.regex('^(Yes|No)$'), property_registration_confirm)
            ],
            
            # Group assignment
            group_assignment: [
                MessageHandler(Filters.text & ~Filters.command, assign_to_group)
            ],
            
            # Normal conversation
            question_asked: [
                MessageHandler(Filters.text & ~Filters.command, handle_question)
            ],
        },
        fallbacks=[
            CommandHandler("help", help_command),
            CommandHandler("register", register_command),
            CommandHandler("start", start)
        ],
    )
    
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CommandHandler("help", help_command))
    
    # Add error handler
    dispatcher.add_error_handler(error_handler)
    
    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
