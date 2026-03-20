"""
Telegram RPG Bot - MoneyGraph Module
===================================
Handles the /moneygraph command for viewing money history graph.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from database import db
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class MoneyGraphHandler:
    """Handles moneygraph command for viewing money history graph."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /moneygraph command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        
        # Get money history (would be stored in a real implementation)
        # For now, show a simple text representation
        economy = db.economy.find_one({"user_id": user_id}) or {}
        
        total_earned = economy.get("total_earned", 0)
        total_spent = economy.get("total_spent", 0)
        
        # Create simple ASCII graph
        max_val = max(total_earned, total_spent, 1)
        earned_bar = int((total_earned / max_val) * 20)
        spent_bar = int((total_spent / max_val) * 20)
        
        text = (
            f"📈 *Money History*\n\n"
            f"Total Earned: {total_earned:,}\n"
            f"{'█' * earned_bar}{'░' * (20 - earned_bar)}\n\n"
            f"Total Spent: {total_spent:,}\n"
            f"{'█' * spent_bar}{'░' * (20 - spent_bar)}\n\n"
            f"Net: {total_earned - total_spent:,}"
        )
        
        await update.message.reply_text(text, parse_mode='Markdown')
