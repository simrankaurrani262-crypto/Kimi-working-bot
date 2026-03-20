"""
Telegram RPG Bot - Medical Module
================================
Handles the /medical command for medical services.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db, UserRepository, LogRepository
from utils.helpers import format_money
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class MedicalHandler:
    """Handles medical command for medical services."""
    
    HEAL_COST = 500
    FULL_HEAL_COST = 1500
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /medical command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        user = db.users.find_one({"user_id": user_id})
        
        health = user.get("health", 100)
        
        text = (
            f"🏥 *Medical Services*\n\n"
            f"Your health: {health}/100\n\n"
            f"*Available Services:*\n"
            f"💊 Basic Healing - {format_money(MedicalHandler.HEAL_COST)} (+25 HP)\n"
            f"🏥 Full Healing - {format_money(MedicalHandler.FULL_HEAL_COST)} (Full HP)\n"
        )
        
        keyboard = [
            [
                InlineKeyboardButton(
                    f"💊 Basic ({format_money(MedicalHandler.HEAL_COST)})",
                    callback_data="medical_basic"
                ),
                InlineKeyboardButton(
                    f"🏥 Full ({format_money(MedicalHandler.FULL_HEAL_COST)})",
                    callback_data="medical_full"
                )
            ],
            [
                InlineKeyboardButton("⬅️ Back", callback_data="profile_view")
            ]
        ]
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    @staticmethod
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle medical callbacks."""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        user = await UserRepository.get_user(user_id)
        
        if query.data == "medical_basic":
            if user["money"] < MedicalHandler.HEAL_COST:
                await query.edit_message_text("❌ Insufficient funds!")
                return
            
            await UserRepository.remove_money(user_id, MedicalHandler.HEAL_COST)
            new_health = min(100, user.get("health", 100) + 25)
            db.users.update_one(
                {"user_id": user_id},
                {"$set": {"health": new_health}}
            )
            
            await LogRepository.log_action(user_id, "healed", {"amount": 25, "cost": MedicalHandler.HEAL_COST})
            
            await query.edit_message_text(
                f"💊 *Healed!*\n\n"
                f"Health restored to {new_health}/100\n"
                f"Cost: {format_money(MedicalHandler.HEAL_COST)}"
            )
        
        elif query.data == "medical_full":
            if user["money"] < MedicalHandler.FULL_HEAL_COST:
                await query.edit_message_text("❌ Insufficient funds!")
                return
            
            await UserRepository.remove_money(user_id, MedicalHandler.FULL_HEAL_COST)
            db.users.update_one(
                {"user_id": user_id},
                {"$set": {"health": 100}}
            )
            
            await LogRepository.log_action(user_id, "healed", {"amount": 100, "cost": MedicalHandler.FULL_HEAL_COST})
            
            await query.edit_message_text(
                f"🏥 *Fully Healed!*\n\n"
                f"Health restored to 100/100\n"
                f"Cost: {format_money(MedicalHandler.FULL_HEAL_COST)}"
            )
