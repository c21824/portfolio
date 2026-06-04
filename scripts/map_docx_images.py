# -*- coding: utf-8 -*-
"""List images in document order per week from LMS.docx."""
import re
import sys
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
z = zipfile.ZipFile(ROOT / "LMS.docx")
doc = z.read("word/document.xml").decode("utf-8")
rels = z.read("word/_rels/document.xml.rels").decode("utf-8")
rid_map = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="([^"]+)"', rels))
blocks = re.findall(r"<w:p[^>]*>.*?</w:p>", doc, re.DOTALL)

week = None
last_text = ""
idx = 0
by_week = {w: [] for w in range(1, 7)}

for bp in blocks:
    text = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", bp)).strip()
    embeds = [
        rid_map.get(r, "").split("/")[-1]
        for r in re.findall(r'r:embed="(rId\d+)"', bp)
        if "media/" in rid_map.get(r, "")
    ]
    wm = re.match(r"(?i)^#?\s*tuần\s*(\d+)", text) or re.match(r"(?i)^tuần\s*(\d+)", text)
    if wm:
        week = int(wm.group(1))
    if week and embeds:
        for img in embeds:
            idx += 1
            by_week[week].append((idx, last_text[:60], img))
    if text:
        last_text = text

for w in range(1, 7):
    print(f"\n=== TUAN {w}: {len(by_week[w])} images ===")
    for i, ctx, img in by_week[w]:
        print(f"  {i:2d}. {img}  <- {ctx}")
