"""
Telegram RPG Bot - Jobs Module
=============================
Handles the /job command for viewing and changing jobs.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db, UserRepository, LogRepository
from utils.helpers import format_money
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class JobsHandler:
    """Handles job command for viewing and changing jobs."""
    
    JOBS = {
        "unemployed": {
            "name": "Unemployed",
            "salary": 0,
            "description": "Looking for work",
            "requirements": "None"
        },
        "cashier": {
            "name": "Cashier",
            "salary": 100,
            "description": "Work at a local store",
            "requirements": "Level 1"
        },
        "teacher": {
            "name": "Teacher",
            "salary": 200,
            "description": "Educate the next generation",
            "requirements": "Level 5"
        },
        "chef": {
            "name": "Chef",
            "salary": 300,
            "description": "Cook delicious meals",
            "requirements": "Level 10"
        },
        "programmer": {
            "name": "Programmer",
            "salary": 500,
            "description": "Build amazing software",
            "requirements": "Level 15"
        },
        "doctor": {
            "name": "Doctor",
            "salary": 800,
            "description": "Save lives",
            "requirements": "Level 20"
        },
        "lawyer": {
            "name": "Lawyer",
            "salary": 1000,
            "description": "Defend the innocent",
            "requirements": "Level 25"
        },
        "ceo": {
            "name": "CEO",
            "salary": 2000,
            "description": "Run a successful company",
            "requirements": "Level 30"
        },
    }
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /job command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        user = await UserRepository.get_user(user_id)
        
        current_job = user.get("job", "unemployed")
        job_info = JobsHandler.JOBS.get(current_job, JobsHandler.JOBS["unemployed"])
        
        # Check if changing job
        if context.args:
            new_job = context.args[0].lower()
            
            if new_job not in JobsHandler.JOBS:
                await update.message.reply_text(
                    f"❌ Invalid job! Available jobs: {', '.join(JobsHandler.JOBS.keys())}"
                )
                return
            
            if new_job == current_job:
                await update.message.reply_text("❌ You already have this job!")
                return
            
            # Check requirements
            new_job_info = JobsHandler.JOBS[new_job]
            req_level = int(new_job_info["requirements"].split()[1]) if "Level" in new_job_info["requirements"] else 1
            
            if user["level"] < req_level:
                await update.message.reply_text(
                    f"❌ You need to be level {req_level} to become a {new_job_info['name']}!"
                )
                return
            
            # Change job
            db.users.update_one(
                {"user_id": user_id},
                {"$set": {"job": new_job}}
            )
            
            await LogRepository.log_action(
                user_id, "job_changed", {"old_job": current_job, "new_job": new_job}
            )
            
            await update.message.reply_text(
                f"💼 *Job Changed!*\n\n"
                f"You are now a {new_job_info['name']}!\n"
                f"Salary: {format_money(new_job_info['salary'])}/work\n\n"
                f"Use `/work` to start working!",
                parse_mode='Markdown'
            )
            return
        
        # Show current job and available jobs
        text = (
            f"💼 *Your Job*\n\n"
            f"Current: *{job_info['name']}*\n"
            f"Salary: {format_money(job_info['salary'])}/work\n"
            f"Description: {job_info['description']}\n\n"
            f"📋 *Available Jobs:*\n"
        )
        
        keyboard = []
        for job_key, job_data in JobsHandler.JOBS.items():
            if job_key != current_job:
                req_level = int(job_data["requirements"].split()[1]) if "Level" in job_data["requirements"] else 1
                can_apply = user["level"] >= req_level
                status = "✅" if can_apply else "🔒"
                
                text += (
                    f"{status} *{job_data['name']}*\n"
                    f"   Salary: {format_money(job_data['salary'])}/work\n"
                    f"   Required: {job_data['requirements']}\n\n"
                )
                
                if can_apply:
                    keyboard.append([
                        InlineKeyboardButton(
                            f"Apply for {job_data['name']}",
                            callback_data=f"job_apply_{job_key}"
                        )
                    ])
        
        keyboard.append([
            InlineKeyboardButton("💪 Work Now", callback_data="work_start"),
            InlineKeyboardButton("⬅️ Back", callback_data="profile_view")
        ])
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
