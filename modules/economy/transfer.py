"""
Telegram RPG Bot - Transfer Module
=================================
Handles the /transfer command for bank transfers.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from database import db, UserRepository, LogRepository
from utils.helpers import format_money
from utils.validators import UserValidator, validate_amount

logger = logging.getLogger(__name__)


class TransferHandler:
    """Handles transfer command for bank transfers."""
    
    TRANSFER_FEE = 0.02  # 2% fee
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /transfer command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        user = await UserRepository.get_user(user_id)
        
        # Check arguments
        if len(context.args) < 2:
            await update.message.reply_text(
                f"🏦 *Bank Transfer*\n\n"
                f"Transfer money from your bank to another user's bank.\n"
                f"Fee: {TransferHandler.TRANSFER_FEE * 100}%\n\n"
                f"Usage: `/transfer <user_id> <amount>`\n\n"
                f"Your bank: {format_money(user['bank'])}",
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
        
        # Check not transferring to self
        if user_id == target_id:
            await update.message.reply_text("❌ You can't transfer to yourself!")
            return
        
        # Check target exists
        target = await UserRepository.get_user(target_id)
        if not target:
            await update.message.reply_text("❌ User not found!")
            return
        
        # Check has enough bank money
        fee = int(amount * TransferHandler.TRANSFER_FEE)
        total_needed = amount + fee
        
        if user["bank"] < total_needed:
            await update.message.reply_text(
                f"❌ Insufficient bank funds!\n"
                f"Amount: {format_money(amount)}\n"
                f"Fee: {format_money(fee)}\n"
                f"Total needed: {format_money(total_needed)}\n"
                f"Your bank: {format_money(user['bank'])}"
            )
            return
        
        # Process transfer
        db.users.update_one(
            {"user_id": user_id},
            {"$inc": {"bank": -total_needed}}
        )
        db.users.update_one(
            {"user_id": target_id},
            {"$inc": {"bank": amount}}
        )
        
        # Log the transfer
        await LogRepository.log_action(
            user_id, "transferred", {"recipient": target_id, "amount": amount, "fee": fee}
        )
        await LogRepository.log_action(
            target_id, "received_transfer", {"sender": user_id, "amount": amount}
        )
        
        # Notify sender
        await update.message.reply_text(
            f"🏦 *Transfer Successful!*\n\n"
            f"To: {target['name']} (@{target['username']})\n"
            f"Amount: {format_money(amount)}\n"
            f"Fee: {format_money(fee)}\n"
            f"New bank balance: {format_money(user['bank'] - total_needed)}",
            parse_mode='Markdown'
        )
        
        # Notify recipient
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text=(
                    f"🏦 *Bank Transfer Received!*\n\n"
                    f"From: {user['name']} (@{user['username']})\n"
                    f"Amount: {format_money(amount)}\n"
                    f"New bank balance: {format_money(target['bank'] + amount)}"
                ),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error notifying recipient: {e}")
