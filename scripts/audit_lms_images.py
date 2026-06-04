# -*- coding: utf-8 -*-
"""Compare image counts per section: LMS.docx vs projects.html."""
import re
import sys
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
html = (ROOT / "projects.html").read_text(encoding="utf-8")

z = zipfile.ZipFile(ROOT / "LMS.docx")
doc = z.read("word/document.xml").decode("utf-8")
rels = z.read("word/_rels/document.xml.rels").decode("utf-8")
rid_map = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="([^"]+)"', rels))

blocks = re.findall(r"<w:p[^>]*>.*?</w:p>", doc, re.DOTALL)

week = None
section = "intro"
docx_sections = {}  # (week, section) -> image count

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
        section = "intro"
        continue
    if week is None:
        continue

    # Section markers: "1.", "1.1.", topic titles
    if re.match(r"^\d+\.\s", text) and len(text) < 120:
        section = text[:80]
    elif re.match(r"^\d+\.\d+", text) and len(text) < 100:
        section = text[:80]

    if embeds:
        key = (week, section)
        docx_sections[key] = docx_sections.get(key, 0) + len(embeds)

# HTML: split by week sections
week_html = {}
for w in range(1, 7):
    pat = rf'id="tuan{w}"[^>]*>.*?(?=id="tuan{w + 1}"|<!-- Week {w + 1}|</section>\s*<section class="section week-content" id="tuan{w + 1}"|$)'
    m = re.search(
        rf'<section class="section week-content" id="tuan{w}"[^>]*>(.*?)(?=<section class="section week-content" id="tuan)',
        html,
        re.DOTALL,
    )
    if not m and w == 6:
        m = re.search(
            rf'<section class="section week-content" id="tuan6"[^>]*>(.*?)(?=\s*</section>\s*\n\s*<!-- Footer)',
            html,
            re.DOTALL,
        )
    if not m:
        m = re.search(rf'id="tuan{w}"[^>]*>(.*?)(?=id="tuan{w + 1}")', html, re.DOTALL)
    chunk = m.group(1) if m else ""
    imgs = re.findall(r'<img[^>]+src="([^"]+)"', chunk)
    topics = re.findall(r'<h4>([^<]+)</h4>', chunk)
    week_html[w] = {"total": len(imgs), "imgs": imgs, "topics": topics}

out = ROOT / "_lms_image_audit.txt"
lines = ["IMAGE AUDIT: LMS.docx vs projects.html\n"]

for w in range(1, 7):
    docx_total = sum(c for (wk, _), c in docx_sections.items() if wk == w)
    html_total = week_html.get(w, {}).get("total", 0)
    status = "OK" if docx_total == html_total else f"GAP ({html_total} html vs {docx_total} docx)"
    lines.append(f"\n=== TUAN {w}: {status} ===")
    lines.append(f"  DOCX total images: {docx_total}")
    lines.append(f"  HTML total images: {html_total}")

    # docx by section (top sections with images)
    sec_imgs = [(s, c) for (wk, s), c in docx_sections.items() if wk == w and c > 0]
    if sec_imgs:
        lines.append("  DOCX images by section:")
        for s, c in sec_imgs[:12]:
            lines.append(f"    [{c}] {s[:70]}")

    h = week_html.get(w, {})
    if h.get("topics"):
        lines.append(f"  HTML topics ({len(h['topics'])}):")
        for t in h["topics"][:15]:
            lines.append(f"    - {t[:70]}")
    if h.get("imgs"):
        lines.append("  HTML image paths (first 8):")
        for p in h["imgs"][:8]:
            exists = (ROOT / p).exists()
            lines.append(f"    {'OK' if exists else 'MISSING'} {p}")
        if len(h["imgs"]) > 8:
            lines.append(f"    ... +{len(h['imgs']) - 8} more")

    # Check missing files
    missing = [p for p in h.get("imgs", []) if not (ROOT / p).exists()]
    if missing:
        lines.append(f"  MISSING FILES ({len(missing)}):")
        for p in missing:
            lines.append(f"    - {p}")

out.write_text("\n".join(lines), encoding="utf-8")
print(out.read_text(encoding="utf-8"))
