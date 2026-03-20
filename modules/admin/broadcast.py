"""
Telegram RPG Bot - Broadcast Module
==================================
Handles the /broadcast command for broadcasting messages.
"""

import logging
import asyncio
from telegram import Update
from telegram.ext import ContextTypes

from database import db, LogRepository
from config import bot_config

logger = logging.getLogger(__name__)


class BroadcastHandler:
    """Handles broadcast command for broadcasting messages."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /broadcast command."""
        user_id = update.effective_user.id
        
        # Check if admin
        if user_id not in bot_config.ADMIN_IDS:
            await update.message.reply_text("❌ You don't have permission to use this command!")
            return
        
        # Check arguments
        if not context.args:
            await update.message.reply_text(
                "📢 *Broadcast Message*\n\n"
                "Usage: `/broadcast <message>`"
            )
            return
        
        message = " ".join(context.args)
        
        # Get all users
        users = list(db.users.find({"banned": False}))
        
        sent = 0
        failed = 0
        
        for user in users:
            try:
                await context.bot.send_message(
                    chat_id=user["user_id"],
                    text=f"📢 *Announcement*\n\n{message}",
                    parse_mode='Markdown'
                )
                sent += 1
                await asyncio.sleep(0.1)  # Rate limit
            except Exception as e:
                logger.error(f"Failed to send broadcast to {user['user_id']}: {e}")
                failed += 1
        
        await LogRepository.log_action(
            user_id, "broadcast_sent", {"message": message, "sent": sent, "failed": failed}
        )
        
        await update.message.reply_text(
            f"📢 *Broadcast Complete*\n\n"
            f"Sent: {sent}\n"
            f"Failed: {failed}"
        )
