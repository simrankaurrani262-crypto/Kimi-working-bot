"""
Telegram RPG Bot - Deposit Module
================================
Handles the /deposit command for depositing to bank.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from database import db, UserRepository, LogRepository
from utils.helpers import format_money
from utils.validators import UserValidator, validate_amount

logger = logging.getLogger(__name__)


class DepositHandler:
    """Handles deposit command for depositing to bank."""
    
    BANK_INTEREST_RATE = 0.02  # 2% interest
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /deposit command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        user = await UserRepository.get_user(user_id)
        
        # Check arguments
        if not context.args:
            await update.message.reply_text(
                f"🏦 *Deposit to Bank*\n\n"
                f"Current wallet: {format_money(user['money'])}\n"
                f"Current bank: {format_money(user['bank'])}\n\n"
                f"Bank interest rate: {DepositHandler.BANK_INTEREST_RATE * 100}%\n\n"
                f"Usage: `/deposit <amount>` or `/deposit all`",
                parse_mode='Markdown'
            )
            return
        
        # Parse amount
        amount_str = context.args[0].lower()
        
        if amount_str == "all":
            amount = user["money"]
        else:
            amount, error = validate_amount(amount_str, min_amount=1, max_amount=user["money"])
            if error:
                await update.message.reply_text(f"❌ {error}")
                return
        
        if amount <= 0:
            await update.message.reply_text("❌ Invalid amount!")
            return
        
        if amount > user["money"]:
            await update.message.reply_text(
                f"❌ Insufficient funds!\n"
                f"You have {format_money(user['money'])}"
            )
            return
        
        # Process deposit
        db.users.update_one(
            {"user_id": user_id},
            {
                "$inc": {"money": -amount, "bank": amount}
            }
        )
        
        # Log the deposit
        await LogRepository.log_action(
            user_id, "deposited", {"amount": amount}
        )
        
        # Calculate potential interest
        interest = int(amount * DepositHandler.BANK_INTEREST_RATE)
        
        await update.message.reply_text(
            f"🏦 *Deposit Successful*\n\n"
            f"Deposited: {format_money(amount)}\n"
            f"Potential daily interest: {format_money(interest)}\n\n"
            f"New wallet: {format_money(user['money'] - amount)}\n"
            f"New bank: {format_money(user['bank'] + amount)}",
            parse_mode='Markdown'
        )
