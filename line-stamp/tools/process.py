from __future__ import annotations

import argparse
import io
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

STRUCT8 = np.ones((3, 3), dtype=int)


def estimate_bg_color(sheet_rgb: np.ndarray) -> np.ndarray:
    h, w = sheet_rgb.shape[:2]
    cy, cx = min(20, h), min(20, w)
    corners = np.concatenate(
        [
            sheet_rgb[:cy, :cx].reshape(-1, 3),
            sheet_rgb[:cy, -cx:].reshape(-1, 3),
            sheet_rgb[-cy:, :cx].reshape(-1, 3),
            sheet_rgb[-cy:, -cx:].reshape(-1, 3),
        ],
        axis=0,
    )
    return np.median(corners, axis=0)


def load_sheet(path: Path, upscale: int) -> np.ndarray:
    image = Image.open(path).convert("RGB")
    if upscale > 1:
        size = (image.width * upscale, image.height * upscale)
        image = image.resize(size, Image.Resampling.LANCZOS).filter(
            ImageFilter.UnsharpMask(radius=upscale, percent=90, threshold=2)
        )
    return np.asarray(image)


def seal_mask(shape: tuple[int, int], seals: list[list[int]], upscale: int) -> np.ndarray:
    canvas = Image.new("L", (shape[1], shape[0]), 0)
    draw = ImageDraw.Draw(canvas)
    for x0, y0, x1, y1 in seals:
        draw.line([(x0 * upscale, y0 * upscale), (x1 * upscale, y1 * upscale)], fill=255, width=upscale)
    return np.asarray(canvas) > 0


def extract_foreground(
    sheet_rgb: np.ndarray,
    box: list[int],
    bg_color: np.ndarray,
    bg_threshold: float,
    barrier: np.ndarray | None = None,
) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    sh, sw = sheet_rgb.shape[:2]
    x0, y0, x1, y1 = (int(round(v)) for v in box)
    x0, x1 = max(0, x0), min(sw, x1)
    y0, y1 = max(0, y0), min(sh, y1)

    rgb = sheet_rgb[y0:y1, x0:x1].copy()
    h, w = rgb.shape[:2]
    if h == 0 or w == 0:
        return np.zeros((0, 0, 4), dtype=np.uint8), (x0, y0, x1, y1)

    dist = np.linalg.norm(rgb.astype(np.float32) - bg_color, axis=-1)
    bg_cand = dist <= bg_threshold
    if barrier is not None:
        cut = barrier[y0:y1, x0:x1]
        rgb[cut & bg_cand] = (255, 255, 255)
        bg_cand = bg_cand & ~cut

    border =np.zeros((h, w), dtype=bool)
    border[0, :] = border[-1, :] = border[:, 0] = border[:, -1] = True

    bg_lbl, _ = ndimage.label(bg_cand, structure=STRUCT8)
    ext_labels = np.unique(bg_lbl[border & (bg_lbl > 0)])
    ext_bg = np.isin(bg_lbl, ext_labels)

    rgb[bg_cand & ~ext_bg] = (255, 255, 255)

    opaque = ~ext_bg
    op_lbl, num_op = ndimage.label(opaque, structure=STRUCT8)
    if num_op > 0:
        counts = np.bincount(op_lbl.ravel())
        edge_labels = np.unique(op_lbl[border & (op_lbl > 0)])
        min_area = np.full(num_op + 1, 12, dtype=int)
        min_area[edge_labels] = 2000
        min_area[0] = 0
        drop = np.flatnonzero(counts < min_area)
        if drop.size:
            opaque[np.isin(op_lbl, drop)] = False

    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[opaque, :3] = rgb[opaque]
    rgba[opaque, 3] = 255
    return rgba, (x0, y0, x1, y1)


def crop_sheet_box(
    cell_rgba: np.ndarray,
    cell_box: tuple[int, int, int, int],
    sub_box: list[int],
) -> np.ndarray:
    cx0, cy0, cx1, cy1 = cell_box
    sx0, sy0, sx1, sy1 = (int(round(v)) for v in sub_box)
    out = np.zeros((max(0, sy1 - sy0), max(0, sx1 - sx0), 4), dtype=np.uint8)
    ix0, iy0 = max(cx0, sx0), max(cy0, sy0)
    ix1, iy1 = min(cx1, sx1), min(cy1, sy1)
    if ix0 < ix1 and iy0 < iy1:
        out[iy0 - sy0 : iy1 - sy0, ix0 - sx0 : ix1 - sx0] = cell_rgba[
            iy0 - cy0 : iy1 - cy0, ix0 - cx0 : ix1 - cx0
        ]
    return out


def keep_largest_component(rgba: np.ndarray) -> np.ndarray:
    labels, count = ndimage.label(rgba[..., 3] > 0, structure=STRUCT8)
    if count == 0:
        return rgba
    areas = np.bincount(labels.ravel())
    areas[0] = 0
    out = rgba.copy()
    out[labels != int(areas.argmax())] = 0
    return out


