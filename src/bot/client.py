from __future__ import annotations

import logging

import discord

from src.bot.events import handle_message, handle_voice_state_update
from src.config import Settings


logger = logging.getLogger(__name__)


class DiscordAIBot(discord.Client):
    def __init__(self, *, intents: discord.Intents, settings: Settings):
        super().__init__(intents=intents)
        self.settings = settings

    async def on_ready(self) -> None:
        user = self.user
        logger.info("Logged in as %s", f"{user} ({user.id})" if user else "unknown")

    async def on_message(self, message: discord.Message) -> None:
        await handle_message(self, message)

    async def on_voice_state_update(
        self,
        member: discord.Member | discord.User,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        await handle_voice_state_update(self, member, before, after)
