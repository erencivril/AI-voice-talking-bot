from __future__ import annotations

import logging

import discord

from src.bot.permissions import is_owner


logger = logging.getLogger(__name__)


def _is_reply_to_bot(bot: discord.Client, message: discord.Message) -> bool:
    if not message.reference:
        return False
    resolved = message.reference.resolved
    if isinstance(resolved, discord.Message) and resolved.author and bot.user:
        return resolved.author.id == bot.user.id
    return False


def _is_mentioning_bot(bot: discord.Client, message: discord.Message) -> bool:
    return bool(bot.user and bot.user.mentioned_in(message))


async def handle_message(bot: discord.Client, message: discord.Message) -> None:
    if not bot.user or message.author.id == bot.user.id:
        return

    should_reply = _is_mentioning_bot(bot, message) or _is_reply_to_bot(bot, message)
    if not should_reply:
        return

    if is_owner(bot, message.author):
        reply = f"Selam patron. ({getattr(bot, 'settings', None).bot_name}) Hazırım."
    else:
        reply = "Heh, bana mı seslendin? Daha AI kısmı gelmedi, ama buradayım."

    await message.reply(reply, mention_author=False)


async def handle_voice_state_update(
    bot: discord.Client,
    member: discord.Member | discord.User,
    before: discord.VoiceState,
    after: discord.VoiceState,
) -> None:
    _ = (bot, member, before, after)
    # Faz 5'te doldurulacak. (Şimdilik no-op)
