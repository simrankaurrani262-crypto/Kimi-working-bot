"""
Telegram RPG Bot - Ratings Module
================================
Handles the /ratings command for friend ratings.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db, UserRepository
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class RatingsHandler:
    """Handles ratings command for friend ratings."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /ratings command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        user = await UserRepository.get_user(user_id)
        
        # Get user's ratings
        ratings_given = db.friends.count_documents({
            "user_id": user_id,
            "rating": {"$exists": True}
        })
        
        ratings_received = db.friends.count_documents({
            "friend_id": user_id,
            "rating": {"$exists": True}
        })
        
        # Calculate average rating received
        pipeline = [
            {"$match": {"friend_id": user_id, "rating": {"$exists": True}}},
            {"$group": {"_id": None, "avg_rating": {"$avg": "$rating"}}}
        ]
        avg_result = list(db.friends.aggregate(pipeline))
        avg_rating = avg_result[0]["avg_rating"] if avg_result else 0
        
        text = (
            f"⭐ *Your Ratings*\n\n"
            f"📊 *Statistics:*\n"
            f"   Ratings Given: {ratings_given}\n"
            f"   Ratings Received: {ratings_received}\n"
            f"   Average Rating: {avg_rating:.1f}/5 ⭐\n\n"
        )
        
        # Get top rated friends
        top_friends = list(db.friends.find({
            "user_id": user_id,
            "rating": {"$exists": True}
        }).sort("rating", -1).limit(5))
        
        if top_friends:
            text += "🏆 *Your Top Rated Friends:*\n"
            for i, entry in enumerate(top_friends, 1):
                friend = await UserRepository.get_user(entry["friend_id"])
                if friend:
                    stars = "⭐" * entry["rating"]
                    text += f"{i}. {friend['name']} - {stars}\n"
        
        keyboard = [
            [
                InlineKeyboardButton("👥 View Friends", callback_data="circle_view"),
                InlineKeyboardButton("⬅️ Back", callback_data="profile_view")
            ]
        ]
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    @staticmethod
    async def rate_friend(user_id: int, friend_id: int, rating: int) -> bool:
        """Rate a friend."""
        if rating < 1 or rating > 5:
            return False
        
        # Update or create rating
        db.friends.update_one(
            {"user_id": user_id, "friend_id": friend_id},
            {"$set": {"rating": rating, "rated_at": db.get_timestamp()}},
            upsert=True
        )
        
        return True
