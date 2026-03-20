"""
Telegram RPG Bot - MoneyBoard Module
===================================
Handles the /moneyboard command for viewing richest players.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db, UserRepository
from utils.helpers import format_money, get_level_emoji
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class MoneyBoardHandler:
    """Handles moneyboard command for viewing richest players."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /moneyboard command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        # Get top players by money
        top_players = await UserRepository.get_leaderboard(limit=10, sort_by="money")
        
        text = "💰 *Richest Players*\n\n"
        
        for i, player in enumerate(top_players, 1):
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
            text += (
                f"{medal} {player['name']} (@{player['username']})\n"
                f"   💰 {format_money(player['money'])}\n"
                f"   {get_level_emoji(player['level'])} Level {player['level']}\n\n"
            )
        
        keyboard = [
            [
                InlineKeyboardButton("🏆 Level Board", callback_data="leaderboard_view"),
                InlineKeyboardButton("👨‍👩‍👧‍👦 Family Board", callback_data="familyboard_view")
            ],
            [
                InlineKeyboardButton("📈 Money Graph", callback_data="moneygraph_view"),
                InlineKeyboardButton("📊 My Stats", callback_data="stats_view")
            ]
        ]
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
