from __future__ import annotations

from dataclasses import dataclass
import json
import re


@dataclass(frozen=True)
class ToolCall:
    tool: str
    query: str


def parse_tool_call(text: str) -> ToolCall | None:
    """
    Beklenen format:
      {"tool":"web_search","query":"..."}
    """
    if not text:
        return None

    # Strip common code fences
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE | re.DOTALL).strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    candidate = cleaned[start : end + 1]
    try:
        obj = json.loads(candidate)
    except json.JSONDecodeError:
        return None

    if not isinstance(obj, dict):
        return None

    tool = str(obj.get("tool", "")).strip()
    query = str(obj.get("query", "")).strip()
    if not tool or not query:
        return None

    return ToolCall(tool=tool, query=query)
