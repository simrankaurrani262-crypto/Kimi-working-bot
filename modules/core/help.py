"""
Telegram RPG Bot - Help Module
=============================
Handles the /help command and command documentation.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


class HelpHandler:
    """Handles help command and documentation."""
    
    # Command categories
    CATEGORIES = {
        "core": {
            "name": "🎯 Core Commands",
            "commands": [
                ("/start", "Start the bot and create profile"),
                ("/help", "Show this help menu"),
                ("/profile", "View your profile"),
                ("/settings", "Bot settings"),
                ("/stats", "Your statistics"),
                ("/activity", "Your activity log"),
            ]
        },
        "family": {
            "name": "👨‍👩‍👧‍👦 Family Commands",
            "commands": [
                ("/family", "Family information"),
                ("/tree", "View family tree (text)"),
                ("/fulltree", "View family tree (image)"),
                ("/adopt", "Adopt a child"),
                ("/marry", "Marry someone"),
                ("/divorce", "Divorce your partner"),
                ("/disown", "Disown a child"),
                ("/relations", "View relationships"),
                ("/parents", "View your parents"),
                ("/children", "View your children"),
            ]
        },
        "friends": {
            "name": "👥 Friends Commands",
            "commands": [
                ("/friend", "Add a friend"),
                ("/unfriend", "Remove a friend"),
                ("/friends", "Your friends list"),
                ("/circle", "Your friend circle"),
                ("/suggestions", "Friend suggestions"),
                ("/ratings", "Friend ratings"),
            ]
        },
        "economy": {
            "name": "💰 Economy Commands",
            "commands": [
                ("/daily", "Claim daily reward"),
                ("/account", "Bank account info"),
                ("/pay", "Pay someone"),
                ("/deposit", "Deposit to bank"),
                ("/withdraw", "Withdraw from bank"),
                ("/job", "View/change job"),
                ("/work", "Work for money"),
                ("/shop", "View shop"),
                ("/buy", "Buy item"),
                ("/sell", "Sell item"),
                ("/inventory", "Your inventory"),
                ("/balance", "Check balance"),
                ("/transfer", "Transfer money"),
                ("/loan", "Take a loan"),
                ("/repay", "Repay loan"),
                ("/bank", "Bank operations"),
            ]
        },
        "crime": {
            "name": "🔪 Crime Commands",
            "commands": [
                ("/rob", "Rob someone"),
                ("/kill", "Attack someone"),
                ("/weapon", "Your weapons"),
                ("/buyweapon", "Buy weapon"),
                ("/insurance", "Insurance info"),
                ("/medical", "Medical services"),
                ("/jail", "Jail status"),
                ("/bail", "Pay bail"),
            ]
        },
        "factory": {
            "name": "🏭 Factory Commands",
            "commands": [
                ("/factory", "Your factory"),
                ("/hire", "Hire workers"),
                ("/fire", "Fire workers"),
                ("/workers", "Your workers"),
                ("/production", "Factory production"),
                ("/factoryupgrade", "Upgrade factory"),
            ]
        },
        "garden": {
            "name": "🌱 Garden Commands",
            "commands": [
                ("/garden", "Your garden"),
                ("/add", "Add plot to garden"),
                ("/plant", "Plant seeds"),
                ("/harvest", "Harvest crops"),
                ("/fertilise", "Fertilise crops"),
                ("/barn", "Your barn"),
                ("/orders", "View orders"),
                ("/seeds", "Your seeds"),
                ("/weather", "Weather forecast"),
            ]
        },
        "market": {
            "name": "🏪 Market Commands",
            "commands": [
                ("/stand", "Your market stand"),
                ("/stands", "View all stands"),
                ("/putstand", "Put item for sale"),
                ("/trade", "Trade with someone"),
                ("/gift", "Gift item"),
                ("/auction", "View auctions"),
                ("/bid", "Place bid"),
            ]
        },
        "games": {
            "name": "🎮 Games Commands",
            "commands": [
                ("/fourpics", "4 Pics 1 Word game"),
                ("/ripple", "Ripple game"),
                ("/lottery", "Buy lottery ticket"),
                ("/nation", "Nation guessing"),
                ("/quiz", "Quiz game"),
                ("/dice", "Dice game"),
                ("/blackjack", "Blackjack"),
                ("/slots", "Slot machine"),
                ("/guess", "Number guessing"),
                ("/trivia", "Trivia game"),
            ]
        },
        "leaderboards": {
            "name": "🏆 Leaderboard Commands",
            "commands": [
                ("/leaderboard", "Top players by level"),
                ("/moneyboard", "Richest players"),
                ("/familyboard", "Top families"),
                ("/factoryboard", "Top factories"),
                ("/moneygraph", "Money history graph"),
            ]
        },
    }
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command."""
        # Show main help menu with categories
        text = (
            "📚 *RPG Bot Help Menu*\n\n"
            "Select a category to view commands:\n\n"
            "🎯 *Core* - Essential commands\n"
            "👨‍👩‍👧‍👦 *Family* - Family management\n"
            "👥 *Friends* - Social features\n"
            "💰 *Economy* - Money and banking\n"
            "🔪 *Crime* - Criminal activities\n"
            "🏭 *Factory* - Factory management\n"
            "🌱 *Garden* - Farming system\n"
            "🏪 *Market* - Trading system\n"
            "🎮 *Games* - Mini games\n"
            "🏆 *Leaderboards* - Rankings\n\n"
            "Click a button below to explore!"
        )
        
        keyboard = HelpHandler._get_category_keyboard()
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    
    @staticmethod
    def _get_category_keyboard() -> InlineKeyboardMarkup:
        """Get category selection keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("🎯 Core", callback_data="help_core"),
                InlineKeyboardButton("👨‍👩‍👧‍👦 Family", callback_data="help_family"),
                InlineKeyboardButton("👥 Friends", callback_data="help_friends"),
            ],
            [
                InlineKeyboardButton("💰 Economy", callback_data="help_economy"),
                InlineKeyboardButton("🔪 Crime", callback_data="help_crime"),
                InlineKeyboardButton("🏭 Factory", callback_data="help_factory"),
            ],
            [
                InlineKeyboardButton("🌱 Garden", callback_data="help_garden"),
                InlineKeyboardButton("🏪 Market", callback_data="help_market"),
                InlineKeyboardButton("🎮 Games", callback_data="help_games"),
            ],
            [
                InlineKeyboardButton("🏆 Leaderboards", callback_data="help_leaderboards"),
                InlineKeyboardButton("📋 All Commands", callback_data="help_all"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle help-related callbacks."""
        query = update.callback_query
        await query.answer()
        
        data = query.data.replace("help_", "")
        
        if data == "all":
            await HelpHandler._show_all_commands(query)
        elif data in HelpHandler.CATEGORIES:
            await HelpHandler._show_category(query, data)
        elif data == "main":
            await HelpHandler._show_main_menu(query)
    
    @staticmethod
    async def _show_category(query, category: str) -> None:
        """Show commands for a specific category."""
        cat_data = HelpHandler.CATEGORIES.get(category)
        if not cat_data:
            await query.edit_message_text("Category not found!")
            return
        
        text = f"{cat_data['name']}\n\n"
        for cmd, desc in cat_data["commands"]:
            text += f"`{cmd}` - {desc}\n"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Back", callback_data="help_main")]
        ])
        
        await query.edit_message_text(
            text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    
    @staticmethod
    async def _show_all_commands(query) -> None:
        """Show all commands."""
        text = "📋 *All Commands*\n\n"
        
        for key, cat_data in HelpHandler.CATEGORIES.items():
            text += f"*{cat_data['name']}*\n"
            for cmd, desc in cat_data["commands"]:
                text += f"`{cmd}` - {desc}\n"
            text += "\n"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Back", callback_data="help_main")]
        ])
        
        await query.edit_message_text(
            text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    
    @staticmethod
    async def _show_main_menu(query) -> None:
        """Show main help menu."""
        text = (
            "📚 *RPG Bot Help Menu*\n\n"
            "Select a category to view commands:\n\n"
            "🎯 *Core* - Essential commands\n"
            "👨‍👩‍👧‍👦 *Family* - Family management\n"
            "👥 *Friends* - Social features\n"
            "💰 *Economy* - Money and banking\n"
            "🔪 *Crime* - Criminal activities\n"
            "🏭 *Factory* - Factory management\n"
            "🌱 *Garden* - Farming system\n"
            "🏪 *Market* - Trading system\n"
            "🎮 *Games* - Mini games\n"
            "🏆 *Leaderboards* - Rankings\n\n"
            "Click a button below to explore!"
        )
        
        keyboard = HelpHandler._get_category_keyboard()
        
        await query.edit_message_text(
            text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
