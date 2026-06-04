# -*- coding: utf-8 -*-
"""Extract LMS.docx structure and compare with projects.html coverage."""
import re
import sys
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
docx = ROOT / "LMS.docx"
html = (ROOT / "projects.html").read_text(encoding="utf-8")

z = zipfile.ZipFile(docx)
doc = z.read("word/document.xml").decode("utf-8")
rels = z.read("word/_rels/document.xml.rels").decode("utf-8")
rid_to_target = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="([^"]+)"', rels))

paras = re.findall(r"<w:t[^>]*>([^<]*)</w:t>", doc)
full = "\n".join(paras)

# Split by week headers
week_pattern = re.compile(
    r"(?i)(?:^|\n)(#?\s*)?(tuần\s*\d+|tuan\s*\d+)",
    re.MULTILINE,
)
parts = re.split(r"(?i)(?=#?\s*tuần\s*\d+|(?<=\n)tuần\s*\d+)", full)
# Better: find positions
weeks = {}
for m in re.finditer(r"(?i)tuần\s*(\d+)", full):
    num = int(m.group(1))
    if num not in weeks:
        weeks[num] = m.start()

week_nums = sorted(weeks.keys())
sections = {}
for i, wn in enumerate(week_nums):
    start = weeks[wn]
    end = weeks[week_nums[i + 1]] if i + 1 < len(week_nums) else len(full)
    sections[wn] = full[start:end]

out = ROOT / "_lms_audit.txt"
lines = []
for wn in week_nums:
    text = sections[wn]
    lines.append(f"\n{'='*60}\nTUAN {wn} ({len(text)} chars)\n{'='*60}")
    # numbered items
    items = re.findall(r"(?m)^\s*(\d+)\.\s+([^\n]+)", text)
    for num, title in items[:25]:
        lines.append(f"  {num}. {title[:80]}")
    # sub items
    subs = re.findall(r"(?m)^\s*(\d+)\.\s+([^\n]+)", text)
    lines.append(f"  (total numbered lines: {len(subs)})")
    # images in week via xml walk
    lines.append(text[:3500])
    if len(text) > 3500:
        lines.append(f"\n... [{len(text)-3500} more chars] ...\n")
        lines.append(text[-1500:])

out.write_text("\n".join(lines), encoding="utf-8")
print("Wrote", out)

# HTML week sections
for w in range(1, 8):
    hid = f'id="tuan{w}"'
    has = hid in html or f"data-week=\"{w}\"" in html
    print(f"HTML week {w}:", "yes" if has else "NO")
