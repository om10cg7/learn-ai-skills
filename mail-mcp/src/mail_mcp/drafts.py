"""下書きメールの組み立て（テキスト形式のみ）。

- 署名は本文末尾に "-- " 区切りで付与（RFC 3676 の慣習）
- 返信は Re: 付与、In-Reply-To / References 引き継ぎ、元メール引用（> 付き）
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid, parseaddr

RE_PREFIX = re.compile(r"^\s*(re|返信|fw|fwd|転送)\s*:\s*", re.IGNORECASE)


@dataclass
class OriginalMail:
    """返信元メールの、下書き作成に必要な情報だけを切り出したもの。"""

    subject: str
    from_: str          # "名前 <addr>" 形式
    to: tuple[str, ...]
    cc: tuple[str, ...]
    reply_to: tuple[str, ...]
    date: datetime | None
    message_id: str | None
    references: str | None
    text: str


@dataclass
class DraftSpec:
    from_name: str
    from_email: str
    to: list[str]
    subject: str
    body: str
    cc: list[str] = field(default_factory=list)
    signature: str = ""
    in_reply_to: str | None = None
    references: str | None = None


def apply_signature(body: str, signature: str) -> str:
    body = body.rstrip("\n")
    if not signature.strip():
        return body + "\n"
    return f"{body}\n\n-- \n{signature.strip()}\n"


def reply_subject(subject: str) -> str:
    s = (subject or "").strip()
    return s if RE_PREFIX.match(s) else f"Re: {s}"


def quote_text(text: str) -> str:
    lines = (text or "").rstrip("\n").splitlines() or [""]
    return "\n".join(f"> {l}" if l else ">" for l in lines)


def quote_header(original: OriginalMail) -> str:
    """メールソフト風の引用ヘッダ。例: 2026/10/28 14:03、山田太郎 <taro@example.jp> wrote:"""
    d = original.date
    if d and d.tzinfo:
        d = d.astimezone()  # 表示はローカル時刻（コンテナの TZ。compose/Docker 設定で TZ=Asia/Tokyo を渡す）
    when = d.strftime("%Y/%m/%d %H:%M") if d else ""
    return f"{when}、{original.from_} wrote:".lstrip("、")


def build_reply_spec(
    original: OriginalMail,
    *,
    from_name: str,
    from_email: str,
    body: str,
    signature: str = "",
    reply_all: bool = False,
    include_quote: bool = True,
) -> DraftSpec:
    # 返信先: Reply-To があればそれ、なければ From
    to = list(original.reply_to) if original.reply_to else [original.from_]
    cc: list[str] = []
    if reply_all:
        me = from_email.lower()
        for addr in (*original.to, *original.cc):
            email_only = parseaddr(addr)[1].lower()
            if email_only and email_only != me and all(parseaddr(x)[1].lower() != email_only for x in to + cc):
                cc.append(addr)

    refs = " ".join(x for x in (original.references, original.message_id) if x) or None

    full_body = body.rstrip("\n")
    if include_quote:
        full_body = f"{full_body}\n\n{quote_header(original)}\n{quote_text(original.text)}"

    return DraftSpec(
        from_name=from_name,
        from_email=from_email,
        to=to,
        cc=cc,
        subject=reply_subject(original.subject),
        body=full_body,
        signature=signature,
        in_reply_to=original.message_id,
        references=refs,
    )


def build_message(spec: DraftSpec) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = formataddr((spec.from_name, spec.from_email))
    msg["To"] = ", ".join(spec.to)
    if spec.cc:
        msg["Cc"] = ", ".join(spec.cc)
    msg["Subject"] = spec.subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=spec.from_email.split("@")[-1])
    if spec.in_reply_to:
        msg["In-Reply-To"] = spec.in_reply_to
    if spec.references:
        msg["References"] = spec.references
    # 日本語は UTF-8 / 8bit でそのまま入れる（EmailMessage がヘッダのエンコードも面倒を見る）
    msg.set_content(apply_signature(spec.body, spec.signature), charset="utf-8")
    return msg
