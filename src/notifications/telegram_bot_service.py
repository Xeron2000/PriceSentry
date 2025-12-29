"""Asynchronous Telegram bot service for simple commands."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from telegram import Update
from telegram.constants import ChatType
from telegram.ext import (
    AIORateLimiter,
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

WELCOME_MESSAGE = "喵～这是 PriceSentry 通知机器人。\n直接配置 chatId 即可接收通知。"

HELP_MESSAGE = "要接收价格通知，请在配置文件中设置 telegram.chatId。"


class TelegramBotService:
    """Thin wrapper around python-telegram-bot for simple commands."""

    def __init__(self, token: Optional[str]):
        self._token = token or ""
        self._application: Optional[Application] = None
        self._lock = asyncio.Lock()
        self._running = False

    async def start(self) -> None:
        if not self._token:
            logging.info("Telegram bot token missing, bot service not started")
            return

        async with self._lock:
            if self._running:
                return

            logging.info("Starting Telegram bot service")
            application = Application.builder().token(self._token).rate_limiter(AIORateLimiter()).build()

            application.add_handler(CommandHandler("start", self._handle_start))
            application.add_handler(CommandHandler("help", self._handle_help))
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_free_text))

            await application.initialize()
            await application.start()
            if application.updater is None:
                raise RuntimeError("Telegram application missing updater instance")
            await application.updater.start_polling(drop_pending_updates=True)

            self._application = application
            self._running = True
            logging.info("Telegram bot service started successfully")

    async def stop(self) -> None:
        async with self._lock:
            if not self._running:
                return

            logging.info("Stopping Telegram bot service")
            application = self._application
            if application is not None:
                if application.updater is not None:
                    await application.updater.stop()
                await application.stop()
                await application.shutdown()
            self._application = None
            self._running = False

    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.effective_chat:
            return
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=WELCOME_MESSAGE,
        )

    async def _handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.effective_chat:
            return
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=HELP_MESSAGE,
        )

    async def _handle_free_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.effective_chat:
            return

        if update.effective_chat.type not in (
            ChatType.PRIVATE,
            ChatType.GROUP,
            ChatType.SUPERGROUP,
        ):
            return

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=HELP_MESSAGE,
        )


__all__ = ["TelegramBotService"]
