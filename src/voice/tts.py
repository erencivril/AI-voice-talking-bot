from __future__ import annotations

import uuid
from pathlib import Path

import httpx


class ElevenLabsTTS:
    def __init__(self, *, api_key: str, voice_id: str):
        self._api_key = api_key
        self._voice_id = voice_id

    async def synthesize_to_mp3(self, *, text: str, out_dir: Path) -> Path:
        out_dir.mkdir(parents=True, exist_ok=True)
        file_path = out_dir / f"tts_{uuid.uuid4().hex}.mp3"

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self._voice_id}"
        headers = {"xi-api-key": self._api_key, "Content-Type": "application/json"}
        payload = {"text": text}

        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            file_path.write_bytes(r.content)

        return file_path
