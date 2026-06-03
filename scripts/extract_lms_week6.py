# -*- coding: utf-8 -*-
import re
import sys
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
docx = ROOT / "LMS.docx"
out_dir = ROOT / "assets" / "week6"
out_dir.mkdir(parents=True, exist_ok=True)

z = zipfile.ZipFile(docx)
doc = z.read("word/document.xml").decode("utf-8")
rels = z.read("word/_rels/document.xml.rels").decode("utf-8")
rid_to_target = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="([^"]+)"', rels))

body = re.findall(
    r"(<w:p[^>]*>.*?</w:p>|<w:drawing>.*?</w:drawing>)", doc, re.DOTALL
)
in_week6 = False
in_section3 = False
section3_images = []

for block in body:
    text = " ".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", block)).lower()
    if "tuần 6" in text or "tuan 6" in text:
        in_week6 = True
    if in_week6 and ("tuần 7" in text or "tuan 7" in text):
        break
    if in_week6 and "3. phân tích các vấn đề đạo đức" in text:
        in_section3 = True
    if in_section3 and "4. bộ nguyên tắc" in text:
        in_section3 = False

    for rid in re.findall(r'r:embed="(rId\d+)"', block):
        if not in_section3:
            continue
        target = rid_to_target.get(rid, "")
        if "media/" not in target:
            continue
        media_path = target.replace("../", "")
        data = z.read("word/" + media_path)
        ext = Path(target).suffix or ".png"
        name = f"ethics-{len(section3_images) + 1}{ext}"
        (out_dir / name).write_bytes(data)
        section3_images.append(name)
        print("saved", name, len(data))

print("count", len(section3_images))

# Week 6 all images
in_week6 = False
all_imgs = []
for block in body:
    text = " ".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", block)).lower()
    if "tuần 6" in text:
        in_week6 = True
    if in_week6 and "tuần 7" in text:
        break
    for rid in re.findall(r'r:embed="(rId\d+)"', block):
        if in_week6:
            all_imgs.append(rid_to_target.get(rid, ""))
print("week6 images", all_imgs)
