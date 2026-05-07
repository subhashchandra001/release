#!/usr/bin/env python3
"""Create a contact sheet from exported keyframes for manual safety review."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--keyframes-csv", required=True)
    parser.add_argument("--keyframes-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-images", type=int, default=80)
    parser.add_argument("--thumb-width", type=int, default=160)
    parser.add_argument("--cols", type=int, default=8)
    return parser.parse_args()


def load_rows(csv_path: Path, max_images: int) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with csv_path.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
            if len(rows) >= max_images:
                break
    return rows


def main() -> None:
    args = parse_args()
    csv_path = Path(args.keyframes_csv)
    keyframes_dir = Path(args.keyframes_dir)
    output_path = Path(args.output)

    rows = load_rows(csv_path, args.max_images)
    if not rows:
        raise SystemExit(f"No keyframe rows found in {csv_path}")

    thumbs: list[tuple[str, Image.Image]] = []
    for row in rows:
        rel_path = row.get("rgb_path", "")
        if not rel_path:
            continue

        image_path = keyframes_dir.parent / rel_path
        if not image_path.exists():
            image_path = keyframes_dir / Path(rel_path).name

        if not image_path.exists():
            print(f"[warn] missing image: {image_path}")
            continue

        with Image.open(image_path) as im:
            im = im.convert("RGB")
            scale = args.thumb_width / im.width
            thumb_size = (args.thumb_width, max(1, int(im.height * scale)))
            im.thumbnail(thumb_size)
            thumbs.append((row.get("keyframe_id", image_path.stem), im.copy()))

    if not thumbs:
        raise SystemExit("No images could be loaded")

    cols = args.cols
    label_h = 18
    pad = 8
    thumb_w = args.thumb_width
    thumb_h = max(im.height for _, im in thumbs)
    rows_n = math.ceil(len(thumbs) / cols)

    sheet_w = cols * thumb_w + (cols + 1) * pad
    sheet_h = rows_n * (thumb_h + label_h) + (rows_n + 1) * pad

    sheet = Image.new("RGB", (sheet_w, sheet_h), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()

    for idx, (label, im) in enumerate(thumbs):
        r = idx // cols
        c = idx % cols
        x = pad + c * (thumb_w + pad)
        y = pad + r * (thumb_h + label_h + pad)

        sheet.paste(im, (x, y))
        draw.text((x, y + thumb_h + 2), label, fill="black", font=font)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path, quality=90)
    print(f"Wrote contact sheet: {output_path}")


if __name__ == "__main__":
    main()
