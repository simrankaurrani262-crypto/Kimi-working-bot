"""
Telegram RPG Bot - Friend Module
===============================
Handles the /friend command for adding friends.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db, UserRepository, LogRepository
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class FriendHandler:
    """Handles friend command for adding friends."""
    
    MAX_FRIENDS = 50
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /friend command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        user = await UserRepository.get_user(user_id)
        
        # Check friend limit
        if len(user.get("friends", [])) >= FriendHandler.MAX_FRIENDS:
            await update.message.reply_text(
                f"❌ You have reached the maximum friend limit ({FriendHandler.MAX_FRIENDS})!\n"
                f"Remove some friends with `/unfriend @username`"
            )
            return
        
        # Check for target user
        if not context.args:
            await update.message.reply_text(
                "👥 *Add a Friend*\n\n"
                f"You have {len(user.get('friends', []))}/{FriendHandler.MAX_FRIENDS} friends.\n\n"
                "Usage: `/friend @username` or `/friend <user_id>`\n\n"
                "Add friends to see their activity and send them gifts!",
                parse_mode='Markdown'
            )
            return
        
        target = context.args[0]
        
        # Parse target user ID
        try:
            if target.startswith('@'):
                await update.message.reply_text(
                    "❌ Please use the user's ID instead of username.\n"
                    "The user can find their ID with /profile"
                )
                return
            else:
                friend_id = int(target)
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!")
            return
        
        # Check not adding self
        if user_id == friend_id:
            await update.message.reply_text("❌ You can't add yourself as a friend!")
            return
        
        # Check friend exists
        friend = await UserRepository.get_user(friend_id)
        if not friend:
            await update.message.reply_text("❌ User not found!")
            return
        
        # Check not already friends
        if friend_id in user.get("friends", []):
            await update.message.reply_text(
                f"❌ {friend['name']} is already your friend!"
            )
            return
        
        # Send friend request
        keyboard = [
            [
                InlineKeyboardButton("✅ Accept", callback_data=f"friend_accept_{user_id}"),
                InlineKeyboardButton("❌ Decline", callback_data=f"friend_decline_{user_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await context.bot.send_message(
                chat_id=friend_id,
                text=(
                    f"👥 *Friend Request*\n\n"
                    f"{user['name']} (@{user['username']}) wants to be your friend!\n\n"
                    f"They are level {user['level']}.\n\n"
                    f"Do you accept?"
                ),
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
            await update.message.reply_text(
                f"📨 Friend request sent to {friend['name']}!\n"
                f"They need to accept your request."
            )
            
        except Exception as e:
            logger.error(f"Error sending friend request: {e}")
            await update.message.reply_text(
                "❌ Could not send friend request. The user may have blocked the bot."
            )
    
    @staticmethod
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle friend callbacks."""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        friend_id = query.from_user.id
        
        if data.startswith("friend_accept_"):
            user_id = int(data.replace("friend_accept_", ""))
            await FriendHandler._process_friendship(context, user_id, friend_id, query)
        elif data.startswith("friend_decline_"):
            user_id = int(data.replace("friend_decline_", ""))
            await FriendHandler._decline_friendship(context, user_id, friend_id, query)
    
    @staticmethod
    async def _process_friendship(context, user1_id: int, user2_id: int, query) -> None:
        """Process accepted friendship."""
        # Add to both users' friend lists
        db.users.update_one(
            {"user_id": user1_id},
            {"$addToSet": {"friends": user2_id}}
        )
        db.users.update_one(
            {"user_id": user2_id},
            {"$addToSet": {"friends": user1_id}}
        )
        
        # Log the friendship
        await LogRepository.log_action(
            user1_id, "friend_added", {"friend": user2_id}
        )
        await LogRepository.log_action(
            user2_id, "friend_added", {"friend": user1_id}
        )
        
        user1 = await UserRepository.get_user(user1_id)
        user2 = await UserRepository.get_user(user2_id)
        
        # Notify user1
        try:
            await context.bot.send_message(
                chat_id=user1_id,
                text=(
                    f"🎉 *Friendship Accepted!*\n\n"
                    f"You are now friends with {user2['name']} (@{user2['username']})!\n\n"
                    f"Use `/gift @{user2_id}` to send them a gift!"
                ),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error notifying user1: {e}")
        
        # Update user2's message
        await query.edit_message_text(
            f"🎉 *Friendship Accepted!*\n\n"
            f"You are now friends with {user1['name']} (@{user1['username']})!",
            parse_mode='Markdown'
        )
    
    @staticmethod
    async def _decline_friendship(context, user_id: int, friend_id: int, query) -> None:
        """Process declined friendship."""
        user = await UserRepository.get_user(user_id)
        
        # Notify user
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    f"❌ *Friend Request Declined*\n\n"
                    f"{query.from_user.first_name} has declined your friend request."
                ),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error notifying user: {e}")
        
        # Update friend's message
        await query.edit_message_text(
            "❌ You have declined the friend request.",
            parse_mode='Markdown'
        )
