"""
Telegram RPG Bot - FamilyBoard Module
====================================
Handles the /familyboard command for viewing top families.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db, FamilyRepository, UserRepository
from utils.helpers import format_money
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class FamilyBoardHandler:
    """Handles familyboard command for viewing top families."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /familyboard command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        # Get top families
        top_families = await FamilyRepository.get_family_leaderboard(limit=10)
        
        text = "👨‍👩‍👧‍👦 *Top Families*\n\n"
        
        for i, family in enumerate(top_families, 1):
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
            creator = await UserRepository.get_user(family['creator_id'])
            creator_name = creator['name'] if creator else "Unknown"
            
            text += (
                f"{medal} *{family['name']}*\n"
                f"   👑 Leader: {creator_name}\n"
                f"   👥 Members: {len(family.get('members', []))}\n"
                f"   💰 Wealth: {format_money(family.get('total_wealth', 0))}\n"
                f"   ⭐ Reputation: {family.get('reputation', 0)}\n\n"
            )
        
        keyboard = [
            [
                InlineKeyboardButton("🏆 Level Board", callback_data="leaderboard_view"),
                InlineKeyboardButton("💰 Money Board", callback_data="moneyboard_view")
            ],
            [
                InlineKeyboardButton("🏭 Factory Board", callback_data="factoryboard_view"),
                InlineKeyboardButton("👨‍👩‍👧‍👦 My Family", callback_data="family_view")
            ]
        ]
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
