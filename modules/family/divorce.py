"""
Telegram RPG Bot - Divorce Module
================================
Handles the /divorce command for divorce.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db, UserRepository, LogRepository
from utils.validators import UserValidator
from utils.helpers import format_money

logger = logging.getLogger(__name__)


class DivorceHandler:
    """Handles divorce command for divorce."""
    
    DIVORCE_COST = 500
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /divorce command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        user = await UserRepository.get_user(user_id)
        
        # Check if user is married
        if not user.get("partner"):
            await update.message.reply_text(
                "❌ You are not married!\n\n"
                "Use `/marry @username` to find a partner!"
            )
            return
        
        partner_id = user["partner"]
        partner = await UserRepository.get_user(partner_id)
        
        if not partner:
            # Partner account deleted or invalid
            db.users.update_one(
                {"user_id": user_id},
                {"$set": {"partner": None}}
            )
            await update.message.reply_text(
                "✅ Your partner's account no longer exists. You are now single."
            )
            return
        
        # Confirm divorce
        keyboard = [
            [
                InlineKeyboardButton("💔 Confirm Divorce", callback_data="divorce_confirm"),
                InlineKeyboardButton("❌ Cancel", callback_data="divorce_cancel")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"💔 *Divorce*\n\n"
            f"Cost: {format_money(DivorceHandler.DIVORCE_COST)}\n\n"
            f"Are you sure you want to divorce {partner['name']} (@{partner['username']})?\n\n"
            f"This action cannot be undone!",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle divorce callbacks."""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        user = await UserRepository.get_user(user_id)
        
        if query.data == "divorce_confirm":
            # Check user has enough money
            if user["money"] < DivorceHandler.DIVORCE_COST:
                await query.edit_message_text(
                    f"❌ You don't have enough money!\n"
                    f"Cost: {format_money(DivorceHandler.DIVORCE_COST)}\n"
                    f"Your balance: {format_money(user['money'])}"
                )
                return
            
            partner_id = user.get("partner")
            if not partner_id:
                await query.edit_message_text("❌ You are no longer married!")
                return
            
            partner = await UserRepository.get_user(partner_id)
            
            # Deduct divorce cost
            await UserRepository.remove_money(user_id, DivorceHandler.DIVORCE_COST)
            
            # Update both users as divorced
            db.users.update_one(
                {"user_id": user_id},
                {"$set": {"partner": None}}
            )
            db.users.update_one(
                {"user_id": partner_id},
                {"$set": {"partner": None}}
            )
            
            # Log the divorce
            await LogRepository.log_action(
                user_id, "divorced", {"partner": partner_id}
            )
            await LogRepository.log_action(
                partner_id, "divorced_by", {"partner": user_id}
            )
            
            # Notify partner
            try:
                await context.bot.send_message(
                    chat_id=partner_id,
                    text=(
                        f"💔 *Divorce*\n\n"
                        f"{user['name']} (@{user['username']}) has divorced you.\n\n"
                        f"You are now single."
                    ),
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Error notifying partner: {e}")
            
            # Update user's message
            await query.edit_message_text(
                f"💔 *Divorce Complete*\n\n"
                f"You have divorced {partner['name'] if partner else 'your partner'}.\n\n"
                f"You are now single.\n"
                f"Cost: {format_money(DivorceHandler.DIVORCE_COST)}",
                parse_mode='Markdown'
            )
            
        elif query.data == "divorce_cancel":
            await query.edit_message_text(
                "✅ Divorce cancelled. Your marriage is safe! 💕"
            )
