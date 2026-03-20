"""
Telegram RPG Bot - Buy Module
============================
Handles the /buy command for buying items.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from database import db, UserRepository, LogRepository
from utils.helpers import format_money
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class BuyHandler:
    """Handles buy command for buying items."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /buy command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        user = await UserRepository.get_user(user_id)
        
        # Check arguments
        if not context.args:
            await update.message.reply_text(
                "🛒 *Buy Item*\n\n"
                "Usage: `/buy <item_key>`\n\n"
                "Use `/shop` to see available items!",
                parse_mode='Markdown'
            )
            return
        
        item_key = context.args[0].lower()
        
        # Get item from shop
        from modules.economy.shop import ShopHandler
        item = ShopHandler.ITEMS.get(item_key)
        
        if not item:
            await update.message.reply_text(
                f"❌ Item not found! Use `/shop` to see available items."
            )
            return
        
        # Check if already owns item
        inventory = db.inventory.find_one({"user_id": user_id, "item_key": item_key})
        if inventory:
            await update.message.reply_text(
                f"❌ You already own {item['name']}!"
            )
            return
        
        # Check has enough money
        if user["money"] < item["price"]:
            await update.message.reply_text(
                f"❌ Insufficient funds!\n"
                f"Price: {format_money(item['price'])}\n"
                f"Your balance: {format_money(user['money'])}"
            )
            return
        
        # Deduct money and add to inventory
        await UserRepository.remove_money(user_id, item["price"])
        
        db.inventory.insert_one({
            "user_id": user_id,
            "item_key": item_key,
            "item_name": item["name"],
            "category": item["category"],
            "purchased_at": db.get_timestamp()
        })
        
        # Update economy stats
        db.economy.update_one(
            {"user_id": user_id},
            {"$inc": {"total_spent": item["price"]}},
            upsert=True
        )
        
        # Log the purchase
        await LogRepository.log_action(
            user_id, "item_bought", {"item": item_key, "price": item["price"]}
        )
        
        await update.message.reply_text(
            f"🛒 *Purchase Successful!*\n\n"
            f"You bought {item['name']}!\n"
            f"Price: {format_money(item['price'])}\n\n"
            f"New balance: {format_money(user['money'] - item['price'])}\n\n"
            f"Use `/inventory` to view your items!",
            parse_mode='Markdown'
        )
