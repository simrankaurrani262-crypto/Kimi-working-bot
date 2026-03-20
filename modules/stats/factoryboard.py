"""
Telegram RPG Bot - FactoryBoard Module
=====================================
Handles the /factoryboard command for viewing top factories.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db, UserRepository
from utils.helpers import format_money
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class FactoryBoardHandler:
    """Handles factoryboard command for viewing top factories."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /factoryboard command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        # Get top factories
        top_factories = list(db.factory.find().sort("total_produced", -1).limit(10))
        
        text = "🏭 *Top Factories*\n\n"
        
        for i, factory in enumerate(top_factories, 1):
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
            owner = await UserRepository.get_user(factory['user_id'])
            owner_name = owner['name'] if owner else "Unknown"
            
            text += (
                f"{medal} *{owner_name}'s Factory*\n"
                f"   ⬆️ Level: {factory.get('level', 1)}\n"
                f"   👷 Workers: {factory.get('workers', 0)}\n"
                f"   📊 Production: {format_money(factory.get('production', 0))}/hour\n"
                f"   💰 Total Produced: {format_money(factory.get('total_produced', 0))}\n\n"
            )
        
        keyboard = [
            [
                InlineKeyboardButton("🏆 Level Board", callback_data="leaderboard_view"),
                InlineKeyboardButton("💰 Money Board", callback_data="moneyboard_view")
            ],
            [
                InlineKeyboardButton("👨‍👩‍👧‍👦 Family Board", callback_data="familyboard_view"),
                InlineKeyboardButton("🏭 My Factory", callback_data="factory_view")
            ]
        ]
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
