"""Asynchronous Telegram bot service for recipient binding commands."""

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

from utils.telegram_recipient_store import TelegramRecipientStore


WELCOME_MESSAGE = (
    "喵～这是 PriceSentry 通知机器人。"
    "\n请发送 /bind <token> 完成绑定，token 由控制台生成。"
)

HELP_MESSAGE = (
    "要绑定通知，请使用 /bind <token>。"
    "\n可在监控面板的“Telegram 接收人”页生成 token。"
)


class TelegramBotService:
    """Thin wrapper around python-telegram-bot for recipient binding."""

    def __init__(self, token: Optional[str], store: Optional[TelegramRecipientStore] = None):
        self._token = token or ""
        self._store = store or TelegramRecipientStore()
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
            application = (
                Application.builder()
                .token(self._token)
                .rate_limiter(AIORateLimiter())
                .build()
            )

            application.add_handler(CommandHandler("start", self._handle_start))
            application.add_handler(CommandHandler("help", self._handle_help))
            application.add_handler(CommandHandler("bind", self._handle_bind))
            application.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_free_text)
            )

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

    async def _handle_bind(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.effective_user or not update.effective_chat:
            return

        if not context.args:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="需要提供令牌喵～ 请发送 /bind <token>",
            )
            return

        token = context.args[0].strip()
        if not token:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="令牌不能为空喵，重新试试 /bind <token>",
            )
            return

        user_id = update.effective_user.id
        username = update.effective_user.username or ""

        try:
            status = self._store.confirm_binding(token, user_id, username)
        except Exception as exc:  # defensive
            logging.exception("Failed to bind Telegram recipient: %s", exc)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="内部错误喵，请稍后重试",  # keep message friendly
            )
            return

        if status == "confirmed":
            message = "绑定成功喵！后续通知会同步给你～"
        elif status == "already_active":
            message = "已经绑定过了喵，等待通知即可～"
        else:
            message = "令牌无效喵，请确认后重新发送 /bind <token>"

        await context.bot.send_message(chat_id=update.effective_chat.id, text=message)

    async def _handle_free_text(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if not update.effective_chat:
            return

        if update.effective_chat.type not in (ChatType.PRIVATE, ChatType.GROUP, ChatType.SUPERGROUP):
            return

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=HELP_MESSAGE,
        )


__all__ = ["TelegramBotService"]
