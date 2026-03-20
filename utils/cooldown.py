"""
Telegram RPG Bot - Cooldown Management
=====================================
Manages command cooldowns for users.
"""

import time
import logging
from typing import Dict, Optional
from dataclasses import dataclass, field
from collections import defaultdict

from config import game_config

logger = logging.getLogger(__name__)


@dataclass
class CooldownEntry:
    """Represents a cooldown entry."""
    last_used: float
    cooldown_seconds: int


class CooldownManager:
    """Manages user command cooldowns."""
    
    def __init__(self):
        # user_id -> command -> CooldownEntry
        self._cooldowns: Dict[int, Dict[str, CooldownEntry]] = defaultdict(dict)
        
        # Default cooldowns
        self._default_cooldowns = {
            "daily": game_config.COOLDOWN_DAILY,
            "rob": game_config.COOLDOWN_ROB,
            "kill": game_config.COOLDOWN_KILL,
            "work": game_config.COOLDOWN_WORK,
            "crime": game_config.COOLDOWN_CRIME,
        }
    
    def get_remaining(self, user_id: int, command: str) -> int:
        """Get remaining cooldown time in seconds."""
        if user_id not in self._cooldowns:
            return 0
        
        if command not in self._cooldowns[user_id]:
            return 0
        
        entry = self._cooldowns[user_id][command]
        elapsed = time.time() - entry.last_used
        remaining = max(0, entry.cooldown_seconds - elapsed)
        
        return int(remaining)
    
    def is_on_cooldown(self, user_id: int, command: str) -> bool:
        """Check if user is on cooldown for command."""
        return self.get_remaining(user_id, command) > 0
    
    def set_cooldown(self, user_id: int, command: str, 
                     cooldown_seconds: Optional[int] = None) -> None:
        """Set cooldown for user command."""
        if cooldown_seconds is None:
            cooldown_seconds = self._default_cooldowns.get(command, 0)
        
        self._cooldowns[user_id][command] = CooldownEntry(
            last_used=time.time(),
            cooldown_seconds=cooldown_seconds
        )
        logger.debug(f"Set cooldown for user {user_id}, command {command}: {cooldown_seconds}s")
    
    def reset_cooldown(self, user_id: int, command: str) -> None:
        """Reset cooldown for user command."""
        if user_id in self._cooldowns and command in self._cooldowns[user_id]:
            del self._cooldowns[user_id][command]
    
    def reset_all_cooldowns(self, user_id: int) -> None:
        """Reset all cooldowns for user."""
        if user_id in self._cooldowns:
            self._cooldowns[user_id].clear()
    
    def format_remaining(self, seconds: int) -> str:
        """Format remaining time as human-readable string."""
        if seconds < 60:
            return f"{seconds} seconds"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"


# Global cooldown manager instance
cooldown_manager = CooldownManager()


def check_cooldown(command: str, cooldown_seconds: Optional[int] = None):
    """Decorator to check cooldown before executing command."""
    def decorator(func):
        async def wrapper(update, context, *args, **kwargs):
            user_id = update.effective_user.id
            
            remaining = cooldown_manager.get_remaining(user_id, command)
            if remaining > 0:
                formatted = cooldown_manager.format_remaining(remaining)
                await update.message.reply_text(
                    f"⏳ Please wait {formatted} before using this command again."
                )
                return
            
            # Execute command
            result = await func(update, context, *args, **kwargs)
            
            # Set cooldown after successful execution
            cooldown_manager.set_cooldown(user_id, command, cooldown_seconds)
            
            return result
        return wrapper
    return decorator
