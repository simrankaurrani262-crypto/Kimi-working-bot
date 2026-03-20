"""
Telegram RPG Bot - Garden Add Module
===================================
Handles the /add command for adding plots.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from database import db, UserRepository
from utils.helpers import format_money
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class GardenAddHandler:
    """Handles add command for adding plots."""
    
    PLOT_COST = 500
    MAX_PLOTS = 10
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /add command."""
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
        
        current_plots = len(garden.get("plots", []))
        
        if current_plots >= GardenAddHandler.MAX_PLOTS:
            await update.message.reply_text(
                f"❌ You already have the maximum number of plots ({GardenAddHandler.MAX_PLOTS})!"
            )
            return
        
        # Check arguments
        if not context.args:
            await update.message.reply_text(
                f"➕ *Add Plot*\n\n"
                f"Cost per plot: {format_money(GardenAddHandler.PLOT_COST)}\n"
                f"Current plots: {current_plots}/{GardenAddHandler.MAX_PLOTS}\n\n"
                f"Usage: `/add <amount>` or `/add 1`"
            )
            return
        
        try:
            amount = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid amount!")
            return
        
        if amount <= 0:
            await update.message.reply_text("❌ Amount must be positive!")
            return
        
        if current_plots + amount > GardenAddHandler.MAX_PLOTS:
            await update.message.reply_text(
                f"❌ You can only add {GardenAddHandler.MAX_PLOTS - current_plots} more plots!"
            )
            return
        
        user = await UserRepository.get_user(user_id)
        total_cost = GardenAddHandler.PLOT_COST * amount
        
        if user["money"] < total_cost:
            await update.message.reply_text(
                f"❌ Insufficient funds!\n"
                f"Cost: {format_money(total_cost)}\n"
                f"Your balance: {format_money(user['money'])}"
            )
            return
        
        # Add plots
        await UserRepository.remove_money(user_id, total_cost)
        
        new_plots = [{"index": current_plots + i, "crop": None, "status": "empty"} 
                     for i in range(amount)]
        
        db.gardens.update_one(
            {"user_id": user_id},
            {"$push": {"plots": {"$each": new_plots}}}
        )
        
        await update.message.reply_text(
            f"➕ *Plots Added!*\n\n"
            f"Added: {amount} plot(s)\n"
            f"Cost: {format_money(total_cost)}\n"
            f"Total plots: {current_plots + amount}"
        )
