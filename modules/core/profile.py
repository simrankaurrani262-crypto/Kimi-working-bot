"""
Telegram RPG Bot - Profile Module
================================
Handles the /profile command and profile viewing.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db, UserRepository
from utils.helpers import format_money, get_level_emoji, get_reputation_emoji, create_progress_bar
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class ProfileHandler:
    """Handles profile command and user profile viewing."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /profile command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        
        # Check if viewing another user's profile
        if context.args:
            try:
                target_id = int(context.args[0])
                target_user = await UserRepository.get_user(target_id)
                if target_user:
                    await ProfileHandler._show_profile(update, target_user, is_own=False)
                    return
                else:
                    await update.message.reply_text("❌ User not found!")
                    return
            except ValueError:
                await update.message.reply_text("❌ Invalid user ID!")
                return
        
        # Show own profile
        user = await UserRepository.get_user(user_id)
        await ProfileHandler._show_profile(update, user, is_own=True)
    
    @staticmethod
    async def _show_profile(update: Update, user: dict, is_own: bool = True) -> None:
        """Display user profile."""
        user_id = user["user_id"]
        
        # Get additional stats
        stats = db.stats.find_one({"user_id": user_id}) or {}
        
        # Calculate XP progress
        xp_needed = int(1000 * (1.5 ** (user["level"] - 1)))
        xp_progress = create_progress_bar(user["experience"], xp_needed, 15)
        
        # Get family info
        family_info = ""
        if user.get("partner"):
            partner = await UserRepository.get_user(user["partner"])
            if partner:
                family_info += f"💍 Partner: {partner['name']}\n"
        
        if user.get("parents"):
            family_info += f"👨‍👩 Parents: {len(user['parents'])}\n"
        
        if user.get("children"):
            family_info += f"👶 Children: {len(user['children'])}\n"
        
        # Get job info
        job_info = user.get("job", "Unemployed")
        
        # Build profile text
        profile_text = (
            f"{'👤' if is_own else '👥'} *{'Your' if is_own else user['name'] + '''s'} Profile*\n"
            f"{'─' * 30}\n\n"
            f"📛 *Name:* {user['name']}\n"
            f"🔤 *Username:* @{user['username']}\n"
            f"🆔 *ID:* `{user_id}`\n\n"
            f"{get_level_emoji(user['level'])} *Level:* {user['level']}\n"
            f"📊 *XP:* {user['experience']:,} / {xp_needed:,}\n"
            f"`{xp_progress}`\n\n"
            f"💰 *Money:* {format_money(user['money'])}\n"
            f"🏦 *Bank:* {format_money(user['bank'])}\n"
            f"💵 *Total:* {format_money(user['money'] + user['bank'])}\n\n"
            f"⭐ *Reputation:* {user['reputation']} {get_reputation_emoji(user['reputation'])}\n"
            f"💼 *Job:* {job_info}\n\n"
        )
        
        if family_info:
            profile_text += f"*Family:*\n{family_info}\n"
        
        # Add stats if available
        if stats:
            profile_text += (
                f"📈 *Statistics:*\n"
                f"🎮 Games Played: {stats.get('games_played', 0)}\n"
                f"🏆 Games Won: {stats.get('games_won', 0)}\n"
                f"💀 Times Robbed: {stats.get('times_robbed', 0)}\n"
                f"⚔️ Attacks Made: {stats.get('attacks_made', 0)}\n"
            )
        
        # Create action buttons
        keyboard = []
        if is_own:
            keyboard = [
                [
                    InlineKeyboardButton("📊 Stats", callback_data="stats_view"),
                    InlineKeyboardButton("👨‍👩‍👧‍👦 Family", callback_data="family_view")
                ],
                [
                    InlineKeyboardButton("💰 Economy", callback_data="economy_view"),
                    InlineKeyboardButton("🎒 Inventory", callback_data="inventory_view")
                ],
                [
                    InlineKeyboardButton("⚙️ Settings", callback_data="settings_view")
                ]
            ]
        else:
            keyboard = [
                [
                    InlineKeyboardButton("➕ Add Friend", callback_data=f"friend_add_{user_id}"),
                    InlineKeyboardButton("💰 Pay", callback_data=f"pay_{user_id}")
                ],
                [
                    InlineKeyboardButton("👨‍👩‍👧‍👦 View Family", callback_data=f"family_view_{user_id}")
                ]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        
        await update.message.reply_text(
            profile_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
