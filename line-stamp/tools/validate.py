#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path

from PIL import Image, UnidentifiedImageError

MAX_BYTES = 1_000_000
STAMP_NAME_RE = re.compile(r"[0-9]{2}\.png")
VALID_COUNTS = {8, 16, 24, 32, 40}


def is_dpi_72(dpi: object) -> bool:
    if not isinstance(dpi, tuple) or len(dpi) != 2:
        return False
    try:
        return all(
            math.isfinite(v := float(d)) and v > 0 and math.floor(v + 0.5) == 72
            for d in dpi
        )
    except (TypeError, ValueError):
        return False


def format_dpi(dpi: object) -> str:
    if isinstance(dpi, tuple) and len(dpi) == 2:
        try:
            return f"{float(dpi[0]):g}x{float(dpi[1]):g}"
        except (TypeError, ValueError):
            pass
    return str(dpi)


def check_file(path: Path | None, kind: str) -> list[str]:
    if path is None or not path.is_file():
        return ["ファイルが存在しません"]

    reasons: list[str] = []
    size = path.stat().st_size
    if size > MAX_BYTES:
        reasons.append(f"ファイルサイズが1MBを超えています ({size:,} bytes)")

    try:
        with Image.open(path) as img:
            img.load()
            if img.format != "PNG":
                reasons.append(f"PNG形式ではありません ({img.format})")
            if img.mode != "RGBA":
                reasons.append(f"モードがRGBAではありません ({img.mode})")

            w, h = img.size
            if kind == "stamp":
                if w % 2 != 0 or h % 2 != 0:
                    reasons.append(f"幅・高さが偶数ではありません ({w}x{h})")
                if w > 370 or h > 320:
                    reasons.append(f"サイズが370x320以下ではありません ({w}x{h})")
            elif kind == "main":
                if (w, h) != (240, 240):
                    reasons.append(f"サイズが240x240ではありません ({w}x{h})")
            elif kind == "tab":
                if (w, h) != (96, 74):
                    reasons.append(f"サイズが96x74ではありません ({w}x{h})")

            if img.mode == "RGBA" and w > 0 and h > 0:
                alpha = img.getchannel("A")
                corners = ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1))
                if any(alpha.getpixel(pt) != 0 for pt in corners):
                    reasons.append("四隅のalphaが0ではありません")

                margin = 2 if kind == "tab" else 8
                bbox = alpha.getbbox()
                if bbox is not None:
                    left, upper, right, lower = bbox
                    if (
                        left < margin
                        or upper < margin
                        or right > w - margin
                        or lower > h - margin
                    ):
                        reasons.append(f"外周{margin}px帯に不透明画素があります")

            dpi = img.info.get("dpi")
            if dpi is None:
                reasons.append("dpi情報がありません")
            elif not is_dpi_72(dpi):
                reasons.append(f"dpiが72ではありません ({format_dpi(dpi)})")
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError) as exc:
        reasons.append(f"画像の読み込みに失敗しました ({exc})")

    return reasons


def main() -> int:
    parser = argparse.ArgumentParser(description="LINE スタンプ出力画像を検査します。")
    parser.add_argument(
        "dir",
        nargs="?",
        default="build",
        help="検査対象ディレクトリ (既定値: build)",
    )
    parser.add_argument(
        "--expect-count",
        type=int,
        default=None,
        help="期待するスタンプ枚数 (未指定時は 8, 16, 24, 32, 40 のいずれか)",
    )
    args = parser.parse_args()

    target_dir = Path(args.dir)
    if not target_dir.is_dir():
        print(f"{target_dir}: NG - ディレクトリが存在しません")
        return 1

    files = {
        p.name: p
        for p in target_dir.iterdir()
        if p.is_file() and not p.name.startswith("_")
    }

    stamp_names = sorted(name for name in files if STAMP_NAME_RE.fullmatch(name))
    targets: list[tuple[str, Path | None, str]] = [
        *((name, files[name], "stamp") for name in stamp_names),
        ("main.png", files.get("main.png"), "main"),
        ("tab.png", files.get("tab.png"), "tab"),
    ]

    has_ng = False
    for name, path, kind in targets:
        reasons = check_file(path, kind)
        if reasons:
            has_ng = True
            print(f"{name}: NG - {'; '.join(reasons)}")
        else:
            print(f"{name}: OK - 問題なし")

    count = len(stamp_names)
    if args.expect_count is not None:
        if count == args.expect_count:
            print(f"枚数判定: OK - スタンプ{count}枚 (指定: {args.expect_count}枚)")
        else:
            has_ng = True
            print(
                f"枚数判定: NG - スタンプ{count}枚 (指定: {args.expect_count}枚と不一致)"
            )
    else:
        if count in VALID_COUNTS:
            print(f"枚数判定: OK - スタンプ{count}枚")
        else:
            has_ng = True
            print(
                f"枚数判定: NG - スタンプ{count}枚 (8, 16, 24, 32, 40 のいずれでもありません)"
            )

    return 1 if has_ng else 0


if __name__ == "__main__":
    sys.exit(main())
