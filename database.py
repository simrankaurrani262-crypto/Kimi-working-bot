"""
Telegram RPG Bot - Database Module (FIXED VERSION)
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
    _instance: Optional['DatabaseManager'] = None
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None

    def __new__(cls) -> 'DatabaseManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def connect(self) -> bool:
        try:
            self._client = MongoClient(db_config.MONGO_URI, serverSelectionTimeoutMS=5000)
            self._client.admin.command('ping')
            self._db = self._client[db_config.DB_NAME]

            logger.info(f"Connected to MongoDB: {db_config.DB_NAME}")

            # 🔥 CLEAN BAD DATA BEFORE INDEX
            self._clean_database()

            self._create_indexes()
            return True

        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False

    def _clean_database(self):
        """🔥 Remove problematic duplicate/null data"""
        try:
            # Remove null परिवार
            self.families.delete_many({"family_id": None})
            self.families.delete_many({"family_id": {"$exists": False}})

            # Remove null users
            self.users.delete_many({"user_id": None})

            logger.info("Database cleaned successfully")

        except Exception as e:
            logger.warning(f"Database cleaning issue: {e}")

    def _create_index_safe(self, collection, field, unique=False, sparse=False):
        try:
            if unique:
                collection.delete_many({field: None})

            collection.create_index(field, unique=unique, sparse=sparse)

        except OperationFailure as e:
            logger.warning(f"Index skipped: {e}")

    def _create_indexes(self):

        # USERS
        self._create_index_safe(self.users, "user_id", unique=True, sparse=True)
        self._create_index_safe(self.users, "username")
        self._create_index_safe(self.users, [("money", DESCENDING)])
        self._create_index_safe(self.users, [("level", DESCENDING)])
        self._create_index_safe(self.users, [("reputation", DESCENDING)])

        # FAMILIES (🔥 FIXED)
        self._create_index_safe(self.families, "family_id", unique=True, sparse=True)
        self._create_index_safe(self.families, "members")
        self._create_index_safe(self.families, "creator_id")

        # FRIENDS
        self._create_index_safe(self.friends, [("user_id", ASCENDING), ("friend_id", ASCENDING)], unique=True)

        # ECONOMY
        self._create_index_safe(self.economy, "user_id", unique=True, sparse=True)
        self._create_index_safe(self.economy, [("total_earned", DESCENDING)])

        # INVENTORY
        self._create_index_safe(self.inventory, "user_id")
        self._create_index_safe(self.inventory, "item_id")

        # OTHER
        self._create_index_safe(self.gardens, "user_id", unique=True, sparse=True)
        self._create_index_safe(self.factory, "user_id", unique=True, sparse=True)

        self._create_index_safe(self.market, "seller_id")
        self._create_index_safe(self.market, "item_id")
        self._create_index_safe(self.market, [("price", ASCENDING)])

        self._create_index_safe(self.games, "user_id")
        self._create_index_safe(self.games, "game_type")

        self._create_index_safe(self.stats, "user_id", unique=True, sparse=True)
        self._create_index_safe(self.stats, [("activity_score", DESCENDING)])

        self._create_index_safe(self.logs, [("timestamp", DESCENDING)])
        self._create_index_safe(self.logs, "user_id")
        self._create_index_safe(self.logs, "action")

        logger.info("Indexes created successfully")

    @property
    def db(self) -> Database:
        if self._db is None:
            raise RuntimeError("Database not connected.")
        return self._db

    @property
    def users(self): return self.db[db_config.USERS_COLLECTION]

    @property
    def families(self): return self.db[db_config.FAMILIES_COLLECTION]

    @property
    def friends(self): return self.db[db_config.FRIENDS_COLLECTION]

    @property
    def inventory(self): return self.db[db_config.INVENTORY_COLLECTION]

    @property
    def economy(self): return self.db[db_config.ECONOMY_COLLECTION]

    @property
    def gardens(self): return self.db[db_config.GARDENS_COLLECTION]

    @property
    def factory(self): return self.db[db_config.FACTORY_COLLECTION]

    @property
    def market(self): return self.db[db_config.MARKET_COLLECTION]

    @property
    def games(self): return self.db[db_config.GAMES_COLLECTION]

    @property
    def stats(self): return self.db[db_config.STATS_COLLECTION]

    @property
    def logs(self): return self.db[db_config.LOGS_COLLECTION]


db = DatabaseManager()


# ================= USER =================

class UserRepository:

    @staticmethod
    async def get_user(user_id: int):
        return db.users.find_one({"user_id": user_id})

    @staticmethod
    async def create_user(user_id: int, username: str, name: str):
        data = {
            "user_id": user_id,
            "username": username,
            "name": name,
            "money": game_config.STARTING_MONEY,
            "bank": game_config.STARTING_BANK,
            "reputation": game_config.STARTING_REPUTATION,
            "level": game_config.STARTING_LEVEL,
            "experience": game_config.STARTING_EXPERIENCE,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        try:
            db.users.insert_one(data)
            return data
        except DuplicateKeyError:
            return db.users.find_one({"user_id": user_id})


# ================= FAMILY =================

class FamilyRepository:

    @staticmethod
    async def create_family(family_id: str, name: str, creator_id: int):

        if not family_id:
            raise ValueError("family_id cannot be null")

        data = {
            "family_id": family_id,
            "name": name,
            "creator_id": creator_id,
            "members": [creator_id],
            "created_at": datetime.utcnow(),
            "total_wealth": 0
        }

        try:
            db.families.insert_one(data)
        except DuplicateKeyError:
            return db.families.find_one({"family_id": family_id})

        return data


# ================= INIT =================

def init_database():
    return db.connect()
