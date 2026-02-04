from __future__ import annotations

import logging
from pathlib import Path

import discord

from src.bot.events import handle_message, handle_voice_state_update
from src.ai.gemini_client import GeminiClient
from src.config import Settings
from src.memory.database import Database
from src.memory.user_memory import UserMemoryManager


logger = logging.getLogger(__name__)


class DiscordAIBot(discord.Client):
    def __init__(self, *, intents: discord.Intents, settings: Settings):
        super().__init__(intents=intents)
        self.settings = settings
        self.ai: GeminiClient | None = None
        self.db: Database | None = None
        self.memory: UserMemoryManager | None = None

        if settings.google_api_key:
            self.ai = GeminiClient(api_key=settings.google_api_key, model_name=settings.gemini_model)

    async def on_ready(self) -> None:
        user = self.user
        logger.info("Logged in as %s", f"{user} ({user.id})" if user else "unknown")

        if not self.db:
            self.db = Database(path=Path("data") / "bot.db")
            await self.db.connect()
            logger.info("SQLite ready: %s", Path("data") / "bot.db")

        if self.ai and not self.memory:
            self.memory = UserMemoryManager(db=self.db, ai=self.ai)

    async def on_message(self, message: discord.Message) -> None:
        await handle_message(self, message)

    async def on_voice_state_update(
        self,
        member: discord.Member | discord.User,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        await handle_voice_state_update(self, member, before, after)
