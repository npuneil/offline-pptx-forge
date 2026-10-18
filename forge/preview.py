"""PPTX -> PNG via PowerPoint COM (local, offline) and a labelled contact sheet."""
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .config import ROOT


def export(pptx, out_dir, width=1600):
    script = ROOT / "tools" / "export-slides.ps1"
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script),
                        "-Pptx", str(pptx), "-OutDir", str(out_dir), "-Width", str(width)],
                       capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        raise RuntimeError(f"PowerPoint export failed: {r.stderr.strip() or r.stdout.strip()}")
    return sorted(Path(out_dir).glob("slide*.png"))


def contact_sheet(pngs, out_png, label="", cols=3, thumb_w=620):
    pngs = list(pngs)
    if not pngs:
        raise ValueError("no slides to sheet")
    th = int(thumb_w * 9 / 16)
    pad, head = 18, 56 if label else 0
    rows = (len(pngs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * thumb_w + (cols + 1) * pad, head + rows * (th + pad) + pad), "#1E1E1E")
    d = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(r"C:\Windows\Fonts\seguisb.ttf", 26)
    small = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 15)
    if label:
        d.text((pad, 14), label, font=font, fill="#FFFFFF")
    for i, p in enumerate(pngs):
        im = Image.open(p).convert("RGB").resize((thumb_w, th), Image.LANCZOS)
        x = pad + (i % cols) * (thumb_w + pad)
        y = head + pad + (i // cols) * (th + pad)
        sheet.paste(im, (x, y))
        d.rectangle([x, y, x + 30, y + 22], fill="#000000")
        d.text((x + 6, y + 1), str(i + 1), font=small, fill="#FFFFFF")
    Path(out_png).parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_png)
    return out_png


def preview(pptx, out_dir, label=""):
    pngs = export(pptx, out_dir)
    sheet = contact_sheet(pngs, Path(out_dir) / "contact-sheet.png", label=label)
    return pngs, sheet
