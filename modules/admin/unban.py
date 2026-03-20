"""
Telegram RPG Bot - Unban Module
==============================
Handles the /unban command for unbanning users.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from database import db, LogRepository
from config import bot_config

logger = logging.getLogger(__name__)


class UnbanHandler:
    """Handles unban command for unbanning users."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /unban command."""
        user_id = update.effective_user.id
        
        # Check if admin
        if user_id not in bot_config.ADMIN_IDS:
            await update.message.reply_text("❌ You don't have permission to use this command!")
            return
        
        # Check arguments
        if not context.args:
            await update.message.reply_text(
                "✅ *Unban User*\n\n"
                "Usage: `/unban <user_id>`"
            )
            return
        
        try:
            target_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!")
            return
        
        # Unban user
        db.users.update_one(
            {"user_id": target_id},
            {"$set": {"banned": False, "ban_reason": None}}
        )
        
        await LogRepository.log_action(
            user_id, "user_unbanned", {"target": target_id}
        )
        
        await update.message.reply_text(
            f"✅ *User Unbanned*\n\n"
            f"User ID: {target_id}"
        )
