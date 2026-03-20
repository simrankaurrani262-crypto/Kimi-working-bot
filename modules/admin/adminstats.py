"""
Telegram RPG Bot - AdminStats Module
===================================
Handles the /adminstats command for viewing bot statistics.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from database import db
from config import bot_config

logger = logging.getLogger(__name__)


class AdminStatsHandler:
    """Handles adminstats command for viewing bot statistics."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /adminstats command."""
        user_id = update.effective_user.id
        
        # Check if admin
        if user_id not in bot_config.ADMIN_IDS:
            await update.message.reply_text("❌ You don't have permission to use this command!")
            return
        
        # Get stats
        total_users = db.users.count_documents({})
        active_users = db.users.count_documents({"banned": False})
        banned_users = db.users.count_documents({"banned": True})
        total_families = db.families.count_documents({})
        total_factories = db.factory.count_documents({})
        total_gardens = db.gardens.count_documents({})
        
        # Get total money in circulation
        pipeline = [
            {"$group": {"_id": None, "total": {"$sum": "$money"}}}
        ]
        money_result = list(db.users.aggregate(pipeline))
        total_money = money_result[0]["total"] if money_result else 0
        
        text = (
            f"📊 *Bot Statistics*\n\n"
            f"👥 *Users:*\n"
            f"   Total: {total_users}\n"
            f"   Active: {active_users}\n"
            f"   Banned: {banned_users}\n\n"
            f"👨‍👩‍👧‍👦 *Families:* {total_families}\n"
            f"🏭 *Factories:* {total_factories}\n"
            f"🌱 *Gardens:* {total_gardens}\n\n"
            f"💰 *Total Money:* {total_money:,}\n"
        )
        
        await update.message.reply_text(text, parse_mode='Markdown')
