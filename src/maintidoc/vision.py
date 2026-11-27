"""Description d'image par un VLM local (Qwen2.5-VL via Ollama)."""
from __future__ import annotations

import os

from ollama import Client

from .config import OLLAMA_HOST

DEFAULT_VISION_MODEL = os.getenv("VISION_MODEL", "qwen2.5vl:3b")

PROMPT_EN = """You are analyzing a maintenance photo of a SAN storage array.
Describe only what is visible: panel, LEDs, labels, alarm codes, connectors,
cabling, displayed text, and any ambiguity.
Do not guess a diagnosis. If a label is unreadable, say so.
Answer in English, in 4 to 8 short bullet points.
"""


def describe_image(image_bytes: bytes, model: str = DEFAULT_VISION_MODEL,
                   timeout: int = 300) -> str:
    """Retourne une description visuelle structurée de l'image."""
    client = Client(host=OLLAMA_HOST, timeout=timeout)
    response = client.chat(
        model=model,
        messages=[{
            "role": "user",
            "content": PROMPT_EN,
            "images": [image_bytes],
        }],
        options={"temperature": 0, "num_ctx": 4096, "num_predict": 500},
    )
    return response.message.content.strip()


if __name__ == "__main__":
    from pathlib import Path

    sample = Path("data/processed/images/fig04_page05.png")
    print(describe_image(sample.read_bytes()))
