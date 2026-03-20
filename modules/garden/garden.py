"""
Telegram RPG Bot - Garden Module
===============================
Handles the /garden command for garden management.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db, UserRepository
from utils.helpers import format_money
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class GardenHandler:
    """Handles garden command for garden management."""
    
    GARDEN_COST = 1000
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /garden command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        
        # Check if user has a garden
        garden = db.gardens.find_one({"user_id": user_id})
        
        if not garden:
            # Offer to create garden
            text = (
                f"🌱 *Garden*\n\n"
                f"You don't have a garden yet!\n\n"
                f"Cost: {format_money(GardenHandler.GARDEN_COST)}\n\n"
                f"Benefits:\n"
                f"• Grow crops for profit\n"
                f"• Harvest and sell produce\n"
                f"• Complete orders for bonuses\n"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton(
                        f"🌱 Buy Garden ({format_money(GardenHandler.GARDEN_COST)})",
                        callback_data="garden_buy"
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
        
        # Show garden info
        plots = garden.get("plots", [])
        total_plots = len(plots)
        
        text = (
            f"🌱 *Your Garden*\n\n"
            f"Plots: {total_plots}\n\n"
        )
        
        # Show crops
        if plots:
            text += "*Your Crops:*\n"
            for plot in plots:
                crop = plot.get("crop", "Empty")
                status = plot.get("status", "empty")
                status_emoji = {"empty": "⚪", "growing": "🌱", "mature": "🌾"}.get(status, "⚪")
                text += f"{status_emoji} {crop}\n"
        else:
            text += "Your garden is empty. Add plots with `/add`!\n"
        
        keyboard = [
            [
                InlineKeyboardButton("🌱 Plant", callback_data="garden_plant"),
                InlineKeyboardButton("🌾 Harvest", callback_data="garden_harvest")
            ],
            [
                InlineKeyboardButton("➕ Add Plot", callback_data="garden_add"),
                InlineKeyboardButton("🚜 Barn", callback_data="garden_barn")
            ],
            [
                InlineKeyboardButton("🌤️ Weather", callback_data="garden_weather")
            ]
        ]
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    @staticmethod
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle garden callbacks."""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        if query.data == "garden_buy":
            user = await UserRepository.get_user(user_id)
            
            if user["money"] < GardenHandler.GARDEN_COST:
                await query.edit_message_text("❌ Insufficient funds!")
                return
            
            # Check if already has garden
            existing = db.gardens.find_one({"user_id": user_id})
            if existing:
                await query.edit_message_text("❌ You already have a garden!")
                return
            
            # Create garden
            await UserRepository.remove_money(user_id, GardenHandler.GARDEN_COST)
            db.gardens.insert_one({
                "user_id": user_id,
                "plots": [],
                "barn": {},
                "created_at": db.get_timestamp()
            })
            
            await query.edit_message_text(
                f"🌱 *Garden Purchased!*\n\n"
                f"You now have a garden!\n"
                f"Use `/garden` to manage it."
            )
