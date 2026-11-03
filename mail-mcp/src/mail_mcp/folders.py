"""特殊フォルダ（下書き・ゴミ箱・送信済み）の判別。

優先順位:
  1. accounts.yaml の folders.* で明示指定されたもの
  2. IMAP SPECIAL-USE 属性（RFC 6154: \\Drafts, \\Trash, \\Sent）
  3. よくあるフォルダ名との一致（Gmail の [Gmail]/下書き、Dovecot の INBOX.Drafts など）
"""

from __future__ import annotations

from dataclasses import dataclass

# 小文字で比較する。区切り文字（/ や .）は末尾要素だけ見る。
COMMON_NAMES: dict[str, tuple[str, ...]] = {
    "drafts": ("drafts", "draft", "下書き", "[gmail]/drafts", "[gmail]/下書き", "inbox.drafts"),
    "trash": ("trash", "deleted", "deleted items", "deleted messages", "ゴミ箱", "削除済みアイテム",
              "[gmail]/trash", "[gmail]/ゴミ箱", "inbox.trash"),
    "sent": ("sent", "sent items", "sent messages", "送信済み", "送信済みアイテム",
             "[gmail]/sent mail", "[gmail]/送信済みメール", "inbox.sent"),
}

SPECIAL_USE_FLAG: dict[str, str] = {
    "drafts": "\\drafts",
    "trash": "\\trash",
    "sent": "\\sent",
}


@dataclass(frozen=True)
class Folder:
    name: str
    delim: str
    flags: tuple[str, ...]


def find_special_folder(kind: str, folders: list[Folder], override: str | None = None) -> str | None:
    """kind は 'drafts' | 'trash' | 'sent'。見つからなければ None。"""
    if override:
        return override

    flag = SPECIAL_USE_FLAG[kind]
    for f in folders:
        if any(x.lower() == flag for x in f.flags):
            return f.name

    candidates = COMMON_NAMES[kind]
    for f in folders:
        full = f.name.lower()
        last = full.split(f.delim)[-1] if f.delim else full
        if full in candidates or last in candidates:
            return f.name
    return None
