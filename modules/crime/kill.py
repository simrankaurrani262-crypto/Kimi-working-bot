"""
Telegram RPG Bot - Kill Module
=============================
Handles the /kill command for attacking other users.
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


class KillHandler:
    """Handles kill command for attacking other users."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /kill command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        user = await UserRepository.get_user(user_id)
        
        # Check cooldown
        remaining = cooldown_manager.get_remaining(user_id, "kill")
        if remaining > 0:
            formatted = cooldown_manager.format_remaining(remaining)
            await update.message.reply_text(
                f"⏳ You need to rest before attacking again!\n"
                f"Wait {formatted}."
            )
            return
        
        # Check for target
        if not context.args:
            await update.message.reply_text(
                "⚔️ *Attack Someone*\n\n"
                "Usage: `/kill <user_id>`\n\n"
                "⚠️ Warning: Attacking is a serious crime with severe consequences!"
            )
            return
        
        try:
            target_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!")
            return
        
        # Check not attacking self
        if user_id == target_id:
            await update.message.reply_text("❌ You can't attack yourself!")
            return
        
        # Check target exists
        target = await UserRepository.get_user(target_id)
        if not target:
            await update.message.reply_text("❌ User not found!")
            return
        
        # Check if target has insurance
        if target.get("insurance", False):
            await update.message.reply_text(
                f"🛡️ {target['name']} has insurance protection!"
            )
            return
        
        # Set cooldown
        cooldown_manager.set_cooldown(user_id, "kill")
        
        # Determine success
        success = random.random() < game_config.KILL_SUCCESS_RATE
        
        if success:
            # Successful attack - steal money and reputation
            stolen = int(target["money"] * 0.1)
            if stolen > 0:
                await UserRepository.remove_money(target_id, stolen)
                await UserRepository.add_money(user_id, stolen)
            
            # Reduce target reputation
            db.users.update_one(
                {"user_id": target_id},
                {"$inc": {"reputation": -10}}
            )
            
            # Add XP
            await UserRepository.add_experience(user_id, 50)
            
            # Log the attack
            await LogRepository.log_action(
                user_id, "attack_attempt", {"target": target_id, "success": True}
            )
            await LogRepository.log_action(
                target_id, "attacked", {"attacker": user_id}
            )
            
            await update.message.reply_text(
                f"⚔️ *Attack Successful!*\n\n"
                f"You attacked {target['name']}!\n"
                f"Stolen: {format_money(stolen)}\n"
                f"Their reputation decreased!\n\n"
                f"💰 New balance: {format_money(user['money'] + stolen)}"
            )
            
            # Notify target
            try:
                await context.bot.send_message(
                    chat_id=target_id,
                    text=(
                        f"💀 *You were attacked!*\n\n"
                        f"{user['name']} attacked you!\n"
                        f"Lost: {format_money(stolen)}\n"
                        f"Reputation: -10\n\n"
                        f"Buy insurance with `/insurance` to protect yourself!"
                    )
                )
            except Exception as e:
                logger.error(f"Error notifying target: {e}")
        else:
            # Failed attack - go to jail
            jail_time = random.randint(15, 30)  # minutes
            
            db.users.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "in_jail": True,
                        "jail_until": db.get_timestamp() + __import__('datetime').timedelta(minutes=jail_time)
                    }
                }
            )
            
            # Log the failed attack
            await LogRepository.log_action(
                user_id, "attack_attempt", {"target": target_id, "success": False}
            )
            
            await update.message.reply_text(
                f"🚔 *Attack Failed!*\n\n"
                f"You failed to attack {target['name']} and got caught!\n\n"
                f"🔒 You've been sent to jail for {jail_time} minutes.\n"
                f"Use `/bail` to pay your way out early."
            )
