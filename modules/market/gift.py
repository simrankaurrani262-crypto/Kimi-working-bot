"""
Telegram RPG Bot - Gift Module
=============================
Handles the /gift command for gifting items.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from database import db, UserRepository, LogRepository
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class GiftHandler:
    """Handles gift command for gifting items."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /gift command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        
        # Check arguments
        if len(context.args) < 2:
            await update.message.reply_text(
                "🎁 *Gift Item*\n\n"
                "Usage: `/gift <user_id> <item_key>`\n\n"
                "Use `/inventory` to see your items!"
            )
            return
        
        try:
            target_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!")
            return
        
        item_key = context.args[1].lower()
        
        # Check not gifting self
        if user_id == target_id:
            await update.message.reply_text("❌ You can't gift yourself!")
            return
        
        # Check target exists
        target = await UserRepository.get_user(target_id)
        if not target:
            await update.message.reply_text("❌ User not found!")
            return
        
        # Check if user owns the item
        inventory_item = db.inventory.find_one({"user_id": user_id, "item_key": item_key})
        if not inventory_item:
            await update.message.reply_text(
                "❌ You don't own this item! Use `/inventory` to see your items."
            )
            return
        
        # Transfer item
        db.inventory.delete_one({"user_id": user_id, "item_key": item_key})
        db.inventory.insert_one({
            "user_id": target_id,
            "item_key": item_key,
            "item_name": inventory_item["item_name"],
            "category": inventory_item["category"],
            "received_at": db.get_timestamp()
        })
        
        await LogRepository.log_action(
            user_id, "item_gifted", {"item": item_key, "recipient": target_id}
        )
        
        await update.message.reply_text(
            f"🎁 *Gift Sent!*\n\n"
            f"You gifted {inventory_item['item_name']} to {target['name']}!"
        )
        
        # Notify recipient
        try:
            user = await UserRepository.get_user(user_id)
            await context.bot.send_message(
                chat_id=target_id,
                text=(
                    f"🎁 *Gift Received!*\n\n"
                    f"{user['name']} gifted you {inventory_item['item_name']}!"
                )
            )
        except Exception as e:
            logger.error(f"Error notifying recipient: {e}")
