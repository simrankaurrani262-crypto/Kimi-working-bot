"""
Telegram RPG Bot - Harvest Module
================================
Handles the /harvest command for harvesting crops.
"""

import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from database import db, UserRepository, LogRepository
from utils.helpers import format_money
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class HarvestHandler:
    """Handles harvest command for harvesting crops."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /harvest command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        
        # Check if user has a garden
        garden = db.gardens.find_one({"user_id": user_id})
        if not garden:
            await update.message.reply_text(
                "❌ You don't have a garden! Use `/garden` to buy one."
            )
            return
        
        plots = garden.get("plots", [])
        
        # Find mature crops
        from modules.garden.plant import PlantHandler
        
        total_earnings = 0
        harvested_crops = {}
        
        for plot in plots:
            if plot.get("status") == "growing":
                mature_at = plot.get("mature_at")
                if mature_at and datetime.utcnow() >= mature_at:
                    crop_key = plot.get("crop")
                    crop = PlantHandler.CROPS.get(crop_key)
                    
                    if crop:
                        total_earnings += crop["sell_price"]
                        harvested_crops[crop["name"]] = harvested_crops.get(crop["name"], 0) + 1
                        
                        # Reset plot
                        db.gardens.update_one(
                            {"user_id": user_id, "plots.index": plot["index"]},
                            {
                                "$set": {
                                    "plots.$.crop": None,
                                    "plots.$.status": "empty",
                                    "plots.$.planted_at": None,
                                    "plots.$.mature_at": None
                                }
                            }
                        )
        
        if total_earnings > 0:
            await UserRepository.add_money(user_id, total_earnings)
            
            await LogRepository.log_action(
                user_id, "crop_harvested", {"amount": total_earnings, "crops": harvested_crops}
            )
            
            crops_text = "\n".join([f"  {count}x {name}" for name, count in harvested_crops.items()])
            
            await update.message.reply_text(
                f"🌾 *Harvest Complete!*\n\n"
                f"Harvested:\n{crops_text}\n\n"
                f"Total earnings: {format_money(total_earnings)}"
            )
        else:
            await update.message.reply_text(
                "❌ No crops ready to harvest!\n\n"
                "Use `/plant <crop>` to plant crops and wait for them to grow."
            )
