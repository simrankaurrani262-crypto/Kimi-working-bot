"""
Telegram RPG Bot - Database Module

MongoDB database connection and operations management.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError, ConnectionFailure, OperationFailure

from config import db_config, game_config

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages MongoDB connections and operations."""

    _instance: Optional['DatabaseManager'] = None
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None

    def __new__(cls) -> 'DatabaseManager':
        """Singleton pattern for database manager."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def connect(self) -> bool:
        """Establish connection to MongoDB."""
        try:
            self._client = MongoClient(db_config.MONGO_URI, serverSelectionTimeoutMS=5000)
            # Verify connection
            self._client.admin.command('ping')
            self._db = self._client[db_config.DB_NAME]
            logger.info(f"Connected to MongoDB: {db_config.DB_NAME}")
            self._create_indexes()
            return True
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False

    def disconnect(self) -> None:
        """Close MongoDB connection."""
        if self._client:
            self._client.close()
            logger.info("Disconnected from MongoDB")

    def _drop_conflicting_index(self, collection, index_name: str):
        """Drop an index if it exists to avoid conflicts."""
        try:
            # Check if index exists
            indexes = collection.list_indexes()
            index_names = [idx['name'] for idx in indexes]
            if index_name in index_names:
                collection.drop_index(index_name)
                logger.info(f"Dropped conflicting index: {index_name}")
        except Exception as e:
            logger.debug(f"Could not drop index {index_name}: {e}")

    def _create_index_safe(self, collection, field, unique=False, sparse=False):
        """Safely create index with error handling."""
        try:
            collection.create_index(field, unique=unique, sparse=sparse)
        except (OperationFailure, DuplicateKeyError) as e:
            logger.warning(f"Index creation skipped: {e}")

    def _create_indexes(self) -> None:
        """Create database indexes for optimal performance."""

        # Users collection indexes
        self._create_index_safe(self.users, "user_id", unique=True, sparse=True)
        self._create_index_safe(self.users, "username")
        self._create_index_safe(self.users, [("money", DESCENDING)])
        self._create_index_safe(self.users, [("level", DESCENDING)])
        self._create_index_safe(self.users, [("reputation", DESCENDING)])

        # Families collection - drop old conflicting index first, then create new one
        self._drop_conflicting_index(self.families, "family_id_1")
        self._create_index_safe(self.families, "family_id", unique=True, sparse=True)
        self._create_index_safe(self.families, "members")
        self._create_index_safe(self.families, "creator_id")

        # Friends collection indexes
        self._create_index_safe(self.friends, [("user_id", ASCENDING), ("friend_id", ASCENDING)], unique=True)

        # Economy collection indexes
        self._create_index_safe(self.economy, "user_id", unique=True, sparse=True)
        self._create_index_safe(self.economy, [("total_earned", DESCENDING)])

        # Inventory collection indexes
        self._create_index_safe(self.inventory, "user_id")
        self._create_index_safe(self.inventory, "item_id")

        # Gardens collection indexes
        self._create_index_safe(self.gardens, "user_id", unique=True, sparse=True)

        # Factory collection indexes
        self._create_index_safe(self.factory, "user_id", unique=True, sparse=True)

        # Market collection indexes
        self._create_index_safe(self.market, "seller_id")
        self._create_index_safe(self.market, "item_id")
        self._create_index_safe(self.market, [("price", ASCENDING)])

        # Games collection indexes
        self._create_index_safe(self.games, "user_id")
        self._create_index_safe(self.games, "game_type")

        # Stats collection indexes
        self._create_index_safe(self.stats, "user_id", unique=True, sparse=True)
        self._create_index_safe(self.stats, [("activity_score", DESCENDING)])

        # Logs collection indexes
        self._create_index_safe(self.logs, [("timestamp", DESCENDING)])
        self._create_index_safe(self.logs, "user_id")
        self._create_index_safe(self.logs, "action")

        logger.info("Database indexes created successfully")

    @property
    def db(self) -> Database:
        """Get database instance."""
        if self._db is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._db

    @property
    def users(self) -> Collection:
        """Get users collection."""
        return self.db[db_config.USERS_COLLECTION]

    @property
    def families(self) -> Collection:
        """Get families collection."""
        return self.db[db_config.FAMILIES_COLLECTION]

    @property
    def friends(self) -> Collection:
        """Get friends collection."""
        return self.db[db_config.FRIENDS_COLLECTION]

    @property
    def inventory(self) -> Collection:
        """Get inventory collection."""
        return self.db[db_config.INVENTORY_COLLECTION]

    @property
    def economy(self) -> Collection:
        """Get economy collection."""
        return self.db[db_config.ECONOMY_COLLECTION]

    @property
    def gardens(self) -> Collection:
        """Get gardens collection."""
        return self.db[db_config.GARDENS_COLLECTION]

    @property
    def factory(self) -> Collection:
        """Get factory collection."""
        return self.db[db_config.FACTORY_COLLECTION]

    @property
    def market(self) -> Collection:
        """Get market collection."""
        return self.db[db_config.MARKET_COLLECTION]

    @property
    def games(self) -> Collection:
        """Get games collection."""
        return self.db[db_config.GAMES_COLLECTION]

    @property
    def stats(self) -> Collection:
        """Get stats collection."""
        return self.db[db_config.STATS_COLLECTION]

    @property
    def logs(self) -> Collection:
        """Get logs collection."""
        return self.db[db_config.LOGS_COLLECTION]


# Global database manager instance
db = DatabaseManager()


class UserRepository:
    """Repository for user-related database operations."""

    @staticmethod
    async def get_user(user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        return db.users.find_one({"user_id": user_id})

    @staticmethod
    async def create_user(user_id: int, username: str, name: str) -> Dict[str, Any]:
        """Create a new user."""
        user_data = {
            "user_id": user_id,
            "username": username,
            "name": name,
            "money": game_config.STARTING_MONEY,
            "bank": game_config.STARTING_BANK,
            "reputation": game_config.STARTING_REPUTATION,
            "level": game_config.STARTING_LEVEL,
            "experience": game_config.STARTING_EXPERIENCE,
            "partner": None,
            "children": [],
            "parents": [],
            "friends": [],
            "job": None,
            "inventory": [],
            "garden": None,
            "factory_workers": 0,
            "weapons": [],
            "insurance": False,
            "last_daily": None,
            "last_rob": None,
            "last_kill": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "banned": False,
            "ban_reason": None,
            "activity_score": 0
        }
        try:
            db.users.insert_one(user_data)
            logger.info(f"Created new user: {user_id} ({username})")
            return user_data
        except DuplicateKeyError:
            logger.warning(f"User already exists: {user_id}")
            return await UserRepository.get_user(user_id)

    @staticmethod
    async def update_user(user_id: int, update_data: Dict[str, Any]) -> bool:
        """Update user data."""
        update_data["updated_at"] = datetime.utcnow()
        result = db.users.update_one(
            {"user_id": user_id},
            {"$set": update_data}
        )
        return result.modified_count > 0

    @staticmethod
    async def add_money(user_id: int, amount: int) -> bool:
        """Add money to user's wallet."""
        result = db.users.update_one(
            {"user_id": user_id},
            {"$inc": {"money": amount}, "$set": {"updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    @staticmethod
    async def remove_money(user_id: int, amount: int) -> bool:
        """Remove money from user's wallet."""
        user = await UserRepository.get_user(user_id)
        if user and user["money"] >= amount:
            result = db.users.update_one(
                {"user_id": user_id},
                {"$inc": {"money": -amount}, "$set": {"updated_at": datetime.utcnow()}}
            )
            return result.modified_count > 0
        return False

    @staticmethod
    async def add_experience(user_id: int, xp: int) -> tuple:
        """Add experience and handle level ups. Returns (new_level, leveled_up)."""
        user = await UserRepository.get_user(user_id)
        if not user:
            return None, False

        new_xp = user["experience"] + xp
        current_level = user["level"]
        xp_needed = int(game_config.XP_PER_LEVEL * (game_config.LEVEL_MULTIPLIER ** (current_level - 1)))

        leveled_up = False
        while new_xp >= xp_needed:
            new_xp -= xp_needed
            current_level += 1
            xp_needed = int(game_config.XP_PER_LEVEL * (game_config.LEVEL_MULTIPLIER ** (current_level - 1)))
            leveled_up = True

        await UserRepository.update_user(user_id, {
            "experience": new_xp,
            "level": current_level
        })

        return current_level, leveled_up

    @staticmethod
    async def get_leaderboard(limit: int = 10, sort_by: str = "money") -> List[Dict[str, Any]]:
        """Get leaderboard sorted by specified field."""
        return list(db.users.find(
            {"banned": False},
            {"user_id": 1, "username": 1, "name": 1, "money": 1, "level": 1, "reputation": 1}
        ).sort(sort_by, DESCENDING).limit(limit))


class FamilyRepository:
    """Repository for family-related database operations."""

    @staticmethod
    async def get_family(family_id: str) -> Optional[Dict[str, Any]]:
        """Get family by ID."""
        return db.families.find_one({"family_id": family_id})

    @staticmethod
    async def get_family_by_member(user_id: int) -> Optional[Dict[str, Any]]:
        """Get family by member ID."""
        return db.families.find_one({"members": user_id})

    @staticmethod
    async def create_family(family_id: str, name: str, creator_id: int) -> Dict[str, Any]:
        """Create a new family."""
        family_data = {
            "family_id": family_id,
            "name": name,
            "creator_id": creator_id,
            "members": [creator_id],
            "created_at": datetime.utcnow(),
            "total_wealth": 0,
            "reputation": 100
        }
        db.families.insert_one(family_data)
        return family_data

    @staticmethod
    async def add_member(family_id: str, user_id: int) -> bool:
        """Add member to family."""
        result = db.families.update_one(
            {"family_id": family_id},
            {"$addToSet": {"members": user_id}}
        )
        return result.modified_count > 0

    @staticmethod
    async def remove_member(family_id: str, user_id: int) -> bool:
        """Remove member from family."""
        result = db.families.update_one(
            {"family_id": family_id},
            {"$pull": {"members": user_id}}
        )
        return result.modified_count > 0

    @staticmethod
    async def get_family_leaderboard(limit: int = 10) -> List[Dict[str, Any]]:
        """Get family leaderboard."""
        return list(db.families.find().sort("total_wealth", DESCENDING).limit(limit))


class LogRepository:
    """Repository for logging operations."""

    @staticmethod
    async def log_action(user_id: int, action: str, details: Dict[str, Any] = None) -> None:
        """Log user action."""
        log_entry = {
            "user_id": user_id,
            "action": action,
            "details": details or {},
            "timestamp": datetime.utcnow()
        }
        db.logs.insert_one(log_entry)

    @staticmethod
    async def get_logs(user_id: int = None, action: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get logs with optional filters."""
        query = {}
        if user_id:
            query["user_id"] = user_id
        if action:
            query["action"] = action

        return list(db.logs.find(query).sort("timestamp", DESCENDING).limit(limit))


# Initialize database connection
def init_database() -> bool:
    """Initialize database connection."""
    return db.connect()
        
