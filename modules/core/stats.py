"""
Telegram RPG Bot - Stats Module
==============================
Handles the /stats command and user statistics.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db
from utils.helpers import format_money, format_number
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class StatsHandler:
    """Handles stats command and user statistics viewing."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /stats command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        
        # Get user stats
        user = db.users.find_one({"user_id": user_id})
        stats = db.stats.find_one({"user_id": user_id}) or {}
        
        # Calculate various statistics
        total_money = user["money"] + user["bank"]
        
        # Get rankings
        money_rank = db.users.count_documents({"money": {"$gt": user["money"]}}) + 1
        level_rank = db.users.count_documents({"level": {"$gt": user["level"]}}) + 1
        
        stats_text = (
            f"📊 *Your Statistics*\n"
            f"{'─' * 30}\n\n"
            f"💰 *Financial Stats*\n"
            f"  Wallet: {format_money(user['money'])}\n"
            f"  Bank: {format_money(user['bank'])}\n"
            f"  Total: {format_money(total_money)}\n"
            f"  Money Rank: #{format_number(money_rank)}\n\n"
            f"📈 *Level Stats*\n"
            f"  Level: {user['level']}\n"
            f"  XP: {user['experience']:,}\n"
            f"  Level Rank: #{format_number(level_rank)}\n\n"
            f"⭐ *Social Stats*\n"
            f"  Reputation: {user['reputation']}\n"
            f"  Friends: {len(user.get('friends', []))}\n"
            f"  Parents: {len(user.get('parents', []))}\n"
            f"  Children: {len(user.get('children', []))}\n"
        )
        
        if user.get("partner"):
            stats_text += f"  Partner: Yes 💍\n"
        
        # Add game stats if available
        if stats:
            stats_text += (
                f"\n🎮 *Game Stats*\n"
                f"  Games Played: {stats.get('games_played', 0)}\n"
                f"  Games Won: {stats.get('games_won', 0)}\n"
                f"  Win Rate: {stats.get('win_rate', 0):.1f}%\n"
                f"  Total Winnings: {format_money(stats.get('total_winnings', 0))}\n"
                f"  Total Losses: {format_money(stats.get('total_losses', 0))}\n"
            )
        
        # Add crime stats if available
        if stats:
            stats_text += (
                f"\n🔪 *Crime Stats*\n"
                f"  Robberies: {stats.get('robberies', 0)}\n"
                f"  Successful Robberies: {stats.get('successful_robberies', 0)}\n"
                f"  Attacks: {stats.get('attacks', 0)}\n"
                f"  Successful Attacks: {stats.get('successful_attacks', 0)}\n"
                f"  Times Robbed: {stats.get('times_robbed', 0)}\n"
                f"  Times Attacked: {stats.get('times_attacked', 0)}\n"
                f"  Jail Time: {stats.get('jail_time', 0)} minutes\n"
            )
        
        # Add economy stats if available
        economy = db.economy.find_one({"user_id": user_id}) or {}
        if economy:
            stats_text += (
                f"\n💵 *Economy Stats*\n"
                f"  Total Earned: {format_money(economy.get('total_earned', 0))}\n"
                f"  Total Spent: {format_money(economy.get('total_spent', 0))}\n"
                f"  Daily Streak: {economy.get('daily_streak', 0)}\n"
                f"  Max Daily Streak: {economy.get('max_daily_streak', 0)}\n"
                f"  Work Sessions: {economy.get('work_sessions', 0)}\n"
            )
        
        keyboard = [
            [
                InlineKeyboardButton("📈 Money Graph", callback_data="moneygraph_view"),
                InlineKeyboardButton("🏆 Leaderboards", callback_data="leaderboard_view")
            ],
            [
                InlineKeyboardButton("📊 Detailed Stats", callback_data="stats_detailed"),
                InlineKeyboardButton("📜 Activity Log", callback_data="activity_view")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            stats_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
