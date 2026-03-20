"""
Telegram RPG Bot - Seeds Module
==============================
Handles the /seeds command for viewing seeds.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db
from utils.helpers import format_money
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class SeedsHandler:
    """Handles seeds command for viewing seeds."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /seeds command."""
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
        
        seeds = garden.get("seeds", {})
        
        text = "🌱 *Your Seeds*\n\n"
        
        from modules.garden.plant import PlantHandler
        
        if seeds:
            for seed_key, amount in seeds.items():
                crop = PlantHandler.CROPS.get(seed_key, {})
                text += f"{crop.get('name', seed_key)}: {amount}\n"
        else:
            text += "You don't have any seeds.\n\n"
        
        text += "\n*Available Seeds:*\n"
        for key, crop in PlantHandler.CROPS.items():
            owned = seeds.get(key, 0)
            text += f"{crop['name']} - {format_money(crop['cost'])} (You have: {owned})\n"
        
        keyboard = [
            [
                InlineKeyboardButton("🌱 Plant", callback_data="garden_plant"),
                InlineKeyboardButton("🛒 Buy Seeds", callback_data="seeds_buy")
            ],
            [
                InlineKeyboardButton("🌱 Garden", callback_data="garden_view")
            ]
        ]
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
