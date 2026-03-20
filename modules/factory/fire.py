"""
Telegram RPG Bot - Fire Module
=============================
Handles the /fire command for firing workers.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from database import db, UserRepository, LogRepository
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class FireHandler:
    """Handles fire command for firing workers."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /fire command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        
        # Check if user has a factory
        factory = db.factory.find_one({"user_id": user_id})
        if not factory:
            await update.message.reply_text(
                "❌ You don't own a factory! Use `/factory` to buy one."
            )
            return
        
        current_workers = factory.get("workers", 0)
        
        if current_workers <= 0:
            await update.message.reply_text("❌ You don't have any workers to fire!")
            return
        
        # Check arguments
        if not context.args:
            await update.message.reply_text(
                f"🔥 *Fire Workers*\n\n"
                f"Current workers: {current_workers}\n\n"
                f"Usage: `/fire <amount>` or `/fire all`"
            )
            return
        
        amount_str = context.args[0].lower()
        
        if amount_str == "all":
            amount = current_workers
        else:
            try:
                amount = int(amount_str)
            except ValueError:
                await update.message.reply_text("❌ Invalid amount!")
                return
        
        if amount <= 0:
            await update.message.reply_text("❌ Amount must be positive!")
            return
        
        if amount > current_workers:
            await update.message.reply_text(
                f"❌ You only have {current_workers} workers!"
            )
            return
        
        # Fire workers
        db.factory.update_one(
            {"user_id": user_id},
            {
                "$inc": {"workers": -amount},
                "$set": {"production": max(100, factory.get("production", 100) - amount * 50)}
            }
        )
        
        await LogRepository.log_action(
            user_id, "worker_fired", {"count": amount}
        )
        
        await update.message.reply_text(
            f"🔥 *Workers Fired!*\n\n"
            f"Fired: {amount} worker(s)\n"
            f"Remaining workers: {current_workers - amount}"
        )
