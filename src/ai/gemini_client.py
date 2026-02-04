from __future__ import annotations

import asyncio
import logging

import google.generativeai as genai


logger = logging.getLogger(__name__)


class GeminiClient:
    def __init__(self, *, api_key: str, model_name: str):
        genai.configure(api_key=api_key)
        self._model_name = model_name
        self._model = genai.GenerativeModel(model_name=model_name)

    async def generate_text(self, *, prompt: str) -> str:
        try:
            response = await asyncio.to_thread(self._model.generate_content, prompt)
        except Exception:
            logger.exception("Gemini generate_content failed")
            raise

        text = getattr(response, "text", None)
        if not text:
            return ""
        return text.strip()
