"""
Telegram RPG Bot - Auction Module
================================
Handles the /auction command for viewing auctions.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db, UserRepository
from utils.helpers import format_money
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class AuctionHandler:
    """Handles auction command for viewing auctions."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /auction command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        # Get active auctions
        auctions = list(db.market.find({"auction": True}).limit(10))
        
        text = "🔨 *Active Auctions*\n\n"
        
        if auctions:
            for auction in auctions:
                seller = await UserRepository.get_user(auction.get("seller_id"))
                seller_name = seller['name'] if seller else "Unknown"
                
                text += (
                    f"📦 {auction.get('item_name', 'Unknown')}\n"
                    f"   Seller: {seller_name}\n"
                    f"   Current Bid: {format_money(auction.get('current_bid', auction.get('starting_bid', 0)))}\n"
                    f"   Ends in: {auction.get('time_remaining', 'Unknown')}\n\n"
                )
        else:
            text += "No active auctions right now.\n\n"
        
        keyboard = [
            [
                InlineKeyboardButton("💰 Place Bid", callback_data="auction_bid"),
                InlineKeyboardButton("🏪 Market", callback_data="stands_browse")
            ]
        ]
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
