"""
Telegram RPG Bot - Factory Module
================================
Handles the /factory command for factory management.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db, UserRepository
from utils.helpers import format_money
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class FactoryHandler:
    """Handles factory command for factory management."""
    
    FACTORY_COST = 5000
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /factory command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        user = await UserRepository.get_user(user_id)
        
        # Check if user has a factory
        factory = db.factory.find_one({"user_id": user_id})
        
        if not factory:
            # Offer to create factory
            text = (
                f"🏭 *Factory*\n\n"
                f"You don't own a factory yet!\n\n"
                f"Cost: {format_money(FactoryHandler.FACTORY_COST)}\n\n"
                f"Benefits:\n"
                f"• Generate passive income\n"
                f"• Hire workers for more production\n"
                f"• Upgrade for better efficiency\n"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton(
                        f"🏭 Buy Factory ({format_money(FactoryHandler.FACTORY_COST)})",
                        callback_data="factory_buy"
                    )
                ],
                [
                    InlineKeyboardButton("⬅️ Back", callback_data="profile_view")
                ]
            ]
            
            await update.message.reply_text(
                text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        
        # Show factory info
        text = (
            f"🏭 *Your Factory*\n\n"
            f"Level: {factory.get('level', 1)}\n"
            f"Workers: {factory.get('workers', 0)}\n"
            f"Production: {format_money(factory.get('production', 100))}/hour\n"
            f"Total Produced: {format_money(factory.get('total_produced', 0))}\n"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("👷 Hire Workers", callback_data="factory_hire"),
                InlineKeyboardButton("🔥 Fire Workers", callback_data="factory_fire")
            ],
            [
                InlineKeyboardButton("📊 Production", callback_data="factory_production"),
                InlineKeyboardButton("⬆️ Upgrade", callback_data="factory_upgrade")
            ],
            [
                InlineKeyboardButton("⬅️ Back", callback_data="profile_view")
            ]
        ]
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    @staticmethod
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle factory callbacks."""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        if query.data == "factory_buy":
            user = await UserRepository.get_user(user_id)
            
            if user["money"] < FactoryHandler.FACTORY_COST:
                await query.edit_message_text("❌ Insufficient funds!")
                return
            
            # Check if already has factory
            existing = db.factory.find_one({"user_id": user_id})
            if existing:
                await query.edit_message_text("❌ You already own a factory!")
                return
            
            # Create factory
            await UserRepository.remove_money(user_id, FactoryHandler.FACTORY_COST)
            db.factory.insert_one({
                "user_id": user_id,
                "level": 1,
                "workers": 0,
                "production": 100,
                "total_produced": 0,
                "created_at": db.get_timestamp()
            })
            
            await query.edit_message_text(
                f"🏭 *Factory Purchased!*\n\n"
                f"You now own a level 1 factory!\n"
                f"Use `/factory` to manage it."
            )
