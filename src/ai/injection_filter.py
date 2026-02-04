from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class FilterResult:
    allowed: bool
    text_or_reason: str


class InjectionFilter:
    DANGEROUS_PATTERNS: list[str] = [
        r"ignore (all |previous |your )?(instructions|prompt|rules)",
        r"you are now",
        r"new (role|persona|identity)",
        r"forget (everything|all|your)",
        r"pretend (to be|you're)",
        r"act as if",
        r"system:?\s*prompt",
        r"<\|.*?\|>",
        r"\[INST\]|\[/INST\]",
    ]

    def __init__(self) -> None:
        self._compiled = [re.compile(p, re.IGNORECASE) for p in self.DANGEROUS_PATTERNS]

    def filter(self, message: str) -> FilterResult:
        if not message:
            return FilterResult(allowed=True, text_or_reason="")

        for pattern in self._compiled:
            if pattern.search(message):
                return FilterResult(allowed=False, text_or_reason="Şüpheli prompt-injection denemesi tespit edildi.")

        cleaned = self._sanitize(message)
        return FilterResult(allowed=True, text_or_reason=cleaned)

    def _sanitize(self, message: str) -> str:
        message = message.replace("\x00", "")
        message = re.sub(r"\s+", " ", message).strip()
        return message
