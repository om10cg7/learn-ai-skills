"""
Outlook(Hotmail) の指定フォルダーを IMAP で全件取得し、
.eml 保存 + 1つの Markdown に結合する。

準備:
    pip install html2text msal
実行:
    python outlook_folder_to_md.py --user <Outlookのアドレス> --client-id <クライアントID> [--folder フォルダー名]
    (初回のみブラウザでサインイン。トークンは .msal_cache.bin にキャッシュ)
"""
import argparse
import base64
import email
import imaplib
import os
import re
from email.header import decode_header, make_header
from email.utils import parsedate_to_datetime
from pathlib import Path

import html2text
import msal

# ===== 設定 =====
FOLDER = "メルマガ"
HOST = "outlook.office365.com"
OUT_DIR = Path("mails")
OUT_MD = Path("all.md")
CACHE = Path(".msal_cache.bin")
SCOPES = ["https://outlook.office.com/IMAP.AccessAsUser.All"]
# ================


def utf7_encode(s: str) -> str:
    """IMAP修正UTF-7エンコード"""
    out, buf = [], ""

    def flush():
        nonlocal buf
        if buf:
            b = base64.b64encode(buf.encode("utf-16-be")).decode().rstrip("=")
            out.append("&" + b.replace("/", ",") + "-")
            buf = ""

    for ch in s:
        if 0x20 <= ord(ch) <= 0x7E:
            flush()
            out.append("&-" if ch == "&" else ch)
        else:
            buf += ch
    flush()
    return "".join(out)


def utf7_decode(s: str) -> str:
    def repl(m):
        t = m.group(1)
        if t == "":
            return "&"
        t = t.replace(",", "/")
        t += "=" * (-len(t) % 4)
        return base64.b64decode(t).decode("utf-16-be")

    return re.sub(r"&([^-]*)-", repl, s)


def dh(v) -> str:
    return str(make_header(decode_header(v))) if v else ""


def get_body(msg) -> str:
    plain, html = None, None
    for part in msg.walk():
        if part.get_content_maintype() == "multipart":
            continue
        if part.get_content_disposition() == "attachment":
            continue
        ctype = part.get_content_type()
        payload = part.get_payload(decode=True)
        if payload is None:
            continue
        text = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        if ctype == "text/plain" and plain is None:
            plain = text
        elif ctype == "text/html" and html is None:
            html = text
    if html:
        h = html2text.HTML2Text()
        h.body_width = 0
        h.ignore_images = True
        return h.handle(html).strip()
    return (plain or "").strip()


def find_folder(imap, name: str) -> str:
    """フォルダー一覧からデコード後の名前が一致するものを探す"""
    _, lst = imap.list()
    for raw in lst:
        line = raw.decode()
        m = re.search(r'"([^"]+)"\s+(.+)$', line)
        if not m:
            continue
        mailbox = m.group(2).strip().strip('"')
        if utf7_decode(mailbox).split("/")[-1].split(".")[-1] == name or utf7_decode(mailbox) == name:
            return mailbox
    return utf7_encode(name)


def get_token(client_id: str, user: str) -> str:
    cache = msal.SerializableTokenCache()
    if CACHE.exists():
        cache.deserialize(CACHE.read_text())
    app = msal.PublicClientApplication(
        client_id, authority="https://login.microsoftonline.com/consumers", token_cache=cache
    )
    result = None
    accounts = app.get_accounts(username=user)
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
    if not result:
        flow = app.initiate_device_flow(scopes=SCOPES)
        if "user_code" not in flow:
            raise SystemExit(f"認証開始に失敗: {flow.get('error')} {flow.get('error_description')}")
        print(flow["message"])  # ブラウザで URL を開き、表示されたコードを入力
        result = app.acquire_token_by_device_flow(flow)
    if cache.has_state_changed:
        CACHE.write_text(cache.serialize())
    if "access_token" not in result:
        raise SystemExit(f"認証失敗: {result.get('error')} {result.get('error_description')}")
    return result["access_token"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", required=True, help="Outlookアドレス")
    ap.add_argument("--client-id", required=True, help="Azureアプリ登録のクライアントID")
    ap.add_argument("--folder", default=FOLDER)
    args = ap.parse_args()
    USER, FOLDER_NAME = args.user, args.folder
    token = get_token(args.client_id, USER)
    OUT_DIR.mkdir(exist_ok=True)

    imap = imaplib.IMAP4_SSL(HOST, 993)
    ctl = chr(1)  # XOAUTH2 の区切り文字
    imap.authenticate("XOAUTH2", lambda _: f"user={USER}{ctl}auth=Bearer {token}{ctl}{ctl}".encode())

    box = find_folder(imap, FOLDER_NAME)
    typ, _ = imap.select(f'"{box}"', readonly=True)
    if typ != "OK":
        print("フォルダーが開けません。フォルダー一覧:")
        for raw in imap.list()[1]:
            print(" ", utf7_decode(raw.decode()))
        return

    _, data = imap.uid("search", None, "ALL")
    uids = data[0].split()
    print(f"{len(uids)} 通を取得します")

    items = []
    for i, uid in enumerate(uids, 1):
        _, d = imap.uid("fetch", uid, "(RFC822)")
        raw = d[0][1]
        (OUT_DIR / f"{uid.decode()}.eml").write_bytes(raw)
        msg = email.message_from_bytes(raw)
        try:
            dt = parsedate_to_datetime(msg["Date"])
        except Exception:
            dt = None
        items.append((dt, dh(msg["Subject"]), dh(msg["From"]), get_body(msg)))
        print(f"  {i}/{len(uids)}", end="\r")
    imap.logout()

    items.sort(key=lambda x: (x[0] is None, x[0]))

    with OUT_MD.open("w", encoding="utf-8") as f:
        f.write(f"# {FOLDER_NAME} フォルダー全メール ({len(items)}通)\n\n")
        for dt, subj, frm, body in items:
            f.write(f"## {subj}\n\n")
            f.write(f"- 受信: {dt:%Y-%m-%d %H:%M}\n" if dt else "- 受信: 不明\n")
            f.write(f"- 差出人: {frm}\n\n")
            f.write(body + "\n\n---\n\n")

    print(f"\n完了: {OUT_MD} / .eml は {OUT_DIR}/")


if __name__ == "__main__":
    main()
