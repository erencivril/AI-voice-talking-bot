from __future__ import annotations

from dataclasses import dataclass
import os

from dotenv import load_dotenv


def _get_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    discord_token: str
    discord_owner_id: int

    bot_name: str
    log_level: str

    google_api_key: str | None
    gemini_model: str

    enable_web_search: bool
    enable_voice: bool

    memory_extract_every_n_messages: int

    brave_api_key: str | None
    serper_api_key: str | None
    tavily_api_key: str | None

    deepgram_api_key: str | None
    elevenlabs_api_key: str | None


def load_settings() -> Settings:
    load_dotenv(override=False)

    discord_token = os.getenv("DISCORD_TOKEN", "").strip()
    if not discord_token:
        raise RuntimeError("DISCORD_TOKEN missing (set it in .env)")

    owner_raw = os.getenv("DISCORD_OWNER_ID", "").strip()
    if not owner_raw:
        raise RuntimeError("DISCORD_OWNER_ID missing (set it in .env)")

    try:
        owner_id = int(owner_raw)
    except ValueError as exc:
        raise RuntimeError("DISCORD_OWNER_ID must be an integer") from exc

    return Settings(
        discord_token=discord_token,
        discord_owner_id=owner_id,
        bot_name=os.getenv("BOT_NAME", "ironik-bot").strip() or "ironik-bot",
        log_level=os.getenv("LOG_LEVEL", "INFO").strip() or "INFO",
        google_api_key=os.getenv("GOOGLE_API_KEY") or None,
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip() or "gemini-1.5-flash",
        enable_web_search=_get_bool("ENABLE_WEB_SEARCH", False),
        enable_voice=_get_bool("ENABLE_VOICE", False),
        memory_extract_every_n_messages=int(os.getenv("MEMORY_EXTRACT_EVERY_N_MESSAGES", "10").strip() or "10"),
        brave_api_key=os.getenv("BRAVE_API_KEY") or None,
        serper_api_key=os.getenv("SERPER_API_KEY") or None,
        tavily_api_key=os.getenv("TAVILY_API_KEY") or None,
        deepgram_api_key=os.getenv("DEEPGRAM_API_KEY") or None,
        elevenlabs_api_key=os.getenv("ELEVENLABS_API_KEY") or None,
    )
