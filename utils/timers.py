"""
Telegram RPG Bot - Timer Management
==================================
Manages scheduled tasks and timers.
"""

import logging
import asyncio
from typing import Callable, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger

from database import db

logger = logging.getLogger(__name__)


@dataclass
class TimerTask:
    """Represents a scheduled timer task."""
    task_id: str
    user_id: int
    task_type: str
    execute_at: datetime
    callback: Callable
    data: Dict[str, Any]


class TimerManager:
    """Manages scheduled timers and tasks."""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._tasks: Dict[str, TimerTask] = {}
    
    def start(self) -> None:
        """Start the scheduler."""
        self.scheduler.start()
        logger.info("Timer scheduler started")
    
    def shutdown(self) -> None:
        """Shutdown the scheduler."""
        self.scheduler.shutdown()
        logger.info("Timer scheduler shutdown")
    
    def schedule_once(self, task_id: str, user_id: int, task_type: str,
                      delay_seconds: int, callback: Callable, 
                      data: Dict[str, Any] = None) -> str:
        """Schedule a one-time task."""
        execute_at = datetime.utcnow() + timedelta(seconds=delay_seconds)
        
        job = self.scheduler.add_job(
            callback,
            trigger=DateTrigger(run_date=execute_at),
            args=[user_id, data],
            id=task_id,
            replace_existing=True
        )
        
        task = TimerTask(
            task_id=task_id,
            user_id=user_id,
            task_type=task_type,
            execute_at=execute_at,
            callback=callback,
            data=data or {}
        )
        self._tasks[task_id] = task
        
        logger.info(f"Scheduled {task_type} task {task_id} for user {user_id}")
        return task_id
    
    def schedule_recurring(self, task_id: str, user_id: int, task_type: str,
                           interval_seconds: int, callback: Callable,
                           data: Dict[str, Any] = None) -> str:
        """Schedule a recurring task."""
        job = self.scheduler.add_job(
            callback,
            trigger=IntervalTrigger(seconds=interval_seconds),
            args=[user_id, data],
            id=task_id,
            replace_existing=True
        )
        
        task = TimerTask(
            task_id=task_id,
            user_id=user_id,
            task_type=task_type,
            execute_at=datetime.utcnow(),
            callback=callback,
            data=data or {}
        )
        self._tasks[task_id] = task
        
        logger.info(f"Scheduled recurring {task_type} task {task_id} for user {user_id}")
        return task_id
    
    def schedule_daily(self, task_id: str, user_id: int, task_type: str,
                       hour: int, minute: int, callback: Callable,
                       data: Dict[str, Any] = None) -> str:
        """Schedule a daily task."""
        job = self.scheduler.add_job(
            callback,
            trigger=CronTrigger(hour=hour, minute=minute),
            args=[user_id, data],
            id=task_id,
            replace_existing=True
        )
        
        task = TimerTask(
            task_id=task_id,
            user_id=user_id,
            task_type=task_type,
            execute_at=datetime.utcnow(),
            callback=callback,
            data=data or {}
        )
        self._tasks[task_id] = task
        
        logger.info(f"Scheduled daily {task_type} task {task_id} for user {user_id}")
        return task_id
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a scheduled task."""
        try:
            self.scheduler.remove_job(task_id)
            if task_id in self._tasks:
                del self._tasks[task_id]
            logger.info(f"Cancelled task {task_id}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling task {task_id}: {e}")
            return False
    
    def get_task(self, task_id: str) -> Optional[TimerTask]:
        """Get task by ID."""
        return self._tasks.get(task_id)
    
    def get_user_tasks(self, user_id: int, task_type: str = None) -> list:
        """Get all tasks for a user."""
        tasks = []
        for task in self._tasks.values():
            if task.user_id == user_id:
                if task_type is None or task.task_type == task_type:
                    tasks.append(task)
        return tasks


# Global timer manager instance
timer_manager = TimerManager()


# Crop growth timer callbacks
async def on_crop_mature(user_id: int, data: Dict[str, Any]) -> None:
    """Called when a crop becomes mature."""
    garden_id = data.get("garden_id")
    plot_index = data.get("plot_index")
    
    garden = db.gardens.find_one({"user_id": user_id})
    if garden and "plots" in garden:
        for plot in garden["plots"]:
            if plot.get("index") == plot_index:
                plot["status"] = "mature"
                db.gardens.update_one(
                    {"user_id": user_id},
                    {"$set": {"plots": garden["plots"]}}
                )
                logger.info(f"Crop matured for user {user_id}, plot {plot_index}")
                break


# Factory production timer callbacks
async def on_production_complete(user_id: int, data: Dict[str, Any]) -> None:
    """Called when factory production completes."""
    factory = db.factory.find_one({"user_id": user_id})
    if factory:
        production = data.get("production", 0)
        
        # Add produced goods to inventory
        db.users.update_one(
            {"user_id": user_id},
            {"$inc": {"money": production}}
        )
        
        # Update factory stats
        db.factory.update_one(
            {"user_id": user_id},
            {"$inc": {"total_produced": production, "production_cycles": 1}}
        )
        
        logger.info(f"Factory production complete for user {user_id}: +{production}")


# Daily reward reset
async def on_daily_reset(user_id: int, data: Dict[str, Any]) -> None:
    """Called when daily reward resets."""
    db.users.update_one(
        {"user_id": user_id},
        {"$set": {"daily_claimed": False}}
    )
    logger.info(f"Daily reward reset for user {user_id}")


# Jail time completion
async def on_jail_release(user_id: int, data: Dict[str, Any]) -> None:
    """Called when jail time completes."""
    db.users.update_one(
        {"user_id": user_id},
        {"$set": {"in_jail": False, "jail_until": None}}
    )
    logger.info(f"User {user_id} released from jail")


# Loan payment due
async def on_loan_due(user_id: int, data: Dict[str, Any]) -> None:
    """Called when loan payment is due."""
    loan_id = data.get("loan_id")
    amount = data.get("amount", 0)
    
    user = db.users.find_one({"user_id": user_id})
    if user:
        if user["money"] >= amount:
            # Auto-deduct payment
            db.users.update_one(
                {"user_id": user_id},
                {"$inc": {"money": -amount}}
            )
            logger.info(f"Loan payment of {amount} deducted from user {user_id}")
        else:
            # User can't pay - add penalty
            penalty = int(amount * 0.1)
            db.economy.update_one(
                {"user_id": user_id},
                {"$inc": {"debt": amount + penalty}}
            )
            logger.warning(f"User {user_id} failed to pay loan. Penalty added.")


def setup_timers() -> None:
    """Setup and start the timer manager."""
    timer_manager.start()


def shutdown_timers() -> None:
    """Shutdown the timer manager."""
    timer_manager.shutdown()
