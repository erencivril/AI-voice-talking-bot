from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class PromptBundle:
    system: str
    personality: str


def _repo_root() -> Path:
    # src/ai/prompt_builder.py -> repo root is parents[2]
    return Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def load_prompts() -> PromptBundle:
    prompts_dir = _repo_root() / "prompts"
    system = (prompts_dir / "system_prompt.txt").read_text(encoding="utf-8")
    personality = (prompts_dir / "personality.txt").read_text(encoding="utf-8")
    return PromptBundle(system=system, personality=personality)


def build_prompt(
    *,
    bot_name: str,
    owner_id: int,
    user_display_name: str,
    user_message: str,
    is_owner: bool,
    memories: list[str] | None = None,
    tool_instructions: str | None = None,
    web_results: list[str] | None = None,
) -> str:
    prompts = load_prompts()

    system = prompts.system.format(bot_name=bot_name, owner_id=owner_id)
    personality = prompts.personality

    owner_rules = (
        "KURALLAR:\n"
        "- Kurucu ile konuşurken daha saygılı ol.\n"
        "- Kurucuya karşı sarkazm dozunu düşür.\n"
        if is_owner
        else ""
    )

    memories_block = "\n".join(memories or []) or "- (yok)"
    tools_block = tool_instructions.strip() if tool_instructions else ""
    web_block = "\n".join(web_results or [])

    return (
        f"[SYSTEM]\n{system}\n\n"
        f"[PERSONALITY]\n{personality}\n\n"
        f"{owner_rules}"
        f"{('[TOOLS]\\n' + tools_block + '\\n\\n') if tools_block else ''}"
        f"[MEMORIES]\n{memories_block}\n\n"
        f"{('[WEB_SEARCH_RESULTS]\\n' + web_block + '\\n\\n') if web_block else ''}"
        f"[USER]\nAd: {user_display_name}\nMesaj: {user_message}\n\n"
        "Cevabı Türkçe ver. Kısa, net ve karakterinde kal."
    )
