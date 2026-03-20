"""
Telegram RPG Bot - Relations Module
==================================
Handles the /relations, /parents, and /children commands.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db, UserRepository
from utils.validators import UserValidator
from utils.helpers import format_money

logger = logging.getLogger(__name__)


class RelationsHandler:
    """Handles relations commands."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /relations command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        user = await UserRepository.get_user(user_id)
        
        await RelationsHandler._show_relations_text(update, user)
    
    @staticmethod
    async def handle_parents(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /parents command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        user = await UserRepository.get_user(user_id)
        
        if not user.get("parents"):
            await update.message.reply_text(
                "👨‍👩 *Your Parents*\n\n"
                "You don't have any parents registered.\n\n"
                "Someone can adopt you using `/adopt @your_username`"
            )
            return
        
        text = "👨‍👩 *Your Parents*\n\n"
        
        for parent_id in user["parents"]:
            parent = await UserRepository.get_user(parent_id)
            if parent:
                text += (
                    f"👤 *{parent['name']}*\n"
                    f"   Username: @{parent['username']}\n"
                    f"   Level: {parent['level']}\n"
                    f"   Money: {format_money(parent['money'])}\n"
                    f"   Children: {len(parent.get('children', []))}\n\n"
                )
        
        keyboard = [
            [
                InlineKeyboardButton("🌳 Family Tree", callback_data="family_tree"),
                InlineKeyboardButton("👶 Siblings", callback_data="relations_siblings")
            ]
        ]
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    @staticmethod
    async def handle_children(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /children command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        user = await UserRepository.get_user(user_id)
        
        if not user.get("children"):
            await update.message.reply_text(
                "👶 *Your Children*\n\n"
                "You don't have any children.\n\n"
                "Use `/adopt @username` to adopt someone!"
            )
            return
        
        text = "👶 *Your Children*\n\n"
        
        for child_id in user["children"]:
            child = await UserRepository.get_user(child_id)
            if child:
                text += (
                    f"👤 *{child['name']}*\n"
                    f"   Username: @{child['username']}\n"
                    f"   Level: {child['level']}\n"
                    f"   Money: {format_money(child['money'])}\n"
                    f"   Parents: {len(child.get('parents', []))}\n\n"
                )
        
        keyboard = [
            [
                InlineKeyboardButton("🌳 Family Tree", callback_data="family_tree"),
                InlineKeyboardButton("👨‍👩 Grandchildren", callback_data="relations_grandchildren")
            ]
        ]
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    @staticmethod
    async def _show_relations_text(update: Update, user: dict) -> None:
        """Show relations text."""
        user_id = user["user_id"]
        
        text = f"👨‍👩‍👧‍👦 *{user['name']}'s Relations*\n\n"
        
        # Partner
        if user.get("partner"):
            partner = await UserRepository.get_user(user["partner"])
            if partner:
                text += f"💍 *Partner:* {partner['name']} (@{partner['username']})\n\n"
        else:
            text += f"💍 *Partner:* None\n\n"
        
        # Parents
        text += f"👨‍👩 *Parents:* {len(user.get('parents', []))}\n"
        for parent_id in user.get("parents", [])[:3]:
            parent = await UserRepository.get_user(parent_id)
            if parent:
                text += f"   • {parent['name']}\n"
        if len(user.get("parents", [])) > 3:
            text += f"   ... and {len(user['parents']) - 3} more\n"
        text += "\n"
        
        # Children
        text += f"👶 *Children:* {len(user.get('children', []))}\n"
        for child_id in user.get("children", [])[:3]:
            child = await UserRepository.get_user(child_id)
            if child:
                text += f"   • {child['name']}\n"
        if len(user.get("children", [])) > 3:
            text += f"   ... and {len(user['children']) - 3} more\n"
        text += "\n"
        
        # Siblings
        siblings = await RelationsHandler._get_siblings(user_id, user)
        if siblings:
            text += f"👫 *Siblings:* {len(siblings)}\n"
            for sibling in siblings[:3]:
                text += f"   • {sibling['name']}\n"
            if len(siblings) > 3:
                text += f"   ... and {len(siblings) - 3} more\n"
            text += "\n"
        
        # Grandparents
        grandparents = await RelationsHandler._get_grandparents(user)
        if grandparents:
            text += f"👴👵 *Grandparents:* {len(grandparents)}\n"
            for gp in grandparents[:2]:
                text += f"   • {gp['name']}\n"
            if len(grandparents) > 2:
                text += f"   ... and {len(grandparents) - 2} more\n"
            text += "\n"
        
        # Grandchildren
        grandchildren = await RelationsHandler._get_grandchildren(user)
        if grandchildren:
            text += f"🍼 *Grandchildren:* {len(grandchildren)}\n"
            for gc in grandchildren[:2]:
                text += f"   • {gc['name']}\n"
            if len(grandchildren) > 2:
                text += f"   ... and {len(grandchildren) - 2} more\n"
        
        keyboard = [
            [
                InlineKeyboardButton("👨‍👩 Parents", callback_data="family_parents"),
                InlineKeyboardButton("👶 Children", callback_data="family_children")
            ],
            [
                InlineKeyboardButton("🌳 Family Tree", callback_data="family_tree"),
                InlineKeyboardButton("🖼️ Tree Image", callback_data="family_tree_image")
            ]
        ]
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    @staticmethod
    async def _show_relations(query) -> None:
        """Show relations from callback."""
        user_id = query.from_user.id
        user = await UserRepository.get_user(user_id)
        
        text = f"👨‍👩‍👧‍👦 *{user['name']}'s Relations*\n\n"
        
        if user.get("partner"):
            partner = await UserRepository.get_user(user["partner"])
            if partner:
                text += f"💍 *Partner:* {partner['name']}\n\n"
        else:
            text += f"💍 *Partner:* None\n\n"
        
        text += f"👨‍👩 *Parents:* {len(user.get('parents', []))}\n"
        text += f"👶 *Children:* {len(user.get('children', []))}\n"
        
        siblings = await RelationsHandler._get_siblings(user_id, user)
        if siblings:
            text += f"👫 *Siblings:* {len(siblings)}\n"
        
        grandparents = await RelationsHandler._get_grandparents(user)
        if grandparents:
            text += f"👴👵 *Grandparents:* {len(grandparents)}\n"
        
        grandchildren = await RelationsHandler._get_grandchildren(user)
        if grandchildren:
            text += f"🍼 *Grandchildren:* {len(grandchildren)}\n"
        
        keyboard = [
            [
                InlineKeyboardButton("👨‍👩 Parents", callback_data="family_parents"),
                InlineKeyboardButton("👶 Children", callback_data="family_children")
            ],
            [
                InlineKeyboardButton("⬅️ Back", callback_data="family_view")
            ]
        ]
        
        await query.edit_message_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    @staticmethod
    async def _get_siblings(user_id: int, user: dict) -> list:
        """Get user's siblings."""
        siblings = []
        for parent_id in user.get("parents", []):
            parent = await UserRepository.get_user(parent_id)
            if parent:
                for sibling_id in parent.get("children", []):
                    if sibling_id != user_id:
                        sibling = await UserRepository.get_user(sibling_id)
                        if sibling and sibling not in siblings:
                            siblings.append(sibling)
        return siblings
    
    @staticmethod
    async def _get_grandparents(user: dict) -> list:
        """Get user's grandparents."""
        grandparents = []
        for parent_id in user.get("parents", []):
            parent = await UserRepository.get_user(parent_id)
            if parent:
                for gp_id in parent.get("parents", []):
                    gp = await UserRepository.get_user(gp_id)
                    if gp and gp not in grandparents:
                        grandparents.append(gp)
        return grandparents
    
    @staticmethod
    async def _get_grandchildren(user: dict) -> list:
        """Get user's grandchildren."""
        grandchildren = []
        for child_id in user.get("children", []):
            child = await UserRepository.get_user(child_id)
            if child:
                for gc_id in child.get("children", []):
                    gc = await UserRepository.get_user(gc_id)
                    if gc and gc not in grandchildren:
                        grandchildren.append(gc)
        return grandchildren
