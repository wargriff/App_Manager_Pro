from __future__ import annotations

from src.cache.translation_cache import (
    TranslationCache
)
from src.ocr.ocr_service import (
    OCRService
)
from src.translation.translation_service import (
    TranslationService
)
from src.services.history_service import (
    HistoryService
)


class TranslationPipeline:

    def __init__(self):

        self.ocr = OCRService()

        self.translator = (
            TranslationService()
        )

        self.cache = (
            TranslationCache()
        )

        self.history = (
            HistoryService()
        )

    def process_image(
        self,
        image,
    ):

        source_text = (
            self.ocr.extract_text(
                image
            )
        )

        if not source_text:
            return ""

        cached = self.cache.get(
            source_text
        )

        if cached:
            return cached

        translated = (
            self.translator.translate(
                source_text
            )
        )

        self.cache.set(
            source_text,
            translated,
        )

        self.history.add(
            source_text,
            translated,
        )

        return translated