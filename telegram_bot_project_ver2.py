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

# Districts in Hong Kong
hk_districts = [
    "Central & Western", "Wan Chai", "Eastern", "Southern", 
    "Yau Tsim Mong", "Sham Shui Po", "Kowloon City", "Wong Tai Sin", 
    "Kwun Tong", "Tsuen Wan", "Tuen Mun", "Yuen Long", 
    "North", "Tai Po", "Sha Tin", "Sai Kung", "Islands"
]

# Property conditions
property_conditions = [
    "Sea View", "Transportation", "New Building", "Renovated", 
    "Pet Friendly", "Furnished", "Near MTR", "Near Schools"
]

class ChatGPT:
    def __init__(self):
        self.apiKey = os.environ.get('CHATGPT_API_KEY')
        self.modelName = "gpt-4-o-mini"
        self.apiVersion = "2024-10-21"
        self.basicUrl = "https://genai.hkbu.edu.hk/general/rest"
        
    def get_response(self, message):
        conversation = [{"role": "user", "content": message}]
        url = self.basicUrl + "/deployments/" + self.modelName + "/chat/completions/?api-version=" + self.apiVersion
        headers = {'Content-Type': 'application/json', 'api-key': self.apiKey} 
        payload = {'messages': conversation}
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            return data['choices'][0]['message']['content']
        else:
            logger.error(f"API Error: {response.status_code} - {response.text}")
            return f"Having trouble connecting to my backend. Error: {response.status_code}"

# User Registration Flow
def register_command(update: Update, context: CallbackContext) -> int:
    # Start the registration process with buttons
    update.message.reply_text(
        "Hello! Let's get you registered for our Hong Kong Property Assistant service.\n"
        "This will help us provide you with personalized property matching.",
        reply_markup=ReplyKeyboardMarkup([['Use my Telegram ID']], one_time_keyboard=True)
    )
    
    return user_telegram_id

def register_telegram_id(update: Update, context: CallbackContext) -> int:
    # Save Telegram ID automatically
    user = update.effective_user
    telegram_id = user.id
    
    # Save to context
    context.user_data['telegram_id'] = telegram_id
    
    update.message.reply_text(
        f"Great! Your Telegram ID ({telegram_id}) has been saved.",
        reply_markup=ReplyKeyboardMarkup([['Use my Telegram username']], one_time_keyboard=True)
    )
    
    return user_username

def register_username(update: Update, context: CallbackContext) -> int:
    # Save username automatically or use input
    user = update.effective_user
    
    if update.message.text == 'Use my Telegram username':
        username = user.username or f"User_{user.id}"
    else:
        username = update.message.text
    
    # Save to context
    context.user_data['username'] = username
    
    # Create buttons for property conditions
    condition_buttons = [[condition] for condition in property_conditions]
    condition_buttons.append(['Other'])
    
    update.message.reply_text(
        f"Username saved as: {username}\n\n"
        "Now, please select your property preferences (you can select multiple):",
        reply_markup=ReplyKeyboardMarkup(condition_buttons, one_time_keyboard=False)
    )
    
    # Initialize empty conditions list
    context.user_data['conditions'] = []
    
    return user_condition

def register_condition(update: Update, context: CallbackContext) -> int:
    # Add conditions one by one until user types "Done"
    user_input = update.message.text
    
    if user_input == 'Done':
        # Proceed to next step when user is done selecting conditions
        district_buttons = []
        for i in range(0, len(hk_districts), 2):
            row = [hk_districts[i]]
            if i+1 < len(hk_districts):
                row.append(hk_districts[i+1])
            district_buttons.append(row)
        district_buttons.append(['All Districts'])
        
        update.message.reply_text(
            "Great! Now, which districts in Hong Kong are you interested in?",
            reply_markup=ReplyKeyboardMarkup(district_buttons, one_time_keyboard=True)
        )
        return user_district
    elif user_input == 'Other':
        update.message.reply_text(
            "Please type your custom condition:"
        )
        return user_condition
    else:
        # Add this condition to the list
        if 'conditions' not in context.user_data:
            context.user_data['conditions'] = []
            
        context.user_data['conditions'].append(user_input)
        
        # Show current selections and option to finish
        conditions_text = ", ".join(context.user_data['conditions'])
        
        # Add "Done" button to the keyboard
        condition_buttons = [[condition] for condition in property_conditions]
        condition_buttons.append(['Other'])
        condition_buttons.append(['Done'])
        
        update.message.reply_text(
            f"Added: {user_input}\nCurrent selections: {conditions_text}\n\n"
            "Select more or press 'Done' when finished:",
            reply_markup=ReplyKeyboardMarkup(condition_buttons, one_time_keyboard=False)
        )
        
        return user_condition

