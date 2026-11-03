"""実 IMAP サーバー（GreenMail / Dovecot）に対する統合テスト。`pytest -m integration`。
既定は GreenMail（localhost:3993, test/test）。環境変数 IMAP_TEST_HOST / IMAP_TEST_PORT / IMAP_TEST_USER /
IMAP_TEST_PASSWORD / IMAP_TEST_DRAFTS / IMAP_TEST_TRASH で変更可。接続できない環境では自動スキップ。"""
import os
import socket

import pytest

from mail_mcp.config import AccountConfig
from mail_mcp.drafts import DraftSpec
from mail_mcp.imap_client import MailAccount

HOST = os.environ.get("IMAP_TEST_HOST", os.environ.get("GREENMAIL_HOST", "localhost"))
PORT = int(os.environ.get("IMAP_TEST_PORT", "3993"))
USER = os.environ.get("IMAP_TEST_USER", "test")
DRAFTS = os.environ.get("IMAP_TEST_DRAFTS", "Drafts")   # SPECIAL-USE 対応サーバーなら空文字で自動判別
TRASH = os.environ.get("IMAP_TEST_TRASH", "Trash")
pytestmark = pytest.mark.integration


def _reachable() -> bool:
    try:
        with socket.create_connection((HOST, PORT), timeout=1):
            return True
    except OSError:
        return False


@pytest.fixture
def acc(monkeypatch):
    if not _reachable():
        pytest.skip(f"IMAP テストサーバー({HOST}:{PORT}) に接続できません")
    monkeypatch.setenv("IMAP_TEST_PASSWORD", os.environ.get("IMAP_TEST_PASSWORD", "test"))
    cfg = AccountConfig(
        name="test", display_name="テスト太郎", email="test@localhost",
        imap_host=HOST, imap_port=PORT, username=USER, password_env="IMAP_TEST_PASSWORD",
        signature="テスト太郎", ssl_verify=False,
        folders={"drafts": DRAFTS or None, "trash": TRASH or None},  # GreenMail は SPECIAL-USE 非対応なので名前指定
    )
    return MailAccount(cfg)


def test_search_and_get(acc):
    with acc.connect() as mb:
        for f in (DRAFTS, TRASH):
            if f and f not in [x.name for x in acc.list_folders(mb)]:
                mb.folder.create(f)
        rows = acc.search(mb, unread_only=False, days=None, limit=5)
        assert rows, "seed_greenmail.py でメールを投入してください"
        d = acc.detail(acc.fetch_one(mb, "INBOX", rows[0]["uid"]), "INBOX", 8000)
        assert d["subject"] and d["message_id"]


def test_reply_draft_roundtrip(acc):
    from mail_mcp.drafts import build_reply_spec

    with acc.connect() as mb:
        m = acc.fetch_one(mb, "INBOX", acc.search(mb, unread_only=False, days=None, limit=1)[0]["uid"])
        spec = build_reply_spec(acc.to_original(m), from_name="テスト太郎", from_email="test@localhost", body="了解しました。", signature="テスト太郎")
        r = acc.save_draft(mb, spec)
        assert r["subject"].startswith("Re:")
        drafts = acc.list_drafts(mb, 10)
        assert any(x["subject"] == r["subject"] for x in drafts)
        acc.delete_draft(mb, drafts[0]["uid"])


def test_trash_moves_not_deletes(acc):
    with acc.connect() as mb:
        acc.save_draft(mb, DraftSpec(from_name="t", from_email="test@localhost", to=["a@localhost"], subject="移動テスト", body="x"))
        uid = acc.list_drafts(mb, 1)[0]["uid"]
        acc.trash(mb, acc.special_folder(mb, "drafts"), [uid])
        mb.folder.set(acc.special_folder(mb, "trash"))
        assert any(x.subject == "移動テスト" for x in mb.fetch("ALL", headers_only=True))
