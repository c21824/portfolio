"""
Upscale small screenshots and apply unsharp mask for sharper web display.
Target width: 1360px (2x for max display ~680px on retina).
"""
from __future__ import annotations

import glob
import os
from pathlib import Path

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
TARGET_WIDTH = 1360
MIN_UPSCALE = 1.05
UNSHARP = dict(radius=1.8, percent=140, threshold=2)


def process(path: Path) -> tuple[str, tuple[int, int], tuple[int, int]]:
    im = Image.open(path)
    if im.mode not in ("RGB", "RGBA"):
        im = im.convert("RGBA")
    w, h = im.size
    scale = max(1.0, TARGET_WIDTH / w) if w < TARGET_WIDTH else 1.0
    if scale >= MIN_UPSCALE:
        nw, nh = int(w * scale), int(h * scale)
        im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    im = im.filter(ImageFilter.UnsharpMask(**UNSHARP))
    im.save(path, optimize=True)
    return str(path.relative_to(ROOT)), (w, h), im.size


def main() -> None:
    patterns = [
        "image copy *.png",
        "image.png",
        "assets/week2/*.png",
        "assets/week5/*.png",
        "assets/week6/*.*",
    ]
    files: list[Path] = []
    for pat in patterns:
        files.extend(Path(p) for p in glob.glob(str(ROOT / pat)))
    files = sorted(set(files))
    print(f"Processing {len(files)} images...")
    upscaled = 0
    for fp in files:
        old, new = process(fp)[1:]
        if new[0] > old[0]:
            upscaled += 1
            print(f"  {fp.name}: {old[0]}x{old[1]} -> {new[0]}x{new[1]}")
    print(f"Done. Upscaled {upscaled}/{len(files)} files.")


if __name__ == "__main__":
    os.chdir(ROOT)
    main()
