"""
Telegram RPG Bot - Withdraw Module
=================================
Handles the /withdraw command for withdrawing from bank.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from database import db, UserRepository, LogRepository
from utils.helpers import format_money
from utils.validators import UserValidator, validate_amount

logger = logging.getLogger(__name__)


class WithdrawHandler:
    """Handles withdraw command for withdrawing from bank."""
    
    WITHDRAWAL_FEE = 0.01  # 1% fee
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /withdraw command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        user = await UserRepository.get_user(user_id)
        
        # Check arguments
        if not context.args:
            await update.message.reply_text(
                f"💸 *Withdraw from Bank*\n\n"
                f"Current wallet: {format_money(user['money'])}\n"
                f"Current bank: {format_money(user['bank'])}\n\n"
                f"Withdrawal fee: {WithdrawHandler.WITHDRAWAL_FEE * 100}%\n\n"
                f"Usage: `/withdraw <amount>` or `/withdraw all`",
                parse_mode='Markdown'
            )
            return
        
        # Parse amount
        amount_str = context.args[0].lower()
        
        if amount_str == "all":
            amount = user["bank"]
        else:
            amount, error = validate_amount(amount_str, min_amount=1, max_amount=user["bank"])
            if error:
                await update.message.reply_text(f"❌ {error}")
                return
        
        if amount <= 0:
            await update.message.reply_text("❌ Invalid amount!")
            return
        
        if amount > user["bank"]:
            await update.message.reply_text(
                f"❌ Insufficient bank funds!\n"
                f"You have {format_money(user['bank'])} in bank"
            )
            return
        
        # Calculate fee
        fee = int(amount * WithdrawHandler.WITHDRAWAL_FEE)
        net_amount = amount - fee
        
        # Process withdrawal
        db.users.update_one(
            {"user_id": user_id},
            {
                "$inc": {"money": net_amount, "bank": -amount}
            }
        )
        
        # Log the withdrawal
        await LogRepository.log_action(
            user_id, "withdrawn", {"amount": amount, "fee": fee}
        )
        
        await update.message.reply_text(
            f"💸 *Withdrawal Successful*\n\n"
            f"Withdrawn: {format_money(amount)}\n"
            f"Fee: {format_money(fee)}\n"
            f"Net amount: {format_money(net_amount)}\n\n"
            f"New wallet: {format_money(user['money'] + net_amount)}\n"
            f"New bank: {format_money(user['bank'] - amount)}",
            parse_mode='Markdown'
        )
