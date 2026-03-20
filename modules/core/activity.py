"""
Telegram RPG Bot - Activity Module
=================================
Handles the /activity command and user activity log.
"""

import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db, LogRepository
from utils.helpers import format_time
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class ActivityHandler:
    """Handles activity command and user activity log viewing."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /activity command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        
        # Get recent activity logs
        logs = await LogRepository.get_logs(user_id=user_id, limit=20)
        
        if not logs:
            await update.message.reply_text(
                "📜 *Activity Log*\n\n"
                "No recent activity found.",
                parse_mode='Markdown'
            )
            return
        
        activity_text = "📜 *Your Recent Activity*\n\n"
        
        for log in logs:
            timestamp = log["timestamp"]
            action = log["action"]
            details = log.get("details", {})
            
            # Format time
            time_ago = ActivityHandler._format_time_ago(timestamp)
            
            # Format action
            action_text = ActivityHandler._format_action(action, details)
            
            activity_text += f"• {time_ago}: {action_text}\n"
        
        # Add activity summary
        today = datetime.utcnow().date()
        today_logs = [l for l in logs if l["timestamp"].date() == today]
        
        activity_text += f"\n📊 *Summary*\n"
        activity_text += f"Today's activities: {len(today_logs)}\n"
        activity_text += f"Total shown: {len(logs)}\n"
        
        keyboard = [
            [
                InlineKeyboardButton("📅 Today", callback_data="activity_today"),
                InlineKeyboardButton("📆 Week", callback_data="activity_week")
            ],
            [
                InlineKeyboardButton("📈 Stats", callback_data="stats_view"),
                InlineKeyboardButton("🔄 Refresh", callback_data="activity_refresh")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            activity_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    @staticmethod
    def _format_time_ago(timestamp: datetime) -> str:
        """Format timestamp as time ago."""
        now = datetime.utcnow()
        diff = now - timestamp
        
        if diff < timedelta(minutes=1):
            return "Just now"
        elif diff < timedelta(hours=1):
            minutes = int(diff.seconds / 60)
            return f"{minutes}m ago"
        elif diff < timedelta(days=1):
            hours = int(diff.seconds / 3600)
            return f"{hours}h ago"
        elif diff < timedelta(days=7):
            days = diff.days
            return f"{days}d ago"
        else:
            return timestamp.strftime("%Y-%m-%d")
    
    @staticmethod
    def _format_action(action: str, details: dict) -> str:
        """Format action with details."""
        action_formatters = {
            "daily_claimed": lambda d: f"💰 Claimed daily reward (+{d.get('amount', 0):,})",
            "money_earned": lambda d: f"💵 Earned {d.get('amount', 0):,} from {d.get('source', 'unknown')}",
            "money_spent": lambda d: f"💸 Spent {d.get('amount', 0):,} on {d.get('item', 'unknown')}",
            "item_bought": lambda d: f"🛒 Bought {d.get('item', 'unknown')} for {d.get('price', 0):,}",
            "item_sold": lambda d: f"💰 Sold {d.get('item', 'unknown')} for {d.get('price', 0):,}",
            "rob_attempt": lambda d: "🔪 Attempted to rob someone" + (" (success)" if d.get('success') else " (failed)"),
            "robbed": lambda d: f"😢 Got robbed by {d.get('robber', 'someone')} (-{d.get('amount', 0):,})",
            "attack_attempt": lambda d: "⚔️ Attacked someone" + (" (success)" if d.get('success') else " (failed)"),
            "attacked": lambda d: f"💀 Got attacked by {d.get('attacker', 'someone')}",
            "married": lambda d: f"💍 Married {d.get('partner', 'someone')}",
            "divorced": lambda d: f"💔 Divorced {d.get('partner', 'someone')}",
            "adopted": lambda d: f"👶 Adopted {d.get('child', 'someone')}",
            "disowned": lambda d: f"😞 Disowned {d.get('child', 'someone')}",
            "friend_added": lambda d: f"👥 Befriended {d.get('friend', 'someone')}",
            "friend_removed": lambda d: f"👋 Unfriended {d.get('friend', 'someone')}",
            "level_up": lambda d: f"📈 Leveled up to level {d.get('level', '?')}!",
            "game_played": lambda d: f"🎮 Played {d.get('game', 'a game')}" + (" (won)" if d.get('won') else " (lost)"),
            "crop_planted": lambda d: f"🌱 Planted {d.get('crop', 'crop')}",
            "crop_harvested": lambda d: f"🌾 Harvested {d.get('crop', 'crop')} (+{d.get('amount', 0)})",
            "factory_upgraded": lambda d: f"🏭 Upgraded factory to level {d.get('level', '?')}",
            "worker_hired": lambda d: f"👷 Hired {d.get('count', 1)} worker(s)",
            "loan_taken": lambda d: f"🏦 Took a loan of {d.get('amount', 0):,}",
            "loan_repaid": lambda d: f"✅ Repaid loan of {d.get('amount', 0):,}",
            "jailed": lambda d: f"🔒 Sent to jail for {d.get('duration', '?')} minutes",
            "released": lambda d: "🔓 Released from jail",
        }
        
        formatter = action_formatters.get(action)
        if formatter:
            return formatter(details)
        
        # Default formatting
        return action.replace("_", " ").title()
    
    @staticmethod
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle activity-related callbacks."""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        if data == "activity_view":
            await ActivityHandler._show_activity(query, user_id)
        elif data == "activity_today":
            await ActivityHandler._show_today_activity(query, user_id)
        elif data == "activity_week":
            await ActivityHandler._show_week_activity(query, user_id)
        elif data == "activity_refresh":
            await ActivityHandler._show_activity(query, user_id)
    
    @staticmethod
    async def _show_activity(query, user_id: int) -> None:
        """Show activity log."""
        logs = await LogRepository.get_logs(user_id=user_id, limit=20)
        
        if not logs:
            await query.edit_message_text(
                "📜 *Activity Log*\n\n"
                "No recent activity found.",
                parse_mode='Markdown'
            )
            return
        
        activity_text = "📜 *Your Recent Activity*\n\n"
        
        for log in logs[:20]:
            timestamp = log["timestamp"]
            action = log["action"]
            details = log.get("details", {})
            
            time_ago = ActivityHandler._format_time_ago(timestamp)
            action_text = ActivityHandler._format_action(action, details)
            
            activity_text += f"• {time_ago}: {action_text}\n"
        
        keyboard = [
            [
                InlineKeyboardButton("📅 Today", callback_data="activity_today"),
                InlineKeyboardButton("📆 Week", callback_data="activity_week")
            ],
            [
                InlineKeyboardButton("🔄 Refresh", callback_data="activity_refresh")
            ]
        ]
        
        await query.edit_message_text(
            activity_text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    @staticmethod
    async def _show_today_activity(query, user_id: int) -> None:
        """Show today's activity."""
        today = datetime.utcnow().date()
        logs = await LogRepository.get_logs(user_id=user_id, limit=100)
        today_logs = [l for l in logs if l["timestamp"].date() == today]
        
        activity_text = "📅 *Today's Activity*\n\n"
        
        if not today_logs:
            activity_text += "No activity today yet.\n"
        else:
            for log in today_logs:
                timestamp = log["timestamp"]
                action = log["action"]
                details = log.get("details", {})
                
                time_str = timestamp.strftime("%H:%M")
                action_text_formatted = ActivityHandler._format_action(action, details)
                
                activity_text += f"• {time_str}: {action_text_formatted}\n"
        
        keyboard = [
            [
                InlineKeyboardButton("📜 All Activity", callback_data="activity_view"),
                InlineKeyboardButton("📆 Week", callback_data="activity_week")
            ]
        ]
        
        await query.edit_message_text(
            activity_text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    @staticmethod
    async def _show_week_activity(query, user_id: int) -> None:
        """Show this week's activity."""
        week_ago = datetime.utcnow() - timedelta(days=7)
        logs = await LogRepository.get_logs(user_id=user_id, limit=200)
        week_logs = [l for l in logs if l["timestamp"] >= week_ago]
        
        activity_text = "📆 *This Week's Activity*\n\n"
        
        if not week_logs:
            activity_text += "No activity this week yet.\n"
        else:
            # Group by day
            days = {}
            for log in week_logs:
                day = log["timestamp"].strftime("%A")
                if day not in days:
                    days[day] = 0
                days[day] += 1
            
            for day, count in days.items():
                activity_text += f"• {day}: {count} activities\n"
            
            activity_text += f"\nTotal: {len(week_logs)} activities\n"
        
        keyboard = [
            [
                InlineKeyboardButton("📜 All Activity", callback_data="activity_view"),
                InlineKeyboardButton("📅 Today", callback_data="activity_today")
            ]
        ]
        
        await query.edit_message_text(
            activity_text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
