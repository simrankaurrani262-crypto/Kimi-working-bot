"""
Telegram RPG Bot - Fertilise Module
==================================
Handles the /fertilise command for fertilising crops.
"""

import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes

from database import db, UserRepository, LogRepository
from utils.helpers import format_money
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class FertiliseHandler:
    """Handles fertilise command for fertilising crops."""
    
    FERTILIZER_COST = 200
    SPEED_UP_PERCENT = 0.5  # 50% faster
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /fertilise command."""
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
        
        # Find growing crops
        growing_plots = [p for p in plots if p.get("status") == "growing"]
        
        if not growing_plots:
            await update.message.reply_text(
                "❌ No growing crops to fertilise!\n\n"
                "Use `/plant <crop>` to plant crops first."
            )
            return
        
        user = await UserRepository.get_user(user_id)
        
        if user["money"] < FertiliseHandler.FERTILIZER_COST:
            await update.message.reply_text(
                f"❌ Insufficient funds!\n"
                f"Cost: {format_money(FertiliseHandler.FERTILIZER_COST)}"
            )
            return
        
        # Fertilise all growing crops
        await UserRepository.remove_money(user_id, FertiliseHandler.FERTILIZER_COST)
        
        fertilised_count = 0
        for plot in growing_plots:
            mature_at = plot.get("mature_at")
            if mature_at:
                # Speed up growth
                time_remaining = (mature_at - datetime.utcnow()).total_seconds()
                new_time_remaining = time_remaining * (1 - FertiliseHandler.SPEED_UP_PERCENT)
                new_mature_at = datetime.utcnow() + timedelta(seconds=new_time_remaining)
                
                db.gardens.update_one(
                    {"user_id": user_id, "plots.index": plot["index"]},
                    {"$set": {"plots.$.mature_at": new_mature_at}}
                )
                fertilised_count += 1
        
        await LogRepository.log_action(
            user_id, "crop_fertilised", {"count": fertilised_count, "cost": FertiliseHandler.FERTILIZER_COST}
        )
        
        await update.message.reply_text(
            f"⚡ *Crops Fertilised!*\n\n"
            f"Fertilised: {fertilised_count} crop(s)\n"
            f"Cost: {format_money(FertiliseHandler.FERTILIZER_COST)}\n"
            f"Growth speed increased by {int(FertiliseHandler.SPEED_UP_PERCENT * 100)}%!"
        )
