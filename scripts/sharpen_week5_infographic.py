# -*- coding: utf-8 -*-
"""Re-build week 5 final infographic from LMS.docx source with multi-step upscale + sharpen."""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
DOCX_MEDIA = "word/media/image61.png"
TARGET_WIDTH = 2040
OUT = ROOT / "assets/week5/infographic-final.png"
HTML_COPY = ROOT / "image copy 31.png"


def upscale_steps(im: Image.Image, target_w: int) -> Image.Image:
    im = im.convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    im = Image.alpha_composite(bg, im).convert("RGB")

    current = im
    while current.width < target_w:
        next_w = min(int(current.width * 1.75), target_w)
        next_h = int(current.height * next_w / current.width)
        current = current.resize((next_w, next_h), Image.Resampling.LANCZOS)
        current = current.filter(
            ImageFilter.UnsharpMask(radius=1.6, percent=175, threshold=1)
        )

    current = ImageEnhance.Contrast(current).enhance(1.1)
    current = ImageEnhance.Sharpness(current).enhance(1.45)
    current = current.filter(ImageFilter.UnsharpMask(radius=1.2, percent=120, threshold=2))
    return current


def main() -> None:
    z = zipfile.ZipFile(ROOT / "LMS.docx")
    raw = z.read(DOCX_MEDIA)
    src = Image.open(io.BytesIO(raw))
    print(f"Source {DOCX_MEDIA}: {src.size}")

    out = upscale_steps(src, TARGET_WIDTH)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.save(OUT, format="PNG", compress_level=3)
    out.save(HTML_COPY, format="PNG", compress_level=3)
    print(f"Saved {OUT} ({out.size}, {OUT.stat().st_size} bytes)")
    print(f"Synced {HTML_COPY}")


if __name__ == "__main__":
    main()
