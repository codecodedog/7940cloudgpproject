import os
import requests
import json

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters, 
    CallbackContext, ConversationHandler, CallbackQueryHandler
)
from util.constant import *
from util.logger import logger

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
    
    if 'preferred_districts' not in context.user_data:
        context.user_data['preferred_districts'] = []
            
    context.user_data['preferred_districts'].append(district)
        
    # Format conditions and districts for confirmation
    conditions = context.user_data.get('conditions', [])
    conditions_str = ", ".join(conditions) if conditions else "None"
    
    districts = context.user_data.get('preferred_districts', [])
    districts_str = ", ".join(districts) if districts else "None"
    
    # Convert lists to JSON strings for database storage
    context.user_data['condition'] = json.dumps(conditions)
    context.user_data['preferred_district'] = json.dumps(districts)
    
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
        
        # Check if user exists
        response = requests.get(f"http://2331899e50f63eff82201bcdfdb02ed6-722521655.ap-southeast-1.elb.amazonaws.com/user/telegram?telegram_id={str(telegram_id)}")
        result = json.loads(response.text)
        userID = result['ID']
        existing_user = response.status_code == 200
        
        if not existing_user:
            # Insert new user
            obj = json.dumps({
                "telegram_id": telegram_id,
                "username": username,
                "condition": condition,
                "preferred_district": preferred_district,
                "isActive": 1,
                "question_count": 0,
                "question_history": None
            })
            response = requests.post("http://2331899e50f63eff82201bcdfdb02ed6-722521655.ap-southeast-1.elb.amazonaws.com/user", data=obj, headers={
                'Content-Type': 'application/json'
            })

            if response.status_code != 200 :
                raise Exception("Database Error")
        
        else:
            # Update existing user
            obj = json.dumps({
                "telegram_id": telegram_id,
                "username": username,
                "condition": condition,
                "preferred_district": preferred_district,
                "isActive": 1,
                "question_count": 0,
                "question_history": None
            })
            response = requests.put("http://2331899e50f63eff82201bcdfdb02ed6-722521655.ap-southeast-1.elb.amazonaws.com/user", data=obj, headers={
                'Content-Type': 'application/json'
            })

            if response.status_code != 200 :
                raise Exception("Database Error")
        
        
        # Provide options to continue
        reply_str = (
            "Registration successful! \n"
            f"Please join the following group for your preferred district discussion! \n\n"
        )
        for district in json.loads(preferred_district):
            reply_str += f"{district}: {group_invite_link[district]}"
            
        update.message.reply_text(
            reply_str, 
            reply_markup=ReplyKeyboardMarkup([
                ['Register a Property'], 
                ['Search for Properties'],
                ['Ask a Question']
            ], one_time_keyboard=True)
        )
        
        return prop_type_choice
        
    except Exception as e:
        logger.error(f"Error: {e}")
        update.message.reply_text(
            "Sorry, there was an error saving your information. Please try again later.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    