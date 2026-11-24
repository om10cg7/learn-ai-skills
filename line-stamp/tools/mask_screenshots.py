"""記事用スクリーンショットの個人情報を塗りつぶして PNG で保存する。"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

# マイページのヘッダーに出る名前の範囲（画面幅 1512 px のときの座標）
NAME_BOX = (1095, 10, 1180, 48)
FRAME_WIDTH = 1512

src_dir = Path(sys.argv[1])
out_dir = Path(sys.argv[2])
out_dir.mkdir(parents=True, exist_ok=True)

# 出力名, 元ファイルの末尾, ヘッダーの名前を隠すか
ITEMS = [
    ("01-top.png", "1794133250034-8ks6c7.jpg", False),
    ("02-login.png", "1794133435940-0l90l8.jpg", False),
    ("03-mypage.png", "1794134643680-x9ddsf.jpg", True),
    ("04-create-type.png", "1794134652886-65km6l.jpg", True),
    ("05-form-details.png", "1794134736187-ee9u3s.jpg", True),
    ("06-form-sales.png", "1794134739361-grj19t.jpg", False),
    ("07-form-options.png", "1794134675216-erempr.jpg", False),
    ("08-form-license.png", "1794134683776-laorja.jpg", False),
    ("09-form-filled.png", "1794134907365-4m3fdb.jpg", False),
    ("10-item-saved.png", "1794134931570-30q3x3.jpg", True),
    ("11-image-edit-empty.png", "1794134953006-o4y4rm.jpg", True),
    ("12-image-uploaded.png", "1794134983233-kkluvq.jpg", True),
    ("13-image-uploaded-bottom.png", "1794134988050-vkthtv.jpg", False),
    ("14-price.png", "1794134991732-ou4w7i.jpg", True),
    ("15-request-agreement.png", "1794135811105-atlcf0.jpg", True),
    ("16-requested.png", "1794135823144-58uij2.jpg", True),
]

# 追加で隠す範囲（スタンプ ID など。画面幅 1512 px のときの座標）
EXTRA_BOXES = {"10-item-saved.png": [(525, 452, 615, 474)]}

for out_name, suffix, hide_name in ITEMS:
    matches = list(src_dir.glob(f"*-{suffix}"))
    if len(matches) != 1:
        raise SystemExit(f"元画像が特定できません: {suffix}")
    image = Image.open(matches[0]).convert("RGB")
    if hide_name:
        ratio = image.width / FRAME_WIDTH
        box = tuple(round(v * ratio) for v in NAME_BOX)
        color = image.getpixel((box[0] - round(15 * ratio), box[1] + round(5 * ratio)))
        ImageDraw.Draw(image).rectangle(box, fill=color)
    for extra in EXTRA_BOXES.get(out_name, []):
        ratio = image.width / FRAME_WIDTH
        ImageDraw.Draw(image).rectangle(tuple(round(v * ratio) for v in extra), fill=(255, 255, 255))
    image.save(out_dir / out_name)
    print(out_name, image.size, "masked" if hide_name else "as-is")
