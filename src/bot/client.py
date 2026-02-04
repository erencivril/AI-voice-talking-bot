from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

import discord

from src.bot.events import handle_message, handle_voice_state_update
from src.ai.gemini_client import GeminiClient
from src.ai.injection_filter import InjectionFilter
from src.config import Settings
from src.bot.rate_limiter import RateLimiter
from src.memory.database import Database
from src.memory.user_memory import UserMemoryManager
from src.tools.web_search import WebSearch
from src.voice.voice_client import VoiceManager


logger = logging.getLogger(__name__)


class DiscordAIBot(discord.Client):
    def __init__(self, *, intents: discord.Intents, settings: Settings):
        super().__init__(intents=intents)
        self.settings = settings
        self.started_at = datetime.now(tz=timezone.utc)
        self.ai: GeminiClient | None = None
        self.db: Database | None = None
        self.memory: UserMemoryManager | None = None
        self.injection_filter = InjectionFilter()
        self.rate_limiter = RateLimiter(
            max_calls=settings.rate_limit_max,
            window_seconds=float(settings.rate_limit_window_seconds),
        )
        self.features = {"web_search": settings.enable_web_search, "voice": settings.enable_voice}
        self.web_search = WebSearch(
            brave_api_key=settings.brave_api_key,
            serper_api_key=settings.serper_api_key,
            tavily_api_key=settings.tavily_api_key,
        )
        self.voice_manager = VoiceManager(
            bot=self,
            elevenlabs_api_key=settings.elevenlabs_api_key,
            elevenlabs_voice_id=settings.elevenlabs_voice_id,
        )

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
