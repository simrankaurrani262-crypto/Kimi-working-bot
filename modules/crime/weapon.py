"""
Telegram RPG Bot - Weapon Module
===============================
Handles the /weapon command for viewing weapons.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class WeaponHandler:
    """Handles weapon command for viewing weapons."""
    
    WEAPONS = {
        "knife": {"name": "🔪 Knife", "damage": 10, "price": 500},
        "pistol": {"name": "🔫 Pistol", "damage": 25, "price": 2000},
        "rifle": {"name": "🔫 Rifle", "damage": 50, "price": 5000},
        "sniper": {"name": "🎯 Sniper", "damage": 75, "price": 10000},
    }
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /weapon command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        user = db.users.find_one({"user_id": user_id})
        
        weapons = user.get("weapons", [])
        
        text = "🔫 *Your Weapons*\n\n"
        
        if weapons:
            for weapon_key in weapons:
                weapon = WeaponHandler.WEAPONS.get(weapon_key)
                if weapon:
                    text += f"{weapon['name']} - Damage: {weapon['damage']}\n"
        else:
            text += "You don't have any weapons.\n\n"
            text += "Use `/buyweapon <type>` to buy weapons!\n\n"
        
        text += "\n*Available Weapons:*\n"
        for key, weapon in WeaponHandler.WEAPONS.items():
            status = "✅" if key in weapons else "❌"
            text += f"{status} {weapon['name']} - {weapon['price']:,} coins\n"
        
        keyboard = [
            [
                InlineKeyboardButton("🛒 Buy Weapon", callback_data="weapon_buy"),
                InlineKeyboardButton("🔪 Attack", callback_data="crime_attack")
            ],
            [
                InlineKeyboardButton("⬅️ Back", callback_data="profile_view")
            ]
        ]
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
