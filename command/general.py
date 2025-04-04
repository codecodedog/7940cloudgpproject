import os
import requests
import json

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters, 
    CallbackContext, ConversationHandler, CallbackQueryHandler
)
from typing import Optional, Dict, List
from util.db_connect import get_connection as db
from util.constant import *
from util.logger import logger

class ChatGPT:
    def __init__(self):
        self.apiKey = os.getenv('CHATGPT_API_KEY')
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
        conn = db()
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
