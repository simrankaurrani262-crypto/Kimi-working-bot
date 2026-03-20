"""
Telegram RPG Bot - Guess Module
==============================
Handles the /guess command for number guessing game.
"""

import logging
import random
from telegram import Update
from telegram.ext import ContextTypes

from database import db, UserRepository, LogRepository
from utils.helpers import format_money
from utils.validators import UserValidator, validate_bet_amount

logger = logging.getLogger(__name__)


class GuessHandler:
    """Handles guess command for number guessing game."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /guess command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        user = await UserRepository.get_user(user_id)
        
        # Check arguments
        if len(context.args) < 2:
            await update.message.reply_text(
                "🔢 *Number Guessing*\n\n"
                "Guess a number between 1 and 10!\n\n"
                "Rules:\n"
                "• Correct guess: Win 8x your bet\n"
                "• Wrong guess: Lose your bet\n\n"
                "Usage: `/guess <bet> <number 1-10>`"
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
        
        # Parse guess
        try:
            guess = int(context.args[1])
        except ValueError:
            await update.message.reply_text("❌ Invalid number!")
            return
        
        if guess < 1 or guess > 10:
            await update.message.reply_text("❌ Number must be between 1 and 10!")
            return
        
        if user["money"] < bet:
            await update.message.reply_text(
                f"❌ Insufficient funds!\n"
                f"Your balance: {format_money(user['money'])}"
            )
            return
        
        # Generate winning number
        winning = random.randint(1, 10)
        
        if guess == winning:
            winnings = bet * 8
            await UserRepository.add_money(user_id, winnings - bet)
            
            await LogRepository.log_action(
                user_id, "game_played", {"game": "guess", "bet": bet, "result": "win", "guess": guess, "winning": winning}
            )
            
            await update.message.reply_text(
                f"🔢 *Correct!*\n\n"
                f"The number was {winning}!\n"
                f"🎉 You win {format_money(winnings)}!"
            )
        else:
            await UserRepository.remove_money(user_id, bet)
            
            await LogRepository.log_action(
                user_id, "game_played", {"game": "guess", "bet": bet, "result": "loss", "guess": guess, "winning": winning}
            )
            
            await update.message.reply_text(
                f"🔢 *Wrong!*\n\n"
                f"You guessed {guess}, but the number was {winning}!\n"
                f"😢 You lose {format_money(bet)}!"
            )
