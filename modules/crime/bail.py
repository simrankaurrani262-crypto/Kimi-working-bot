"""
Telegram RPG Bot - Bail Module
=============================
Handles the /bail command for paying bail.
"""

import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from database import db, UserRepository, LogRepository
from utils.helpers import format_money
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class BailHandler:
    """Handles bail command for paying bail."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /bail command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        user = await UserRepository.get_user(user_id)
        
        # Check if in jail
        if not user.get("in_jail", False):
            await update.message.reply_text(
                "✅ *You are not in jail!*\n\n"
                "No need to pay bail!"
            )
            return
        
        # Calculate bail cost
        jail_until = user.get("jail_until")
        if jail_until:
            if isinstance(jail_until, str):
                jail_until = datetime.fromisoformat(jail_until)
            remaining = (jail_until - datetime.utcnow()).total_seconds()
            bail_cost = max(500, int(remaining / 60) * 50)
        else:
            bail_cost = 1000
        
        # Check has enough money
        if user["money"] < bail_cost:
            await update.message.reply_text(
                f"❌ Insufficient funds!\n"
                f"Bail cost: {format_money(bail_cost)}\n"
                f"Your balance: {format_money(user['money'])}"
            )
            return
        
        # Pay bail
        await UserRepository.remove_money(user_id, bail_cost)
        
        # Release from jail
        db.users.update_one(
            {"user_id": user_id},
            {"$set": {"in_jail": False, "jail_until": None}}
        )
        
        # Log the bail
        await LogRepository.log_action(
            user_id, "bail_paid", {"cost": bail_cost}
        )
        
        await update.message.reply_text(
            f"💰 *Bail Paid!*\n\n"
            f"You paid {format_money(bail_cost)} and are now free!\n\n"
            f"Stay out of trouble! 🚔"
        )