def register_district(update: Update, context: CallbackContext) -> int:
    # Save preferred district
    district = update.message.text
    
    if district == 'All Districts':
        context.user_data['preferred_district'] = json.dumps(hk_districts)
    else:
        if 'preferred_districts' not in context.user_data:
            context.user_data['preferred_districts'] = []
            
        context.user_data['preferred_districts'].append(district)
        
    # Format conditions and districts for confirmation
    conditions = context.user_data.get('conditions', [])
    conditions_str = ", ".join(conditions) if conditions else "None"
    
    districts = context.user_data.get('preferred_districts', [])
    if district == 'All Districts':
        districts_str = "All Districts"
    else:
        districts_str = ", ".join(districts) if districts else "None"
    
    # Convert lists to JSON strings for database storage
    context.user_data['condition'] = json.dumps(conditions)
    context.user_data['preferred_district'] = json.dumps(districts) if district != 'All Districts' else json.dumps(hk_districts)
    
    update.message.reply_text(
        "Please confirm your registration details:\n\n"
        f"Telegram ID: {context.user_data.get('telegram_id')}\n"
        f"Username: {context.user_data.get('username')}\n"
        f"Conditions: {conditions_str}\n"
        f"Preferred Districts: {districts_str}\n\n"
        "Is this information correct?",
        reply_markup=ReplyKeyboardMarkup([['Yes', 'No']], one_time_keyboard=True)
    )
    
    return user_confirm

