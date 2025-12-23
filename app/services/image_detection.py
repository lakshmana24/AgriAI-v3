from __future__ import annotations

from typing import List

from app.schemas.chat import DiseasePrediction


class CropDiseaseDetector:
    """Stub detector.

    Swap this implementation with YOLOv8 / EfficientNet later.
    """

    async def detect(self, image_bytes: bytes, filename: str) -> List[DiseasePrediction]:
        if not image_bytes:
            return []
        return [DiseasePrediction(label="unclassified", confidence=0.10)]


crop_disease_detector = CropDiseaseDetector()
