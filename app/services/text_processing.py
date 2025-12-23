from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TextSignals:
    normalized_text: str
    language: str


class TextProcessor:
    def normalize(self, text: str) -> str:
        cleaned = text.strip()
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned

    def detect_language(self, text: str) -> str:
        if not text:
            return "unknown"

        for ch in text:
            code = ord(ch)
            if 0x0900 <= code <= 0x097F:
                return "hi"

        if all(ord(ch) < 128 for ch in text):
            return "en"

        return "unknown"

    def process(self, text: Optional[str]) -> Optional[TextSignals]:
        if text is None:
            return None
        normalized = self.normalize(text)
        if not normalized:
            return None
        return TextSignals(normalized_text=normalized, language=self.detect_language(normalized))


text_processor = TextProcessor()
