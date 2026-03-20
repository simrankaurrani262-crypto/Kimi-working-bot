"""
Telegram RPG Bot - Trade Module
==============================
Handles the /trade command for trading with other users.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from database import db, UserRepository, LogRepository
from utils.helpers import format_money
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class TradeHandler:
    """Handles trade command for trading with other users."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /trade command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        await update.message.reply_text(
            "🔄 *Trade*\n\n"
            "Trading feature coming soon!\n\n"
            "For now, use `/putstand` to sell items or `/gift` to give items to friends!"
        )
