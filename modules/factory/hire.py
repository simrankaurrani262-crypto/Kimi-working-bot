"""
Telegram RPG Bot - Hire Module
=============================
Handles the /hire command for hiring workers.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from database import db, UserRepository, LogRepository
from utils.helpers import format_money
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class HireHandler:
    """Handles hire command for hiring workers."""
    
    WORKER_COST = 500
    MAX_WORKERS = 10
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /hire command."""
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
        
        if current_workers >= HireHandler.MAX_WORKERS:
            await update.message.reply_text(
                f"❌ You already have the maximum number of workers ({HireHandler.MAX_WORKERS})!"
            )
            return
        
        # Check arguments
        if not context.args:
            await update.message.reply_text(
                f"👷 *Hire Workers*\n\n"
                f"Cost per worker: {format_money(HireHandler.WORKER_COST)}\n"
                f"Current workers: {current_workers}/{HireHandler.MAX_WORKERS}\n\n"
                f"Usage: `/hire <amount>` or `/hire 1`"
            )
            return
        
        try:
            amount = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid amount!")
            return
        
        if amount <= 0:
            await update.message.reply_text("❌ Amount must be positive!")
            return
        
        if current_workers + amount > HireHandler.MAX_WORKERS:
            await update.message.reply_text(
                f"❌ You can only hire {HireHandler.MAX_WORKERS - current_workers} more workers!"
            )
            return
        
        user = await UserRepository.get_user(user_id)
        total_cost = HireHandler.WORKER_COST * amount
        
        if user["money"] < total_cost:
            await update.message.reply_text(
                f"❌ Insufficient funds!\n"
                f"Cost: {format_money(total_cost)}\n"
                f"Your balance: {format_money(user['money'])}"
            )
            return
        
        # Hire workers
        await UserRepository.remove_money(user_id, total_cost)
        db.factory.update_one(
            {"user_id": user_id},
            {
                "$inc": {"workers": amount},
                "$set": {"production": (factory.get("production", 100) + amount * 50)}
            }
        )
        
        await LogRepository.log_action(
            user_id, "worker_hired", {"count": amount, "cost": total_cost}
        )
        
        await update.message.reply_text(
            f"👷 *Workers Hired!*\n\n"
            f"Hired: {amount} worker(s)\n"
            f"Cost: {format_money(total_cost)}\n"
            f"Total workers: {current_workers + amount}"
        )
