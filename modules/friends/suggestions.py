"""
Telegram RPG Bot - Suggestions Module
====================================
Handles the /suggestions command for friend suggestions.
"""

import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db, UserRepository
from utils.validators import UserValidator
from utils.helpers import format_money

logger = logging.getLogger(__name__)


class SuggestionsHandler:
    """Handles suggestions command for friend suggestions."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /suggestions command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        user = await UserRepository.get_user(user_id)
        
        # Get suggestions
        suggestions = await SuggestionsHandler._get_suggestions(user_id, user)
        
        if not suggestions:
            await update.message.reply_text(
                "🔍 *Friend Suggestions*\n\n"
                "No suggestions available right now.\n\n"
                "Try again later or invite friends to join!",
                parse_mode='Markdown'
            )
            return
        
        text = "🔍 *Friend Suggestions*\n\n"
        text += "People you might know:\n\n"
        
        keyboard = []
        
        for i, suggested_user in enumerate(suggestions[:5], 1):
            text += (
                f"{i}. *{suggested_user['name']}*\n"
                f"   Level: {suggested_user['level']}\n"
                f"   Money: {format_money(suggested_user['money'])}\n\n"
            )
            
            keyboard.append([
                InlineKeyboardButton(
                    f"➕ Add {suggested_user['name']}",
                    callback_data=f"friend_request_{suggested_user['user_id']}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("🔄 Refresh", callback_data="suggestions_refresh"),
            InlineKeyboardButton("⬅️ Back", callback_data="circle_view")
        ])
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    @staticmethod
    async def _get_suggestions(user_id: int, user: dict) -> list:
        """Get friend suggestions based on various factors."""
        suggestions = []
        existing_friends = set(user.get("friends", []))
        existing_friends.add(user_id)
        
        # 1. Suggest friends of friends
        for friend_id in user.get("friends", []):
            friend = await UserRepository.get_user(friend_id)
            if friend:
                for fof_id in friend.get("friends", []):
                    if fof_id not in existing_friends:
                        fof = await UserRepository.get_user(fof_id)
                        if fof:
                            suggestions.append(fof)
        
        # 2. Suggest users with similar level
        if len(suggestions) < 10:
            level_range = 3
            similar_users = list(db.users.find({
                "user_id": {"$nin": list(existing_friends)},
                "level": {"$gte": user["level"] - level_range, "$lte": user["level"] + level_range},
                "banned": False
            }).limit(10))
            
            for u in similar_users:
                if u not in suggestions:
                    suggestions.append(u)
        
        # 3. Suggest random active users
        if len(suggestions) < 10:
            random_users = list(db.users.aggregate([
                {"$match": {"user_id": {"$nin": list(existing_friends)}, "banned": False}},
                {"$sample": {"size": 10}}
            ]))
            
            for u in random_users:
                if u not in suggestions:
                    suggestions.append(u)
        
        # Shuffle and limit
        random.shuffle(suggestions)
        return suggestions[:10]
    
    @staticmethod
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle suggestions callbacks."""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "suggestions_view":
            await SuggestionsHandler._show_suggestions(query)
        elif data == "suggestions_refresh":
            await SuggestionsHandler._show_suggestions(query)
        elif data.startswith("friend_request_"):
            friend_id = int(data.replace("friend_request_", ""))
            await query.edit_message_text(
                f"➕ Use `/friend {friend_id}` to add this user!",
                parse_mode='Markdown'
            )
    
    @staticmethod
    async def _show_suggestions(query) -> None:
        """Show suggestions from callback."""
        user_id = query.from_user.id
        user = await UserRepository.get_user(user_id)
        
        suggestions = await SuggestionsHandler._get_suggestions(user_id, user)
        
        if not suggestions:
            await query.edit_message_text(
                "🔍 *Friend Suggestions*\n\n"
                "No suggestions available right now.\n\n"
                "Try again later or invite friends to join!",
                parse_mode='Markdown'
            )
            return
        
        text = "🔍 *Friend Suggestions*\n\n"
        text += "People you might know:\n\n"
        
        keyboard = []
        
        for i, suggested_user in enumerate(suggestions[:5], 1):
            text += (
                f"{i}. *{suggested_user['name']}*\n"
                f"   Level: {suggested_user['level']}\n"
                f"   Money: {format_money(suggested_user['money'])}\n\n"
            )
            
            keyboard.append([
                InlineKeyboardButton(
                    f"➕ Add {suggested_user['name']}",
                    callback_data=f"friend_request_{suggested_user['user_id']}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("🔄 Refresh", callback_data="suggestions_refresh"),
            InlineKeyboardButton("⬅️ Back", callback_data="circle_view")
        ])
        
        await query.edit_message_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
