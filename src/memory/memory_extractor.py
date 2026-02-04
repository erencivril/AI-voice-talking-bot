from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from pathlib import Path
import re

from src.ai.gemini_client import GeminiClient


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExtractedMemory:
    memory_type: str
    content: str
    confidence: float


def _repo_root() -> Path:
    # src/memory/memory_extractor.py -> repo root is parents[2]
    return Path(__file__).resolve().parents[2]


def _load_extraction_prompt() -> str:
    return (_repo_root() / "prompts" / "memory_extraction.txt").read_text(encoding="utf-8")


def _extract_json_array(text: str) -> list[object]:
    # Gemini bazen ```json ... ``` dönebiliyor; ilk [ ... ] bloğunu al.
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return []
    candidate = text[start : end + 1]
    candidate = re.sub(r"^```(?:json)?\s*|\s*```$", "", candidate.strip(), flags=re.IGNORECASE | re.DOTALL)
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


class MemoryExtractor:
    def __init__(self, *, ai: GeminiClient):
        self._ai = ai
        self._base_prompt = _load_extraction_prompt()

    async def extract(self, *, conversation: list[str]) -> list[ExtractedMemory]:
        convo_text = "\n".join(conversation[-20:])
        prompt = f"{self._base_prompt}\n\nKONUŞMA:\n{convo_text}\n"

        try:
            raw = await self._ai.generate_text(prompt=prompt)
        except Exception:
            logger.exception("Memory extraction failed")
            return []

        items = _extract_json_array(raw)
        out: list[ExtractedMemory] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            mtype = str(item.get("type", "")).strip()
            content = str(item.get("content", "")).strip()
            try:
                conf = float(item.get("confidence", 0))
            except (TypeError, ValueError):
                conf = 0.0

            if not mtype or not content:
                continue

            out.append(ExtractedMemory(memory_type=mtype, content=content, confidence=conf))
        return out
