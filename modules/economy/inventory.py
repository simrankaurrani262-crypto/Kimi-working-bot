"""
Telegram RPG Bot - Inventory Module
==================================
Handles the /inventory command for viewing inventory.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class InventoryHandler:
    """Handles inventory command for viewing inventory."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /inventory command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        
        # Get inventory items
        items = list(db.inventory.find({"user_id": user_id}))
        
        if not items:
            await update.message.reply_text(
                "🎒 *Your Inventory*\n\n"
                "Your inventory is empty!\n\n"
                "Use `/shop` to buy items!",
                parse_mode='Markdown'
            )
            return
        
        # Group items by category
        categories = {}
        for item in items:
            cat = item.get("category", "other")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(item)
        
        text = f"🎒 *Your Inventory* ({len(items)} items)\n\n"
        
        category_emojis = {
            "tools": "🛠️",
            "consumables": "🍎",
            "accessories": "💎",
            "pets": "🐾",
            "other": "📦"
        }
        
        for cat, cat_items in categories.items():
            emoji = category_emojis.get(cat, "📦")
            text += f"{emoji} *{cat.title()}*\n"
            for item in cat_items:
                text += f"  • {item['item_name']}\n"
            text += "\n"
        
        keyboard = [
            [
                InlineKeyboardButton("🏪 Shop", callback_data="shop_view"),
                InlineKeyboardButton("💰 Sell Item", callback_data="inventory_sell")
            ],
            [
                InlineKeyboardButton("⬅️ Back", callback_data="profile_view")
            ]
        ]
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
