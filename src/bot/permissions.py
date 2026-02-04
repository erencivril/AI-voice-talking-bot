from __future__ import annotations

import discord


def is_owner(bot: discord.Client, user: discord.abc.User) -> bool:
    settings = getattr(bot, "settings", None)
    if not settings:
        return False
    return int(user.id) == int(settings.discord_owner_id)
