import os
import requests
import json

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters, 
    CallbackContext, ConversationHandler, CallbackQueryHandler
)
from util.db_connect import get_connection as db
from util.constant import *
from util.logger import logger
from command.general import assign_to_group

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
            "What are you looking for?",
            reply_markup=ReplyKeyboardMarkup([['Base on my profile']], one_time_keyboard=True)
        )
        return prop_search
        
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
    
    return prop_condition_selection

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
        return prop_condition_selection
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
        
        return prop_condition_selection

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
        conn = db()
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

# Implement property search functionality
def property_search(update: Update, context: CallbackContext) -> int:
    try:
        user_telegramId = context._user_id_and_data[0]
        user_district = ''
        user_factor = []
        properties_preferences = []

        conn = db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM user where telegram_id = " + str(user_telegramId))
        user = cursor.fetchone()
        user_id = user[0]
        user_factor = json.loads(user[3])
        user_district = json.loads(user[4])

        cursor.execute("SELECT * FROM property INNER JOIN user ON property.user_id = user.ID WHERE property.user_id <>" + str(user_id))
        propertyList = cursor.fetchall()
        
        conn.commit()
        cursor.close()
        conn.close()

        for row in propertyList:
            
            properties_preferences.append({
                "district": row[2],
                "factor": json.loads(row[4]),
                "owner": {
                    "telegram_id": row[10],
                    "username": row[11],
                },
                "is_rent":  "Rent" if row[5] else "Leasing", 
                "address": row[3],
                "price_range": f"{row[6]} - {row[7]}",
                "paid_duration": row[8]
            })
        
        print(properties_preferences)

        result = []

        for property in properties_preferences:
            if(any(item in property["factor"] for item in user_factor) and property["district"] in user_district):
                result.append(property)
        
        if len(result) == 0:
            update.message.reply_text(
                "Sorry, there are no property that are suitable at the moment"
            )
        else:
            reply_str = "There are several property that you may feel interested:\n\n"
            for filterProperty in result:
                reply_str += (f"{filterProperty['address']} \n"
                + f"District: {filterProperty['district']}\n"
                + f"Conditions: {filterProperty['factor']}\n"
                + f"Owner: @{filterProperty['owner']['username']}\n"
                + f"Price Range: {filterProperty['price_range']}\n"
                + f"Paid Duration: {filterProperty['paid_duration']}\n"
                + "\n\n")

            update.message.reply_text(
                reply_str
            )
      

        return question_asked

    except Exception as e:
        update.message.reply_text(
            "Sorry, there was an error. Please try again later.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    