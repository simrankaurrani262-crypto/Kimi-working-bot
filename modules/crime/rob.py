"""
Telegram RPG Bot - Rob Module
============================
Handles the /rob command for robbing other users.
"""

import logging
import random
from telegram import Update
from telegram.ext import ContextTypes

from database import db, UserRepository, LogRepository
from utils.cooldown import cooldown_manager
from utils.helpers import format_money
from utils.validators import UserValidator
from config import game_config

logger = logging.getLogger(__name__)


class RobHandler:
    """Handles rob command for robbing other users."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /rob command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        user = await UserRepository.get_user(user_id)
        
        # Check cooldown
        remaining = cooldown_manager.get_remaining(user_id, "rob")
        if remaining > 0:
            formatted = cooldown_manager.format_remaining(remaining)
            await update.message.reply_text(
                f"⏳ You're still laying low from your last robbery!\n"
                f"Wait {formatted} before robbing again."
            )
            return
        
        # Check for target
        if not context.args:
            await update.message.reply_text(
                "🔪 *Rob Someone*\n\n"
                "Usage: `/rob <user_id>`\n\n"
                "⚠️ Warning: Robbery is a crime! You might get caught and sent to jail."
            )
            return
        
        try:
            target_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!")
            return
        
        # Check not robbing self
        if user_id == target_id:
            await update.message.reply_text("❌ You can't rob yourself!")
            return
        
        # Check target exists
        target = await UserRepository.get_user(target_id)
        if not target:
            await update.message.reply_text("❌ User not found!")
            return
        
        # Check target has money
        if target["money"] < 100:
            await update.message.reply_text(
                f"❌ {target['name']} doesn't have enough money to rob!"
            )
            return
        
        # Check if target has insurance
        if target.get("insurance", False):
            await update.message.reply_text(
                f"🛡️ {target['name']} has insurance! You can't rob them."
            )
            return
        
        # Set cooldown
        cooldown_manager.set_cooldown(user_id, "rob")
        
        # Determine success
        success = random.random() < game_config.ROB_SUCCESS_RATE
        
        if success:
            # Calculate stolen amount
            steal_percent = random.uniform(
                game_config.ROB_MIN_AMOUNT,
                game_config.ROB_MAX_AMOUNT
            )
            stolen = int(target["money"] * steal_percent)
            
            # Transfer money
            await UserRepository.remove_money(target_id, stolen)
            await UserRepository.add_money(user_id, stolen)
            
            # Add XP
            await UserRepository.add_experience(user_id, 20)
            
            # Log the robbery
            await LogRepository.log_action(
                user_id, "rob_attempt", {"target": target_id, "amount": stolen, "success": True}
            )
            await LogRepository.log_action(
                target_id, "robbed", {"robber": user_id, "amount": stolen}
            )
            
            await update.message.reply_text(
                f"🔪 *Robbery Successful!*\n\n"
                f"You robbed {target['name']} and got away with {format_money(stolen)}!\n\n"
                f"💰 New balance: {format_money(user['money'] + stolen)}"
            )
            
            # Notify target
            try:
                await context.bot.send_message(
                    chat_id=target_id,
                    text=(
                        f"😢 *You were robbed!*\n\n"
                        f"{user['name']} robbed you and took {format_money(stolen)}!\n\n"
                        f"💰 New balance: {format_money(target['money'] - stolen)}\n\n"
                        f"Buy insurance with `/insurance` to protect yourself!"
                    )
                )
            except Exception as e:
                logger.error(f"Error notifying target: {e}")
        else:
            # Failed robbery - go to jail
            jail_time = random.randint(5, 15)  # minutes
            
            db.users.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "in_jail": True,
                        "jail_until": db.get_timestamp() + __import__('datetime').timedelta(minutes=jail_time)
                    }
                }
            )
            
            # Log the failed robbery
            await LogRepository.log_action(
                user_id, "rob_attempt", {"target": target_id, "success": False}
            )
            
            await update.message.reply_text(
                f"🚔 *Robbery Failed!*\n\n"
                f"You got caught trying to rob {target['name']}!\n\n"
                f"🔒 You've been sent to jail for {jail_time} minutes.\n"
                f"Use `/bail` to pay your way out early."
            )
