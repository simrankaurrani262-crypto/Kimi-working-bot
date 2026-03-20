"""
Telegram RPG Bot - Admin Logs Module
===================================
Handles the /logs command for viewing bot logs.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from database import db, LogRepository
from config import bot_config

logger = logging.getLogger(__name__)


class AdminLogsHandler:
    """Handles logs command for viewing bot logs."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /logs command."""
        user_id = update.effective_user.id
        
        # Check if admin
        if user_id not in bot_config.ADMIN_IDS:
            await update.message.reply_text("❌ You don't have permission to use this command!")
            return
        
        # Get recent logs
        logs = await LogRepository.get_logs(limit=20)
        
        text = "📜 *Recent Logs*\n\n"
        
        for log in logs:
            timestamp = log["timestamp"].strftime("%H:%M:%S") if log.get("timestamp") else "Unknown"
            action = log.get("action", "Unknown")
            user_id_log = log.get("user_id", "Unknown")
            
            text += f"`{timestamp}` | User {user_id_log} | {action}\n"
        
        await update.message.reply_text(text, parse_mode='Markdown')