def write_submission(cfg: dict, base_dir: Path, out_dir: Path) -> None:
    submission = cfg.get("submission")
    if not submission:
        return
    target = (base_dir / submission["dir"]).resolve()
    target.mkdir(parents=True, exist_ok=True)
    for old in target.glob("*.png"):
        old.unlink()
    for number, cell_id in enumerate(submission["cells"], start=1):
        (target / f"{number:02d}.png").write_bytes((out_dir / f"{cell_id}.png").read_bytes())
    for name in ("main.png", "tab.png"):
        (target / name).write_bytes((out_dir / name).read_bytes())


def render_outlined_content(
    rgba: np.ndarray,
    max_w: int,
    max_h: int,
    outline_px: float,
    allow_upscale: bool,
) -> np.ndarray:
    ys, xs = np.nonzero(rgba[..., 3] > 0)
    if ys.size == 0:
        return np.zeros((2, 2, 4), dtype=np.uint8)
    cropped = rgba[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1]
    bh, bw = cropped.shape[:2]

    avail_w = max(1.0, max_w - 2.0 * outline_px)
    avail_h = max(1.0, max_h - 2.0 * outline_px)
    scale = min(avail_w / bw, avail_h / bh)
    if not allow_upscale:
        scale = min(scale, 1.0)

    content = cropped
    for _ in range(4):
        r = outline_px / scale
        pad = int(math.ceil(r)) + 2
        padded = np.pad(cropped, ((pad, pad), (pad, pad), (0, 0)))

        src_rgb = padded[..., :3].astype(np.float32)
        src_a = padded[..., 3].astype(np.float32) / 255.0

        d = ndimage.distance_transform_edt(src_a == 0.0)
        alpha_outline = np.clip(r + 0.5 - d, 0.0, 1.0).astype(np.float32)

        comp_a = src_a + alpha_outline * (1.0 - src_a)
        comp_rgb = np.where(
            comp_a[..., None] > 0.0,
            (
                src_rgb * src_a[..., None]
                + 255.0 * alpha_outline[..., None] * (1.0 - src_a[..., None])
            )
            / np.maximum(comp_a[..., None], 1e-8),
            0.0,
        )

        ph, pw = padded.shape[:2]
        nw = max(1, int(round(pw * scale)))
        nh = max(1, int(round(ph * scale)))

        pre_rgb = comp_rgb * comp_a[..., None]
        res_pre = np.stack(
            [
                np.asarray(
                    Image.fromarray(
                        np.ascontiguousarray(pre_rgb[..., c], dtype=np.float32)
                    ).resize((nw, nh), Image.Resampling.LANCZOS)
                )
                for c in range(3)
            ],
            axis=-1,
        )
        res_a = np.asarray(
            Image.fromarray(np.ascontiguousarray(comp_a, dtype=np.float32)).resize(
                (nw, nh), Image.Resampling.LANCZOS
            )
        )
        support = (
            np.asarray(
                Image.fromarray(
                    np.ascontiguousarray(comp_a > 0.0, dtype=np.float32)
                ).resize((nw, nh), Image.Resampling.BILINEAR)
            )
            > 0.0
        )

        res_a = np.where(support, np.clip(res_a, 0.0, 1.0), 0.0)
        res_alpha = np.clip(np.rint(res_a * 255.0), 0, 255).astype(np.uint8)
        res_rgb = np.where(
            res_a[..., None] > 1e-6,
            res_pre / np.maximum(res_a[..., None], 1e-6),
            0.0,
        )
        res_rgb = np.clip(np.rint(res_rgb), 0, 255).astype(np.uint8)
        res_rgb[res_alpha == 0] = 0
        res_rgba = np.dstack([res_rgb, res_alpha])

        oys, oxs = np.nonzero(res_alpha > 0)
        if oys.size == 0:
            return np.zeros((2, 2, 4), dtype=np.uint8)
        content = res_rgba[oys.min() : oys.max() + 1, oxs.min() : oxs.max() + 1]
        ch, cw = content.shape[:2]
        if cw <= max_w and ch <= max_h:
            return content
        scale *= min(max_w / cw, max_h / ch) * 0.995

    return content[:max_h, :max_w]


def build_stamp(cell_rgba: np.ndarray, outline_px: float) -> Image.Image:
    content = render_outlined_content(
        cell_rgba, 350, 300, outline_px, allow_upscale=True
    )
    ch, cw = content.shape[:2]
    ow = cw + 20 + ((cw + 20) % 2)
    oh = ch + 20 + ((ch + 20) % 2)
    canvas = np.zeros((oh, ow, 4), dtype=np.uint8)
    canvas[10 : 10 + ch, 10 : 10 + cw] = content
    return Image.fromarray(canvas)


def build_fixed_icon(
    rgba: np.ndarray,
    canvas_w: int,
    canvas_h: int,
    margin: int,
    outline_px: float,
) -> Image.Image:
    content = render_outlined_content(
        rgba,
        canvas_w - 2 * margin,
        canvas_h - 2 * margin,
        outline_px,
        allow_upscale=False,
    )
    ch, cw = content.shape[:2]
    canvas = np.zeros((canvas_h, canvas_w, 4), dtype=np.uint8)
    x = (canvas_w - cw) // 2
    y = (canvas_h - ch) // 2
    canvas[y : y + ch, x : x + cw] = content
    return Image.fromarray(canvas)


