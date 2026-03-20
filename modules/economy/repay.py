"""
Telegram RPG Bot - Repay Module
==============================
Handles the /repay command for repaying loans.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from database import db, UserRepository, LogRepository
from utils.helpers import format_money
from utils.validators import UserValidator, validate_amount

logger = logging.getLogger(__name__)


class RepayHandler:
    """Handles repay command for repaying loans."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /repay command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        user = await UserRepository.get_user(user_id)
        
        # Get loan info
        economy = db.economy.find_one({"user_id": user_id}) or {}
        loan_amount = economy.get("loan_amount", 0)
        
        if loan_amount <= 0:
            await update.message.reply_text(
                "✅ You don't have any active loans!\n\n"
                "Use `/loan <amount>` if you need to borrow money."
            )
            return
        
        # Check arguments
        if not context.args:
            due_date = economy.get("loan_due_date")
            due_text = due_date.strftime('%Y-%m-%d') if due_date else "Unknown"
            
            await update.message.reply_text(
                f"🏦 *Loan Repayment*\n\n"
                f"Amount owed: {format_money(loan_amount)}\n"
                f"Due date: {due_text}\n\n"
                f"Usage: `/repay <amount>` or `/repay all`\n\n"
                f"Your balance: {format_money(user['money'])}",
                parse_mode='Markdown'
            )
            return
        
        # Parse amount
        amount_str = context.args[0].lower()
        
        if amount_str == "all":
            repay_amount = min(loan_amount, user["money"])
        else:
            repay_amount, error = validate_amount(amount_str, min_amount=1)
            if error:
                await update.message.reply_text(f"❌ {error}")
                return
        
        if repay_amount <= 0:
            await update.message.reply_text("❌ Invalid amount!")
            return
        
        if repay_amount > user["money"]:
            await update.message.reply_text(
                f"❌ Insufficient funds!\n"
                f"You have {format_money(user['money'])}"
            )
            return
        
        # Process repayment
        await UserRepository.remove_money(user_id, repay_amount)
        
        new_loan_amount = max(0, loan_amount - repay_amount)
        db.economy.update_one(
            {"user_id": user_id},
            {"$set": {"loan_amount": new_loan_amount}}
        )
        
        # Log the repayment
        await LogRepository.log_action(
            user_id, "loan_repaid", {"amount": repay_amount, "remaining": new_loan_amount}
        )
        
        if new_loan_amount <= 0:
            await update.message.reply_text(
                f"🎉 *Loan Fully Repaid!*\n\n"
                f"You repaid: {format_money(repay_amount)}\n"
                f"Your loan is now fully paid off!\n\n"
                f"New balance: {format_money(user['money'] - repay_amount)}",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"✅ *Payment Received!*\n\n"
                f"Paid: {format_money(repay_amount)}\n"
                f"Remaining: {format_money(new_loan_amount)}\n\n"
                f"New balance: {format_money(user['money'] - repay_amount)}",
                parse_mode='Markdown'
            )
