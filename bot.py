"""
Telegram RPG Bot - Main Application
==================================
Family Tree Life Simulation RPG Bot for Telegram.

Features:
- Complete family tree system with visual generation
- Economy, crime, factory, farming systems
- Mini-games and leaderboards
- Friend system and social features
"""

import logging
import asyncio
from typing import Optional

from telegram import Update, BotCommand, MenuButtonCommands
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes
)

from config import bot_config, validate_config, game_config
from database import init_database, db

# Import all module handlers
from modules.core.start import StartHandler
from modules.core.help import HelpHandler
from modules.core.profile import ProfileHandler
from modules.core.settings import SettingsHandler
from modules.core.stats import StatsHandler
from modules.core.activity import ActivityHandler

from modules.family.family import FamilyHandler
from modules.family.tree import TreeHandler
from modules.family.adopt import AdoptHandler
from modules.family.marry import MarryHandler
from modules.family.divorce import DivorceHandler
from modules.family.disown import DisownHandler
from modules.family.relations import RelationsHandler

from modules.friends.friend import FriendHandler
from modules.friends.unfriend import UnfriendHandler
from modules.friends.circle import CircleHandler
from modules.friends.ratings import RatingsHandler
from modules.friends.suggestions import SuggestionsHandler

from modules.economy.daily import DailyHandler
from modules.economy.account import AccountHandler
from modules.economy.pay import PayHandler
from modules.economy.deposit import DepositHandler
from modules.economy.withdraw import WithdrawHandler
from modules.economy.jobs import JobsHandler
from modules.economy.work import WorkHandler
from modules.economy.shop import ShopHandler
from modules.economy.buy import BuyHandler
from modules.economy.sell import SellHandler
from modules.economy.inventory import InventoryHandler
from modules.economy.balance import BalanceHandler
from modules.economy.transfer import TransferHandler
from modules.economy.loan import LoanHandler
from modules.economy.repay import RepayHandler
from modules.economy.bank import BankHandler

from modules.crime.rob import RobHandler
from modules.crime.kill import KillHandler
from modules.crime.weapon import WeaponHandler
from modules.crime.buyweapon import BuyWeaponHandler
from modules.crime.insurance import InsuranceHandler
from modules.crime.medical import MedicalHandler
from modules.crime.jail import JailHandler
from modules.crime.bail import BailHandler

from modules.factory.factory import FactoryHandler
from modules.factory.hire import HireHandler
from modules.factory.fire import FireHandler
from modules.factory.workers import WorkersHandler
from modules.factory.production import ProductionHandler
from modules.factory.factoryupgrade import FactoryUpgradeHandler

from modules.garden.garden import GardenHandler
from modules.garden.add import GardenAddHandler
from modules.garden.plant import PlantHandler
from modules.garden.harvest import HarvestHandler
from modules.garden.fertilise import FertiliseHandler
from modules.garden.barn import BarnHandler
from modules.garden.orders import OrdersHandler
from modules.garden.seeds import SeedsHandler
from modules.garden.weather import WeatherHandler

from modules.market.stand import StandHandler
from modules.market.stands import StandsHandler
from modules.market.putstand import PutStandHandler
from modules.market.trade import TradeHandler
from modules.market.gift import GiftHandler
from modules.market.auction import AuctionHandler
from modules.market.bid import BidHandler

from modules.games.fourpics import FourPicsHandler
from modules.games.ripple import RippleHandler
from modules.games.lottery import LotteryHandler
from modules.games.nation import NationHandler
from modules.games.quiz import QuizHandler
from modules.games.dice import DiceHandler
from modules.games.blackjack import BlackjackHandler
from modules.games.slots import SlotsHandler
from modules.games.guess import GuessHandler
from modules.games.trivia import TriviaHandler

from modules.stats.leaderboard import LeaderboardHandler
from modules.stats.moneyboard import MoneyBoardHandler
from modules.stats.familyboard import FamilyBoardHandler
from modules.stats.factoryboard import FactoryBoardHandler
from modules.stats.moneygraph import MoneyGraphHandler

from modules.admin.ban import BanHandler
from modules.admin.unban import UnbanHandler
from modules.admin.broadcast import BroadcastHandler
from modules.admin.adminstats import AdminStatsHandler
from modules.admin.logs import AdminLogsHandler

from utils.logger import setup_logging
from utils.cooldown import CooldownManager

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


