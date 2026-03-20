"""
Telegram RPG Bot - Nation Module
===============================
Handles the /nation command for nation guessing game.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class NationHandler:
    """Handles nation command for nation guessing game."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /nation command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        await update.message.reply_text(
            "🌍 *Nation Guessing*\n\n"
            "Coming soon!\n\n"
            "Try other games:\n"
            "• `/dice <bet>` - Dice game\n"
            "• `/slots <bet>` - Slot machine\n"
            "• `/guess <bet> <number>` - Number guessing\n"
            "• `/blackjack <bet>` - Blackjack\n"
            "• `/trivia` - Trivia quiz"
        )
