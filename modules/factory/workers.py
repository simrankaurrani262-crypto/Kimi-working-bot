"""
Telegram RPG Bot - Workers Module
================================
Handles the /workers command for viewing workers.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class WorkersHandler:
    """Handles workers command for viewing workers."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /workers command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        
        # Check if user has a factory
        factory = db.factory.find_one({"user_id": user_id})
        if not factory:
            await update.message.reply_text(
                "❌ You don't own a factory! Use `/factory` to buy one."
            )
            return
        
        workers = factory.get("workers", 0)
        max_workers = 10
        
        text = (
            f"👷 *Your Workers*\n\n"
            f"Current workers: {workers}/{max_workers}\n"
            f"Production bonus: +{workers * 50}/hour\n\n"
        )
        
        if workers > 0:
            text += f"Your workers are working hard to produce goods! 💪\n"
        else:
            text += "You don't have any workers. Hire some with `/hire <amount>`!\n"
        
        keyboard = [
            [
                InlineKeyboardButton("➕ Hire", callback_data="factory_hire"),
                InlineKeyboardButton("➖ Fire", callback_data="factory_fire")
            ],
            [
                InlineKeyboardButton("🏭 Factory", callback_data="factory_view")
            ]
        ]
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
