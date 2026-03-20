"""
Telegram RPG Bot - BuyWeapon Module
==================================
Handles the /buyweapon command for buying weapons.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from database import db, UserRepository, LogRepository
from utils.helpers import format_money
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class BuyWeaponHandler:
    """Handles buyweapon command for buying weapons."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /buyweapon command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        user = await UserRepository.get_user(user_id)
        
        # Check arguments
        if not context.args:
            from modules.crime.weapon import WeaponHandler
            text = "🔫 *Buy Weapon*\n\n"
            for key, weapon in WeaponHandler.WEAPONS.items():
                text += f"`{key}` - {weapon['name']} - {format_money(weapon['price'])}\n"
            text += "\nUsage: `/buyweapon <type>`"
            
            await update.message.reply_text(text, parse_mode='Markdown')
            return
        
        weapon_key = context.args[0].lower()
        
        from modules.crime.weapon import WeaponHandler
        weapon = WeaponHandler.WEAPONS.get(weapon_key)
        
        if not weapon:
            await update.message.reply_text("❌ Invalid weapon type!")
            return
        
        # Check if already owns
        if weapon_key in user.get("weapons", []):
            await update.message.reply_text(f"❌ You already own {weapon['name']}!")
            return
        
        # Check has enough money
        if user["money"] < weapon["price"]:
            await update.message.reply_text(
                f"❌ Insufficient funds!\n"
                f"Price: {format_money(weapon['price'])}\n"
                f"Your balance: {format_money(user['money'])}"
            )
            return
        
        # Buy weapon
        await UserRepository.remove_money(user_id, weapon["price"])
        db.users.update_one(
            {"user_id": user_id},
            {"$addToSet": {"weapons": weapon_key}}
        )
        
        await LogRepository.log_action(
            user_id, "weapon_bought", {"weapon": weapon_key, "price": weapon["price"]}
        )
        
        await update.message.reply_text(
            f"🔫 *Weapon Purchased!*\n\n"
            f"You bought {weapon['name']}!\n"
            f"Damage: {weapon['damage']}\n"
            f"Price: {format_money(weapon['price'])}"
        )
