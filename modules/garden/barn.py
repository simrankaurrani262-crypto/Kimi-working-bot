"""
Telegram RPG Bot - Barn Module
=============================
Handles the /barn command for viewing barn contents.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db
from utils.helpers import format_money
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class BarnHandler:
    """Handles barn command for viewing barn contents."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /barn command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        
        # Check if user has a garden
        garden = db.gardens.find_one({"user_id": user_id})
        if not garden:
            await update.message.reply_text(
                "❌ You don't have a garden! Use `/garden` to buy one."
            )
            return
        
        barn = garden.get("barn", {})
        
        text = "🚜 *Your Barn*\n\n"
        
        if barn:
            text += "*Stored Crops:*\n"
            for crop, amount in barn.items():
                text += f"  {crop}: {amount}\n"
        else:
            text += "Your barn is empty.\n\n"
            text += "Harvest crops to store them here!"
        
        keyboard = [
            [
                InlineKeyboardButton("🌾 Harvest", callback_data="garden_harvest"),
                InlineKeyboardButton("🌱 Plant", callback_data="garden_plant")
            ],
            [
                InlineKeyboardButton("🏪 Sell", callback_data="barn_sell"),
                InlineKeyboardButton("🌱 Garden", callback_data="garden_view")
            ]
        ]
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
