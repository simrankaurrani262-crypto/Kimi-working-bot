"""
Telegram RPG Bot - Adopt Module
==============================
Handles the /adopt command for adopting children.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db, UserRepository, LogRepository
from utils.validators import validate_adoption_eligibility, UserValidator
from utils.helpers import format_money

logger = logging.getLogger(__name__)


class AdoptHandler:
    """Handles adopt command for adopting children."""
    
    ADOPTION_COST = 500
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /adopt command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            await validator.check_money(AdoptHandler.ADOPTION_COST)
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        
        # Check for target user
        if not context.args:
            await update.message.reply_text(
                "👶 *Adopt a Child*\n\n"
                f"Cost: {format_money(AdoptHandler.ADOPTION_COST)}\n\n"
                "Usage: `/adopt @username` or `/adopt <user_id>`\n\n"
                "You can adopt up to 10 children!",
                parse_mode='Markdown'
            )
            return
        
        target = context.args[0]
        
        # Parse target user ID
        try:
            if target.startswith('@'):
                # Need to resolve username - for now, require ID
                await update.message.reply_text(
                    "❌ Please use the user's ID instead of username.\n"
                    "The user can find their ID with /profile"
                )
                return
            else:
                child_id = int(target)
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!")
            return
        
        # Validate adoption
        valid, error = await validate_adoption_eligibility(user_id, child_id)
        if not valid:
            await update.message.reply_text(f"❌ {error}")
            return
        
        user = await UserRepository.get_user(user_id)
        child = await UserRepository.get_user(child_id)
        
        # Check if user already has 10 children
        if len(user.get("children", [])) >= 10:
            await update.message.reply_text(
                "❌ You already have 10 children! That's the maximum limit."
            )
            return
        
        # Send adoption request
        keyboard = [
            [
                InlineKeyboardButton("✅ Accept", callback_data=f"adopt_accept_{user_id}"),
                InlineKeyboardButton("❌ Decline", callback_data=f"adopt_decline_{user_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await context.bot.send_message(
                chat_id=child_id,
                text=(
                    f"👶 *Adoption Request*\n\n"
                    f"{user['name']} (@{user['username']}) wants to adopt you!\n\n"
                    f"They are level {user['level']} with {format_money(user['money'])}.\n\n"
                    f"Do you accept?"
                ),
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
            await update.message.reply_text(
                f"📨 Adoption request sent to {child['name']}!\n"
                f"They need to accept your request."
            )
            
        except Exception as e:
            logger.error(f"Error sending adoption request: {e}")
            await update.message.reply_text(
                "❌ Could not send adoption request. The user may have blocked the bot."
            )
    
    @staticmethod
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle adoption callbacks."""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        child_id = query.from_user.id
        
        if data.startswith("adopt_accept_"):
            parent_id = int(data.replace("adopt_accept_", ""))
            await AdoptHandler._process_adoption(context, parent_id, child_id, query)
        elif data.startswith("adopt_decline_"):
            parent_id = int(data.replace("adopt_decline_", ""))
            await AdoptHandler._decline_adoption(context, parent_id, child_id, query)
    
    @staticmethod
    async def _process_adoption(context, parent_id: int, child_id: int, query) -> None:
        """Process accepted adoption."""
        # Deduct adoption cost
        success = await UserRepository.remove_money(parent_id, AdoptHandler.ADOPTION_COST)
        if not success:
            await query.edit_message_text(
                "❌ The adoption failed because the parent doesn't have enough money."
            )
            return
        
        # Update parent's children list
        db.users.update_one(
            {"user_id": parent_id},
            {"$addToSet": {"children": child_id}}
        )
        
        # Update child's parents list
        db.users.update_one(
            {"user_id": child_id},
            {"$addToSet": {"parents": parent_id}}
        )
        
        # Log the adoption
        await LogRepository.log_action(
            parent_id, "adopted", {"child": child_id}
        )
        await LogRepository.log_action(
            child_id, "adopted_by", {"parent": parent_id}
        )
        
        parent = await UserRepository.get_user(parent_id)
        child = await UserRepository.get_user(child_id)
        
        # Notify parent
        try:
            await context.bot.send_message(
                chat_id=parent_id,
                text=(
                    f"🎉 *Adoption Successful!*\n\n"
                    f"You have adopted {child['name']} (@{child['username']})!\n\n"
                    f"Welcome to the family! 👶"
                ),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error notifying parent: {e}")
        
        # Update child's message
        await query.edit_message_text(
            f"🎉 *Adoption Accepted!*\n\n"
            f"You are now the child of {parent['name']} (@{parent['username']})!\n\n"
            f"Welcome to your new family! 👶",
            parse_mode='Markdown'
        )
    
    @staticmethod
    async def _decline_adoption(context, parent_id: int, child_id: int, query) -> None:
        """Process declined adoption."""
        parent = await UserRepository.get_user(parent_id)
        
        # Notify parent
        try:
            await context.bot.send_message(
                chat_id=parent_id,
                text=(
                    f"❌ *Adoption Declined*\n\n"
                    f"{query.from_user.first_name} has declined your adoption request."
                ),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error notifying parent: {e}")
        
        # Update child's message
        await query.edit_message_text(
            "❌ You have declined the adoption request.",
            parse_mode='Markdown'
        )
