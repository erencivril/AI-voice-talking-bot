from __future__ import annotations

import logging

from src.ai.gemini_client import GeminiClient
from src.memory.database import Database
from src.memory.memory_extractor import MemoryExtractor


logger = logging.getLogger(__name__)


class UserMemoryManager:
    def __init__(self, *, db: Database, ai: GeminiClient):
        self._db = db
        self._extractor = MemoryExtractor(ai=ai)

    async def get_prompt_memories(self, *, discord_id: str, limit: int = 5) -> list[str]:
        rows = await self._db.list_memories(discord_id=discord_id, limit=limit)
        memories: list[str] = []
        for r in rows:
            memories.append(f"- ({r['memory_type']}, {r['confidence']:.2f}) {r['content']}")
        return memories

    async def extract_and_store(
        self,
        *,
        discord_id: str,
        source_message_id: str | None,
    ) -> None:
        conversation = await self._db.get_recent_conversation(discord_id=discord_id, limit=10)
        convo_lines = [f"{row.role}: {row.content}" for row in conversation]
        extracted = await self._extractor.extract(conversation=convo_lines)
        if not extracted:
            return

        saved = 0
        for m in extracted:
            if m.confidence < 0.7:
                continue
            await self._db.add_memory(
                discord_id=discord_id,
                memory_type=m.memory_type,
                content=m.content,
                confidence=m.confidence,
                source_message_id=source_message_id,
            )
            saved += 1

        if saved:
            logger.info("Saved %s memories for %s", saved, discord_id)
