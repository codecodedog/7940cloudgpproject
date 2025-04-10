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
from util.constant import *
from util.logger import logger

class hkproperty_legalasst:
    def __init__(self):
        self.apiKey = os.getenv("CHATGPT_API_KEY")
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
    
    group_type = "Rental" if is_rent else "Sales"
    
    update.message.reply_text(
        f"Your property has been successfully registered!\n\n"
        f"Based on your information, you have been added to:\n"
        f"- {district} {group_type} Group\n\n"
        "You can now connect with potential buyers/tenants in these groups.",
        reply_markup=ReplyKeyboardMarkup([
            ['Register Another Property'],
            ['Search for Properties'],
            ['Ask a Question']
        ], one_time_keyboard=True)
    )
    
    return prop_type_choice

def start(update: Update, context: CallbackContext) -> int:
    # /start function
    user = update.effective_user

    try:
        response = requests.get(f"http://2331899e50f63eff82201bcdfdb02ed6-722521655.ap-southeast-1.elb.amazonaws.com/user/telegram?telegram_id={user.id}")
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
    # Handle user questions and provide responses
    user_text = update.message.text
    user = update.effective_user
    user_id = user.id
    
    try:
        # Get current time for timestamping questions
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Check if user exists in Database
        response = requests.get(f"http://2331899e50f63eff82201bcdfdb02ed6-722521655.ap-southeast-1.elb.amazonaws.com/user/telegram?telegram_id={str(user_id)}")
        
        # Check if request was successful (status code 200)
        if response.status_code == 200:

            user_record = json.loads(response.text)
            existing_user = True
            
            # User exists, get their current question count and history
            db_user_id = user_record['ID']
            question_count = user_record['question_count'] if user_record['question_count'] is not None else 0
            
            # Parse existing question history or create new array
            if user_record['question_history']:
                try:
                    question_history = json.loads(user_record['question_history'])
                except json.JSONDecodeError:
                    question_history = []
            else:
                question_history = []
            

            context.user_data['user_id'] = db_user_id
        else:
            # User does not exist, create a new record
            existing_user = False
            question_count = 0
            question_history = []
            
            # Create minimal user record with their first question
            obj = json.dumps({
                "telegram_id": user_id,
                "question_count": 1,
                "question_history": json.dumps([{"question": user_text, "timestamp": current_time}])
            })
            response = requests.post("http://2331899e50f63eff82201bcdfdb02ed6-722521655.ap-southeast-1.elb.amazonaws.com/user/question", data=obj, headers={
                'Content-Type': 'application/json'
            })

            if response.status_code != 200:
                raise Exception(f"Database Error: {response.status_code} - {response.text}")
            
            # Parse the response text first, then access properties
            response_json = json.loads(response.text)
            result = response_json['result']
            db_user_id = result['lastrowid'] if 'lastrowid' in result else None
            context.user_data['user_id'] = db_user_id
            
            # Get response and return since we've already incremented in DB
            response_str = get_chatgpt_response(user_text)
            update.message.reply_text(
                response_str,
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
        obj = json.dumps({
            "ID": db_user_id,
            "question_count": question_count,
            "question_history": json.dumps(question_history),
        })
        response = requests.put("http://2331899e50f63eff82201bcdfdb02ed6-722521655.ap-southeast-1.elb.amazonaws.com/user/question", data=obj, headers={
            'Content-Type': 'application/json'
        })

        if response.status_code != 200:
            raise Exception(f"Database Error: {response.status_code} - {response.text}")

        # Get response from legal assistant
        response_str = get_chatgpt_response(user_text)
        
        # Check if we've reached 3 questions for unregistered users
        # Assume isActive = 0 or NULL means not fully registered
        if question_count >= 3:
            # Check if user is fully registered
            response = requests.get(f"http://2331899e50f63eff82201bcdfdb02ed6-722521655.ap-southeast-1.elb.amazonaws.com/user/telegram?telegram_id={str(user_id)}")
            
            if response.status_code == 200:
                user_record = json.loads(response.text)
                # If user is not active/registered, prompt them to register
                if user_record['isActive'] != 1:
                    # Prompt for registration after 3rd question
                    update.message.reply_text(
                        response_str + "\n\nI've noticed you're interested in Hong Kong property matters! To get personalized property recommendations and join district-specific groups, please register your profile.",
                        reply_markup=ReplyKeyboardMarkup([
                            ['Register Now'],
                            ['Ask Another Question']
                        ], one_time_keyboard=True)
                    )
                    return user_telegram_id
                else:
                    # User is registered but still prompt them occasionally
                    update.message.reply_text(response_str)
            else:
                # User doesn't exist in the database anymore or error
                update.message.reply_text(
                    response_str + "\n\nI've noticed you're interested in Hong Kong property matters! To get personalized property recommendations and join district-specific groups, please register your profile.",
                    reply_markup=ReplyKeyboardMarkup([
                        ['Register Now'],
                        ['Ask Another Question']
                    ], one_time_keyboard=True)
                )
                return user_telegram_id
        else:
            # Normal response for questions 1-2
            update.message.reply_text(response_str)
        
        return question_asked
        
    except Exception as e:
        logger.error(f"Error in handle_question: {e}")
        # Fallback in case of database error
        update.message.reply_text(response)
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
