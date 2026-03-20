"""
Telegram RPG Bot - Insurance Module
==================================
Handles the /insurance command for insurance.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db, UserRepository, LogRepository
from utils.helpers import format_money
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class InsuranceHandler:
    """Handles insurance command for insurance."""
    
    INSURANCE_COST = 2000
    INSURANCE_DURATION_DAYS = 7
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /insurance command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        user = await UserRepository.get_user(user_id)
        
        has_insurance = user.get("insurance", False)
        
        text = (
            f"🛡️ *Insurance*\n\n"
            f"Protect yourself from robberies and attacks!\n\n"
            f"Cost: {format_money(InsuranceHandler.INSURANCE_COST)}\n"
            f"Duration: {InsuranceHandler.INSURANCE_DURATION_DAYS} days\n\n"
        )
        
        if has_insurance:
            text += "✅ *You currently have insurance!*\n"
        else:
            text += "❌ *You don't have insurance!*\n"
            text += "You are vulnerable to robberies and attacks.\n"
        
        keyboard = []
        
        if not has_insurance:
            keyboard.append([
                InlineKeyboardButton(
                    f"🛡️ Buy Insurance ({format_money(InsuranceHandler.INSURANCE_COST)})",
                    callback_data="insurance_buy"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("⬅️ Back", callback_data="profile_view")
        ])
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    @staticmethod
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle insurance callbacks."""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        user = await UserRepository.get_user(user_id)
        
        if query.data == "insurance_buy":
            if user.get("insurance", False):
                await query.edit_message_text("✅ You already have insurance!")
                return
            
            if user["money"] < InsuranceHandler.INSURANCE_COST:
                await query.edit_message_text(
                    f"❌ Insufficient funds!\n"
                    f"Cost: {format_money(InsuranceHandler.INSURANCE_COST)}"
                )
                return
            
            # Buy insurance
            await UserRepository.remove_money(user_id, InsuranceHandler.INSURANCE_COST)
            db.users.update_one(
                {"user_id": user_id},
                {"$set": {"insurance": True}}
            )
            
            await LogRepository.log_action(
                user_id, "insurance_bought", {"cost": InsuranceHandler.INSURANCE_COST}
            )
            
            await query.edit_message_text(
                f"🛡️ *Insurance Purchased!*\n\n"
                f"You are now protected from robberies and attacks for {InsuranceHandler.INSURANCE_DURATION_DAYS} days!"
            )
