import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
W, H = 1280, 670
rng = np.random.default_rng(11)

# 和紙の地
base = np.zeros((H, W, 3), float); base[:] = (238, 229, 209)
n = rng.normal(0, 1, (H // 8 + 1, W // 8 + 1))
n = np.array(Image.fromarray(((n - n.min()) / (n.max() - n.min()) * 255).astype('uint8')).resize((W, H), Image.BICUBIC), float) / 255
base += (n[..., None] - 0.5) * 26
base += rng.normal(0, 3.2, (H, W, 1))
yy, xx = np.mgrid[0:H, 0:W]
d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
base -= (np.clip(d - 0.55, 0, 1) ** 1.6)[..., None] * np.array([40, 48, 62])
img = Image.fromarray(np.clip(base, 0, 255).astype('uint8')).convert('RGB')
dr = ImageDraw.Draw(img)

serif = "C:/Windows/Fonts/NotoSerifJP-VF.ttf"
def font(path, size, var=None):
    f = ImageFont.truetype(path, size)
    if var:
        try: f.set_variation_by_axes([var])
        except Exception: pass
    return f
ft = font(serif, 80, 900)
fs = font("C:/Windows/Fonts/YuGothB.ttc", 27)
fb = font("C:/Windows/Fonts/YuGothB.ttc", 30)
fm = font("C:/Windows/Fonts/YuGothM.ttc", 34)
ink = (28, 26, 26); red = (176, 40, 34); gray = (110, 104, 98)

dr.text((64, 44), "AIの日本語を", font=ft, fill=ink, stroke_width=1, stroke_fill=ink)
dr.text((64, 138), "自然に直すスキル", font=ft, fill=ink, stroke_width=1, stroke_fill=ink)
dr.text((68, 248), "yomiyasu を Claude Code で試してみた", font=fs, fill=(70, 64, 60))

# 前後の比較: 左 = 直す前（取り消し線）、右 = 直した後
def card(x, y, w, h, label, lines, col, strike):
    dr.rounded_rectangle((x, y, x + w, y + h), radius=10, outline=col, width=3, fill=(244, 237, 222))
    dr.text((x + 24, y + 16), label, font=fb, fill=col)
    ly = y + 74
    for t in lines:
        dr.text((x + 24, ly), t, font=fm, fill=ink if not strike else gray)
        if strike:
            tw = dr.textlength(t, font=fm)
            dr.line((x + 22, ly + 22, x + 26 + tw, ly + 22), fill=red, width=4)
        ly += 62

card(64, 322, 520, 270, "直す前", ["時間を溶かす", "静かに壊れる", "強力なパートナー"], gray, True)
card(696, 322, 520, 270, "直した後", ["手間が省ける", "気づかないうちにおかしくなる", "知識基盤を支える存在"], red, False)
# 矢印
dr.polygon([(604, 436), (664, 436), (664, 412), (692, 457), (664, 502), (664, 478), (604, 478)], fill=red)

# 落款
seal = Image.new('RGBA', (96, 96), (0, 0, 0, 0)); sd = ImageDraw.Draw(seal)
sd.rounded_rectangle((2, 2, 93, 93), radius=7, fill=(182, 38, 32, 235))
sd.text((48, 48), "読", font=font(serif, 64, 900), fill=(244, 230, 214, 255), anchor='mm')
seal = seal.rotate(6, expand=True, resample=Image.BICUBIC)
img = img.convert('RGBA'); img.alpha_composite(seal, (1140, 36)); img = img.convert('RGB')
img.save("見出し画像.jpg", quality=92)
print(img.size)
