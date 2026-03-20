"""
Telegram RPG Bot - Pay Module
============================
Handles the /pay command for paying other users.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from database import db, UserRepository, LogRepository
from utils.helpers import format_money
from utils.validators import UserValidator, validate_amount

logger = logging.getLogger(__name__)


class PayHandler:
    """Handles pay command for paying other users."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /pay command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        
        # Check arguments
        if len(context.args) < 2:
            await update.message.reply_text(
                "💳 *Pay Someone*\n\n"
                "Usage: `/pay <user_id> <amount>`\n\n"
                "Example: `/pay 123456789 1000`",
                parse_mode='Markdown'
            )
            return
        
        # Parse target
        try:
            target_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!")
            return
        
        # Parse amount
        amount, error = validate_amount(context.args[1], min_amount=1)
        if error:
            await update.message.reply_text(f"❌ {error}")
            return
        
        # Check not paying self
        if user_id == target_id:
            await update.message.reply_text("❌ You can't pay yourself!")
            return
        
        # Check target exists
        target = await UserRepository.get_user(target_id)
        if not target:
            await update.message.reply_text("❌ User not found!")
            return
        
        # Check has enough money
        valid, error = await UserValidator.check_money(user_id, amount)
        if not valid:
            await update.message.reply_text(f"❌ {error}")
            return
        
        # Process payment
        await UserRepository.remove_money(user_id, amount)
        await UserRepository.add_money(target_id, amount)
        
        # Log the payment
        user = await UserRepository.get_user(user_id)
        await LogRepository.log_action(
            user_id, "money_sent", {"recipient": target_id, "amount": amount}
        )
        await LogRepository.log_action(
            target_id, "money_received", {"sender": user_id, "amount": amount}
        )
        
        # Notify sender
        await update.message.reply_text(
            f"💳 *Payment Sent*\n\n"
            f"To: {target['name']} (@{target['username']})\n"
            f"Amount: {format_money(amount)}\n"
            f"Your new balance: {format_money(user['money'] - amount)}",
            parse_mode='Markdown'
        )
        
        # Notify recipient
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text=(
                    f"💰 *Payment Received*\n\n"
                    f"From: {user['name']} (@{user['username']})\n"
                    f"Amount: {format_money(amount)}\n"
                    f"Your new balance: {format_money(target['money'] + amount)}"
                ),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error notifying recipient: {e}")
