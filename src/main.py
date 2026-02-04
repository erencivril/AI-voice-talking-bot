from __future__ import annotations

import logging

import discord

from src.bot.client import DiscordAIBot
from src.config import load_settings


def main() -> None:
    settings = load_settings()

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = False
    intents.voice_states = True

    bot = DiscordAIBot(intents=intents, settings=settings)
    bot.run(settings.discord_token, log_handler=None)


if __name__ == "__main__":
    main()
