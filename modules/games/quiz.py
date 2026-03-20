"""
Telegram RPG Bot - Quiz Module
=============================
Handles the /quiz command for quiz game.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class QuizHandler:
    """Handles quiz command for quiz game."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /quiz command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        await update.message.reply_text(
            "❓ *Quiz Game*\n\n"
            "Use `/trivia` for trivia questions!\n\n"
            "Try other games:\n"
            "• `/dice <bet>` - Dice game\n"
            "• `/slots <bet>` - Slot machine\n"
            "• `/guess <bet> <number>` - Number guessing\n"
            "• `/blackjack <bet>` - Blackjack\n"
            "• `/lottery buy` - Lottery"
        )
