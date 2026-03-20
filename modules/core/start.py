"""
Telegram RPG Bot - Start Module
==============================
Handles the /start command and user registration.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import UserRepository
from utils.helpers import format_money, get_level_emoji
from config import game_config

logger = logging.getLogger(__name__)


class StartHandler:
    """Handles start command and user registration."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        user = update.effective_user
        chat = update.effective_chat
        
        # Check if user exists
        existing_user = await UserRepository.get_user(user.id)
        
        if existing_user:
            # Welcome back message
            welcome_text = (
                f"👋 Welcome back, {user.first_name}!\n\n"
                f"{get_level_emoji(existing_user['level'])} Level: {existing_user['level']}\n"
                f"💰 Money: {format_money(existing_user['money'])}\n"
                f"🏦 Bank: {format_money(existing_user['bank'])}\n"
                f"⭐ Reputation: {existing_user['reputation']}\n\n"
                f"Use /help to see available commands!"
            )
        else:
            # Create new user
            new_user = await UserRepository.create_user(
                user_id=user.id,
                username=user.username or f"user_{user.id}",
                name=user.first_name or "Unknown"
            )
            
            welcome_text = (
                f"🎉 Welcome to the RPG Bot, {user.first_name}!\n\n"
                f"✨ Your adventure begins now!\n\n"
                f"💰 Starting Money: {format_money(game_config.STARTING_MONEY)}\n"
                f"⭐ Starting Reputation: {game_config.STARTING_REPUTATION}\n"
                f"📊 Starting Level: {game_config.STARTING_LEVEL}\n\n"
                f"🎮 What would you like to do?\n"
                f"• Build your family with /family\n"
                f"• Make friends with /friend\n"
                f"• Claim daily reward with /daily\n"
                f"• View all commands with /help"
            )
            
            logger.info(f"New user registered: {user.id} ({user.username})")
        
        # Create welcome keyboard
        keyboard = [
            [
                InlineKeyboardButton("📋 Profile", callback_data="profile_view"),
                InlineKeyboardButton("👨‍👩‍👧‍👦 Family", callback_data="family_view")
            ],
            [
                InlineKeyboardButton("💰 Daily Reward", callback_data="daily_claim"),
                InlineKeyboardButton("❓ Help", callback_data="help_main")
            ],
            [
                InlineKeyboardButton("🎮 Games", callback_data="help_games"),
                InlineKeyboardButton("🏪 Shop", callback_data="shop_view")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    
    @staticmethod
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle start-related callbacks."""
        query = update.callback_query
        await query.answer()
        
        if query.data == "start_menu":
            await StartHandler.handle(update, context)
