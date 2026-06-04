# -*- coding: utf-8 -*-
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

# Ordered blocks: paragraph text + images
blocks = re.findall(r"<w:p[^>]*>.*?</w:p>", doc, re.DOTALL)
lines = []
week = None
week_data = {}

for bp in blocks:
    text = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", bp)).strip()
    embeds = re.findall(r'r:embed="(rId\d+)"', bp)
    low = text.lower()

    wm = re.match(r"(?i)^#?\s*tuần\s*(\d+)", text) or re.match(r"(?i)^tuần\s*(\d+)", text)
    if wm:
        week = int(wm.group(1))
        week_data.setdefault(week, {"headings": [], "images": [], "chars": 0})
        lines.append(f"\n\n===== TUAN {week} =====\n")

    if week is None:
        continue

    if text:
        week_data[week]["chars"] += len(text)
        if re.match(r"^\d+\.", text) or re.match(r"^\d+\.\d+", text):
            week_data[week]["headings"].append(text[:100])
        lines.append(text)

    for rid in embeds:
        tgt = rid_map.get(rid, "")
        if "media/" in tgt:
            week_data[week]["images"].append(tgt.split("/")[-1])

out = ROOT / "LMS_extracted.txt"
out.write_text("\n".join(lines), encoding="utf-8")

summary = ROOT / "LMS_week_summary.txt"
s = ["WEEK SUMMARY FROM DOCX\n"]
for w in sorted(week_data):
    d = week_data[w]
    s.append(f"Week {w}: {d['chars']} chars, {len(d['images'])} images")
    s.append(f"  images: {', '.join(d['images'][:15])}")
    for h in d["headings"][:20]:
        s.append(f"  - {h}")
    if len(d["headings"]) > 20:
        s.append(f"  ... +{len(d['headings'])-20} more headings")
    s.append("")
summary.write_text("\n".join(s), encoding="utf-8")
print(summary.read_text(encoding="utf-8"))
