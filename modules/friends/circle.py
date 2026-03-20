"""
Telegram RPG Bot - Circle Module
===============================
Handles the /friends and /circle commands.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db, UserRepository
from utils.validators import UserValidator
from utils.helpers import format_money

logger = logging.getLogger(__name__)


class CircleHandler:
    """Handles friends and circle commands."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /circle command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        user = await UserRepository.get_user(user_id)
        
        friends = user.get("friends", [])
        
        if not friends:
            await update.message.reply_text(
                "👥 *Your Friend Circle*\n\n"
                "You don't have any friends yet.\n\n"
                "Use `/friend @username` to add friends!",
                parse_mode='Markdown'
            )
            return
        
        # Get friend details
        friend_details = []
        for friend_id in friends:
            friend = await UserRepository.get_user(friend_id)
            if friend:
                friend_details.append(friend)
        
        # Sort by level
        friend_details.sort(key=lambda x: x['level'], reverse=True)
        
        text = f"👥 *Your Friend Circle* ({len(friends)} friends)\n\n"
        
        for i, friend in enumerate(friend_details[:10], 1):
            status = "🟢" if friend.get('last_active') else "⚪"
            text += (
                f"{i}. {status} *{friend['name']}*\n"
                f"   Level: {friend['level']} | Money: {format_money(friend['money'])}\n"
            )
        
        if len(friend_details) > 10:
            text += f"\n... and {len(friend_details) - 10} more friends\n"
        
        # Calculate circle stats
        total_levels = sum(f['level'] for f in friend_details)
        avg_level = total_levels / len(friend_details) if friend_details else 0
        
        text += f"\n📊 *Circle Stats:*\n"
        text += f"   Average Level: {avg_level:.1f}\n"
        text += f"   Total Friends: {len(friend_details)}\n"
        
        keyboard = [
            [
                InlineKeyboardButton("➕ Add Friend", callback_data="friend_add"),
                InlineKeyboardButton("❌ Remove Friend", callback_data="friend_remove")
            ],
            [
                InlineKeyboardButton("🎁 Send Gift", callback_data="gift_friend"),
                InlineKeyboardButton("💰 Pay Friend", callback_data="pay_friend")
            ],
            [
                InlineKeyboardButton("🔍 Suggestions", callback_data="suggestions_view")
            ]
        ]
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    @staticmethod
    async def handle_friends(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /friends command (alias for /circle)."""
        await CircleHandler.handle(update, context)
    
    @staticmethod
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle circle-related callbacks."""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "circle_view":
            await CircleHandler._show_circle(query)
        elif data == "friend_add":
            await query.edit_message_text(
                "➕ Use `/friend @username` to add a friend!",
                parse_mode='Markdown'
            )
        elif data == "friend_remove":
            await query.edit_message_text(
                "❌ Use `/unfriend @username` to remove a friend!",
                parse_mode='Markdown'
            )
        elif data == "gift_friend":
            await query.edit_message_text(
                "🎁 Use `/gift @username <item>` to send a gift!",
                parse_mode='Markdown'
            )
        elif data == "pay_friend":
            await query.edit_message_text(
                "💰 Use `/pay @username <amount>` to pay a friend!",
                parse_mode='Markdown'
            )
    
    @staticmethod
    async def _show_circle(query) -> None:
        """Show friend circle from callback."""
        user_id = query.from_user.id
        user = await UserRepository.get_user(user_id)
        
        friends = user.get("friends", [])
        
        if not friends:
            await query.edit_message_text(
                "👥 *Your Friend Circle*\n\n"
                "You don't have any friends yet.\n\n"
                "Use `/friend @username` to add friends!",
                parse_mode='Markdown'
            )
            return
        
        friend_details = []
        for friend_id in friends:
            friend = await UserRepository.get_user(friend_id)
            if friend:
                friend_details.append(friend)
        
        friend_details.sort(key=lambda x: x['level'], reverse=True)
        
        text = f"👥 *Your Friend Circle* ({len(friends)} friends)\n\n"
        
        for i, friend in enumerate(friend_details[:10], 1):
            text += (
                f"{i}. *{friend['name']}* (@{friend['username']})\n"
                f"   Level: {friend['level']} | Money: {format_money(friend['money'])}\n"
            )
        
        if len(friend_details) > 10:
            text += f"\n... and {len(friend_details) - 10} more friends\n"
        
        keyboard = [
            [
                InlineKeyboardButton("➕ Add Friend", callback_data="friend_add"),
                InlineKeyboardButton("❌ Remove Friend", callback_data="friend_remove")
            ],
            [
                InlineKeyboardButton("🔍 Suggestions", callback_data="suggestions_view")
            ],
            [
                InlineKeyboardButton("⬅️ Back", callback_data="profile_view")
            ]
        ]
        
        await query.edit_message_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
