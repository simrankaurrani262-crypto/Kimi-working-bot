"""
Telegram RPG Bot - Leaderboard Module
====================================
Handles the /leaderboard command for viewing top players.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db, UserRepository
from utils.helpers import format_money, get_level_emoji
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class LeaderboardHandler:
    """Handles leaderboard command for viewing top players."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /leaderboard command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        # Get top players by level
        top_players = await UserRepository.get_leaderboard(limit=10, sort_by="level")
        
        text = "🏆 *Top Players by Level*\n\n"
        
        for i, player in enumerate(top_players, 1):
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
            text += (
                f"{medal} {player['name']} (@{player['username']})\n"
                f"   {get_level_emoji(player['level'])} Level {player['level']}\n"
                f"   💰 {format_money(player['money'])}\n\n"
            )
        
        keyboard = [
            [
                InlineKeyboardButton("💰 Money Board", callback_data="moneyboard_view"),
                InlineKeyboardButton("👨‍👩‍👧‍👦 Family Board", callback_data="familyboard_view")
            ],
            [
                InlineKeyboardButton("🏭 Factory Board", callback_data="factoryboard_view"),
                InlineKeyboardButton("📊 My Stats", callback_data="stats_view")
            ]
        ]
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
