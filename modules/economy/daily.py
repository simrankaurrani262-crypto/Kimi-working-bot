"""
Telegram RPG Bot - Daily Module
==============================
Handles the /daily command for daily rewards.
"""

import logging
import random
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db, UserRepository, LogRepository
from utils.cooldown import cooldown_manager
from utils.helpers import format_money
from utils.validators import UserValidator
from config import game_config

logger = logging.getLogger(__name__)


class DailyHandler:
    """Handles daily command for daily rewards."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /daily command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        user = await UserRepository.get_user(user_id)
        
        # Check cooldown
        remaining = cooldown_manager.get_remaining(user_id, "daily")
        if remaining > 0:
            formatted = cooldown_manager.format_remaining(remaining)
            
            # Get streak info
            economy = db.economy.find_one({"user_id": user_id}) or {}
            streak = economy.get("daily_streak", 0)
            
            await update.message.reply_text(
                f"⏳ *Daily Reward*\n\n"
                f"You've already claimed your daily reward!\n\n"
                f"Next claim in: {formatted}\n"
                f"Current streak: {streak} days 🔥",
                parse_mode='Markdown'
            )
            return
        
        # Get economy data
        economy = db.economy.find_one({"user_id": user_id})
        if not economy:
            economy = {
                "user_id": user_id,
                "daily_streak": 0,
                "max_daily_streak": 0,
                "last_daily": None
            }
            db.economy.insert_one(economy)
        
        # Check streak
        last_daily = economy.get("last_daily")
        streak = economy.get("daily_streak", 0)
        
        if last_daily:
            last_date = last_daily.date() if isinstance(last_daily, datetime) else last_daily
            today = datetime.utcnow().date()
            yesterday = today - timedelta(days=1)
            
            if last_date == yesterday:
                streak += 1
            elif last_date < yesterday:
                streak = 1  # Reset streak
        else:
            streak = 1
        
        # Calculate reward
        base_reward = random.randint(
            game_config.DAILY_REWARD_MIN,
            game_config.DAILY_REWARD_MAX
        )
        streak_bonus = min(streak * game_config.DAILY_STREAK_BONUS, 500)
        total_reward = base_reward + streak_bonus
        
        # Add money
        await UserRepository.add_money(user_id, total_reward)
        
        # Update economy data
        max_streak = max(streak, economy.get("max_daily_streak", 0))
        db.economy.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "daily_streak": streak,
                    "max_daily_streak": max_streak,
                    "last_daily": datetime.utcnow()
                },
                "$inc": {"total_earned": total_reward}
            }
        )
        
        # Set cooldown
        cooldown_manager.set_cooldown(user_id, "daily")
        
        # Log the action
        await LogRepository.log_action(
            user_id, "daily_claimed", {"amount": total_reward, "streak": streak}
        )
        
        # Send reward message
        streak_text = f"\n🔥 Streak: {streak} days!" if streak > 1 else ""
        bonus_text = f"\n✨ Streak Bonus: {format_money(streak_bonus)}" if streak_bonus > 0 else ""
        
        await update.message.reply_text(
            f"🎁 *Daily Reward Claimed!*\n\n"
            f"Base Reward: {format_money(base_reward)}"
            f"{bonus_text}"
            f"{streak_text}\n"
            f"{'─' * 20}\n"
            f"💰 Total: {format_money(total_reward)}\n\n"
            f"Come back tomorrow for more! 🌟",
            parse_mode='Markdown'
        )