def register_confirm(update: Update, context: CallbackContext) -> int:
    # Complete registration and save to database
    confirmation = update.message.text.lower()
    
    if confirmation == 'no':
        update.message.reply_text(
            "Registration cancelled. You can start over by typing /register.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    # Get all data from context
    telegram_id = context.user_data.get('telegram_id')
    username = context.user_data.get('username')
    condition = context.user_data.get('condition')
    preferred_district = context.user_data.get('preferred_district')
    
    # Store in database
    try:
        conn = db_connect.get_connection()
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT ID FROM user WHERE telegram_id = %s", (str(telegram_id),))
        existing_user = cursor.fetchone()
        
        if not existing_user:
            # Insert new user
            cursor.execute(
                "INSERT INTO user (telegram_id, username, `condition`, preferred_district) "
                "VALUES (%s, %s, %s, %s)",
                (str(telegram_id), username, condition, preferred_district)
            )
        else:
            # Update existing user
            cursor.execute(
                "UPDATE user SET username = %s, `condition` = %s, preferred_district = %s "
                "WHERE telegram_id = %s",
                (username, condition, preferred_district, str(telegram_id))
            )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Provide options to continue
        update.message.reply_text(
            "Registration successful! What would you like to do next?",
            reply_markup=ReplyKeyboardMarkup([
                ['Register a Property'], 
                ['Search for Properties'],
                ['Ask a Question']
            ], one_time_keyboard=True)
        )
        
        # Remember user ID for future operations
        context.user_data['user_id'] = existing_user[0] if existing_user else cursor.lastrowid
        
        return prop_type_choice
        
    except Exception as e:
        logger.error(f"Database error: {e}")
        update.message.reply_text(
            "Sorry, there was an error saving your information. Please try again later.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

# Property Registration Flow
def property_type_choice(update: Update, context: CallbackContext) -> int:
    user_choice = update.message.text
    
    if user_choice == 'Ask a Question':
        update.message.reply_text(
            "What would you like to know about Hong Kong property?",
            reply_markup=ReplyKeyboardRemove()
        )
        return question_asked
    
    if user_choice == 'Search for Properties':
        # Implement property search functionality
        update.message.reply_text(
            "Property search feature coming soon!",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
        
    # Starting property registration
    update.message.reply_text(
        "Let's register your property. First, are you leasing or selling?",
        reply_markup=ReplyKeyboardMarkup([['Leasing', 'Selling']], one_time_keyboard=True)
    )
    
    return prop_district

def property_district(update: Update, context: CallbackContext) -> int:
    # Save property type (leasing or selling)
    prop_type = update.message.text
    
    if prop_type == 'Leasing':
        context.user_data['is_rent'] = 1
    else:  # Selling
        context.user_data['is_rent'] = 0
    
    # Create district buttons
    district_buttons = []
    for i in range(0, len(hk_districts), 2):
        row = [hk_districts[i]]
        if i+1 < len(hk_districts):
            row.append(hk_districts[i+1])
        district_buttons.append(row)
    
    update.message.reply_text(
        "In which district is your property located?",
        reply_markup=ReplyKeyboardMarkup(district_buttons, one_time_keyboard=True)
    )
    
    return prop_address

def property_address(update: Update, context: CallbackContext) -> int:
    # Save district
    district = update.message.text
    context.user_data['district'] = district
    
    update.message.reply_text(
        "Please enter the full address of your property:",
        reply_markup=ReplyKeyboardRemove()
    )
    
    return prop_condition

def property_condition(update: Update, context: CallbackContext) -> int:
    # Save address
    address = update.message.text
    context.user_data['address'] = address
    
    # Create buttons for property conditions
    condition_buttons = [[condition] for condition in property_conditions]
    condition_buttons.append(['Other'])
    condition_buttons.append(['Done'])
    
    update.message.reply_text(
        "What special conditions or features does your property have? (Select multiple)",
        reply_markup=ReplyKeyboardMarkup(condition_buttons, one_time_keyboard=False)
    )
    
    # Initialize empty property conditions list
    context.user_data['property_conditions'] = []
    
    return prop_price_min

def property_conditions_selection(update: Update, context: CallbackContext) -> int:
    # Add conditions one by one until user types "Done"
    user_input = update.message.text
    
    if user_input == 'Done':
        # Proceed to price when done selecting conditions
        is_rent = context.user_data.get('is_rent')
        price_text = "rental price" if is_rent else "selling price"
        
        update.message.reply_text(
            f"What is the minimum {price_text} you're asking? (in HKD)",
            reply_markup=ReplyKeyboardRemove()
        )
        return prop_price_min
    elif user_input == 'Other':
        update.message.reply_text(
            "Please type your custom condition:"
        )
        return prop_condition
    else:
        # Add this condition to the property conditions list
        if 'property_conditions' not in context.user_data:
            context.user_data['property_conditions'] = []
            
        context.user_data['property_conditions'].append(user_input)
        
        # Show current selections
        conditions_text = ", ".join(context.user_data['property_conditions'])
        
        # Add "Done" button to the keyboard
        condition_buttons = [[condition] for condition in property_conditions]
        condition_buttons.append(['Other'])
        condition_buttons.append(['Done'])
        
        update.message.reply_text(
            f"Added: {user_input}\nCurrent selections: {conditions_text}\n\n"
            "Select more or press 'Done' when finished:",
            reply_markup=ReplyKeyboardMarkup(condition_buttons, one_time_keyboard=False)
        )
        
        return prop_condition

def property_price_min(update: Update, context: CallbackContext) -> int:
    # If coming from condition selection, we need to convert conditions to JSON
    if 'property_conditions' in context.user_data:
        conditions = context.user_data.get('property_conditions', [])
        context.user_data['condition'] = json.dumps(conditions)
    
    # Save minimum price
    try:
        price_min = float(update.message.text)
        context.user_data['price_min'] = price_min
        
        is_rent = context.user_data.get('is_rent')
        price_text = "rental price" if is_rent else "selling price"
        
        update.message.reply_text(
            f"What is the maximum {price_text} you're asking? (in HKD)",
            reply_markup=ReplyKeyboardRemove()
        )
        
        return prop_price_max
    except ValueError:
        update.message.reply_text(
            "Please enter a valid number for the minimum price."
        )
        return prop_price_min

def property_price_max(update: Update, context: CallbackContext) -> int:
    # Save maximum price
    try:
        price_max = float(update.message.text)
        context.user_data['price_max'] = price_max
        
        is_rent = context.user_data.get('is_rent')
        
        if is_rent:
            # For rentals, ask about lease duration
            update.message.reply_text(
                "What is the lease duration? (e.g., 1 year, 2 years, etc.)",
                reply_markup=ReplyKeyboardMarkup([
                    ['6 months', '1 year'],
                    ['2 years', 'Flexible']
                ], one_time_keyboard=True)
            )
        else:
            # For sales, use a default value
            context.user_data['paid_duration'] = "N/A"
            return property_confirm(update, context)
        
        return prop_duration
    except ValueError:
        update.message.reply_text(
            "Please enter a valid number for the maximum price."
        )
        return prop_price_max

def property_duration(update: Update, context: CallbackContext) -> int:
    # Save lease duration
    duration = update.message.text
    context.user_data['paid_duration'] = duration
    
    return property_confirm(update, context)

def property_confirm(update: Update, context: CallbackContext) -> int:
    # Show property summary for confirmation
    is_rent = context.user_data.get('is_rent')
    property_type = "Rental" if is_rent else "Sale"
    district = context.user_data.get('district')
    address = context.user_data.get('address')
    
    # Get conditions
    if 'property_conditions' in context.user_data:
        conditions = context.user_data.get('property_conditions', [])
        conditions_str = ", ".join(conditions) if conditions else "None"
    else:
        conditions_str = "None"
    
    price_min = context.user_data.get('price_min')
    price_max = context.user_data.get('price_max')
    duration = context.user_data.get('paid_duration', "N/A")
    
    update.message.reply_text(
        "Please confirm your property details:\n\n"
        f"Property Type: {property_type}\n"
        f"District: {district}\n"
        f"Address: {address}\n"
        f"Conditions: {conditions_str}\n"
        f"Price Range: ${price_min:,.2f} - ${price_max:,.2f} HKD\n"
        f"Duration: {duration}\n\n"
        "Is this information correct?",
        reply_markup=ReplyKeyboardMarkup([['Yes', 'No']], one_time_keyboard=True)
    )
    
    return prop_confirm

def property_registration_confirm(update: Update, context: CallbackContext) -> int:
    # Complete property registration and save to database
    confirmation = update.message.text.lower()
    
    if confirmation == 'no':
        update.message.reply_text(
            "Property registration cancelled. You can start over or try again later.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    # Get user ID
    user_id = context.user_data.get('user_id')
    
    # Get all property data from context
    district = context.user_data.get('district')
    address = context.user_data.get('address')
    
    # Get conditions
    if 'property_conditions' in context.user_data:
        conditions = context.user_data.get('property_conditions', [])
        condition_json = json.dumps(conditions)
    else:
        condition_json = context.user_data.get('condition', '[]')
    
    is_rent = context.user_data.get('is_rent')
    price_min = context.user_data.get('price_min')
    price_max = context.user_data.get('price_max')
    paid_duration = context.user_data.get('paid_duration')
    
    try:
        # Store property in database
        conn = db_connect.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO property (user_id, district, address, `condition`, is_rent, price_min, price_max, paid_duration) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (user_id, district, address, condition_json, is_rent, price_min, price_max, paid_duration)
        )
        
        property_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        
        # Send to group assignment
        return assign_to_group(update, context)
        
    except Exception as e:
        logger.error(f"Database error during property registration: {e}")
        update.message.reply_text(
            "Sorry, there was an error saving your property information. Please try again later.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

def assign_to_group(update: Update, context: CallbackContext) -> int:
    # Assign user to relevant property groups based on their preferences and property
    district = context.user_data.get('district')
    is_rent = context.user_data.get('is_rent')
    
    # This would involve actual group assignments in Telegram
    # For now, we'll just simulate this with a message
    
    group_type = "Rental" if is_rent else "Sales"
    
    update.message.reply_text(
        f"Your property has been successfully registered!\n\n"
        f"Based on your information, you have been added to:\n"
        f"- {district} {group_type} Group\n\n"
        "You can now connect with potential buyers/tenants in these groups.",
        reply_markup=ReplyKeyboardMarkup([
            ['Register Another Property'],
            ['Search Properties'],
            ['Ask a Question']
        ], one_time_keyboard=True)
    )
    
    return prop_type_choice

# Existing functions
def start(update: Update, context: CallbackContext) -> int:
    user = update.effective_user
    
    # Check if user is already registered
    try:
        conn = db_connect.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT ID FROM user WHERE telegram_id = %s", (str(user.id),))
        existing_user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if existing_user:
            # User exists, store their ID
            context.user_data['user_id'] = existing_user[0]
            
            update.message.reply_text(
                f"Welcome back, {user.first_name}! What would you like to do?",
                reply_markup=ReplyKeyboardMarkup([
                    ['Register a Property'], 
                    ['Search for Properties'],
                    ['Update My Profile'],
                    ['Ask a Question']
                ], one_time_keyboard=True)
            )
            
            return prop_type_choice
        else:
            # New user, suggest registration
            update.message.reply_text(
                f"Hello {user.first_name}! Welcome to Hong Kong Property Assistant.\n\n"
                "To get started, please register your profile first.",
                reply_markup=ReplyKeyboardMarkup([['Register Now']], one_time_keyboard=True)
            )
            
            return user_telegram_id
    
    except Exception as e:
        logger.error(f"Database error during start: {e}")
        update.message.reply_text(
            f"Hello {user.first_name}! I'm your Hong Kong Property Assistant. "
            "How can I help you today?",
            reply_markup=ReplyKeyboardMarkup([
                ['Register'], 
                ['Ask a Question']
            ], one_time_keyboard=True)
        )
        
        return question_asked

def handle_question(update: Update, context: CallbackContext) -> int:
    user_text = update.message.text
    user = update.effective_user
    
    # Get ChatGPT response
    response = get_chatgpt_response(user_text, context="Hong Kong property law and real estate")
    
    update.message.reply_text(
        response,
        reply_markup=ReplyKeyboardMarkup([
            ['Register a Property'], 
            ['Search for Properties'],
            ['Ask Another Question']
        ], one_time_keyboard=True)
    )
    
    return question_asked

def get_chatgpt_response(query: str, context: Optional[str] = None) -> str:
    # Get a response from ChatGPT based on the user's query
    chatgpt_instance = ChatGPT()
    
    if context:
        query = f"Context: {context}\n\nUser question: {query}"
            
    return chatgpt_instance.get_response(query)

def help_command(update: Update, context: CallbackContext) -> None:
    help_text = (
        "I can help you with Hong Kong property transactions:\n\n"
        "Commands:\n"
        "/start - Begin using the bot\n"
        "/register - Register your profile\n"
        "/property - Register a property\n"
        "/search - Search for properties\n"
        "/help - Show this help message\n\n"
        "You can also ask me any questions about Hong Kong property!"
    )
    update.message.reply_text(help_text)

def error_handler(update: Update, context: CallbackContext) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    if update:
        update.message.reply_text("Sorry, something went wrong. Please try again.")

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
