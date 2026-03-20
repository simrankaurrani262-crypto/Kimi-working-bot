"""
Telegram RPG Bot - Tree Module
=============================
Handles the /tree and /fulltree commands for family tree visualization.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ContextTypes

from database import db, UserRepository
from utils.tree_generator import generate_family_tree, generate_full_family_tree
from utils.helpers import format_money
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class TreeHandler:
    """Handles tree commands and family tree visualization."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /tree command (text-based tree)."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        
        # Check if viewing another user's tree
        if context.args:
            try:
                target_id = int(context.args[0])
                target_user = await UserRepository.get_user(target_id)
                if target_user:
                    await TreeHandler._show_text_tree(update, target_user)
                    return
                else:
                    await update.message.reply_text("❌ User not found!")
                    return
            except ValueError:
                await update.message.reply_text("❌ Invalid user ID!")
                return
        
        # Show own tree
        user = await UserRepository.get_user(user_id)
        await TreeHandler._show_text_tree(update, user)
    
    @staticmethod
    async def handle_full(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /fulltree command (image-based tree)."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        
        # Check if viewing another user's tree
        if context.args:
            try:
                target_id = int(context.args[0])
                target_user = await UserRepository.get_user(target_id)
                if target_user:
                    user_id = target_id
                else:
                    await update.message.reply_text("❌ User not found!")
                    return
            except ValueError:
                await update.message.reply_text("❌ Invalid user ID!")
                return
        
        # Generate and send tree image
        message = await update.message.reply_text("🌳 Generating family tree image...")
        
        try:
            image_buffer = await generate_family_tree(user_id)
            
            if image_buffer:
                await message.delete()
                await update.message.reply_photo(
                    photo=InputFile(image_buffer, filename="family_tree.png"),
                    caption="🌳 Your Family Tree"
                )
            else:
                await message.edit_text(
                    "❌ Could not generate family tree. Make sure you have family members registered!"
                )
        except Exception as e:
            logger.error(f"Error generating family tree: {e}")
            await message.edit_text(
                "❌ An error occurred while generating the family tree. Please try again later."
            )
    
    @staticmethod
    async def _show_text_tree(update: Update, user: dict) -> None:
        """Show text-based family tree."""
        user_id = user["user_id"]
        
        # Build ASCII tree
        tree_text = f"🌳 *Family Tree - {user['name']}*\n\n"
        
        # Get all family members
        grandparents = []
        parents = []
        partner = None
        children = []
        grandchildren = []
        
        # Fetch grandparents and parents
        for parent_id in user.get("parents", []):
            parent = await UserRepository.get_user(parent_id)
            if parent:
                parents.append(parent)
                for gp_id in parent.get("parents", []):
                    gp = await UserRepository.get_user(gp_id)
                    if gp and gp not in grandparents:
                        grandparents.append(gp)
        
        # Fetch partner
        if user.get("partner"):
            partner = await UserRepository.get_user(user["partner"])
        
        # Fetch children and grandchildren
        for child_id in user.get("children", []):
            child = await UserRepository.get_user(child_id)
            if child:
                children.append(child)
                for gc_id in child.get("children", []):
                    gc = await UserRepository.get_user(gc_id)
                    if gc and gc not in grandchildren:
                        grandchildren.append(gc)
        
        # Build tree structure
        # Grandparents level
        if grandparents:
            tree_text += "*Grandparents:*\n"
            for gp in grandparents:
                tree_text += f"  👴👵 {gp['name']}\n"
            tree_text += "    │\n"
        
        # Parents level
        if parents:
            tree_text += "*Parents:*\n"
            for p in parents:
                tree_text += f"  👨‍👩 {p['name']}\n"
            tree_text += "    │\n"
        
        # User level
        tree_text += "*You:*\n"
        if partner:
            tree_text += f"  💑 {user['name']} 💕 {partner['name']}\n"
        else:
            tree_text += f"  👤 {user['name']}\n"
        
        # Children level
        if children:
            tree_text += "    │\n"
            tree_text += "*Children:*\n"
            for child in children:
                tree_text += f"  👶 {child['name']}\n"
        
        # Grandchildren level
        if grandchildren:
            tree_text += "    │\n"
            tree_text += "*Grandchildren:*\n"
            for gc in grandchildren:
                tree_text += f"  🍼 {gc['name']}\n"
        
        # Summary
        tree_text += f"\n📊 *Summary:*\n"
        tree_text += f"  Grandparents: {len(grandparents)}\n"
        tree_text += f"  Parents: {len(parents)}\n"
        tree_text += f"  Partner: {'Yes' if partner else 'No'}\n"
        tree_text += f"  Children: {len(children)}\n"
        tree_text += f"  Grandchildren: {len(grandchildren)}\n"
        
        keyboard = [
            [
                InlineKeyboardButton("🖼️ View Image", callback_data="family_tree_image"),
                InlineKeyboardButton("🔄 Refresh", callback_data="family_tree")
            ],
            [
                InlineKeyboardButton("👨‍👩 Parents", callback_data="family_parents"),
                InlineKeyboardButton("👶 Children", callback_data="family_children")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            tree_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def _show_tree(query) -> None:
        """Show tree from callback query."""
        user_id = query.from_user.id
        user = await UserRepository.get_user(user_id)
        
        # Build ASCII tree (similar to above)
        tree_text = f"🌳 *Family Tree - {user['name']}*\n\n"
        
        grandparents = []
        parents = []
        partner = None
        children = []
        
        for parent_id in user.get("parents", []):
            parent = await UserRepository.get_user(parent_id)
            if parent:
                parents.append(parent)
                for gp_id in parent.get("parents", []):
                    gp = await UserRepository.get_user(gp_id)
                    if gp and gp not in grandparents:
                        grandparents.append(gp)
        
        if user.get("partner"):
            partner = await UserRepository.get_user(user["partner"])
        
        for child_id in user.get("children", []):
            child = await UserRepository.get_user(child_id)
            if child:
                children.append(child)
        
        if grandparents:
            tree_text += "*Grandparents:*\n"
            for gp in grandparents:
                tree_text += f"  👴👵 {gp['name']}\n"
            tree_text += "    │\n"
        
        if parents:
            tree_text += "*Parents:*\n"
            for p in parents:
                tree_text += f"  👨‍👩 {p['name']}\n"
            tree_text += "    │\n"
        
        tree_text += "*You:*\n"
        if partner:
            tree_text += f"  💑 {user['name']} 💕 {partner['name']}\n"
        else:
            tree_text += f"  👤 {user['name']}\n"
        
        if children:
            tree_text += "    │\n"
            tree_text += "*Children:*\n"
            for child in children:
                tree_text += f"  👶 {child['name']}\n"
        
        keyboard = [
            [
                InlineKeyboardButton("🖼️ View Image", callback_data="family_tree_image"),
                InlineKeyboardButton("🔄 Refresh", callback_data="family_tree")
            ],
            [
                InlineKeyboardButton("⬅️ Back", callback_data="family_view")
            ]
        ]
        
        await query.edit_message_text(
            tree_text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    @staticmethod
    async def _send_tree_image(query) -> None:
        """Send tree image from callback query."""
        user_id = query.from_user.id
        
        await query.edit_message_text("🌳 Generating family tree image...")
        
        try:
            image_buffer = await generate_family_tree(user_id)
            
            if image_buffer:
                await query.message.reply_photo(
                    photo=InputFile(image_buffer, filename="family_tree.png"),
                    caption="🌳 Your Family Tree"
                )
                await query.edit_message_text(
                    "✅ Family tree generated!",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⬅️ Back", callback_data="family_tree")]
                    ])
                )
            else:
                await query.edit_message_text(
                    "❌ Could not generate family tree. Make sure you have family members registered!",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⬅️ Back", callback_data="family_tree")]
                    ])
                )
        except Exception as e:
            logger.error(f"Error generating family tree: {e}")
            await query.edit_message_text(
                "❌ An error occurred while generating the family tree.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Back", callback_data="family_tree")]
                ])
            )
    
    @staticmethod
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle tree-related callbacks."""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "tree_view":
            await TreeHandler._show_tree(query)
        elif data == "tree_image":
            await TreeHandler._send_tree_image(query)
