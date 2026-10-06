Outlookのフォルダーにたまったメールを、あとからAIに読ませたいことがあります。メールのまま1通ずつ開くのは手間で、コピーして貼る作業も続きません。

この記事では、OutlookのフォルダーをIMAPで全件取り込み、1つのMarkdownにまとめるスクリプトを作るところまでをまとめます。パスワードでは入れず、OAuth2に切り替えたときのつまずきも書いておきます。個人情報が外に出ない作りにしました。

## なぜメールをMarkdownにしたいか

購読しているメルマガが、Outlookのフォルダーに1年半分たまっています。読み返したり、AIに要約させたりしたいのですが、メールのままでは扱いにくい状態です。

Markdownなら、エディターでもAIでも同じように読めます。1号1見出しにそろえておけば、検索や引用もしやすくなります。

前回は、AIの日本語を直すスキルyomiyasuを試しました。今回は、AIに読ませる文章を集める側の作業です。

https://note.com/om10cg72/n/n62928ada43f4

## outlook_folder_to_mdとは？

私が自分用に作った、OutlookのフォルダーをMarkdownにまとめるスクリプトです。2本で合わせて278行になります。

- outlook_folder_to_md.py：フォルダーをIMAPで全件取得し、元の.emlと、結合したMarkdownを出力する
- format_md.py：取得したMarkdownから定型文と個人情報を取り除き、件名の発行日順に並べ直す

取得と整形を分けたのは、元データを残したまま整形をやり直せるようにするためです。整形のルールは何度か直したので、この分け方が役に立ちました。

**個人情報を出さないための設計**

記事にするつもりだったので、最初から個人情報が外に出にくい形にしました。確認できたことは次のとおりです。

- アドレスとクライアントIDは、コードに書かず引数で渡す
- パスワードは使わない。トークンのキャッシュ、取得した.eml、Markdownは `.gitignore` で除外する
- 整形で、メールアドレス、`mailto:`、トークン付きのログイン用URLを取り除く

本文は著作物なので、この記事にも載せていません。書いているのは、仕組みと件数だけです。

## 導入手順

### 環境

- OS：Windows 11 Pro
- Python：3.11.9
- msal：1.39.0
- html2text：2025.4.15

### 1. パッケージを入れる

```bash
pip install html2text msal
```

### 2. Azureでアプリを登録する

Azureポータルの「アプリの登録」で、新規登録します。リダイレクトURIは、パブリッククライアントとして `http://localhost` を入れました。

個人のHotmailアカウントで使うには、サポートするアカウントの種類に個人用Microsoftアカウントを含める必要があります。画面からは保存できなかったので、マニフェストを直接編集しました。詳しくは「ハマったところ」に書いています。

### 3. 取得する

```bash
python outlook_folder_to_md.py --user <Outlookのアドレス> --client-id <クライアントID>
```

初回は、画面に表示されたURLをブラウザで開き、表示されたコードを入力してサインインします。トークンは `.msal_cache.bin` に保存されるので、2回目以降は入力が要りません。

### 4. 整形する

```bash
python format_md.py
```

`clean.md` ができます。元の `all.md` と.emlは変更しません。

## ハマったところ

### パスワードでは入れない

最初は、アプリパスワードでIMAPにログインする方式で書きました。結果は次のエラーです。

```
imaplib.IMAP4.error: b'Basic authentication is disabled.'
```

Outlook.comのIMAPは、パスワード方式のログインを受け付けない設定でした。パスワードの間違いではないので、入れ直しても通りません。その前に、パスワード欄に全角文字が入って `UnicodeEncodeError` も出しています。こちらは入力ミスでした。

MSALによるOAuth2(XOAUTH2)に書き換えて、解決しました。

### アプリ登録の種類が合わない

登録直後は、サポートするアカウントの種類が「所属する組織のみ」でした。これでは個人のアカウントでサインインできません。

画面で変更すると、次のエラーで保存に失敗しました。

```
Property api.requestedAccessTokenVersion is invalid.
```

マニフェストを直接編集して、次の3か所を変えると保存できました。

- `signInAudience` を `AzureADandPersonalMicrosoftAccount` にする
- `requestedAccessTokenVersion` を `2` にする
- `isFallbackPublicClient` を `true` にする

### ブラウザが開かない

サインインは、最初はブラウザが自動で開く方式でした。環境によっては開かないので、デバイスコード方式に変えました。画面に出るURLとコードを、好きなブラウザで入力する形です。

コードには有効期限があります。入力する前にCtrl+Cで止めると使えなくなるので、スクリプトをもう一度実行して、新しいコードを取り直します。

### XOAUTH2の区切り文字

IMAPへの認証は、トークンを使って次のように行います。

```python
ctl = chr(1)  # XOAUTH2 の区切り文字
imap.authenticate("XOAUTH2", lambda _: f"user={USER}{ctl}auth=Bearer {token}{ctl}{ctl}".encode())
```

区切り文字の `\x01` は、最初はコードに制御文字として直接書いてしまいました。動きますが壊れやすいので、`chr(1)` に直しています。

## 実際に取得して整形してみる

### 結果

67通を取得して、約1.5MBのMarkdownになりました。受信日は2025年3月から2026年10月までです。

整形後のファイルで、メールアドレスの形の文字列は0件でした。整形前は153件ありました。`mailto:` と、トークン付きのログイン用URLも、残っていません。

並び順は、受信日ではなく件名の発行日にしました。過去の号がまとめて同じ日時に届いていて、受信日順だと順番が決まらないからです。本文は、要約も書き換えもしていません。

### 残った課題

- 試したのは、1つのフォルダー、1種類のメルマガだけ。整形のルールはその形に合わせてあり、別のメールでは書き換えが必要
- `IMAP.AccessAsUser.All` の権限は、ポータルで追加できなかった。取得は通ったが、同意画面が出たかどうかは確認していない
- 6月17日号が2通ある(受信日が1日違い)。再送の可能性があるが、内容の違いは確認していない。どちらも残した
- トークンのキャッシュは平文のファイル。使い終わったら削除する
- 本文は著作物なので、取得したMarkdownは公開できない

## まとめ

- IMAPのパスワード方式は `Basic authentication is disabled.` で通らない。MSALのOAuth2(XOAUTH2)に切り替える
- 個人アカウントで使うには、アプリ登録のアカウントの種類とトークンのバージョンを、マニフェストで直す
- ブラウザが開かないときは、デバイスコード方式にすると進められる
- 67通を取得し、定型文とメールアドレスを除いた約1.5MBのMarkdownにできた
- アドレスとクライアントIDは引数で渡し、出力とトークンは `.gitignore` で、リポジトリに入れない

次回は、まとめたMarkdownをAIに読ませて、号ごとの要約や横断した質問を試します。

## 付録：プログラム全文

**取得するスクリプト(outlook_folder_to_md.py)**

```python
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
```

**整形するスクリプト(format_md.py)**

整形のルールは、読み込んだメルマガの形に合わせてあります。別のメールに使うときは、`FOOTER_START` と `LOGIN_NOTICE` の正規表現を書き換えてください。

```python
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
```

※動作確認はWindows 11での結果です。数値は2026年10月6日時点のものです。コードは自分の環境で実行したもので、別のメールでは整形のルールの調整が必要です。
