"""
Telegram RPG Bot - Loan Module
=============================
Handles the /loan command for taking loans.
"""

import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes

from database import db, UserRepository, LogRepository
from utils.helpers import format_money
from utils.validators import UserValidator, validate_amount

logger = logging.getLogger(__name__)


class LoanHandler:
    """Handles loan command for taking loans."""
    
    MAX_LOAN = 10000
    INTEREST_RATE = 0.10  # 10% interest
    LOAN_DURATION_DAYS = 7
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /loan command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        user = await UserRepository.get_user(user_id)
        
        # Get existing loans
        existing_loans = list(db.economy.find({
            "user_id": user_id,
            "loan_amount": {"$gt": 0}
        }))
        
        total_owed = sum(loan.get("loan_amount", 0) for loan in existing_loans)
        
        # Check arguments
        if not context.args:
            text = (
                f"🏦 *Loan Center*\n\n"
                f"Maximum loan: {format_money(LoanHandler.MAX_LOAN)}\n"
                f"Interest rate: {LoanHandler.INTEREST_RATE * 100}%\n"
                f"Duration: {LoanHandler.LOAN_DURATION_DAYS} days\n\n"
            )
            
            if existing_loans:
                text += f"⚠️ *You have existing loans:*\n"
                text += f"   Total owed: {format_money(total_owed)}\n\n"
            
            text += (
                f"Usage: `/loan <amount>`\n\n"
                f"Example: `/loan 5000`"
            )
            
            await update.message.reply_text(text, parse_mode='Markdown')
            return
        
        # Parse amount
        amount, error = validate_amount(
            context.args[0],
            min_amount=100,
            max_amount=LoanHandler.MAX_LOAN
        )
        if error:
            await update.message.reply_text(f"❌ {error}")
            return
        
        # Check if already has max loans
        if total_owed + amount > LoanHandler.MAX_LOAN:
            await update.message.reply_text(
                f"❌ You can't borrow more than {format_money(LoanHandler.MAX_LOAN)} total!\n"
                f"Current debt: {format_money(total_owed)}\n"
                f"Requested: {format_money(amount)}"
            )
            return
        
        # Calculate total repayment
        interest = int(amount * LoanHandler.INTEREST_RATE)
        total_repayment = amount + interest
        due_date = datetime.utcnow() + timedelta(days=LoanHandler.LOAN_DURATION_DAYS)
        
        # Give loan
        await UserRepository.add_money(user_id, amount)
        
        # Record loan
        db.economy.update_one(
            {"user_id": user_id},
            {
                "$inc": {"loan_amount": total_repayment},
                "$set": {"loan_due_date": due_date}
            },
            upsert=True
        )
        
        # Log the loan
        await LogRepository.log_action(
            user_id, "loan_taken", {
                "amount": amount,
                "interest": interest,
                "total": total_repayment,
                "due_date": due_date
            }
        )
        
        await update.message.reply_text(
            f"🏦 *Loan Approved!*\n\n"
            f"Amount borrowed: {format_money(amount)}\n"
            f"Interest: {format_money(interest)}\n"
            f"Total to repay: {format_money(total_repayment)}\n"
            f"Due date: {due_date.strftime('%Y-%m-%d')}\n\n"
            f"Use `/repay <amount>` to repay your loan!",
            parse_mode='Markdown'
        )
