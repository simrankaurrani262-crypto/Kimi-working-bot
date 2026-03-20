"""
Telegram RPG Bot - Input Validators
==================================
Input validation utilities.
"""

import re
from typing import Optional, Tuple
from telegram import Update

from database import db


class ValidationError(Exception):
    """Custom validation error."""
    pass


async def validate_user_exists(user_id: int) -> bool:
    """Check if user exists in database."""
    user = db.users.find_one({"user_id": user_id})
    return user is not None


async def validate_not_banned(user_id: int) -> Tuple[bool, Optional[str]]:
    """Check if user is not banned."""
    user = db.users.find_one({"user_id": user_id})
    if not user:
        return False, "User not found"
    if user.get("banned", False):
        return False, f"You are banned. Reason: {user.get('ban_reason', 'No reason provided')}"
    return True, None


async def validate_has_money(user_id: int, amount: int) -> Tuple[bool, Optional[str]]:
    """Check if user has enough money."""
    user = db.users.find_one({"user_id": user_id})
    if not user:
        return False, "User not found"
    if user["money"] < amount:
        return False, f"Insufficient funds. You have {user['money']:,} but need {amount:,}"
    return True, None


async def validate_has_bank_money(user_id: int, amount: int) -> Tuple[bool, Optional[str]]:
    """Check if user has enough money in bank."""
    user = db.users.find_one({"user_id": user_id})
    if not user:
        return False, "User not found"
    if user["bank"] < amount:
        return False, f"Insufficient bank funds. You have {user['bank']:,} but need {amount:,}"
    return True, None


async def validate_target_exists(target_id: int) -> Tuple[bool, Optional[str]]:
    """Check if target user exists."""
    exists = await validate_user_exists(target_id)
    if not exists:
        return False, "Target user not found"
    return True, None


async def validate_not_self(user_id: int, target_id: int) -> Tuple[bool, Optional[str]]:
    """Check if user is not targeting themselves."""
    if user_id == target_id:
        return False, "You cannot perform this action on yourself"
    return True, None


async def validate_level_requirement(user_id: int, required_level: int) -> Tuple[bool, Optional[str]]:
    """Check if user meets level requirement."""
    user = db.users.find_one({"user_id": user_id})
    if not user:
        return False, "User not found"
    if user["level"] < required_level:
        return False, f"You need to be level {required_level} to use this feature"
    return True, None


def validate_username(username: str) -> Tuple[bool, Optional[str]]:
    """Validate username format."""
    if not username:
        return False, "Username cannot be empty"
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    if len(username) > 32:
        return False, "Username cannot exceed 32 characters"
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscores"
    return True, None


def validate_amount(amount_str: str, min_amount: int = 1, max_amount: int = None) -> Tuple[Optional[int], Optional[str]]:
    """Validate and parse amount string."""
    try:
        amount = int(amount_str.replace(',', ''))
    except ValueError:
        return None, "Invalid amount. Please enter a number"
    
    if amount < min_amount:
        return None, f"Amount must be at least {min_amount:,}"
    
    if max_amount is not None and amount > max_amount:
        return None, f"Amount cannot exceed {max_amount:,}"
    
    return amount, None


def validate_item_name(name: str) -> Tuple[bool, Optional[str]]:
    """Validate item name."""
    if not name:
        return False, "Item name cannot be empty"
    if len(name) < 2:
        return False, "Item name must be at least 2 characters"
    if len(name) > 50:
        return False, "Item name cannot exceed 50 characters"
    return True, None


async def validate_marriage_eligibility(user_id: int) -> Tuple[bool, Optional[str]]:
    """Check if user is eligible to marry."""
    user = db.users.find_one({"user_id": user_id})
    if not user:
        return False, "User not found"
    if user.get("partner"):
        return False, "You are already married"
    return True, None


async def validate_adoption_eligibility(user_id: int, child_id: int) -> Tuple[bool, Optional[str]]:
    """Check if adoption is valid."""
    # Check user exists
    user = db.users.find_one({"user_id": user_id})
    if not user:
        return False, "Parent not found"
    
    # Check child exists
    child = db.users.find_one({"user_id": child_id})
    if not child:
        return False, "Child not found"
    
    # Check child doesn't already have 2 parents
    if len(child.get("parents", [])) >= 2:
        return False, "This person already has 2 parents"
    
    # Check not adopting self
    if user_id == child_id:
        return False, "You cannot adopt yourself"
    
    # Check not adopting partner
    if child_id == user.get("partner"):
        return False, "You cannot adopt your partner"
    
    # Check not adopting own parent
    if user_id in child.get("parents", []):
        return False, "You are already this person's parent"
    
    return True, None


async def validate_factory_ownership(user_id: int) -> Tuple[bool, Optional[str]]:
    """Check if user owns a factory."""
    factory = db.factory.find_one({"user_id": user_id})
    if not factory:
        return False, "You don't own a factory. Use /factory to create one"
    return True, None


async def validate_garden_exists(user_id: int) -> Tuple[bool, Optional[str]]:
    """Check if user has a garden."""
    garden = db.gardens.find_one({"user_id": user_id})
    if not garden:
        return False, "You don't have a garden. Use /garden to create one"
    return True, None


def validate_bet_amount(amount: int, min_bet: int = 10, max_bet: int = 100000) -> Tuple[bool, Optional[str]]:
    """Validate bet amount."""
    if amount < min_bet:
        return False, f"Minimum bet is {min_bet:,}"
    if amount > max_bet:
        return False, f"Maximum bet is {max_bet:,}"
    return True, None


async def validate_admin(user_id: int, admin_ids: list) -> bool:
    """Check if user is admin."""
    return user_id in admin_ids


class UserValidator:
    """Context manager for user validation."""
    
    def __init__(self, update: Update):
        self.update = update
        self.user_id = update.effective_user.id
        self.errors = []
    
    async def __aenter__(self):
        """Enter context."""
        # Check if user exists, create if not
        exists = await validate_user_exists(self.user_id)
        if not exists:
            from database import UserRepository
            await UserRepository.create_user(
                self.user_id,
                self.update.effective_user.username or "unknown",
                self.update.effective_user.first_name or "Unknown"
            )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context."""
        if self.errors:
            error_msg = "\n".join(f"❌ {e}" for e in self.errors)
            await self.update.message.reply_text(error_msg)
            return True  # Suppress exception
        return False
    
    async def check_banned(self) -> 'UserValidator':
        """Check if user is banned."""
        valid, error = await validate_not_banned(self.user_id)
        if not valid:
            self.errors.append(error)
        return self
    
    async def check_money(self, amount: int) -> 'UserValidator':
        """Check if user has enough money."""
        valid, error = await validate_has_money(self.user_id, amount)
        if not valid:
            self.errors.append(error)
        return self
    
    async def check_level(self, required_level: int) -> 'UserValidator':
        """Check if user meets level requirement."""
        valid, error = await validate_level_requirement(self.user_id, required_level)
        if not valid:
            self.errors.append(error)
        return self
