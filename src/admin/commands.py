from __future__ import annotations

import re

import discord


def _parse_on_off(arg: str) -> bool | None:
    arg = arg.strip().lower()
    if arg in {"on", "true", "1", "yes"}:
        return True
    if arg in {"off", "false", "0", "no"}:
        return False
    return None


def _extract_id(text: str) -> str | None:
    m = re.search(r"(\d{15,25})", text)
    return m.group(1) if m else None


async def handle_owner_command(bot: discord.Client, message: discord.Message) -> None:
    content = (message.content or "").strip()
    parts = content.split()
    cmd = parts[0].lower() if parts else ""
    args = parts[1:]

    if cmd == "/status":
        settings = getattr(bot, "settings", None)
        features = getattr(bot, "features", {})
        await message.reply(
            "\n".join(
                [
                    f"Bot: {getattr(bot.user, 'name', '?')} ({getattr(bot.user, 'id', '?')})",
                    f"Guilds: {len(getattr(bot, 'guilds', []))}",
                    f"Web search: {features.get('web_search', False)}",
                    f"Voice: {features.get('voice', False)}",
                    f"Memory every N msgs: {getattr(settings, 'memory_extract_every_n_messages', '?')}",
                ]
            )
        )
        return

    if cmd in {"/search", "/voice"}:
        if not args:
            await message.reply("Kullanım: /search on|off")
            return
        value = _parse_on_off(args[0])
        if value is None:
            await message.reply("Kullanım: /search on|off")
            return
        features = getattr(bot, "features", None)
        if isinstance(features, dict):
            key = "web_search" if cmd == "/search" else "voice"
            features[key] = value
            await message.reply(f"{key} = {value}")
        else:
            await message.reply("Feature bayrakları hazır değil.")
        return

    if cmd == "/memories":
        target_id = _extract_id(" ".join(args)) or str(message.author.id)
        db = getattr(bot, "db", None)
        if not db:
            await message.reply("DB hazır değil.")
            return
        rows = await db.list_memories(discord_id=target_id, limit=10)
        if not rows:
            await message.reply("Hafıza yok.")
            return
        lines = []
        for r in rows:
            lines.append(f"- ({r['memory_type']}, {float(r['confidence']):.2f}) {r['content']}")
        await message.reply("\n".join(lines)[:1900])
        return

    if cmd == "/say":
        if len(args) < 2:
            await message.reply("Kullanım: /say #channel mesaj")
            return
        chan_id = _extract_id(args[0])
        if not chan_id:
            await message.reply("Kanal bulunamadı. #kanal mention veya channel_id ver.")
            return
        channel = bot.get_channel(int(chan_id))
        if not isinstance(channel, (discord.TextChannel, discord.Thread)):
            await message.reply("Bu kanal yazı kanalı değil (veya erişim yok).")
            return
        text = " ".join(args[1:])
        await channel.send(text)
        await message.reply("Gönderildi.")
        return

    if cmd == "/dm":
        if len(args) < 2:
            await message.reply("Kullanım: /dm @user mesaj")
            return
        user_id = _extract_id(args[0])
        if not user_id:
            await message.reply("Kullanıcı bulunamadı. mention veya user_id ver.")
            return
        user = await bot.fetch_user(int(user_id))
        await user.send(" ".join(args[1:]))
        await message.reply("DM gönderildi.")
        return

    await message.reply("Bilinmeyen komut. (/status, /memories, /search, /voice, /say, /dm)")
