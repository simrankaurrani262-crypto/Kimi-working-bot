"""
Telegram RPG Bot - Dice Module
=============================
Handles the /dice command for dice game.
"""

import logging
import random
from telegram import Update
from telegram.ext import ContextTypes

from database import db, UserRepository, LogRepository
from utils.helpers import format_money
from utils.validators import UserValidator, validate_bet_amount

logger = logging.getLogger(__name__)


class DiceHandler:
    """Handles dice command for dice game."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /dice command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        user = await UserRepository.get_user(user_id)
        
        # Check arguments
        if not context.args:
            await update.message.reply_text(
                "🎲 *Dice Game*\n\n"
                "Roll the dice and win!\n\n"
                "Rules:\n"
                "• Roll 4, 5, or 6: Win 1.5x your bet\n"
                "• Roll 1, 2, or 3: Lose your bet\n\n"
                "Usage: `/dice <bet_amount>`"
            )
            return
        
        # Parse bet
        try:
            bet = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid bet amount!")
            return
        
        valid, error = validate_bet_amount(bet)
        if not valid:
            await update.message.reply_text(f"❌ {error}")
            return
        
        if user["money"] < bet:
            await update.message.reply_text(
                f"❌ Insufficient funds!\n"
                f"Your balance: {format_money(user['money'])}"
            )
            return
        
        # Roll dice
        roll = random.randint(1, 6)
        
        # Determine outcome
        if roll >= 4:
            winnings = int(bet * 1.5)
            await UserRepository.add_money(user_id, winnings - bet)
            result = "win"
            
            await LogRepository.log_action(
                user_id, "game_played", {"game": "dice", "bet": bet, "result": "win", "roll": roll}
            )
            
            await update.message.reply_text(
                f"🎲 *You rolled a {roll}!*\n\n"
                f"🎉 You win {format_money(winnings)}!\n"
                f"Profit: {format_money(winnings - bet)}"
            )
        else:
            await UserRepository.remove_money(user_id, bet)
            result = "loss"
            
            await LogRepository.log_action(
                user_id, "game_played", {"game": "dice", "bet": bet, "result": "loss", "roll": roll}
            )
            
            await update.message.reply_text(
                f"🎲 *You rolled a {roll}!*\n\n"
                f"😢 You lose {format_money(bet)}!"
            )
        
        # Update stats
        db.stats.update_one(
            {"user_id": user_id},
            {
                "$inc": {
                    "games_played": 1,
                    "games_won": 1 if result == "win" else 0,
                    "total_winnings": winnings - bet if result == "win" else 0,
                    "total_losses": bet if result == "loss" else 0
                }
            },
            upsert=True
        )
