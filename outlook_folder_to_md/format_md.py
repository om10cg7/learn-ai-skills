"""
all.md を整形して clean.md にする(元ファイルと .eml は変更しない)。
 - 毎号共通のヘッダー/フッターを除去
 - 個人を特定しうる情報(メールアドレス、mailto、トークン付きログインURL)を除去
 - 1号=1見出し(件名)、受信日、本文。件名の発行日の昇順
実行: python format_md.py
"""
import re
from pathlib import Path

SRC = Path("all.md")
DST = Path("clean.md")

FOOTER_START = re.compile(r"^★\s*(このメルマガの一部|『週刊 Life is beautiful』のバックナンバー)")
LOGIN_NOTICE = re.compile(r"動画、音声を見るには.*ログイン")
IMAGE_LINE = re.compile(r"^\s*https?://\S+\.(jpg|jpeg|png|gif|webp)(\?\S*)?\s*$", re.I)
IMAGE_LINK = re.compile(r"<?https?://[^\s<>]+\.(jpg|jpeg|png|gif|webp)(\?[^\s<>]*)?>?", re.I)
LINE_PROMO = re.compile(
    r"(◇[ 　]*◇[ 　]*◇\s*)?私の過去のメルマガを活用して.*?https://lin\.ee/\S+\s*(◇[ 　]*◇[ 　]*◇)?",
    re.S,
)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")
ISSUE_DATE = re.compile(r"(\d{4})年(\d{1,2})月(\d{1,2})日号")


def split_issues(text: str):
    body = text.split("\n\n", 1)[1]  # 先頭の総見出しを除く
    for chunk in re.split(r"\n---\n\s*(?=## )", body):
        chunk = chunk.strip().rstrip("-").strip()
        if chunk:
            yield chunk


def clean_body(body: str) -> str:
    lines = []
    for line in body.splitlines():
        if FOOTER_START.match(line.strip()):
            break
        lines.append(line)

    out, skip_url = [], False
    for i, line in enumerate(lines):
        s = line.strip()
        if LOGIN_NOTICE.search(s):
            skip_url = True  # 直後のログイン案内URL(トークン付き)も落とす
            continue
        if skip_url and re.match(r"https?://\S*webdoku\.jp\S*$", s):
            skip_url = False
            continue
        if s and skip_url:
            skip_url = False
        if "webdoku.jp/melma_box" in s or s.startswith("mailto:") or IMAGE_LINE.match(line):
            continue
        if s == "表紙":
            continue
        out.append(EMAIL.sub("", line))

    text = "\n".join(out)
    text = LINE_PROMO.sub("", text)
    text = IMAGE_LINK.sub("", text)
    text = re.sub(r"^(\s*)={5,}\s*$", "", text, flags=re.M)  # 区切り線の装飾
    text = re.sub(r"^(\s*)[━─=\-]{5,}\s*$", "", text, flags=re.M)
    text = re.sub(r"^#{1,6} ", lambda m: "#### ", text, flags=re.M)  # 本文内見出しは号見出しより下げる
    text = re.sub(r"[ 　]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def main():
    issues = []
    for chunk in split_issues(SRC.read_text(encoding="utf-8")):
        head, _, rest = chunk.partition("\n")
        subject = head.removeprefix("## ").strip()
        m = re.search(r"^- 受信: (.*)$", rest, re.M)
        received = m.group(1).strip() if m else "不明"
        body = rest.split("- 差出人:", 1)[-1].split("\n", 1)[-1]
        d = ISSUE_DATE.search(subject)
        key = (int(d[1]), int(d[2]), int(d[3])) if d else (9999, 0, 0)
        issues.append((key, received, subject, clean_body(body)))

    issues.sort(key=lambda x: (x[0], x[1]))
    with DST.open("w", encoding="utf-8") as f:
        f.write(f"# メルマガ全号 ({len(issues)}号)\n\n")
        for _, received, subject, body in issues:
            f.write(f"## {subject}\n\n- 受信日: {received}\n\n{body}\n\n")
    print(f"{len(issues)}号 -> {DST}")


if __name__ == "__main__":
    main()
