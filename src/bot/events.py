from __future__ import annotations

import asyncio
import logging
import re

import discord

from src.admin.commands import handle_owner_command
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

    user_is_owner = is_owner(bot, message.author)
    is_dm = message.guild is None

    if is_dm and user_is_owner:
        raw = (message.content or "").strip()
        if raw.startswith("/"):
            await handle_owner_command(bot, message)
            return

    should_reply = (is_dm and user_is_owner) or _is_mentioning_bot(bot, message) or _is_reply_to_bot(bot, message)
    if not should_reply:
        return

    settings = getattr(bot, "settings", None)
    if not settings:
        return

    db = getattr(bot, "db", None)
    if not db:
        await message.reply("DB hazır değil. Biraz sonra dene.", mention_author=False)
        return

    user_text = _extract_user_message(bot, message)
    discord_id = str(message.author.id)

    limiter = getattr(bot, "rate_limiter", None)
    if not user_is_owner and limiter and not limiter.allow(discord_id):
        await message.reply("Yavaş. (Rate limit)", mention_author=False)
        return

    if not user_text:
        user_text = "Selam"

    inj = getattr(bot, "injection_filter", None)
    if inj:
        res = inj.filter(user_text)
        if not res.allowed:
            await message.reply(res.text_or_reason, mention_author=False)
            return
        user_text = res.text_or_reason

    try:
        message_count = await db.touch_user(
            discord_id=discord_id,
            username=str(message.author),
            display_name=getattr(message.author, "display_name", str(message.author)),
        )
    except Exception:
        logger.exception("touch_user failed")
        message_count = 0

    try:
        await db.add_conversation(
            discord_id=discord_id,
            channel_id=str(message.channel.id) if message.channel else None,
            message_id=str(message.id),
            role="user",
            content=user_text or "",
        )
    except Exception:
        logger.exception("add_conversation(user) failed")

    if not getattr(bot, "ai", None):
        reply = "GOOGLE_API_KEY ayarlı değil. Şimdilik konuşamıyorum."
        await message.reply(reply, mention_author=False)
        return

    memories: list[str] = []
    mem_mgr = getattr(bot, "memory", None)
    if mem_mgr:
        try:
            memories = await mem_mgr.get_prompt_memories(discord_id=discord_id, limit=5)
        except Exception:
            logger.exception("get_prompt_memories failed")

    prompt = build_prompt(
        bot_name=settings.bot_name,
        owner_id=settings.discord_owner_id,
        user_display_name=getattr(message.author, "display_name", "kullanıcı"),
        user_message=user_text,
        is_owner=user_is_owner,
        memories=memories,
    )

    try:
        reply = await bot.ai.generate_text(prompt=prompt)  # type: ignore[union-attr]
    except Exception:
        await message.reply("Şu an kafam yandı. Biraz sonra dene.", mention_author=False)
        return

    if not reply:
        reply = "Cevap üretemedim. (Bence bu da bir cevap.)"

    await message.reply(reply, mention_author=False)

    try:
        await db.add_conversation(
            discord_id=discord_id,
            channel_id=str(message.channel.id) if message.channel else None,
            message_id=None,
            role="assistant",
            content=reply,
        )
    except Exception:
        logger.exception("add_conversation(assistant) failed")

    every_n = int(getattr(settings, "memory_extract_every_n_messages", 0) or 0)
    if mem_mgr and every_n > 0 and message_count > 0 and message_count % every_n == 0:
        task = asyncio.create_task(
            mem_mgr.extract_and_store(discord_id=discord_id, source_message_id=str(message.id))
        )

        def _log_task_result(t: asyncio.Task[object]) -> None:
            try:
                t.result()
            except Exception:
                logger.exception("memory task failed")

        task.add_done_callback(_log_task_result)


async def handle_voice_state_update(
    bot: discord.Client,
    member: discord.Member | discord.User,
    before: discord.VoiceState,
    after: discord.VoiceState,
) -> None:
    _ = (bot, member, before, after)
    # Faz 5'te doldurulacak. (Şimdilik no-op)
