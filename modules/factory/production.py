"""
Telegram RPG Bot - Production Module
===================================
Handles the /production command for viewing production.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db
from utils.helpers import format_money
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class ProductionHandler:
    """Handles production command for viewing production."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /production command."""
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
        
        level = factory.get("level", 1)
        workers = factory.get("workers", 0)
        production = factory.get("production", 100)
        total_produced = factory.get("total_produced", 0)
        
        # Calculate hourly and daily production
        hourly = production
        daily = hourly * 24
        
        text = (
            f"📊 *Factory Production*\n\n"
            f"Factory Level: {level}\n"
            f"Workers: {workers}\n\n"
            f"*Production Rate:*\n"
            f"  Per hour: {format_money(hourly)}\n"
            f"  Per day: {format_money(daily)}\n\n"
            f"*Total Produced:* {format_money(total_produced)}\n"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("⬆️ Upgrade", callback_data="factory_upgrade"),
                InlineKeyboardButton("👷 Workers", callback_data="factory_workers")
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
