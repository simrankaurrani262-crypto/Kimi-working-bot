"""
Telegram RPG Bot - Orders Module
===============================
Handles the /orders command for viewing orders.
"""

import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db, UserRepository
from utils.helpers import format_money
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class OrdersHandler:
    """Handles orders command for viewing orders."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /orders command."""
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
        
        # Get or generate orders
        orders = garden.get("orders", [])
        
        if not orders:
            # Generate new orders
            from modules.garden.plant import PlantHandler
            orders = OrdersHandler._generate_orders()
            db.gardens.update_one(
                {"user_id": user_id},
                {"$set": {"orders": orders}}
            )
        
        text = "📋 *Current Orders*\n\n"
        
        for i, order in enumerate(orders[:3], 1):
            text += (
                f"*{i}. {order['customer']}*\n"
                f"   Wants: {order['crop']}\n"
                f"   Amount: {order['amount']}\n"
                f"   Reward: {format_money(order['reward'])}\n\n"
            )
        
        keyboard = [
            [
                InlineKeyboardButton("🌱 Plant", callback_data="garden_plant"),
                InlineKeyboardButton("🌾 Harvest", callback_data="garden_harvest")
            ],
            [
                InlineKeyboardButton("🔄 New Orders", callback_data="orders_refresh")
            ]
        ]
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    @staticmethod
    def _generate_orders():
        """Generate random orders."""
        from modules.garden.plant import PlantHandler
        customers = ["Alice", "Bob", "Charlie", "Diana", "Eve"]
        crops = list(PlantHandler.CROPS.keys())
        
        orders = []
        for _ in range(3):
            crop_key = random.choice(crops)
            crop = PlantHandler.CROPS[crop_key]
            amount = random.randint(1, 5)
            reward = crop["sell_price"] * amount * 2  # Double price for orders
            
            orders.append({
                "customer": random.choice(customers),
                "crop": crop["name"],
                "crop_key": crop_key,
                "amount": amount,
                "reward": reward
            })
        
        return orders
