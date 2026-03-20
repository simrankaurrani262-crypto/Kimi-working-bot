"""
Telegram RPG Bot - Jail Module
=============================
Handles the /jail command for jail status.
"""

import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db
from utils.helpers import format_time
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class JailHandler:
    """Handles jail command for jail status."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /jail command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        user = db.users.find_one({"user_id": user_id})
        
        in_jail = user.get("in_jail", False)
        jail_until = user.get("jail_until")
        
        if not in_jail:
            await update.message.reply_text(
                "✅ *You are not in jail!*\n\n"
                "Stay out of trouble and keep it that way! 🚔"
            )
            return
        
        # Calculate remaining time
        if jail_until:
            if isinstance(jail_until, str):
                jail_until = datetime.fromisoformat(jail_until)
            remaining = (jail_until - datetime.utcnow()).total_seconds()
            if remaining <= 0:
                # Release user
                db.users.update_one(
                    {"user_id": user_id},
                    {"$set": {"in_jail": False, "jail_until": None}}
                )
                await update.message.reply_text(
                    "🎉 *You have been released!*\n\n"
                    "Stay out of trouble! 🚔"
                )
                return
            
            remaining_text = format_time(int(remaining))
        else:
            remaining_text = "Unknown"
        
        bail_cost = max(500, int(remaining / 60) * 50)  # 50 coins per minute
        
        text = (
            f"🔒 *You are in jail!*\n\n"
            f"Time remaining: {remaining_text}\n\n"
            f"💰 Bail cost: {bail_cost:,} coins\n\n"
            f"You can wait out your sentence or pay bail to get out early."
        )
        
        keyboard = [
            [
                InlineKeyboardButton(
                    f"💰 Pay Bail ({bail_cost:,})",
                    callback_data="jail_bail"
                )
            ],
            [
                InlineKeyboardButton("⏳ Wait", callback_data="jail_wait")
            ]
        ]
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
