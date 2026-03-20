"""
Telegram RPG Bot - Unfriend Module
=================================
Handles the /unfriend command for removing friends.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db, UserRepository, LogRepository
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class UnfriendHandler:
    """Handles unfriend command for removing friends."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /unfriend command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        user = await UserRepository.get_user(user_id)
        
        # Check if user has friends
        if not user.get("friends"):
            await update.message.reply_text(
                "❌ You don't have any friends to remove!\n\n"
                "Use `/friend @username` to add friends!"
            )
            return
        
        # Check for target user
        if not context.args:
            # Show list of friends
            friends_text = "👥 *Your Friends*\n\nSelect a friend to remove:\n\n"
            
            keyboard = []
            for friend_id in user["friends"]:
                friend = await UserRepository.get_user(friend_id)
                if friend:
                    friends_text += f"• {friend['name']} (ID: {friend_id})\n"
                    keyboard.append([
                        InlineKeyboardButton(
                            f"❌ Remove {friend['name']}",
                            callback_data=f"unfriend_{friend_id}"
                        )
                    ])
            
            keyboard.append([InlineKeyboardButton("Cancel", callback_data="unfriend_cancel")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                friends_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            return
        
        try:
            friend_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!")
            return
        
        # Check if friend is actually in friend list
        if friend_id not in user.get("friends", []):
            await update.message.reply_text("❌ This user is not your friend!")
            return
        
        friend = await UserRepository.get_user(friend_id)
        if not friend:
            await update.message.reply_text("❌ Friend not found!")
            return
        
        # Confirm unfriend
        keyboard = [
            [
                InlineKeyboardButton("❌ Confirm Remove", callback_data=f"unfriend_confirm_{friend_id}"),
                InlineKeyboardButton("Cancel", callback_data="unfriend_cancel")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"❌ *Remove Friend*\n\n"
            f"Are you sure you want to remove {friend['name']} (@{friend['username']}) from your friends?\n\n"
            f"They will be notified.",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle unfriend callbacks."""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        if data == "unfriend_cancel":
            await query.edit_message_text(
                "✅ Cancelled. Your friends list is unchanged! 👥"
            )
        elif data.startswith("unfriend_confirm_"):
            friend_id = int(data.replace("unfriend_confirm_", ""))
            await UnfriendHandler._process_unfriend(context, user_id, friend_id, query)
        elif data.startswith("unfriend_"):
            friend_id = int(data.replace("unfriend_", ""))
            await UnfriendHandler._confirm_unfriend_prompt(user_id, friend_id, query)
    
    @staticmethod
    async def _confirm_unfriend_prompt(user_id: int, friend_id: int, query) -> None:
        """Show unfriend confirmation prompt."""
        friend = await UserRepository.get_user(friend_id)
        if not friend:
            await query.edit_message_text("❌ Friend not found!")
            return
        
        keyboard = [
            [
                InlineKeyboardButton("❌ Confirm Remove", callback_data=f"unfriend_confirm_{friend_id}"),
                InlineKeyboardButton("Cancel", callback_data="unfriend_cancel")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"❌ *Remove Friend*\n\n"
            f"Are you sure you want to remove {friend['name']} (@{friend['username']})?",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def _process_unfriend(context, user_id: int, friend_id: int, query) -> None:
        """Process unfriending."""
        user = await UserRepository.get_user(user_id)
        friend = await UserRepository.get_user(friend_id)
        
        if not user or not friend:
            await query.edit_message_text("❌ Error: User not found!")
            return
        
        if friend_id not in user.get("friends", []):
            await query.edit_message_text("❌ This user is not your friend!")
            return
        
        # Remove from both users' friend lists
        db.users.update_one(
            {"user_id": user_id},
            {"$pull": {"friends": friend_id}}
        )
        db.users.update_one(
            {"user_id": friend_id},
            {"$pull": {"friends": user_id}}
        )
        
        # Log the unfriend
        await LogRepository.log_action(
            user_id, "friend_removed", {"friend": friend_id}
        )
        await LogRepository.log_action(
            friend_id, "friend_removed_by", {"friend": user_id}
        )
        
        # Notify friend
        try:
            await context.bot.send_message(
                chat_id=friend_id,
                text=(
                    f"👋 *Friend Removed*\n\n"
                    f"{user['name']} (@{user['username']}) has removed you from their friends."
                ),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error notifying friend: {e}")
        
        # Update user's message
        await query.edit_message_text(
            f"✅ *Friend Removed*\n\n"
            f"You have removed {friend['name']} (@{friend['username']}) from your friends.",
            parse_mode='Markdown'
        )