class RPGBot:
    """Main RPG Bot class."""
    
    def __init__(self):
        self.application: Optional[Application] = None
        self.cooldown_manager = CooldownManager()
    
    async def setup_commands(self, application: Application) -> None:
        """Setup bot commands menu."""
        commands = [
            # Core Commands
            BotCommand("start", "Start the bot and create profile"),
            BotCommand("help", "Show help menu"),
            BotCommand("profile", "View your profile"),
            BotCommand("settings", "Bot settings"),
            BotCommand("stats", "Your statistics"),
            BotCommand("activity", "Your activity"),
            
            # Family Commands
            BotCommand("family", "Family information"),
            BotCommand("tree", "View family tree"),
            BotCommand("fulltree", "View full family tree image"),
            BotCommand("adopt", "Adopt a child"),
            BotCommand("marry", "Marry someone"),
            BotCommand("divorce", "Divorce your partner"),
            BotCommand("disown", "Disown a child"),
            BotCommand("relations", "View relationships"),
            BotCommand("parents", "View your parents"),
            BotCommand("children", "View your children"),
            
            # Friends Commands
            BotCommand("friend", "Add a friend"),
            BotCommand("unfriend", "Remove a friend"),
            BotCommand("friends", "Your friends list"),
            BotCommand("circle", "Your friend circle"),
            BotCommand("suggestions", "Friend suggestions"),
            BotCommand("ratings", "Friend ratings"),
            
            # Economy Commands
            BotCommand("daily", "Claim daily reward"),
            BotCommand("account", "Bank account info"),
            BotCommand("pay", "Pay someone"),
            BotCommand("deposit", "Deposit to bank"),
            BotCommand("withdraw", "Withdraw from bank"),
            BotCommand("job", "View/change job"),
            BotCommand("work", "Work for money"),
            BotCommand("shop", "View shop"),
            BotCommand("buy", "Buy item"),
            BotCommand("sell", "Sell item"),
            BotCommand("inventory", "Your inventory"),
            BotCommand("balance", "Check balance"),
            BotCommand("transfer", "Transfer money"),
            BotCommand("loan", "Take a loan"),
            BotCommand("repay", "Repay loan"),
            BotCommand("bank", "Bank operations"),
            
            # Crime Commands
            BotCommand("rob", "Rob someone"),
            BotCommand("kill", "Attack someone"),
            BotCommand("weapon", "Your weapons"),
            BotCommand("buyweapon", "Buy weapon"),
            BotCommand("insurance", "Insurance info"),
            BotCommand("medical", "Medical services"),
            BotCommand("jail", "Jail status"),
            BotCommand("bail", "Pay bail"),
            
            # Factory Commands
            BotCommand("factory", "Your factory"),
            BotCommand("hire", "Hire workers"),
            BotCommand("fire", "Fire workers"),
            BotCommand("workers", "Your workers"),
            BotCommand("production", "Factory production"),
            BotCommand("factoryupgrade", "Upgrade factory"),
            
            # Garden Commands
            BotCommand("garden", "Your garden"),
            BotCommand("add", "Add plot to garden"),
            BotCommand("plant", "Plant seeds"),
            BotCommand("harvest", "Harvest crops"),
            BotCommand("fertilise", "Fertilise crops"),
            BotCommand("barn", "Your barn"),
            BotCommand("orders", "View orders"),
            BotCommand("seeds", "Your seeds"),
            BotCommand("weather", "Weather forecast"),
            
            # Market Commands
            BotCommand("stand", "Your market stand"),
            BotCommand("stands", "View all stands"),
            BotCommand("putstand", "Put item for sale"),
            BotCommand("trade", "Trade with someone"),
            BotCommand("gift", "Gift item"),
            BotCommand("auction", "View auctions"),
            BotCommand("bid", "Place bid"),
            
            # Games Commands
            BotCommand("fourpics", "4 Pics 1 Word game"),
            BotCommand("ripple", "Ripple game"),
            BotCommand("lottery", "Buy lottery ticket"),
            BotCommand("nation", "Nation guessing"),
            BotCommand("quiz", "Quiz game"),
            BotCommand("dice", "Dice game"),
            BotCommand("blackjack", "Blackjack"),
            BotCommand("slots", "Slot machine"),
            BotCommand("guess", "Number guessing"),
            BotCommand("trivia", "Trivia game"),
            
            # Leaderboard Commands
            BotCommand("leaderboard", "Top players"),
            BotCommand("moneyboard", "Richest players"),
            BotCommand("familyboard", "Top families"),
            BotCommand("factoryboard", "Top factories"),
            BotCommand("moneygraph", "Money history graph"),
            
            # Admin Commands (hidden from menu)
        ]
        
        await application.bot.set_my_commands(commands)
        await application.bot.set_chat_menu_button(menu_button=MenuButtonCommands())
        logger.info("Bot commands menu set up successfully")
    
    def register_handlers(self, application: Application) -> None:
        """Register all command handlers."""
        # Core handlers
        application.add_handler(CommandHandler("start", StartHandler.handle))
        application.add_handler(CommandHandler("help", HelpHandler.handle))
        application.add_handler(CommandHandler("profile", ProfileHandler.handle))
        application.add_handler(CommandHandler("settings", SettingsHandler.handle))
        application.add_handler(CommandHandler("stats", StatsHandler.handle))
        application.add_handler(CommandHandler("activity", ActivityHandler.handle))
        
        # Family handlers
        application.add_handler(CommandHandler("family", FamilyHandler.handle))
        application.add_handler(CommandHandler("tree", TreeHandler.handle))
        application.add_handler(CommandHandler("fulltree", TreeHandler.handle_full))
        application.add_handler(CommandHandler("adopt", AdoptHandler.handle))
        application.add_handler(CommandHandler("marry", MarryHandler.handle))
        application.add_handler(CommandHandler("divorce", DivorceHandler.handle))
        application.add_handler(CommandHandler("disown", DisownHandler.handle))
        application.add_handler(CommandHandler("relations", RelationsHandler.handle))
        application.add_handler(CommandHandler("parents", RelationsHandler.handle_parents))
        application.add_handler(CommandHandler("children", RelationsHandler.handle_children))
        
        # Friends handlers
        application.add_handler(CommandHandler("friend", FriendHandler.handle))
        application.add_handler(CommandHandler("unfriend", UnfriendHandler.handle))
        application.add_handler(CommandHandler("friends", CircleHandler.handle_friends))
        application.add_handler(CommandHandler("circle", CircleHandler.handle))
        application.add_handler(CommandHandler("suggestions", SuggestionsHandler.handle))
        application.add_handler(CommandHandler("ratings", RatingsHandler.handle))
        
        # Economy handlers
        application.add_handler(CommandHandler("daily", DailyHandler.handle))
        application.add_handler(CommandHandler("account", AccountHandler.handle))
        application.add_handler(CommandHandler("pay", PayHandler.handle))
        application.add_handler(CommandHandler("deposit", DepositHandler.handle))
        application.add_handler(CommandHandler("withdraw", WithdrawHandler.handle))
        application.add_handler(CommandHandler("job", JobsHandler.handle))
        application.add_handler(CommandHandler("work", WorkHandler.handle))
        application.add_handler(CommandHandler("shop", ShopHandler.handle))
        application.add_handler(CommandHandler("buy", BuyHandler.handle))
        application.add_handler(CommandHandler("sell", SellHandler.handle))
        application.add_handler(CommandHandler("inventory", InventoryHandler.handle))
        application.add_handler(CommandHandler("balance", BalanceHandler.handle))
        application.add_handler(CommandHandler("transfer", TransferHandler.handle))
        application.add_handler(CommandHandler("loan", LoanHandler.handle))
        application.add_handler(CommandHandler("repay", RepayHandler.handle))
        application.add_handler(CommandHandler("bank", BankHandler.handle))
        
        # Crime handlers
        application.add_handler(CommandHandler("rob", RobHandler.handle))
        application.add_handler(CommandHandler("kill", KillHandler.handle))
        application.add_handler(CommandHandler("weapon", WeaponHandler.handle))
        application.add_handler(CommandHandler("buyweapon", BuyWeaponHandler.handle))
        application.add_handler(CommandHandler("insurance", InsuranceHandler.handle))
        application.add_handler(CommandHandler("medical", MedicalHandler.handle))
        application.add_handler(CommandHandler("jail", JailHandler.handle))
        application.add_handler(CommandHandler("bail", BailHandler.handle))
        
        # Factory handlers
        application.add_handler(CommandHandler("factory", FactoryHandler.handle))
        application.add_handler(CommandHandler("hire", HireHandler.handle))
        application.add_handler(CommandHandler("fire", FireHandler.handle))
        application.add_handler(CommandHandler("workers", WorkersHandler.handle))
        application.add_handler(CommandHandler("production", ProductionHandler.handle))
        application.add_handler(CommandHandler("factoryupgrade", FactoryUpgradeHandler.handle))
        
        # Garden handlers
        application.add_handler(CommandHandler("garden", GardenHandler.handle))
        application.add_handler(CommandHandler("add", GardenAddHandler.handle))
        application.add_handler(CommandHandler("plant", PlantHandler.handle))
        application.add_handler(CommandHandler("harvest", HarvestHandler.handle))
        application.add_handler(CommandHandler("fertilise", FertiliseHandler.handle))
        application.add_handler(CommandHandler("barn", BarnHandler.handle))
        application.add_handler(CommandHandler("orders", OrdersHandler.handle))
        application.add_handler(CommandHandler("seeds", SeedsHandler.handle))
        application.add_handler(CommandHandler("weather", WeatherHandler.handle))
        
        # Market handlers
        application.add_handler(CommandHandler("stand", StandHandler.handle))
        application.add_handler(CommandHandler("stands", StandsHandler.handle))
        application.add_handler(CommandHandler("putstand", PutStandHandler.handle))
        application.add_handler(CommandHandler("trade", TradeHandler.handle))
        application.add_handler(CommandHandler("gift", GiftHandler.handle))
        application.add_handler(CommandHandler("auction", AuctionHandler.handle))
        application.add_handler(CommandHandler("bid", BidHandler.handle))
        
        # Games handlers
        application.add_handler(CommandHandler("fourpics", FourPicsHandler.handle))
        application.add_handler(CommandHandler("ripple", RippleHandler.handle))
        application.add_handler(CommandHandler("lottery", LotteryHandler.handle))
        application.add_handler(CommandHandler("nation", NationHandler.handle))
        application.add_handler(CommandHandler("quiz", QuizHandler.handle))
        application.add_handler(CommandHandler("dice", DiceHandler.handle))
        application.add_handler(CommandHandler("blackjack", BlackjackHandler.handle))
        application.add_handler(CommandHandler("slots", SlotsHandler.handle))
        application.add_handler(CommandHandler("guess", GuessHandler.handle))
        application.add_handler(CommandHandler("trivia", TriviaHandler.handle))
        
        # Leaderboard handlers
        application.add_handler(CommandHandler("leaderboard", LeaderboardHandler.handle))
        application.add_handler(CommandHandler("moneyboard", MoneyBoardHandler.handle))
        application.add_handler(CommandHandler("familyboard", FamilyBoardHandler.handle))
        application.add_handler(CommandHandler("factoryboard", FactoryBoardHandler.handle))
        application.add_handler(CommandHandler("moneygraph", MoneyGraphHandler.handle))
        
        # Admin handlers
        application.add_handler(CommandHandler("ban", BanHandler.handle))
        application.add_handler(CommandHandler("unban", UnbanHandler.handle))
        application.add_handler(CommandHandler("broadcast", BroadcastHandler.handle))
        application.add_handler(CommandHandler("adminstats", AdminStatsHandler.handle))
        application.add_handler(CommandHandler("logs", AdminLogsHandler.handle))
        
        # Callback query handlers
        application.add_handler(CallbackQueryHandler(HelpHandler.handle_callback, pattern="^help_"))
        application.add_handler(CallbackQueryHandler(ShopHandler.handle_callback, pattern="^shop_"))
        application.add_handler(CallbackQueryHandler(TreeHandler.handle_callback, pattern="^tree_"))
        application.add_handler(CallbackQueryHandler(FamilyHandler.handle_callback, pattern="^family_"))
        application.add_handler(CallbackQueryHandler(SettingsHandler.handle_callback, pattern="^settings_"))
        
        logger.info("All handlers registered successfully")
    
    async def post_init(self, application: Application) -> None:
        """Post-initialization tasks."""
        await self.setup_commands(application)
        logger.info("Bot post-initialization completed")
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors."""
        logger.error(f"Update {update} caused error: {context.error}")
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ An error occurred. Please try again later."
            )
    
    def run(self) -> None:
        """Run the bot."""
        # Validate configuration
        error = validate_config()
        if error:
            logger.error(f"Configuration error: {error}")
            return
        
        # Initialize database
        if not init_database():
            logger.error("Failed to initialize database")
            return
        
        # Build application
        self.application = Application.builder().token(bot_config.TOKEN).build()
        
        # Register handlers
        self.register_handlers(self.application)
        
        # Add error handler
        self.application.add_error_handler(self.error_handler)
        
        # Setup post-init
        self.application.post_init = self.post_init
        
        logger.info("Starting bot...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Main entry point."""
    bot = RPGBot()
    bot.run()


if __name__ == "__main__":
    main()
