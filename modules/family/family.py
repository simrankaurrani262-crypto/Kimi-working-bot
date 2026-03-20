"""
Telegram RPG Bot - Family Module
===============================
Handles the /family command and family management.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db, UserRepository, FamilyRepository
from utils.helpers import format_money
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class FamilyHandler:
    """Handles family command and family management."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /family command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        user = await UserRepository.get_user(user_id)
        
        # Get family info
        family = await FamilyRepository.get_family_by_member(user_id)
        
        family_text = f"👨‍👩‍👧‍👦 *Family Information*\n\n"
        
        if family:
            family_text += (
                f"🏠 *Family Name:* {family['name']}\n"
                f"👑 *Creator:* {(await UserRepository.get_user(family['creator_id']))['name']}\n"
                f"👥 *Members:* {len(family['members'])}\n"
                f"💰 *Total Wealth:* {format_money(family.get('total_wealth', 0))}\n"
                f"⭐ *Reputation:* {family.get('reputation', 0)}\n\n"
            )
            
            # List members
            family_text += "*Members:*\n"
            for member_id in family['members'][:10]:
                member = await UserRepository.get_user(member_id)
                if member:
                    role = "👑" if member_id == family['creator_id'] else "👤"
                    family_text += f"  {role} {member['name']}\n"
            
            if len(family['members']) > 10:
                family_text += f"  ... and {len(family['members']) - 10} more\n"
        
        # Personal family info
        family_text += f"\n*Your Family:*\n"
        
        if user.get("partner"):
            partner = await UserRepository.get_user(user["partner"])
            if partner:
                family_text += f"💍 Partner: {partner['name']}\n"
        else:
            family_text += f"💍 Partner: None\n"
        
        if user.get("parents"):
            parents_names = []
            for parent_id in user["parents"]:
                parent = await UserRepository.get_user(parent_id)
                if parent:
                    parents_names.append(parent['name'])
            family_text += f"👨‍👩 Parents: {', '.join(parents_names)}\n"
        else:
            family_text += f"👨‍👩 Parents: None\n"
        
        if user.get("children"):
            family_text += f"👶 Children: {len(user['children'])}\n"
            for child_id in user["children"][:5]:
                child = await UserRepository.get_user(child_id)
                if child:
                    family_text += f"    • {child['name']}\n"
            if len(user['children']) > 5:
                family_text += f"    ... and {len(user['children']) - 5} more\n"
        else:
            family_text += f"👶 Children: None\n"
        
        # Create action buttons
        keyboard = [
            [
                InlineKeyboardButton("🌳 Family Tree", callback_data="family_tree"),
                InlineKeyboardButton("🖼️ Tree Image", callback_data="family_tree_image")
            ],
            [
                InlineKeyboardButton("💍 Marry", callback_data="family_marry"),
                InlineKeyboardButton("👶 Adopt", callback_data="family_adopt")
            ],
            [
                InlineKeyboardButton("👨‍👩 Parents", callback_data="family_parents"),
                InlineKeyboardButton("👶 Children", callback_data="family_children")
            ],
            [
                InlineKeyboardButton("📊 Relations", callback_data="family_relations")
            ]
        ]
        
        if not family:
            keyboard.insert(0, [InlineKeyboardButton("🏠 Create Family", callback_data="family_create")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            family_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle family-related callbacks."""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "family_view":
            await FamilyHandler._show_family_menu(query)
        elif data == "family_tree":
            from modules.family.tree import TreeHandler
            await TreeHandler._show_tree(query)
        elif data == "family_tree_image":
            from modules.family.tree import TreeHandler
            await TreeHandler._send_tree_image(query)
        elif data == "family_marry":
            await query.edit_message_text(
                "💍 Use `/marry @username` to propose to someone!",
                parse_mode='Markdown'
            )
        elif data == "family_adopt":
            await query.edit_message_text(
                "👶 Use `/adopt @username` to adopt someone!",
                parse_mode='Markdown'
            )
        elif data == "family_parents":
            await FamilyHandler._show_parents(query)
        elif data == "family_children":
            await FamilyHandler._show_children(query)
        elif data == "family_relations":
            from modules.family.relations import RelationsHandler
            await RelationsHandler._show_relations(query)
        elif data == "family_create":
            await FamilyHandler._create_family_prompt(query)
    
    @staticmethod
    async def _show_family_menu(query) -> None:
        """Show family menu."""
        user_id = query.from_user.id
        user = await UserRepository.get_user(user_id)
        
        family_text = f"👨‍👩‍👧‍👦 *Family Information*\n\n"
        
        # Personal family info
        family_text += f"*Your Family:*\n"
        
        if user.get("partner"):
            partner = await UserRepository.get_user(user["partner"])
            if partner:
                family_text += f"💍 Partner: {partner['name']}\n"
        else:
            family_text += f"💍 Partner: None\n"
        
        if user.get("parents"):
            parents_names = []
            for parent_id in user["parents"]:
                parent = await UserRepository.get_user(parent_id)
                if parent:
                    parents_names.append(parent['name'])
            family_text += f"👨‍👩 Parents: {', '.join(parents_names)}\n"
        else:
            family_text += f"👨‍👩 Parents: None\n"
        
        if user.get("children"):
            family_text += f"👶 Children: {len(user['children'])}\n"
        else:
            family_text += f"👶 Children: None\n"
        
        keyboard = [
            [
                InlineKeyboardButton("🌳 Family Tree", callback_data="family_tree"),
                InlineKeyboardButton("🖼️ Tree Image", callback_data="family_tree_image")
            ],
            [
                InlineKeyboardButton("💍 Marry", callback_data="family_marry"),
                InlineKeyboardButton("👶 Adopt", callback_data="family_adopt")
            ],
            [
                InlineKeyboardButton("👨‍👩 Parents", callback_data="family_parents"),
                InlineKeyboardButton("👶 Children", callback_data="family_children")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            family_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def _show_parents(query) -> None:
        """Show user's parents."""
        user_id = query.from_user.id
        user = await UserRepository.get_user(user_id)
        
        if not user.get("parents"):
            await query.edit_message_text(
                "👨‍👩 *Your Parents*\n\n"
                "You don't have any parents registered.\n\n"
                "Someone can adopt you using `/adopt @your_username`",
                parse_mode='Markdown'
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
                    f"   Money: {format_money(parent['money'])}\n\n"
                )
        
        keyboard = [
            [InlineKeyboardButton("⬅️ Back", callback_data="family_view")]
        ]
        
        await query.edit_message_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    @staticmethod
    async def _show_children(query) -> None:
        """Show user's children."""
        user_id = query.from_user.id
        user = await UserRepository.get_user(user_id)
        
        if not user.get("children"):
            await query.edit_message_text(
                "👶 *Your Children*\n\n"
                "You don't have any children.\n\n"
                "Use `/adopt @username` to adopt someone!",
                parse_mode='Markdown'
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
                    f"   Money: {format_money(child['money'])}\n\n"
                )
        
        keyboard = [
            [InlineKeyboardButton("⬅️ Back", callback_data="family_view")]
        ]
        
        await query.edit_message_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    @staticmethod
    async def _create_family_prompt(query) -> None:
        """Prompt user to create a family."""
        text = (
            "🏠 *Create a Family*\n\n"
            "Create your own family clan!\n\n"
            "Benefits:\n"
            "• Family leaderboard rankings\n"
            "• Shared family wealth tracking\n"
            "• Family reputation system\n\n"
            "Use `/familycreate <name>` to create your family!"
        )
        
        keyboard = [
            [InlineKeyboardButton("⬅️ Back", callback_data="family_view")]
        ]
        
        await query.edit_message_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
