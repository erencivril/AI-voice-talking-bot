from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import discord

from src.voice.tts import ElevenLabsTTS


logger = logging.getLogger(__name__)


class VoiceManager:
    def __init__(
        self,
        *,
        bot: discord.Client,
        elevenlabs_api_key: str | None,
        elevenlabs_voice_id: str | None,
    ) -> None:
        self._bot = bot
        self._lock = asyncio.Lock()
        self._tts: ElevenLabsTTS | None = None
        if elevenlabs_api_key and elevenlabs_voice_id:
            self._tts = ElevenLabsTTS(api_key=elevenlabs_api_key, voice_id=elevenlabs_voice_id)

    async def join(self, channel: discord.VoiceChannel) -> discord.VoiceClient:
        vc = channel.guild.voice_client
        if vc and vc.is_connected():
            if vc.channel and vc.channel.id == channel.id:
                return vc
            await vc.move_to(channel)
            return vc
        return await channel.connect()

    async def leave(self, *, guild: discord.Guild) -> None:
        vc = guild.voice_client
        if vc and vc.is_connected():
            await vc.disconnect(force=True)

    async def speak(self, *, guild: discord.Guild, text: str) -> None:
        if not self._tts:
            return
        text = (text or "").strip()
        if not text:
            return
        text = text[:400]

        vc = guild.voice_client
        if not vc or not vc.is_connected():
            return

        async with self._lock:
            out_dir = Path("data") / "tts"
            mp3_path = await self._tts.synthesize_to_mp3(text=text, out_dir=out_dir)

            loop = asyncio.get_running_loop()
            done: asyncio.Future[Exception | None] = loop.create_future()

            def _after(err: Exception | None) -> None:
                loop.call_soon_threadsafe(done.set_result, err)

            source = discord.FFmpegPCMAudio(str(mp3_path))
            vc.play(source, after=_after)
            err = await done
            try:
                mp3_path.unlink(missing_ok=True)
            except Exception:
                logger.exception("Failed to delete tts file: %s", mp3_path)
            if err:
                raise err
