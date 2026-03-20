"""
Telegram RPG Bot - Balance Module
================================
Handles the /balance command for checking balance.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db, UserRepository
from utils.helpers import format_money
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class BalanceHandler:
    """Handles balance command for checking balance."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /balance command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        user = await UserRepository.get_user(user_id)
        
        total = user["money"] + user["bank"]
        
        text = (
            f"💰 *Your Balance*\n"
            f"{'─' * 25}\n\n"
            f"💵 *Wallet:* {format_money(user['money'])}\n"
            f"🏦 *Bank:* {format_money(user['bank'])}\n"
            f"{'─' * 25}\n"
            f"💎 *Total:* {format_money(total)}\n\n"
        )
        
        # Add economy stats
        economy = db.economy.find_one({"user_id": user_id}) or {}
        if economy:
            text += (
                f"📊 *Statistics:*\n"
                f"   Total Earned: {format_money(economy.get('total_earned', 0))}\n"
                f"   Total Spent: {format_money(economy.get('total_spent', 0))}\n"
            )
        
        keyboard = [
            [
                InlineKeyboardButton("💰 Deposit", callback_data="account_deposit"),
                InlineKeyboardButton("💸 Withdraw", callback_data="account_withdraw")
            ],
            [
                InlineKeyboardButton("💳 Pay", callback_data="account_pay"),
                InlineKeyboardButton("🏦 Account", callback_data="account_view")
            ]
        ]
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
