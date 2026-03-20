"""
Telegram RPG Bot - PutStand Module
=================================
Handles the /putstand command for listing items.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from database import db, UserRepository, LogRepository
from utils.helpers import format_money
from utils.validators import UserValidator, validate_amount

logger = logging.getLogger(__name__)


class PutStandHandler:
    """Handles putstand command for listing items."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /putstand command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        
        # Check arguments
        if len(context.args) < 2:
            await update.message.reply_text(
                "🏪 *List Item for Sale*\n\n"
                "Usage: `/putstand <item_key> <price>`\n\n"
                "Use `/inventory` to see your items!"
            )
            return
        
        item_key = context.args[0].lower()
        
        # Parse price
        price, error = validate_amount(context.args[1], min_amount=1)
        if error:
            await update.message.reply_text(f"❌ {error}")
            return
        
        # Check if user owns the item
        inventory_item = db.inventory.find_one({"user_id": user_id, "item_key": item_key})
        if not inventory_item:
            await update.message.reply_text(
                "❌ You don't own this item! Use `/inventory` to see your items."
            )
            return
        
        # Check if already listed
        existing = db.market.find_one({"seller_id": user_id, "item_key": item_key})
        if existing:
            await update.message.reply_text("❌ This item is already listed!")
            return
        
        # List item
        db.market.insert_one({
            "seller_id": user_id,
            "item_key": item_key,
            "item_name": inventory_item["item_name"],
            "price": price,
            "listed_at": db.get_timestamp()
        })
        
        await LogRepository.log_action(
            user_id, "item_listed", {"item": item_key, "price": price}
        )
        
        await update.message.reply_text(
            f"🏪 *Item Listed!*\n\n"
            f"Item: {inventory_item['item_name']}\n"
            f"Price: {format_money(price)}\n\n"
            f"Use `/stand` to view your stand!"
        )
