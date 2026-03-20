"""
Telegram RPG Bot - Ban Module
============================
Handles the /ban command for banning users.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from database import db, UserRepository, LogRepository
from config import bot_config

logger = logging.getLogger(__name__)


class BanHandler:
    """Handles ban command for banning users."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /ban command."""
        user_id = update.effective_user.id
        
        # Check if admin
        if user_id not in bot_config.ADMIN_IDS:
            await update.message.reply_text("❌ You don't have permission to use this command!")
            return
        
        # Check arguments
        if len(context.args) < 2:
            await update.message.reply_text(
                "🚫 *Ban User*\n\n"
                "Usage: `/ban <user_id> <reason>`"
            )
            return
        
        try:
            target_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!")
            return
        
        reason = " ".join(context.args[1:])
        
        # Ban user
        db.users.update_one(
            {"user_id": target_id},
            {"$set": {"banned": True, "ban_reason": reason}}
        )
        
        await LogRepository.log_action(
            user_id, "user_banned", {"target": target_id, "reason": reason}
        )
        
        await update.message.reply_text(
            f"🚫 *User Banned*\n\n"
            f"User ID: {target_id}\n"
            f"Reason: {reason}"
        )
