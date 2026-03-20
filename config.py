"""
Telegram RPG Bot - Configuration Module
======================================
Centralized configuration management for the RPG bot.
"""

import os
from dataclasses import dataclass
from typing import Optional, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class BotConfig:
    """Bot configuration settings."""
    TOKEN: str = os.getenv("BOT_TOKEN", "")
    BOT_USERNAME: str = os.getenv("BOT_USERNAME", "")
    ADMIN_IDS: List[int] = None
    
    def __post_init__(self):
        admin_ids_str = os.getenv("ADMIN_IDS", "")
        self.ADMIN_IDS = [int(x.strip()) for x in admin_ids_str.split(",") if x.strip()]


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DB_NAME: str = os.getenv("DB_NAME", "telegram_rpg_bot")
    
    # Collection names
    USERS_COLLECTION: str = "users"
    FAMILIES_COLLECTION: str = "families"
    FRIENDS_COLLECTION: str = "friends"
    INVENTORY_COLLECTION: str = "inventory"
    ECONOMY_COLLECTION: str = "economy"
    GARDENS_COLLECTION: str = "gardens"
    FACTORY_COLLECTION: str = "factory"
    MARKET_COLLECTION: str = "market"
    GAMES_COLLECTION: str = "games"
    STATS_COLLECTION: str = "stats"
    LOGS_COLLECTION: str = "logs"


@dataclass
class GameConfig:
    """Game mechanics configuration."""
    # Starting values
    STARTING_MONEY: int = 1000
    STARTING_BANK: int = 0
    STARTING_REPUTATION: int = 100
    STARTING_LEVEL: int = 1
    STARTING_EXPERIENCE: int = 0
    
    # Daily rewards
    DAILY_REWARD_MIN: int = 100
    DAILY_REWARD_MAX: int = 500
    DAILY_STREAK_BONUS: int = 50
    
    # Cooldowns (in seconds)
    COOLDOWN_DAILY: int = 86400  # 24 hours
    COOLDOWN_ROB: int = 3600     # 1 hour
    COOLDOWN_KILL: int = 7200    # 2 hours
    COOLDOWN_WORK: int = 1800    # 30 minutes
    COOLDOWN_CRIME: int = 1800   # 30 minutes
    
    # Crime settings
    ROB_SUCCESS_RATE: float = 0.6
    ROB_MIN_AMOUNT: float = 0.05
    ROB_MAX_AMOUNT: float = 0.25
    KILL_SUCCESS_RATE: float = 0.3
    
    # Factory settings
    FACTORY_BASE_PRODUCTION: int = 100
    FACTORY_UPGRADE_COST_BASE: int = 5000
    FACTORY_WORKER_COST: int = 100
    FACTORY_PRODUCTION_INTERVAL: int = 3600  # 1 hour
    
    # Garden settings
    CROP_GROWTH_BASE_TIME: int = 3600  # 1 hour
    FERTILIZER_BOOST: float = 0.5
    
    # Leveling
    XP_PER_LEVEL: int = 1000
    LEVEL_MULTIPLIER: float = 1.5


@dataclass
class ImageConfig:
    """Image generation configuration."""
    TREE_IMAGE_WIDTH: int = 1600
    TREE_IMAGE_HEIGHT: int = 1200
    TREE_DPI: int = 100
    
    # Node colors
    NODE_COLOR_USER: str = "#FFD700"        # Gold
    NODE_COLOR_PARTNER: str = "#FF69B4"     # Hot Pink
    NODE_COLOR_PARENT: str = "#4169E1"      # Royal Blue
    NODE_COLOR_CHILD: str = "#32CD32"       # Lime Green
    NODE_COLOR_GRANDPARENT: str = "#8B4513" # Saddle Brown
    NODE_COLOR_GRANDCHILD: str = "#00CED1"  # Dark Turquoise
    
    # Edge colors
    EDGE_COLOR_MARRIAGE: str = "#FF1493"    # Deep Pink
    EDGE_COLOR_PARENT: str = "#2F4F4F"      # Dark Slate Gray


@dataclass
class LoggingConfig:
    """Logging configuration."""
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "bot.log")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    MAX_LOG_SIZE: int = 10 * 1024 * 1024  # 10 MB
    LOG_BACKUP_COUNT: int = 5


# Initialize configurations
bot_config = BotConfig()
db_config = DatabaseConfig()
game_config = GameConfig()
image_config = ImageConfig()
logging_config = LoggingConfig()


# Validation
def validate_config() -> Optional[str]:
    """Validate configuration settings."""
    if not bot_config.TOKEN:
        return "BOT_TOKEN is required"
    if not bot_config.ADMIN_IDS:
        return "At least one ADMIN_ID is required"
    return None
