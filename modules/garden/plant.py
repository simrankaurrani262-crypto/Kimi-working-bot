"""
Telegram RPG Bot - Plant Module
==============================
Handles the /plant command for planting crops.
"""

import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes

from database import db, UserRepository, LogRepository
from utils.helpers import format_money
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class PlantHandler:
    """Handles plant command for planting crops."""
    
    CROPS = {
        "wheat": {"name": "🌾 Wheat", "cost": 50, "grow_time": 3600, "sell_price": 100},
        "corn": {"name": "🌽 Corn", "cost": 100, "grow_time": 7200, "sell_price": 250},
        "tomato": {"name": "🍅 Tomato", "cost": 150, "grow_time": 5400, "sell_price": 350},
        "carrot": {"name": "🥕 Carrot", "cost": 80, "grow_time": 4500, "sell_price": 180},
        "potato": {"name": "🥔 Potato", "cost": 120, "grow_time": 6000, "sell_price": 280},
    }
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /plant command."""
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
        
        # Check arguments
        if not context.args:
            text = "🌱 *Plant Crops*\n\n"
            for key, crop in PlantHandler.CROPS.items():
                text += (
                    f"`{key}` - {crop['name']}\n"
                    f"   Cost: {format_money(crop['cost'])}\n"
                    f"   Grow time: {crop['grow_time'] // 3600}h\n"
                    f"   Sell price: {format_money(crop['sell_price'])}\n\n"
                )
            text += "Usage: `/plant <crop_type>`"
            
            await update.message.reply_text(text, parse_mode='Markdown')
            return
        
        crop_key = context.args[0].lower()
        crop = PlantHandler.CROPS.get(crop_key)
        
        if not crop:
            await update.message.reply_text("❌ Invalid crop type!")
            return
        
        # Find empty plot
        plots = garden.get("plots", [])
        empty_plot = None
        for plot in plots:
            if plot.get("status") == "empty":
                empty_plot = plot
                break
        
        if not empty_plot:
            await update.message.reply_text(
                "❌ No empty plots! Add more with `/add` or harvest existing crops."
            )
            return
        
        user = await UserRepository.get_user(user_id)
        
        if user["money"] < crop["cost"]:
            await update.message.reply_text(
                f"❌ Insufficient funds!\n"
                f"Cost: {format_money(crop['cost'])}"
            )
            return
        
        # Plant crop
        await UserRepository.remove_money(user_id, crop["cost"])
        
        mature_time = datetime.utcnow() + timedelta(seconds=crop["grow_time"])
        
        db.gardens.update_one(
            {"user_id": user_id, "plots.index": empty_plot["index"]},
            {
                "$set": {
                    "plots.$.crop": crop_key,
                    "plots.$.status": "growing",
                    "plots.$.planted_at": datetime.utcnow(),
                    "plots.$.mature_at": mature_time
                }
            }
        )
        
        await LogRepository.log_action(
            user_id, "crop_planted", {"crop": crop_key, "cost": crop["cost"]}
        )
        
        await update.message.reply_text(
            f"🌱 *Crop Planted!*\n\n"
            f"Planted: {crop['name']}\n"
            f"Cost: {format_money(crop['cost'])}\n"
            f"Will be ready in {crop['grow_time'] // 3600} hours!"
        )
