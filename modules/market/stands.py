"""
Telegram RPG Bot - Stands Module
===============================
Handles the /stands command for browsing all stands.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db, UserRepository
from utils.helpers import format_money
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class StandsHandler:
    """Handles stands command for browsing all stands."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /stands command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        # Get all market items
        items = list(db.market.find().limit(20))
        
        text = "🏪 *Market Stands*\n\n"
        
        if items:
            for item in items[:10]:
                seller = await UserRepository.get_user(item.get("seller_id"))
                seller_name = seller['name'] if seller else "Unknown"
                
                text += (
                    f"📦 {item.get('item_name', 'Unknown')}\n"
                    f"   Seller: {seller_name}\n"
                    f"   Price: {format_money(item.get('price', 0))}\n\n"
                )
        else:
            text += "No items for sale right now.\n\n"
            text += "Be the first to list something!"
        
        keyboard = [
            [
                InlineKeyboardButton("➕ List Item", callback_data="stand_list"),
                InlineKeyboardButton("🏪 My Stand", callback_data="stand_view")
            ],
            [
                InlineKeyboardButton("🔄 Refresh", callback_data="stands_refresh")
            ]
        ]
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
