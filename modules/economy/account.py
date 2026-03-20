"""
Telegram RPG Bot - Account Module
================================
Handles the /account command for bank account info.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db, UserRepository
from utils.helpers import format_money
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class AccountHandler:
    """Handles account command for bank account info."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /account command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        user = await UserRepository.get_user(user_id)
        
        # Get economy data
        economy = db.economy.find_one({"user_id": user_id}) or {}
        
        # Calculate totals
        total_money = user["money"] + user["bank"]
        wallet_percent = (user["money"] / total_money * 100) if total_money > 0 else 0
        bank_percent = (user["bank"] / total_money * 100) if total_money > 0 else 0
        
        account_text = (
            f"🏦 *Bank Account*\n"
            f"{'─' * 30}\n\n"
            f"👤 *Account Holder:* {user['name']}\n"
            f"🆔 *Account ID:* `{user_id}`\n\n"
            f"💰 *Wallet Balance:*\n"
            f"   {format_money(user['money'])} ({wallet_percent:.1f}%)\n\n"
            f"🏦 *Bank Balance:*\n"
            f"   {format_money(user['bank'])} ({bank_percent:.1f}%)\n\n"
            f"💵 *Total Assets:*\n"
            f"   {format_money(total_money)}\n\n"
        )
        
        # Add economy stats if available
        if economy:
            account_text += (
                f"📊 *Statistics:*\n"
                f"   Total Earned: {format_money(economy.get('total_earned', 0))}\n"
                f"   Total Spent: {format_money(economy.get('total_spent', 0))}\n"
                f"   Net Worth: {format_money(economy.get('total_earned', 0) - economy.get('total_spent', 0))}\n"
            )
        
        keyboard = [
            [
                InlineKeyboardButton("💰 Deposit", callback_data="account_deposit"),
                InlineKeyboardButton("💸 Withdraw", callback_data="account_withdraw")
            ],
            [
                InlineKeyboardButton("💳 Pay", callback_data="account_pay"),
                InlineKeyboardButton("📊 Balance", callback_data="balance_view")
            ],
            [
                InlineKeyboardButton("🏦 Bank", callback_data="bank_view"),
                InlineKeyboardButton("💰 Daily", callback_data="daily_claim")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            account_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
