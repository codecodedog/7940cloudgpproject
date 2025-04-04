import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters, 
    CallbackContext, ConversationHandler, CallbackQueryHandler
)
from command.general import *
from command.register import *
from command.property import *
from util.constant import *
from util.logger import logger

# Load environment variables from .env file
load_dotenv()

def main() -> None:
    # Start the bot
    updater = Updater(token=os.getenv("TELEGRAM_KEY"))
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
                MessageHandler(Filters.text & ~Filters.command, property_condition)
            ],
            prop_condition_selection: [
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
            # Property search
            prop_search: [
                MessageHandler(Filters.text & ~Filters.command, property_search)
            ]
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
