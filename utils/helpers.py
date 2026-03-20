"""
Telegram RPG Bot - Helper Utilities
==================================
Common helper functions used across the bot.
"""

import re
import random
import string
from typing import Optional, List
from datetime import datetime, timedelta


def generate_id(length: int = 8) -> str:
    """Generate a random alphanumeric ID."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def format_money(amount: int) -> str:
    """Format money amount with currency symbol."""
    if amount >= 1_000_000_000:
        return f"💰 {amount / 1_000_000_000:.2f}B"
    elif amount >= 1_000_000:
        return f"💰 {amount / 1_000_000:.2f}M"
    elif amount >= 1_000:
        return f"💰 {amount / 1_000:.2f}K"
    else:
        return f"💰 {amount:,}"


def format_number(num: int) -> str:
    """Format large numbers with suffixes."""
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    return str(num)


def format_time(seconds: int) -> str:
    """Format seconds into human-readable time."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s"
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{days}d {hours}h"


def parse_time_string(time_str: str) -> Optional[int]:
    """Parse time string (e.g., '1h30m') into seconds."""
    pattern = r'^(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$'
    match = re.match(pattern, time_str.lower())
    
    if not match:
        return None
    
    days, hours, minutes, seconds = match.groups()
    total = 0
    
    if days:
        total += int(days) * 86400
    if hours:
        total += int(hours) * 3600
    if minutes:
        total += int(minutes) * 60
    if seconds:
        total += int(seconds)
    
    return total


def escape_markdown(text: str) -> str:
    """Escape markdown special characters."""
    chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in chars:
        text = text.replace(char, f'\\{char}')
    return text


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to maximum length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def calculate_percentage(part: int, whole: int) -> float:
    """Calculate percentage."""
    if whole == 0:
        return 0.0
    return (part / whole) * 100


def weighted_random_choice(choices: List[tuple]) -> any:
    """Make weighted random choice from list of (item, weight) tuples."""
    total_weight = sum(weight for _, weight in choices)
    r = random.uniform(0, total_weight)
    
    cumulative = 0
    for item, weight in choices:
        cumulative += weight
        if r <= cumulative:
            return item
    
    return choices[-1][0]


def get_level_emoji(level: int) -> str:
    """Get emoji based on level."""
    if level >= 100:
        return "👑"
    elif level >= 50:
        return "💎"
    elif level >= 25:
        return "🥇"
    elif level >= 10:
        return "🥈"
    else:
        return "🥉"


def get_reputation_emoji(reputation: int) -> str:
    """Get emoji based on reputation."""
    if reputation >= 1000:
        return "⭐⭐⭐⭐⭐"
    elif reputation >= 500:
        return "⭐⭐⭐⭐"
    elif reputation >= 200:
        return "⭐⭐⭐"
    elif reputation >= 100:
        return "⭐⭐"
    else:
        return "⭐"


def create_progress_bar(current: int, maximum: int, length: int = 20) -> str:
    """Create a text progress bar."""
    if maximum == 0:
        return "░" * length
    
    filled = int((current / maximum) * length)
    filled = min(filled, length)
    
    return "█" * filled + "░" * (length - filled)


def get_timestamp() -> datetime:
    """Get current UTC timestamp."""
    return datetime.utcnow()


def add_days(days: int) -> datetime:
    """Get timestamp after specified days."""
    return datetime.utcnow() + timedelta(days=days)


def is_expired(timestamp: datetime) -> bool:
    """Check if timestamp has expired."""
    return datetime.utcnow() > timestamp


def parse_mention(text: str) -> Optional[int]:
    """Parse user ID from mention text."""
    # Try to extract from @username
    if text.startswith('@'):
        return None  # Need to resolve username
    
    # Try to extract from user ID
    try:
        return int(text)
    except ValueError:
        pass
    
    # Try to extract from mention link
    match = re.search(r'tg://user\?id=(\d+)', text)
    if match:
        return int(match.group(1))
    
    return None


def calculate_xp_for_level(level: int, base_xp: int = 1000, multiplier: float = 1.5) -> int:
    """Calculate XP needed for a level."""
    return int(base_xp * (multiplier ** (level - 1)))


def pluralize(count: int, singular: str, plural: str = None) -> str:
    """Return singular or plural form based on count."""
    if count == 1:
        return f"{count} {singular}"
    if plural is None:
        plural = singular + "s"
    return f"{count} {plural}"


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """Split list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers."""
    if denominator == 0:
        return default
    return numerator / denominator
