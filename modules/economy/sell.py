"""
Telegram RPG Bot - Sell Module
=============================
Handles the /sell command for selling items.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from database import db, UserRepository, LogRepository
from utils.helpers import format_money
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class SellHandler:
    """Handles sell command for selling items."""
    
    SELL_RATE = 0.5  # Sell for 50% of original price
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /sell command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        
        # Check arguments
        if not context.args:
            await update.message.reply_text(
                "💰 *Sell Item*\n\n"
                f"Sell rate: {SellHandler.SELL_RATE * 100}% of original price\n\n"
                "Usage: `/sell <item_key>`\n\n"
                "Use `/inventory` to see your items!",
                parse_mode='Markdown'
            )
            return
        
        item_key = context.args[0].lower()
        
        # Check if user owns item
        inventory_item = db.inventory.find_one({"user_id": user_id, "item_key": item_key})
        if not inventory_item:
            await update.message.reply_text(
                f"❌ You don't own this item! Use `/inventory` to see your items."
            )
            return
        
        # Get original price
        from modules.economy.shop import ShopHandler
        shop_item = ShopHandler.ITEMS.get(item_key)
        
        if not shop_item:
            await update.message.reply_text("❌ This item cannot be sold!")
            return
        
        sell_price = int(shop_item["price"] * SellHandler.SELL_RATE)
        
        # Remove from inventory and add money
        db.inventory.delete_one({"user_id": user_id, "item_key": item_key})
        await UserRepository.add_money(user_id, sell_price)
        
        # Log the sale
        await LogRepository.log_action(
            user_id, "item_sold", {"item": item_key, "price": sell_price}
        )
        
        await update.message.reply_text(
            f"💰 *Item Sold!*\n\n"
            f"You sold {shop_item['name']}!\n"
            f"Sell price: {format_money(sell_price)}\n\n"
            f"Use `/shop` to buy more items!",
            parse_mode='Markdown'
        )
