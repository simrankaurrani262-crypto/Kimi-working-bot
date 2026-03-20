"""
Telegram RPG Bot - Blackjack Module
==================================
Handles the /blackjack command for blackjack game.
"""

import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db, UserRepository, LogRepository
from utils.helpers import format_money
from utils.validators import UserValidator, validate_bet_amount

logger = logging.getLogger(__name__)


class BlackjackHandler:
    """Handles blackjack command for blackjack game."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /blackjack command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        user = await UserRepository.get_user(user_id)
        
        # Check arguments
        if not context.args:
            await update.message.reply_text(
                "🃏 *Blackjack*\n\n"
                "Get as close to 21 as possible without going over!\n\n"
                "• Beat the dealer to win 2x your bet\n"
                "• Blackjack (21) pays 2.5x\n\n"
                "Usage: `/blackjack <bet_amount>`"
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
        
        # Deal cards
        player_cards = [random.randint(1, 11), random.randint(1, 11)]
        dealer_cards = [random.randint(1, 11), random.randint(1, 11)]
        
        player_total = sum(player_cards)
        dealer_total = sum(dealer_cards)
        
        text = (
            f"🃏 *Blackjack*\n\n"
            f"Your cards: {player_cards[0]}, {player_cards[1]} = {player_total}\n"
            f"Dealer shows: {dealer_cards[0]}\n\n"
        )
        
        # Determine winner
        if player_total == 21:
            winnings = int(bet * 2.5)
            await UserRepository.add_money(user_id, winnings - bet)
            
            await LogRepository.log_action(
                user_id, "game_played", {"game": "blackjack", "bet": bet, "result": "blackjack"}
            )
            
            await update.message.reply_text(
                f"{text}"
                f"🎉 *BLACKJACK!* You win {format_money(winnings)}!"
            )
        elif player_total > 21:
            await UserRepository.remove_money(user_id, bet)
            
            await LogRepository.log_action(
                user_id, "game_played", {"game": "blackjack", "bet": bet, "result": "bust"}
            )
            
            await update.message.reply_text(
                f"{text}"
                f"😢 *Bust!* You lose {format_money(bet)}!"
            )
        elif dealer_total > 21 or player_total > dealer_total:
            winnings = bet * 2
            await UserRepository.add_money(user_id, winnings - bet)
            
            await LogRepository.log_action(
                user_id, "game_played", {"game": "blackjack", "bet": bet, "result": "win"}
            )
            
            await update.message.reply_text(
                f"{text}"
                f"Dealer has: {dealer_total}\n"
                f"🎉 *You win!* {format_money(winnings)}!"
            )
        elif player_total == dealer_total:
            await LogRepository.log_action(
                user_id, "game_played", {"game": "blackjack", "bet": bet, "result": "push"}
            )
            
            await update.message.reply_text(
                f"{text}"
                f"Dealer has: {dealer_total}\n"
                f"🤝 *Push!* Your bet is returned."
            )
        else:
            await UserRepository.remove_money(user_id, bet)
            
            await LogRepository.log_action(
                user_id, "game_played", {"game": "blackjack", "bet": bet, "result": "loss"}
            )
            
            await update.message.reply_text(
                f"{text}"
                f"Dealer has: {dealer_total}\n"
                f"😢 *You lose!* {format_money(bet)}!"
            )
