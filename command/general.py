import os
import requests
import json
from datetime import datetime
import requests

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters, 
    CallbackContext, ConversationHandler, CallbackQueryHandler
)
from typing import Optional, Dict, List
from util.db_connect import get_connection as db
from util.constant import *
from util.logger import logger

class hkproperty_legalasst:
    def __init__(self):
        self.apiKey = os.getenv('CHATGPT_API_KEY')
        self.modelName = "gpt-4-o-mini"
        self.apiVersion = "2024-10-21"
        self.basicUrl = "https://genai.hkbu.edu.hk/general/rest"
        
    def get_response(self, message):
        # Incorporate the message from legal chatbot into the conversation
        conversation = [
            {'role': 'system', 'content': 'You are a chatbot in a chat group, familiar with Hong Kong Regulations and Property Laws.\n You act as a legal consultant to answer property buy/sell or lease questions professionally.\n You always answer questions based on Hong Kong Regulation only in legal context.\n To be accurate, include but not limited to Hong Kong Cap. 511 Estate Agents Ordinance and Cap. 219 Conveyancing and Property Ordinance.\n Introduce yourself as ‘Dr Law’ and always use happy emojis to answer the user in the first question but no need to use emoji again in the conversation.\n You must always answer correctly based on actual Hong Kong Regulations and best practices, if you are not absolutely sure, please state your educated answer as ‘suggestion’.\n As a consultant  to link up users with similar interests in buy/sell/lease in the same district, you must ask the user politely to enter district group by start the "/register" command after 3 questions you answered from user. \n The user that is interested to join the district group, ask them to use  "/register". \n If the user asks in Chinese, always answer in Traditional Chinese'},
            {'role': 'user', 'content': message},
        ]
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

        response = requests.get(f"http://localhost:5000/user/telegram?telegram_id={user.id}")
        result = json.loads(response.text)
        userID = result['ID']
        existing_user = response.status_code == 200
        
        if existing_user:
            # User exists, store their ID
            context.user_data['user_id'] = userID
            
            # Introduce Dr. Law
            intro_message = "Hello! I'm Dr. Law, your Hong Kong Property Legal Assistant! 😊 I can answer your questions about Hong Kong property laws and regulations. What would you like to know today?"
            update.message.reply_text(intro_message)

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

            intro_message = "Hello! I'm Dr. Law, your Hong Kong Property Legal Assistant! 😊 I can answer your questions about Hong Kong property laws and regulations. What would you like to know today?"
            update.message.reply_text(intro_message)

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
    user_id = user.id
    
    try:
        # Get current time for timestamping questions
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Connect to database
        conn = db()
        cursor = conn.cursor()
        
        # Check if user exists in database
        cursor.execute("SELECT ID, question_count, question_history FROM user WHERE telegram_id = %s", (str(user_id),))
        user_record = cursor.fetchone()
        
        if user_record:
            # User exists, get their current question count and history
            db_user_id = user_record[0]
            question_count = user_record[1] if user_record[1] is not None else 0
            
            # Parse existing question history or create new array
            if user_record[2]:
                try:
                    question_history = json.loads(user_record[2])
                except json.JSONDecodeError:
                    question_history = []
            else:
                question_history = []
            
            # Store user ID in context
            context.user_data['user_id'] = db_user_id
        else:
            # User doesn't exist - they should register first, but we'll track anyway
            question_count = 0
            question_history = []
            
            # Create minimal user record with their first question
            cursor.execute(
                "INSERT INTO user (telegram_id, question_count, question_history) VALUES (%s, %s, %s)",
                (user_id, 1, json.dumps([{"question": user_text, "timestamp": current_time}]))
            )
            db_user_id = cursor.lastrowid
            context.user_data['user_id'] = db_user_id
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Get response and return since we've already incremented in DB
            response = get_chatgpt_response(user_text)
            update.message.reply_text(
                response,
                reply_markup=ReplyKeyboardMarkup([
                    ['Register Now'], 
                    ['Ask Another Question']
                ], one_time_keyboard=True)
            )
            return question_asked
        
        # Add current question to history
        question_history.append({
            "question": user_text,
            "timestamp": current_time
        })
        
        # Increment question count
        question_count += 1
        
        # Update the database with new count and history
        cursor.execute(
            "UPDATE user SET question_count = %s, question_history = %s WHERE ID = %s",
            (question_count, json.dumps(question_history), db_user_id)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Get response from legal assistant
        response = get_chatgpt_response(user_text)
        
        # Check if we've reached 3 questions for unregistered users
        # (assuming isActive = 0 or NULL means not fully registered)
        if question_count >= 3:
            # Check if user is fully registered
            conn = db()
            cursor = conn.cursor()
            cursor.execute("SELECT isActive FROM user WHERE ID = %s", (db_user_id,))
            user_status = cursor.fetchone()
            cursor.close()
            conn.close()
            
            # If user is not active/registered, prompt them to register
            if not user_status or user_status[0] != 1:
                # Prompt for registration after 3rd question
                update.message.reply_text(
                    response + "\n\nI've noticed you're interested in Hong Kong property matters! To get personalized property recommendations and join district-specific groups, please register your profile.",
                    reply_markup=ReplyKeyboardMarkup([
                        ['Register Now'],
                        ['Ask Another Question']
                    ], one_time_keyboard=True)
                )
                
                # We don't reset the counter here - we'll only reset it when they actually register
                return user_telegram_id
            else:
                # User is registered but still prompt them occasionally
                update.message.reply_text(
                    response,
                    reply_markup=ReplyKeyboardMarkup([
                        ['Register a Property'], 
                        ['Search for Properties'],
                        ['Ask Another Question']
                    ], one_time_keyboard=True)
                )
        else:
            # Normal response for questions 1-2
            update.message.reply_text(
                response,
                reply_markup=ReplyKeyboardMarkup([
                    ['Register Now'], 
                    ['Ask Another Question']
                ], one_time_keyboard=True)
            )
        
        return question_asked
        
    except Exception as e:
        logger.error(f"Error in handle_question: {e}")
        # Fallback in case of database error
        response = get_chatgpt_response(user_text)
        update.message.reply_text(
            response,
            reply_markup=ReplyKeyboardMarkup([
                ['Register Now'], 
                ['Ask Another Question']
            ], one_time_keyboard=True)
        )
        return question_asked

def get_chatgpt_response(query: str, context: Optional[str] = None) -> str:
    # Get a response from ChatGPT based on the user's query
    legal_assistant = hkproperty_legalasst()
            
    return legal_assistant.get_response(query)

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
