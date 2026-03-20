"""
Telegram RPG Bot - Disown Module
===============================
Handles the /disown command for disowning children.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db, UserRepository, LogRepository
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class DisownHandler:
    """Handles disown command for disowning children."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /disown command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        user = await UserRepository.get_user(user_id)
        
        # Check if user has children
        if not user.get("children"):
            await update.message.reply_text(
                "❌ You don't have any children to disown!\n\n"
                "Use `/adopt @username` to adopt someone first!"
            )
            return
        
        # Check for target child
        if not context.args:
            # Show list of children
            children_text = "👶 *Your Children*\n\nSelect a child to disown:\n\n"
            
            keyboard = []
            for child_id in user["children"]:
                child = await UserRepository.get_user(child_id)
                if child:
                    children_text += f"• {child['name']} (ID: {child_id})\n"
                    keyboard.append([
                        InlineKeyboardButton(
                            f"❌ Disown {child['name']}",
                            callback_data=f"disown_{child_id}"
                        )
                    ])
            
            children_text += "\nUsage: `/disown <user_id>`"
            
            keyboard.append([InlineKeyboardButton("Cancel", callback_data="disown_cancel")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                children_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            return
        
        try:
            child_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!")
            return
        
        # Check if child is actually user's child
        if child_id not in user.get("children", []):
            await update.message.reply_text("❌ This user is not your child!")
            return
        
        child = await UserRepository.get_user(child_id)
        if not child:
            await update.message.reply_text("❌ Child not found!")
            return
        
        # Confirm disown
        keyboard = [
            [
                InlineKeyboardButton("😞 Confirm Disown", callback_data=f"disown_confirm_{child_id}"),
                InlineKeyboardButton("❌ Cancel", callback_data="disown_cancel")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"😞 *Disown Child*\n\n"
            f"Are you sure you want to disown {child['name']} (@{child['username']})?\n\n"
            f"They will no longer be your child, and you will no longer be their parent.\n\n"
            f"⚠️ This action cannot be undone!",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle disown callbacks."""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        if data == "disown_cancel":
            await query.edit_message_text(
                "✅ Disown cancelled. Your family remains intact! 👨‍👩‍👧‍👦"
            )
        elif data.startswith("disown_confirm_"):
            child_id = int(data.replace("disown_confirm_", ""))
            await DisownHandler._process_disown(context, user_id, child_id, query)
        elif data.startswith("disown_"):
            child_id = int(data.replace("disown_", ""))
            await DisownHandler._confirm_disown_prompt(user_id, child_id, query)
    
    @staticmethod
    async def _confirm_disown_prompt(user_id: int, child_id: int, query) -> None:
        """Show disown confirmation prompt."""
        child = await UserRepository.get_user(child_id)
        if not child:
            await query.edit_message_text("❌ Child not found!")
            return
        
        keyboard = [
            [
                InlineKeyboardButton("😞 Confirm Disown", callback_data=f"disown_confirm_{child_id}"),
                InlineKeyboardButton("❌ Cancel", callback_data="disown_cancel")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"😞 *Disown Child*\n\n"
            f"Are you sure you want to disown {child['name']} (@{child['username']})?\n\n"
            f"⚠️ This action cannot be undone!",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def _process_disown(context, parent_id: int, child_id: int, query) -> None:
        """Process disowning."""
        parent = await UserRepository.get_user(parent_id)
        child = await UserRepository.get_user(child_id)
        
        if not parent or not child:
            await query.edit_message_text("❌ Error: User not found!")
            return
        
        if child_id not in parent.get("children", []):
            await query.edit_message_text("❌ This user is not your child!")
            return
        
        # Remove child from parent's children list
        db.users.update_one(
            {"user_id": parent_id},
            {"$pull": {"children": child_id}}
        )
        
        # Remove parent from child's parents list
        db.users.update_one(
            {"user_id": child_id},
            {"$pull": {"parents": parent_id}}
        )
        
        # Log the disown
        await LogRepository.log_action(
            parent_id, "disowned", {"child": child_id}
        )
        await LogRepository.log_action(
            child_id, "disowned_by", {"parent": parent_id}
        )
        
        # Notify child
        try:
            await context.bot.send_message(
                chat_id=child_id,
                text=(
                    f"😞 *Disowned*\n\n"
                    f"{parent['name']} (@{parent['username']}) has disowned you.\n\n"
                    f"You are no longer their child."
                ),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error notifying child: {e}")
        
        # Update parent's message
        await query.edit_message_text(
            f"😞 *Disown Complete*\n\n"
            f"You have disowned {child['name']} (@{child['username']}).\n\n"
            f"They are no longer your child.",
            parse_mode='Markdown'
        )
