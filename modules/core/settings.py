"""
Telegram RPG Bot - Settings Module
=================================
Handles the /settings command and user preferences.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db
from utils.validators import UserValidator

logger = logging.getLogger(__name__)


class SettingsHandler:
    """Handles settings command and user preferences."""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /settings command."""
        async with UserValidator(update) as validator:
            await validator.check_banned()
            if validator.errors:
                return
        
        user_id = update.effective_user.id
        user = db.users.find_one({"user_id": user_id})
        
        # Get user settings
        settings = user.get("settings", {})
        
        settings_text = (
            "⚙️ *Settings*\n\n"
            "Configure your bot preferences:\n\n"
            f"🔔 *Notifications:* {'✅ On' if settings.get('notifications', True) else '❌ Off'}\n"
            f"🌐 *Language:* {settings.get('language', 'English')}\n"
            f"💱 *Currency:* {settings.get('currency', 'USD')}\n"
            f"🎨 *Theme:* {settings.get('theme', 'Default')}\n"
            f"🔒 *Privacy:* {'Private' if settings.get('private', False) else 'Public'}\n\n"
            "Select an option to change:"
        )
        
        keyboard = [
            [
                InlineKeyboardButton(
                    f"🔔 Notifications: {'ON' if settings.get('notifications', True) else 'OFF'}",
                    callback_data="settings_toggle_notifications"
                )
            ],
            [
                InlineKeyboardButton("🌐 Language", callback_data="settings_language"),
                InlineKeyboardButton("💱 Currency", callback_data="settings_currency")
            ],
            [
                InlineKeyboardButton("🎨 Theme", callback_data="settings_theme"),
                InlineKeyboardButton(
                    f"🔒 Privacy: {'PRIVATE' if settings.get('private', False) else 'PUBLIC'}",
                    callback_data="settings_toggle_privacy"
                )
            ],
            [
                InlineKeyboardButton("🗑️ Delete Account", callback_data="settings_delete"),
                InlineKeyboardButton("📊 Data Export", callback_data="settings_export")
            ],
            [
                InlineKeyboardButton("❌ Close", callback_data="settings_close")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            settings_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle settings callbacks."""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        if data == "settings_view":
            await SettingsHandler._show_settings_menu(query)
        elif data == "settings_toggle_notifications":
            await SettingsHandler._toggle_setting(user_id, "notifications")
            await SettingsHandler._show_settings_menu(query)
        elif data == "settings_toggle_privacy":
            await SettingsHandler._toggle_setting(user_id, "private")
            await SettingsHandler._show_settings_menu(query)
        elif data == "settings_language":
            await SettingsHandler._show_language_options(query)
        elif data == "settings_currency":
            await SettingsHandler._show_currency_options(query)
        elif data == "settings_theme":
            await SettingsHandler._show_theme_options(query)
        elif data == "settings_close":
            await query.delete_message()
        elif data.startswith("settings_lang_"):
            lang = data.replace("settings_lang_", "")
            await SettingsHandler._update_setting(user_id, "language", lang)
            await SettingsHandler._show_settings_menu(query)
        elif data.startswith("settings_curr_"):
            curr = data.replace("settings_curr_", "")
            await SettingsHandler._update_setting(user_id, "currency", curr)
            await SettingsHandler._show_settings_menu(query)
        elif data.startswith("settings_theme_"):
            theme = data.replace("settings_theme_", "")
            await SettingsHandler._update_setting(user_id, "theme", theme)
            await SettingsHandler._show_settings_menu(query)
    
    @staticmethod
    async def _show_settings_menu(query) -> None:
        """Show settings menu."""
        user_id = query.from_user.id
        user = db.users.find_one({"user_id": user_id})
        settings = user.get("settings", {})
        
        settings_text = (
            "⚙️ *Settings*\n\n"
            "Configure your bot preferences:\n\n"
            f"🔔 *Notifications:* {'✅ On' if settings.get('notifications', True) else '❌ Off'}\n"
            f"🌐 *Language:* {settings.get('language', 'English')}\n"
            f"💱 *Currency:* {settings.get('currency', 'USD')}\n"
            f"🎨 *Theme:* {settings.get('theme', 'Default')}\n"
            f"🔒 *Privacy:* {'Private' if settings.get('private', False) else 'Public'}\n\n"
            "Select an option to change:"
        )
        
        keyboard = [
            [
                InlineKeyboardButton(
                    f"🔔 Notifications: {'ON' if settings.get('notifications', True) else 'OFF'}",
                    callback_data="settings_toggle_notifications"
                )
            ],
            [
                InlineKeyboardButton("🌐 Language", callback_data="settings_language"),
                InlineKeyboardButton("💱 Currency", callback_data="settings_currency")
            ],
            [
                InlineKeyboardButton("🎨 Theme", callback_data="settings_theme"),
                InlineKeyboardButton(
                    f"🔒 Privacy: {'PRIVATE' if settings.get('private', False) else 'PUBLIC'}",
                    callback_data="settings_toggle_privacy"
                )
            ],
            [
                InlineKeyboardButton("❌ Close", callback_data="settings_close")
            ]
        ]
        
        await query.edit_message_text(
            settings_text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    @staticmethod
    async def _toggle_setting(user_id: int, setting: str) -> None:
        """Toggle a boolean setting."""
        user = db.users.find_one({"user_id": user_id})
        settings = user.get("settings", {})
        settings[setting] = not settings.get(setting, True)
        
        db.users.update_one(
            {"user_id": user_id},
            {"$set": {"settings": settings}}
        )
    
    @staticmethod
    async def _update_setting(user_id: int, setting: str, value: any) -> None:
        """Update a setting value."""
        user = db.users.find_one({"user_id": user_id})
        settings = user.get("settings", {})
        settings[setting] = value
        
        db.users.update_one(
            {"user_id": user_id},
            {"$set": {"settings": settings}}
        )
    
    @staticmethod
    async def _show_language_options(query) -> None:
        """Show language options."""
        keyboard = [
            [
                InlineKeyboardButton("🇺🇸 English", callback_data="settings_lang_English"),
                InlineKeyboardButton("🇪🇸 Español", callback_data="settings_lang_Spanish")
            ],
            [
                InlineKeyboardButton("🇫🇷 Français", callback_data="settings_lang_French"),
                InlineKeyboardButton("🇩🇪 Deutsch", callback_data="settings_lang_German")
            ],
            [
                InlineKeyboardButton("🇷🇺 Русский", callback_data="settings_lang_Russian"),
                InlineKeyboardButton("🇨🇳 中文", callback_data="settings_lang_Chinese")
            ],
            [
                InlineKeyboardButton("⬅️ Back", callback_data="settings_view")
            ]
        ]
        
        await query.edit_message_text(
            "🌐 *Select Language*\n\nChoose your preferred language:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    @staticmethod
    async def _show_currency_options(query) -> None:
        """Show currency options."""
        keyboard = [
            [
                InlineKeyboardButton("💵 USD", callback_data="settings_curr_USD"),
                InlineKeyboardButton("💶 EUR", callback_data="settings_curr_EUR")
            ],
            [
                InlineKeyboardButton("💷 GBP", callback_data="settings_curr_GBP"),
                InlineKeyboardButton("💴 JPY", callback_data="settings_curr_JPY")
            ],
            [
                InlineKeyboardButton("⬅️ Back", callback_data="settings_view")
            ]
        ]
        
        await query.edit_message_text(
            "💱 *Select Currency*\n\nChoose your preferred currency:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    @staticmethod
    async def _show_theme_options(query) -> None:
        """Show theme options."""
        keyboard = [
            [
                InlineKeyboardButton("🌙 Dark", callback_data="settings_theme_Dark"),
                InlineKeyboardButton("☀️ Light", callback_data="settings_theme_Light")
            ],
            [
                InlineKeyboardButton("🌈 Colorful", callback_data="settings_theme_Colorful"),
                InlineKeyboardButton("⚫ Minimal", callback_data="settings_theme_Minimal")
            ],
            [
                InlineKeyboardButton("⬅️ Back", callback_data="settings_view")
            ]
        ]
        
        await query.edit_message_text(
            "🎨 *Select Theme*\n\nChoose your preferred theme:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
