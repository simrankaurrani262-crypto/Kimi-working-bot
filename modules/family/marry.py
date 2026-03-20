"""
Telegram RPG Bot - Marry Module
==============================
Handles the /marry command for marriage.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db, UserRepository, LogRepository
from utils.validators import validate_marriage_eligibility, UserValidator
from utils.helpers import format_money

logger = logging.getLogger(__name__)


class MarryHandler:
    """Handles marry command for marriage."""
    
    MARRIAGE_COST = 1000
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /marry command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            await validator.check_money(MarryHandler.MARRIAGE_COST)
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        
        # Check if user is already married
        valid, error = await validate_marriage_eligibility(user_id)
        if not valid:
            await update.message.reply_text(f"❌ {error}")
            return
        
        # Check for target user
        if not context.args:
            await update.message.reply_text(
                "💍 *Get Married*\n\n"
                f"Cost: {format_money(MarryHandler.MARRIAGE_COST)}\n\n"
                "Usage: `/marry @username` or `/marry <user_id>`\n\n"
                "Find your soulmate and start a family!",
                parse_mode='Markdown'
            )
            return
        
        target = context.args[0]
        
        # Parse target user ID
        try:
            if target.startswith('@'):
                await update.message.reply_text(
                    "❌ Please use the user's ID instead of username.\n"
                    "The user can find their ID with /profile"
                )
                return
            else:
                partner_id = int(target)
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!")
            return
        
        # Check not marrying self
        if user_id == partner_id:
            await update.message.reply_text("❌ You can't marry yourself!")
            return
        
        # Check partner exists
        partner = await UserRepository.get_user(partner_id)
        if not partner:
            await update.message.reply_text("❌ User not found!")
            return
        
        # Check partner not already married
        if partner.get("partner"):
            await update.message.reply_text(
                f"❌ {partner['name']} is already married!"
            )
            return
        
        # Check partner not a child or parent
        user = await UserRepository.get_user(user_id)
        if partner_id in user.get("children", []):
            await update.message.reply_text("❌ You can't marry your own child!")
            return
        if partner_id in user.get("parents", []):
            await update.message.reply_text("❌ You can't marry your own parent!")
            return
        
        # Send marriage proposal
        keyboard = [
            [
                InlineKeyboardButton("💍 Accept", callback_data=f"marry_accept_{user_id}"),
                InlineKeyboardButton("❌ Decline", callback_data=f"marry_decline_{user_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await context.bot.send_message(
                chat_id=partner_id,
                text=(
                    f"💍 *Marriage Proposal*\n\n"
                    f"{user['name']} (@{user['username']}) has proposed to you!\n\n"
                    f"They are level {user['level']} with {format_money(user['money'])}.\n\n"
                    f"Will you marry them?"
                ),
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
            await update.message.reply_text(
                f"💍 Marriage proposal sent to {partner['name']}!\n"
                f"They need to accept your proposal."
            )
            
        except Exception as e:
            logger.error(f"Error sending marriage proposal: {e}")
            await update.message.reply_text(
                "❌ Could not send marriage proposal. The user may have blocked the bot."
            )
    
    @staticmethod
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle marriage callbacks."""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        partner_id = query.from_user.id
        
        if data.startswith("marry_accept_"):
            proposer_id = int(data.replace("marry_accept_", ""))
            await MarryHandler._process_marriage(context, proposer_id, partner_id, query)
        elif data.startswith("marry_decline_"):
            proposer_id = int(data.replace("marry_decline_", ""))
            await MarryHandler._decline_marriage(context, proposer_id, partner_id, query)
    
    @staticmethod
    async def _process_marriage(context, user1_id: int, user2_id: int, query) -> None:
        """Process accepted marriage."""
        # Deduct marriage cost from proposer
        success = await UserRepository.remove_money(user1_id, MarryHandler.MARRIAGE_COST)
        if not success:
            await query.edit_message_text(
                "❌ The marriage failed because the proposer doesn't have enough money."
            )
            return
        
        # Update both users as married
        db.users.update_one(
            {"user_id": user1_id},
            {"$set": {"partner": user2_id}}
        )
        db.users.update_one(
            {"user_id": user2_id},
            {"$set": {"partner": user1_id}}
        )
        
        # Log the marriage
        await LogRepository.log_action(
            user1_id, "married", {"partner": user2_id}
        )
        await LogRepository.log_action(
            user2_id, "married", {"partner": user1_id}
        )
        
        user1 = await UserRepository.get_user(user1_id)
        user2 = await UserRepository.get_user(user2_id)
        
        # Notify user1
        try:
            await context.bot.send_message(
                chat_id=user1_id,
                text=(
                    f"🎉 *Marriage Successful!*\n\n"
                    f"💍 You are now married to {user2['name']} (@{user2['username']})!\n\n"
                    f"Congratulations on your wedding! 🥂🎊"
                ),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error notifying user1: {e}")
        
        # Update user2's message
        await query.edit_message_text(
            f"🎉 *Marriage Accepted!*\n\n"
            f"💍 You are now married to {user1['name']} (@{user1['username']})!\n\n"
            f"Congratulations on your wedding! 🥂🎊",
            parse_mode='Markdown'
        )
    
    @staticmethod
    async def _decline_marriage(context, proposer_id: int, partner_id: int, query) -> None:
        """Process declined marriage."""
        proposer = await UserRepository.get_user(proposer_id)
        
        # Notify proposer
        try:
            await context.bot.send_message(
                chat_id=proposer_id,
                text=(
                    f"❌ *Marriage Declined*\n\n"
                    f"{query.from_user.first_name} has declined your marriage proposal."
                ),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error notifying proposer: {e}")
        
        # Update partner's message
        await query.edit_message_text(
            "❌ You have declined the marriage proposal.",
            parse_mode='Markdown'
        )
