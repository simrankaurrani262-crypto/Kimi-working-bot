"""
Telegram RPG Bot - Bank Module
=============================
Handles the /bank command for bank operations.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db, UserRepository
from utils.helpers import format_money
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class BankHandler:
    """Handles bank command for bank operations."""
    
    INTEREST_RATE = 0.02  # 2% daily interest
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /bank command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        user = await UserRepository.get_user(user_id)
        
        # Calculate daily interest
        daily_interest = int(user["bank"] * BankHandler.INTEREST_RATE)
        
        text = (
            f"🏦 *Bank Operations*\n"
            f"{'─' * 25}\n\n"
            f"💰 *Your Balance:*\n"
            f"   Wallet: {format_money(user['money'])}\n"
            f"   Bank: {format_money(user['bank'])}\n\n"
            f"📊 *Bank Info:*\n"
            f"   Interest Rate: {BankHandler.INTEREST_RATE * 100}% daily\n"
            f"   Daily Interest: {format_money(daily_interest)}\n\n"
            f"*Available Operations:*"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("💰 Deposit", callback_data="bank_deposit"),
                InlineKeyboardButton("💸 Withdraw", callback_data="bank_withdraw")
            ],
            [
                InlineKeyboardButton("💳 Transfer", callback_data="bank_transfer"),
                InlineKeyboardButton("🏦 Account", callback_data="account_view")
            ],
            [
                InlineKeyboardButton("💵 Loan", callback_data="loan_view"),
                InlineKeyboardButton("💰 Repay", callback_data="repay_view")
            ]
        ]
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
