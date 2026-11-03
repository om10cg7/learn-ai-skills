"""IMAP 操作（1 アカウント分）。ツール呼び出しごとに接続→処理→切断するシンプルな方式。"""

from __future__ import annotations

import logging
import ssl
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from typing import Any, Iterator

from imap_tools import AND, MailBox, MailMessage, MailMessageFlags

from .config import AccountConfig
from .drafts import DraftSpec, OriginalMail, build_message
from .folders import Folder, find_special_folder

log = logging.getLogger(__name__)


class MailAccount:
    def __init__(self, cfg: AccountConfig):
        self.cfg = cfg

    # ---------- 接続 ----------

    @contextmanager
    def connect(self, folder: str = "INBOX") -> Iterator[MailBox]:
        ctx = ssl.create_default_context(cafile=self.cfg.ssl_ca_file)
        if not self.cfg.ssl_verify:
            log.warning("[%s] 証明書検証を無効化しています（テスト専用）", self.cfg.name)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        mb = MailBox(self.cfg.imap_host, port=self.cfg.imap_port, timeout=self.cfg.timeout, ssl_context=ctx)
        if self.cfg.auth == "oauth2":
            from .auth import access_token
            mb.xoauth2(self.cfg.username, access_token(self.cfg), initial_folder=folder)
        else:
            mb.login(self.cfg.username, self.cfg.password(), initial_folder=folder)
        try:
            yield mb
        finally:
            try:
                mb.logout()
            except Exception:  # noqa: BLE001
                pass

    # ---------- フォルダ ----------

    def list_folders(self, mb: MailBox) -> list[Folder]:
        return [Folder(f.name, f.delim, tuple(f.flags)) for f in mb.folder.list()]

    def special_folder(self, mb: MailBox, kind: str) -> str:
        override = getattr(self.cfg.folders, kind, None) if kind in ("drafts", "trash") else None
        name = find_special_folder(kind, self.list_folders(mb), override)
        if not name:
            raise RuntimeError(
                f"[{self.cfg.name}] {kind} フォルダを自動判別できません。accounts.yaml の folders.{kind} で指定してください"
            )
        return name

    # ---------- 読み取り ----------

    @staticmethod
    def _criteria(unread_only: bool, days: int | None, from_: str | None, subject: str | None, text: str | None):
        kw: dict[str, Any] = {}
        if unread_only:
            kw["seen"] = False
        if days:
            kw["date_gte"] = date.today() - timedelta(days=days)
        if from_:
            kw["from_"] = from_
        if subject:
            kw["subject"] = subject
        if text:
            kw["text"] = text
        return AND(**kw) if kw else "ALL"

    def search(
        self,
        mb: MailBox,
        *,
        folder: str = "INBOX",
        unread_only: bool,
        days: int | None,
        from_: str | None = None,
        subject: str | None = None,
        text: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        mb.folder.set(folder)
        crit = self._criteria(unread_only, days, from_, subject, text)
        charset = "UTF-8" if any(_non_ascii(x) for x in (from_, subject, text) if x) else None  # ASCII のみなら CHARSET を付けない（GreenMail 等が拒否するため）
        msgs = mb.fetch(crit, charset=charset, limit=limit, reverse=True, mark_seen=False, headers_only=True, bulk=True)
        return [self.summary(m, folder) for m in msgs]

    def fetch_one(self, mb: MailBox, folder: str, uid: str) -> MailMessage:
        mb.folder.set(folder)
        for m in mb.fetch(uid_list=[uid], mark_seen=False, limit=1):
            return m
        raise KeyError(f"[{self.cfg.name}] {folder} に UID {uid} のメールはありません")

    def summary(self, m: MailMessage, folder: str) -> dict[str, Any]:
        return {
            "account": self.cfg.name,
            "folder": folder,
            "uid": m.uid,
            "date": m.date.isoformat() if m.date else m.date_str,
            "from": _fmt_addr(m.from_values) if m.from_values else m.from_,
            "to": [_fmt_addr(v) for v in m.to_values],
            "subject": m.subject,
            "unread": MailMessageFlags.SEEN not in m.flags,
            "has_attachments": bool(m.attachments),
        }

    def detail(self, m: MailMessage, folder: str, body_max_chars: int) -> dict[str, Any]:
        body = (m.text or _html_to_text(m.html)).replace("\r\n", "\n")
        truncated = len(body) > body_max_chars
        d = self.summary(m, folder)
        d.update(
            {
                "cc": list(m.cc),
                "reply_to": list(m.reply_to),
                "message_id": _header(m, "message-id"),
                "body": body[:body_max_chars],
                "body_truncated": truncated,
                "attachments": [
                    {"filename": a.filename, "content_type": a.content_type, "size": a.size} for a in m.attachments
                ],
            }
        )
        return d

    # ---------- 下書き ----------

    def to_original(self, m: MailMessage) -> OriginalMail:
        return OriginalMail(
            subject=m.subject,
            from_=_fmt_addr(m.from_values),
            to=tuple(_fmt_addr(v) for v in m.to_values),
            cc=tuple(_fmt_addr(v) for v in m.cc_values),
            reply_to=tuple(_fmt_addr(v) for v in m.reply_to_values),
            date=m.date,
            message_id=_header(m, "message-id"),
            references=_header(m, "references"),
            text=(m.text or _html_to_text(m.html)).replace("\r\n", "\n"),
        )

    def save_draft(self, mb: MailBox, spec: DraftSpec) -> dict[str, Any]:
        folder = self.special_folder(mb, "drafts")
        msg = build_message(spec)
        mb.append(msg.as_bytes(), folder, dt=datetime.now().astimezone(), flag_set=(MailMessageFlags.DRAFT,))
        return {
            "account": self.cfg.name,
            "folder": folder,
            "to": spec.to,
            "cc": spec.cc,
            "subject": spec.subject,
            "message_id": msg["Message-ID"],
            "preview": msg.get_content()[:500],
        }

    def list_drafts(self, mb: MailBox, limit: int) -> list[dict[str, Any]]:
        folder = self.special_folder(mb, "drafts")
        mb.folder.set(folder)
        return [self.summary(m, folder) for m in mb.fetch("ALL", charset=None, limit=limit, reverse=True, mark_seen=False, headers_only=True, bulk=True)]

    def delete_draft(self, mb: MailBox, uid: str) -> dict[str, Any]:
        folder = self.special_folder(mb, "drafts")
        mb.folder.set(folder)
        mb.delete(uid)  # 下書きは完全削除でよい（ゴミ箱に残す意味がない）
        return {"account": self.cfg.name, "folder": folder, "uid": uid, "deleted": True}

    # ---------- 整理 ----------

    def mark_read(self, mb: MailBox, folder: str, uids: list[str], read: bool) -> dict[str, Any]:
        mb.folder.set(folder)
        mb.flag(uids, MailMessageFlags.SEEN, read)
        return {"account": self.cfg.name, "folder": folder, "uids": uids, "read": read}

    def move(self, mb: MailBox, folder: str, uids: list[str], destination: str) -> dict[str, Any]:
        mb.folder.set(folder)
        mb.move(uids, destination)
        return {"account": self.cfg.name, "from": folder, "to": destination, "uids": uids}

    def trash(self, mb: MailBox, folder: str, uids: list[str]) -> dict[str, Any]:
        dest = self.special_folder(mb, "trash")
        return self.move(mb, folder, uids, dest)


# ---------- 小物 ----------

def _non_ascii(s: str) -> bool:
    return any(ord(c) > 127 for c in s)


def _header(m: MailMessage, name: str) -> str | None:
    v = m.headers.get(name.lower())
    return v[0].strip() if v else None


def _fmt_addr(v) -> str:
    name = (v.name or "").strip()
    return f"{name} <{v.email}>" if name else v.email


def _html_to_text(html: str | None) -> str:
    """HTML だけのメール向けの簡易テキスト化（タグ除去）。"""
    if not html:
        return ""
    import re
    from html import unescape

    s = re.sub(r"(?is)<(script|style).*?</\1>", "", html)
    s = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = unescape(s)
    return re.sub(r"\n{3,}", "\n\n", s).strip()