def save_png(img: Image.Image, path: Path, max_bytes: int = 1_000_000) -> None:
    rgba_img = img.convert("RGBA")
    buf = io.BytesIO()
    rgba_img.save(buf, format="PNG", dpi=(72, 72), optimize=True)
    if buf.tell() > max_bytes:
        for colors in (256, 128, 64, 32):
            quantized = rgba_img.quantize(
                colors=colors, method=Image.Quantize.FASTOCTREE
            )
            buf = io.BytesIO()
            quantized.convert("RGBA").save(
                buf, format="PNG", dpi=(72, 72), optimize=True
            )
            if buf.tell() <= max_bytes:
                break
            buf = io.BytesIO()
            quantized.save(buf, format="PNG", dpi=(72, 72), optimize=True)
            if buf.tell() <= max_bytes:
                break
    path.write_bytes(buf.getvalue())


def build_preview(items: list[Image.Image], cols: int = 4) -> Image.Image:
    if not items:
        return Image.new("RGBA", (64, 64), (0, 0, 0, 255))
    slot_w = max(im.width for im in items)
    slot_h = max(im.height for im in items)
    gap = 16
    rows = math.ceil(len(items) / cols)
    canvas_w = cols * slot_w + (cols + 1) * gap
    canvas_h = rows * slot_h + (rows + 1) * gap

    yy, xx = np.indices((canvas_h, canvas_w))
    checker = ((yy // 16) + (xx // 16)) % 2 == 0
    bg = np.where(
        checker[..., None], (212, 216, 224, 255), (26, 36, 64, 255)
    ).astype(np.uint8)
    preview = Image.fromarray(bg)

    for idx, im in enumerate(items):
        r, c = divmod(idx, cols)
        ox = gap + c * (slot_w + gap) + (slot_w - im.width) // 2
        oy = gap + r * (slot_h + gap) + (slot_h - im.height) // 2
        preview.alpha_composite(im.convert("RGBA"), (ox, oy))
    return preview


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="tools/stamps.json")
    parser.add_argument("--out", default="build")
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    base_dir = config_path.parent.parent
    out_dir = (base_dir / args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    sheet_path = base_dir / cfg["sheet"]
    bg_threshold = float(cfg["background_threshold"])
    outline_px = float(cfg["outline_px"])

    sheet_rgb = np.asarray(Image.open(sheet_path).convert("RGB"))
    bg_color = estimate_bg_color(sheet_rgb)

    processed_cells: dict[str, tuple[np.ndarray, tuple[int, int, int, int]]] = {}
    preview_items: list[Image.Image] = []

    for cell in cfg["cells"]:
        cell_id = str(cell["id"])
        if "sheet" in cell:
            upscale = int(cell.get("upscale", 1))
            cell_sheet = load_sheet(base_dir / cell["sheet"], upscale)
            cell_bg = np.array(cell["background"], dtype=np.float32)
            barrier = seal_mask(cell_sheet.shape[:2], cell.get("seals", []), upscale)
            cell_rgba, cell_box = extract_foreground(
                cell_sheet,
                [v * upscale for v in cell["box"]],
                cell_bg,
                float(cell.get("threshold", bg_threshold)),
                barrier,
            )
        else:
            cell_rgba, cell_box = extract_foreground(
                sheet_rgb, cell["box"], bg_color, bg_threshold
            )
        processed_cells[cell_id] = (cell_rgba, cell_box)

        stamp_img = build_stamp(cell_rgba, outline_px)
        save_png(stamp_img, out_dir / f"{cell_id}.png")
        preview_items.append(stamp_img)

    if "main" in cfg:
        m_cfg = cfg["main"]
        c_rgba, c_box = processed_cells[str(m_cfg["cell"])]
        m_src = keep_largest_component(crop_sheet_box(c_rgba, c_box, m_cfg["box"]))
        main_img = build_fixed_icon(m_src, 240, 240, margin=10, outline_px=4.0)
        save_png(main_img, out_dir / "main.png")
        preview_items.append(main_img)

    if "tab" in cfg:
        t_cfg = cfg["tab"]
        c_rgba, c_box = processed_cells[str(t_cfg["cell"])]
        t_src = keep_largest_component(crop_sheet_box(c_rgba, c_box, t_cfg["box"]))
        tab_img = build_fixed_icon(t_src, 96, 74, margin=4, outline_px=2.0)
        save_png(tab_img, out_dir / "tab.png")
        preview_items.append(tab_img)

    preview_img = build_preview(preview_items)
    preview_img.save(out_dir / "_preview.png", format="PNG", dpi=(72, 72), optimize=True)
    write_submission(cfg, base_dir, out_dir)


if __name__ == "__main__":
    main()
