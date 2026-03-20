"""
Telegram RPG Bot - Shop Module
=============================
Handles the /shop command for viewing the shop.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db
from utils.helpers import format_money
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class ShopHandler:
    """Handles shop command for viewing the shop."""
    
    ITEMS = {
        "fishing_rod": {
            "name": "🎣 Fishing Rod",
            "price": 500,
            "description": "Catch fish and sell them for profit",
            "category": "tools"
        },
        "pickaxe": {
            "name": "⛏️ Pickaxe",
            "price": 1000,
            "description": "Mine for valuable ores",
            "category": "tools"
        },
        "laptop": {
            "name": "💻 Laptop",
            "price": 2000,
            "description": "Work remotely and earn more",
            "category": "tools"
        },
        "medkit": {
            "name": "🏥 Medkit",
            "price": 300,
            "description": "Heal yourself after attacks",
            "category": "consumables"
        },
        "energy_drink": {
            "name": "⚡ Energy Drink",
            "price": 100,
            "description": "Restore energy instantly",
            "category": "consumables"
        },
        "lucky_charm": {
            "name": "🍀 Lucky Charm",
            "price": 5000,
            "description": "Increase your luck in games",
            "category": "accessories"
        },
        "pet_dog": {
            "name": "🐕 Pet Dog",
            "price": 10000,
            "description": "A loyal companion that finds coins",
            "category": "pets"
        },
        "pet_cat": {
            "name": "🐈 Pet Cat",
            "price": 8000,
            "description": "A cute companion that brings joy",
            "category": "pets"
        },
    }
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /shop command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        # Show shop categories
        text = (
            f"🏪 *Welcome to the Shop!*\n\n"
            f"Browse our categories:\n"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("🛠️ Tools", callback_data="shop_category_tools"),
                InlineKeyboardButton("🍎 Consumables", callback_data="shop_category_consumables")
            ],
            [
                InlineKeyboardButton("💎 Accessories", callback_data="shop_category_accessories"),
                InlineKeyboardButton("🐾 Pets", callback_data="shop_category_pets")
            ],
            [
                InlineKeyboardButton("📋 All Items", callback_data="shop_all"),
                InlineKeyboardButton("🎒 My Inventory", callback_data="inventory_view")
            ]
        ]
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    @staticmethod
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle shop callbacks."""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "shop_view":
            await ShopHandler._show_shop_menu(query)
        elif data == "shop_all":
            await ShopHandler._show_all_items(query)
        elif data.startswith("shop_category_"):
            category = data.replace("shop_category_", "")
            await ShopHandler._show_category(query, category)
        elif data.startswith("shop_buy_"):
            item_key = data.replace("shop_buy_", "")
            await ShopHandler._buy_item_prompt(query, item_key)
    
    @staticmethod
    async def _show_shop_menu(query) -> None:
        """Show shop menu."""
        text = (
            f"🏪 *Welcome to the Shop!*\n\n"
            f"Browse our categories:\n"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("🛠️ Tools", callback_data="shop_category_tools"),
                InlineKeyboardButton("🍎 Consumables", callback_data="shop_category_consumables")
            ],
            [
                InlineKeyboardButton("💎 Accessories", callback_data="shop_category_accessories"),
                InlineKeyboardButton("🐾 Pets", callback_data="shop_category_pets")
            ],
            [
                InlineKeyboardButton("📋 All Items", callback_data="shop_all")
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
    
    @staticmethod
    async def _show_all_items(query) -> None:
        """Show all shop items."""
        text = "📋 *All Shop Items*\n\n"
        
        for item_key, item_data in ShopHandler.ITEMS.items():
            text += (
                f"{item_data['name']}\n"
                f"   💰 Price: {format_money(item_data['price'])}\n"
                f"   📝 {item_data['description']}\n\n"
            )
        
        keyboard = [
            [InlineKeyboardButton("⬅️ Back", callback_data="shop_view")]
        ]
        
        await query.edit_message_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    @staticmethod
    async def _show_category(query, category: str) -> None:
        """Show items in a category."""
        category_names = {
            "tools": "🛠️ Tools",
            "consumables": "🍎 Consumables",
            "accessories": "💎 Accessories",
            "pets": "🐾 Pets"
        }
        
        text = f"{category_names.get(category, category)}\n\n"
        
        keyboard = []
        
        for item_key, item_data in ShopHandler.ITEMS.items():
            if item_data["category"] == category:
                text += (
                    f"{item_data['name']}\n"
                    f"   💰 {format_money(item_data['price'])}\n"
                    f"   📝 {item_data['description']}\n\n"
                )
                keyboard.append([
                    InlineKeyboardButton(
                        f"Buy {item_data['name']}",
                        callback_data=f"shop_buy_{item_key}"
                    )
                ])
        
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="shop_view")])
        
        await query.edit_message_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    @staticmethod
    async def _buy_item_prompt(query, item_key: str) -> None:
        """Show buy item prompt."""
        await query.edit_message_text(
            f"Use `/buy {item_key}` to purchase this item!",
            parse_mode='Markdown'
        )
