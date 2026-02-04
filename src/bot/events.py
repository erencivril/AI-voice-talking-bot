from __future__ import annotations

import logging
import re

import discord

from src.bot.permissions import is_owner
from src.ai.prompt_builder import build_prompt


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


def _extract_user_message(bot: discord.Client, message: discord.Message) -> str:
    text = message.content or ""
    if bot.user:
        uid = bot.user.id
        text = text.replace(f"<@{uid}>", "").replace(f"<@!{uid}>", "")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:2000]


async def handle_message(bot: discord.Client, message: discord.Message) -> None:
    if not bot.user or message.author.id == bot.user.id:
        return

    should_reply = _is_mentioning_bot(bot, message) or _is_reply_to_bot(bot, message)
    if not should_reply:
        return

    settings = getattr(bot, "settings", None)
    if not settings:
        return

    user_text = _extract_user_message(bot, message)
    user_is_owner = is_owner(bot, message.author)

    if not getattr(bot, "ai", None):
        reply = "GOOGLE_API_KEY ayarlı değil. Şimdilik konuşamıyorum."
        await message.reply(reply, mention_author=False)
        return

    if not user_text:
        user_text = "Selam"

    prompt = build_prompt(
        bot_name=settings.bot_name,
        owner_id=settings.discord_owner_id,
        user_display_name=getattr(message.author, "display_name", "kullanıcı"),
        user_message=user_text,
        is_owner=user_is_owner,
    )

    try:
        reply = await bot.ai.generate_text(prompt=prompt)  # type: ignore[union-attr]
    except Exception:
        await message.reply("Şu an kafam yandı. Biraz sonra dene.", mention_author=False)
        return

    if not reply:
        reply = "Cevap üretemedim. (Bence bu da bir cevap.)"

    await message.reply(reply, mention_author=False)


async def handle_voice_state_update(
    bot: discord.Client,
    member: discord.Member | discord.User,
    before: discord.VoiceState,
    after: discord.VoiceState,
) -> None:
    _ = (bot, member, before, after)
    # Faz 5'te doldurulacak. (Şimdilik no-op)
