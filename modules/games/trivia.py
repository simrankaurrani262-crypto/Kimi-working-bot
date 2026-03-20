"""
Telegram RPG Bot - Trivia Module
===============================
Handles the /trivia command for trivia game.
"""

import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db, UserRepository, LogRepository
from utils.helpers import format_money
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class TriviaHandler:
    """Handles trivia command for trivia game."""
    
    QUESTIONS = [
        {
            "question": "What is the capital of France?",
            "options": ["London", "Berlin", "Paris", "Madrid"],
            "answer": 2  # Paris
        },
        {
            "question": "What is 2 + 2?",
            "options": ["3", "4", "5", "6"],
            "answer": 1  # 4
        },
        {
            "question": "What planet is known as the Red Planet?",
            "options": ["Venus", "Mars", "Jupiter", "Saturn"],
            "answer": 1  # Mars
        },
        {
            "question": "Who painted the Mona Lisa?",
            "options": ["Van Gogh", "Picasso", "Da Vinci", "Michelangelo"],
            "answer": 2  # Da Vinci
        },
        {
            "question": "What is the largest ocean?",
            "options": ["Atlantic", "Indian", "Arctic", "Pacific"],
            "answer": 3  # Pacific
        },
    ]
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /trivia command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        # Select random question
        question = random.choice(TriviaHandler.QUESTIONS)
        
        text = f"❓ *Trivia Question*\n\n{question['question']}\n\n"
        
        keyboard = []
        for i, option in enumerate(question['options']):
            keyboard.append([
                InlineKeyboardButton(
                    option,
                    callback_data=f"trivia_answer_{i}_{question['answer']}"
                )
            ])
        
        # Store question in user data
        context.user_data['trivia_question'] = question
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    @staticmethod
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle trivia callbacks."""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data.startswith("trivia_answer_"):
            parts = data.split("_")
            selected = int(parts[2])
            correct = int(parts[3])
            
            if selected == correct:
                winnings = 100
                await UserRepository.add_money(query.from_user.id, winnings)
                
                await LogRepository.log_action(
                    query.from_user.id, "game_played", {"game": "trivia", "result": "win"}
                )
                
                await query.edit_message_text(
                    f"✅ *Correct!*\n\n"
                    f"🎉 You win {format_money(winnings)}!"
                )
            else:
                await LogRepository.log_action(
                    query.from_user.id, "game_played", {"game": "trivia", "result": "loss"}
                )
                
                await query.edit_message_text(
                    f"❌ *Wrong!*\n\n"
                    f"Better luck next time!"
                )
