"""
Telegram RPG Bot - Stand Module
==============================
Handles the /stand command for viewing your market stand.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db
from utils.helpers import format_money
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class StandHandler:
    """Handles stand command for viewing your market stand."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /stand command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        
        # Get user's stand items
        items = list(db.market.find({"seller_id": user_id}))
        
        text = "🏪 *Your Market Stand*\n\n"
        
        if items:
            text += "*Your Items for Sale:*\n\n"
            for item in items:
                text += (
                    f"📦 {item.get('item_name', 'Unknown')}\n"
                    f"   Price: {format_money(item.get('price', 0))}\n"
                    f"   Listed: {item.get('listed_at', 'Unknown')}\n\n"
                )
        else:
            text += "Your stand is empty.\n\n"
            text += "Use `/putstand <item> <price>` to list items!"
        
        keyboard = [
            [
                InlineKeyboardButton("➕ List Item", callback_data="stand_list"),
                InlineKeyboardButton("🗑️ Remove Item", callback_data="stand_remove")
            ],
            [
                InlineKeyboardButton("🏪 Browse Stands", callback_data="stands_browse"),
                InlineKeyboardButton("🎁 Gift", callback_data="gift_view")
            ]
        ]
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
