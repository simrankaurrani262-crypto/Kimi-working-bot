"""
Telegram RPG Bot - Weather Module
================================
Handles the /weather command for weather forecast.
"""

import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class WeatherHandler:
    """Handles weather command for weather forecast."""
    
    WEATHER_TYPES = {
        "sunny": {"emoji": "☀️", "name": "Sunny", "effect": "Crops grow 20% faster!"},
        "rainy": {"emoji": "🌧️", "name": "Rainy", "effect": "No watering needed today!"},
        "cloudy": {"emoji": "☁️", "name": "Cloudy", "effect": "Normal growing conditions."},
        "stormy": {"emoji": "⛈️", "name": "Stormy", "effect": "Crops grow 10% slower."},
    }
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /weather command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        # Generate weather (in a real bot, this would be stored and updated periodically)
        weather_key = random.choice(list(WeatherHandler.WEATHER_TYPES.keys()))
        weather = WeatherHandler.WEATHER_TYPES[weather_key]
        
        text = (
            f"🌤️ *Weather Forecast*\n\n"
            f"{weather['emoji']} *{weather['name']}*\n\n"
            f"Effect: {weather['effect']}\n\n"
            f"*Tip:* Check the weather before planting!"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("🌱 Plant", callback_data="garden_plant"),
                InlineKeyboardButton("🌾 Harvest", callback_data="garden_harvest")
            ],
            [
                InlineKeyboardButton("🌱 Garden", callback_data="garden_view")
            ]
        ]
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
