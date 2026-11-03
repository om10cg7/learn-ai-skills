from datetime import datetime

from mail_mcp.drafts import DraftSpec, OriginalMail, apply_signature, build_message, build_reply_spec, reply_subject


def _orig(**kw):
    base = dict(
        subject="打ち合わせ日程のご相談",
        from_="山田 太郎 <yamada@example.jp>",
        to=("田中 一郎 <ichiro@example.jp>",),
        cc=("鈴木 <suzuki@example.jp>",),
        reply_to=(),
        date=datetime(2026, 10, 28, 14, 3),
        message_id="<abc@example.jp>",
        references=None,
        text="来週の打ち合わせですが\n火曜か水曜はいかがでしょうか。",
    )
    base.update(kw)
    return OriginalMail(**base)


def test_reply_subject():
    assert reply_subject("件名") == "Re: 件名"
    assert reply_subject("Re: 件名") == "Re: 件名"
    assert reply_subject("RE: 件名") == "RE: 件名"


def test_signature():
    assert apply_signature("本文", "署名") == "本文\n\n-- \n署名\n"
    assert apply_signature("本文\n", "") == "本文\n"


def test_reply_spec_threading_and_quote():
    spec = build_reply_spec(_orig(), from_name="田中", from_email="ichiro@example.jp", body="水曜でお願いします。")
    assert spec.to == ["山田 太郎 <yamada@example.jp>"]
    assert spec.cc == []
    assert spec.in_reply_to == "<abc@example.jp>"
    assert spec.references == "<abc@example.jp>"
    assert "2026/10/28 14:03、山田 太郎 <yamada@example.jp> wrote:" in spec.body
    assert "> 来週の打ち合わせですが" in spec.body
    assert spec.body.startswith("水曜でお願いします。")


def test_reply_all_excludes_self_and_dedups():
    spec = build_reply_spec(_orig(), from_name="田中", from_email="ichiro@example.jp", body="了解", reply_all=True)
    assert spec.cc == ["鈴木 <suzuki@example.jp>"]


def test_reply_to_header_wins():
    spec = build_reply_spec(_orig(reply_to=("desk@example.jp",)), from_name="田中", from_email="ichiro@example.jp", body="了解")
    assert spec.to == ["desk@example.jp"]


def test_references_chain():
    spec = build_reply_spec(_orig(references="<r1@x> <r2@x>"), from_name="田中", from_email="ichiro@example.jp", body="了解")
    assert spec.references == "<r1@x> <r2@x> <abc@example.jp>"


def test_build_message_japanese_roundtrip():
    spec = DraftSpec(from_name="田中 一郎", from_email="ichiro@example.jp", to=["a@example.jp"], subject="テスト件名", body="本文です", signature="署名")
    msg = build_message(spec)
    raw = msg.as_bytes()
    assert b"Subject: =?utf-8?" in raw
    assert msg["In-Reply-To"] is None
    assert msg.get_content() == "本文です\n\n-- \n署名\n"
