"""
Telegram RPG Bot - Lottery Module
================================
Handles the /lottery command for lottery game.
"""

import logging
import random
from telegram import Update
from telegram.ext import ContextTypes

from database import db, UserRepository, LogRepository
from utils.helpers import format_money
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class LotteryHandler:
    """Handles lottery command for lottery game."""
    
    TICKET_PRICE = 100
    JACKPOT = 10000
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /lottery command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        user = await UserRepository.get_user(user_id)
        
        # Check arguments
        if not context.args:
            await update.message.reply_text(
                f"🎫 *Lottery*\n\n"
                f"Ticket price: {format_money(LotteryHandler.TICKET_PRICE)}\n"
                f"Jackpot: {format_money(LotteryHandler.JACKPOT)}\n\n"
                f"Usage: `/lottery buy` to purchase a ticket"
            )
            return
        
        if context.args[0].lower() != "buy":
            await update.message.reply_text("Usage: `/lottery buy`")
            return
        
        if user["money"] < LotteryHandler.TICKET_PRICE:
            await update.message.reply_text(
                f"❌ Insufficient funds!\n"
                f"Ticket price: {format_money(LotteryHandler.TICKET_PRICE)}"
            )
            return
        
        # Buy ticket
        await UserRepository.remove_money(user_id, LotteryHandler.TICKET_PRICE)
        
        # Draw numbers
        winning_numbers = sorted(random.sample(range(1, 50), 6))
        player_numbers = sorted(random.sample(range(1, 50), 6))
        
        matches = len(set(winning_numbers) & set(player_numbers))
        
        text = (
            f"🎫 *Lottery Results*\n\n"
            f"Winning numbers: {winning_numbers}\n"
            f"Your numbers: {player_numbers}\n"
            f"Matches: {matches}/6\n\n"
        )
        
        if matches == 6:
            await UserRepository.add_money(user_id, LotteryHandler.JACKPOT)
            
            await LogRepository.log_action(
                user_id, "lottery_won", {"jackpot": LotteryHandler.JACKPOT}
            )
            
            await update.message.reply_text(
                f"{text}"
                f"🎉 *JACKPOT!* You win {format_money(LotteryHandler.JACKPOT)}!!!"
            )
        elif matches >= 3:
            prize = LotteryHandler.TICKET_PRICE * matches
            await UserRepository.add_money(user_id, prize)
            
            await LogRepository.log_action(
                user_id, "lottery_won", {"prize": prize, "matches": matches}
            )
            
            await update.message.reply_text(
                f"{text}"
                f"🎉 You win {format_money(prize)}!"
            )
        else:
            await LogRepository.log_action(
                user_id, "lottery_lost", {"matches": matches}
            )
            
            await update.message.reply_text(
                f"{text}"
                f"😢 No win this time. Try again!"
            )
