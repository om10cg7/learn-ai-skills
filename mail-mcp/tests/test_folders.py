from mail_mcp.folders import Folder, find_special_folder

F = lambda n, d="/", *fl: Folder(n, d, tuple(fl))  # noqa: E731


def test_override_wins():
    assert find_special_folder("drafts", [F("Drafts", "/", "\\Drafts")], override="MyDrafts") == "MyDrafts"


def test_special_use_flag():
    folders = [F("INBOX"), F("[Gmail]/下書き", "/", "\\HasNoChildren", "\\Drafts"), F("[Gmail]/ゴミ箱", "/", "\\Trash")]
    assert find_special_folder("drafts", folders) == "[Gmail]/下書き"
    assert find_special_folder("trash", folders) == "[Gmail]/ゴミ箱"


def test_common_name_dovecot_dot_delim():
    folders = [F("INBOX", "."), F("INBOX.Drafts", "."), F("INBOX.Trash", ".")]
    assert find_special_folder("drafts", folders) == "INBOX.Drafts"
    assert find_special_folder("trash", folders) == "INBOX.Trash"


def test_japanese_name():
    assert find_special_folder("trash", [F("削除済みアイテム")]) == "削除済みアイテム"


def test_not_found():
    assert find_special_folder("drafts", [F("INBOX")]) is None
