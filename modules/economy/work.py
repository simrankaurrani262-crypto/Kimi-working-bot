"""
Telegram RPG Bot - Work Module
=============================
Handles the /work command for working.
"""

import logging
import random
from telegram import Update
from telegram.ext import ContextTypes

from database import db, UserRepository, LogRepository
from utils.cooldown import cooldown_manager
from utils.helpers import format_money
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class WorkHandler:
    """Handles work command for working."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /work command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        user = await UserRepository.get_user(user_id)
        
        # Check cooldown
        remaining = cooldown_manager.get_remaining(user_id, "work")
        if remaining > 0:
            formatted = cooldown_manager.format_remaining(remaining)
            await update.message.reply_text(
                f"⏳ You're still tired from your last work session!\n"
                f"Rest for {formatted} before working again."
            )
            return
        
        # Get job info
        from modules.economy.jobs import JobsHandler
        job_key = user.get("job", "unemployed")
        job_info = JobsHandler.JOBS.get(job_key, JobsHandler.JOBS["unemployed"])
        
        if job_key == "unemployed":
            await update.message.reply_text(
                "❌ You don't have a job!\n\n"
                "Use `/job` to find and apply for a job!"
            )
            return
        
        # Calculate earnings
        base_salary = job_info["salary"]
        level_bonus = int(user["level"] * 10)
        random_bonus = random.randint(0, 50)
        total_earnings = base_salary + level_bonus + random_bonus
        
        # Add XP
        xp_gained = random.randint(10, 30)
        new_level, leveled_up = await UserRepository.add_experience(user_id, xp_gained)
        
        # Add money
        await UserRepository.add_money(user_id, total_earnings)
        
        # Update work stats
        db.economy.update_one(
            {"user_id": user_id},
            {
                "$inc": {"work_sessions": 1, "total_earned": total_earnings},
                "$set": {"last_work": db.get_timestamp()}
            },
            upsert=True
        )
        
        # Set cooldown
        cooldown_manager.set_cooldown(user_id, "work")
        
        # Log the action
        await LogRepository.log_action(
            user_id, "worked", {"earnings": total_earnings, "job": job_key}
        )
        
        # Work messages
        work_messages = [
            f"You worked hard as a {job_info['name']} and earned",
            f"Your shift as a {job_info['name']} was productive! You earned",
            f"Great work today as a {job_info['name']}! You earned",
            f"Your dedication as a {job_info['name']} paid off! You earned",
        ]
        
        message = random.choice(work_messages)
        
        response = (
            f"💼 *Work Complete!*\n\n"
            f"{message}\n"
            f"💰 {format_money(total_earnings)}\n\n"
            f"Breakdown:\n"
            f"  Base Salary: {format_money(base_salary)}\n"
            f"  Level Bonus: {format_money(level_bonus)}\n"
            f"  Performance Bonus: {format_money(random_bonus)}\n\n"
            f"📈 XP Gained: +{xp_gained}\n"
        )
        
        if leveled_up:
            response += f"🎉 *LEVEL UP!* You are now level {new_level}!\n"
        
        await update.message.reply_text(response, parse_mode='Markdown')
