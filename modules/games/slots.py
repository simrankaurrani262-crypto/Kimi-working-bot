"""
Telegram RPG Bot - Slots Module
==============================
Handles the /slots command for slot machine game.
"""

import logging
import random
from telegram import Update
from telegram.ext import ContextTypes

from database import db, UserRepository, LogRepository
from utils.helpers import format_money
from utils.validators import UserValidator, validate_bet_amount

logger = logging.getLogger(__name__)


class SlotsHandler:
    """Handles slots command for slot machine game."""
    
    SYMBOLS = ["🍒", "🍋", "🍊", "🍇", "💎", "7️⃣"]
    PAYOUTS = {
        "🍒🍒🍒": 3,
        "🍋🍋🍋": 4,
        "🍊🍊🍊": 5,
        "🍇🍇🍇": 8,
        "💎💎💎": 15,
        "7️⃣7️⃣7️⃣": 50,
    }
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /slots command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        user = await UserRepository.get_user(user_id)
        
        # Check arguments
        if not context.args:
            await update.message.reply_text(
                "🎰 *Slot Machine*\n\n"
                "Match 3 symbols to win!\n\n"
                "Payouts:\n"
                "🍒🍒🍒 3x | 🍋🍋🍋 4x\n"
                "🍊🍊🍊 5x | 🍇🍇🍇 8x\n"
                "💎💎💎 15x | 7️⃣7️⃣7️⃣ 50x\n\n"
                "Usage: `/slots <bet_amount>`"
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
        
        # Spin slots
        result = [random.choice(SlotsHandler.SYMBOLS) for _ in range(3)]
        result_str = "".join(result)
        
        # Check for win
        payout = SlotsHandler.PAYOUTS.get(result_str, 0)
        
        if payout > 0:
            winnings = bet * payout
            await UserRepository.add_money(user_id, winnings - bet)
            
            await LogRepository.log_action(
                user_id, "game_played", {"game": "slots", "bet": bet, "result": "win", "symbols": result_str}
            )
            
            await update.message.reply_text(
                f"🎰 *{result[0]} | {result[1]} | {result[2]}*\n\n"
                f"🎉 JACKPOT! You win {format_money(winnings)}!\n"
                f"Payout: {payout}x"
            )
        else:
            await UserRepository.remove_money(user_id, bet)
            
            await LogRepository.log_action(
                user_id, "game_played", {"game": "slots", "bet": bet, "result": "loss", "symbols": result_str}
            )
            
            await update.message.reply_text(
                f"🎰 *{result[0]} | {result[1]} | {result[2]}*\n\n"
                f"😢 No match! You lose {format_money(bet)}!"
            )
        
        # Update stats
        db.stats.update_one(
            {"user_id": user_id},
            {
                "$inc": {
                    "games_played": 1,
                    "games_won": 1 if payout > 0 else 0,
                    "total_winnings": winnings - bet if payout > 0 else 0,
                    "total_losses": bet if payout == 0 else 0
                }
            },
            upsert=True
        )
