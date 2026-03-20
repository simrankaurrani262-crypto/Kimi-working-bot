"""
Telegram RPG Bot - FactoryUpgrade Module
=======================================
Handles the /factoryupgrade command for upgrading factory.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from database import db, UserRepository, LogRepository
from utils.helpers import format_money
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class FactoryUpgradeHandler:
    """Handles factoryupgrade command for upgrading factory."""
    
    BASE_UPGRADE_COST = 5000
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /factoryupgrade command."""
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
        
        current_level = factory.get("level", 1)
        upgrade_cost = FactoryUpgradeHandler.BASE_UPGRADE_COST * current_level
        
        # Check arguments
        if not context.args or context.args[0].lower() != "confirm":
            await update.message.reply_text(
                f"⬆️ *Upgrade Factory*\n\n"
                f"Current level: {current_level}\n"
                f"Upgrade cost: {format_money(upgrade_cost)}\n\n"
                f"Benefits of upgrading:\n"
                f"• Increased base production\n"
                f"• Higher worker efficiency\n\n"
                f"Use `/factoryupgrade confirm` to upgrade!"
            )
            return
        
        user = await UserRepository.get_user(user_id)
        
        if user["money"] < upgrade_cost:
            await update.message.reply_text(
                f"❌ Insufficient funds!\n"
                f"Cost: {format_money(upgrade_cost)}\n"
                f"Your balance: {format_money(user['money'])}"
            )
            return
        
        # Upgrade factory
        await UserRepository.remove_money(user_id, upgrade_cost)
        db.factory.update_one(
            {"user_id": user_id},
            {
                "$inc": {"level": 1, "production": 100},
                "$set": {"last_upgrade": db.get_timestamp()}
            }
        )
        
        await LogRepository.log_action(
            user_id, "factory_upgraded", {"new_level": current_level + 1, "cost": upgrade_cost}
        )
        
        await update.message.reply_text(
            f"⬆️ *Factory Upgraded!*\n\n"
            f"New level: {current_level + 1}\n"
            f"Cost: {format_money(upgrade_cost)}\n\n"
            f"Your factory is now more efficient! 📈"
        )
