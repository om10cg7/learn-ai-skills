"""OAuth2 まわりの単体テスト（実アカウント不要。外部通信はモック）。"""
import json
from unittest.mock import MagicMock, patch

import pytest

from mail_mcp import auth
from mail_mcp.config import AccountConfig
from mail_mcp.imap_client import MailAccount


def _ms(tmp_path):
    return AccountConfig(name="ms", display_name="x", email="a@outlook.com", imap_host="outlook.office365.com",
                         username="a@outlook.com", auth="oauth2", oauth2_provider="microsoft",
                         oauth2_client_id="cid", token_file=str(tmp_path / "ms.json"))


def _g(tmp_path, monkeypatch):
    monkeypatch.setenv("GSEC", "secret")
    return AccountConfig(name="g", display_name="x", email="a@gmail.com", imap_host="imap.gmail.com",
                         username="a@gmail.com", auth="oauth2", oauth2_provider="google",
                         oauth2_client_id="cid", oauth2_client_secret_env="GSEC", token_file=str(tmp_path / "g.json"))


def test_config_validation():
    with pytest.raises(ValueError):
        AccountConfig(name="a", display_name="x", email="a@b", imap_host="h", username="u", auth="oauth2")
    with pytest.raises(ValueError):
        AccountConfig(name="a", display_name="x", email="a@b", imap_host="h", username="u")  # password_env なし
    with pytest.raises(ValueError):
        AccountConfig(name="a", display_name="x", email="a@b", imap_host="h", username="u",
                      auth="oauth2", oauth2_provider="google", oauth2_client_id="c")  # secret なし


def test_microsoft_not_logged_in(tmp_path):
    app = MagicMock()
    app.get_accounts.return_value = []
    with patch.object(auth, "_msal_app", return_value=(app, MagicMock())):
        with pytest.raises(RuntimeError, match="未ログイン"):
            auth.microsoft_access_token(_ms(tmp_path))


def test_microsoft_silent_refresh_and_cache_save(tmp_path):
    cfg = _ms(tmp_path)
    app = MagicMock()
    app.get_accounts.return_value = [{"username": "a@outlook.com"}]
    app.acquire_token_silent.return_value = {"access_token": "TOK"}
    cache = MagicMock(has_state_changed=True)
    cache.serialize.return_value = '{"cache": 1}'
    with patch.object(auth, "_msal_app", return_value=(app, cache)):
        assert auth.microsoft_access_token(cfg) == "TOK"
    assert json.loads((tmp_path / "ms.json").read_text()) == {"cache": 1}
    app.acquire_token_silent.assert_called_once_with(auth.MS_SCOPES, account={"username": "a@outlook.com"})


def test_google_refresh_when_expired(tmp_path, monkeypatch):
    cfg = _g(tmp_path, monkeypatch)
    (tmp_path / "g.json").write_text(json.dumps({"token": "old", "refresh_token": "r", "client_id": "cid",
                                                 "client_secret": "secret", "token_uri": "https://oauth2.googleapis.com/token"}))
    creds = MagicMock(valid=False, refresh_token="r", token="NEW")
    creds.to_json.return_value = '{"token": "NEW"}'
    with patch("google.oauth2.credentials.Credentials.from_authorized_user_info", return_value=creds):
        assert auth.google_access_token(cfg) == "NEW"
    creds.refresh.assert_called_once()
    assert json.loads((tmp_path / "g.json").read_text())["token"] == "NEW"


def test_connect_uses_xoauth2(tmp_path):
    cfg = _ms(tmp_path)
    with patch.object(auth, "access_token", return_value="TOK"), patch("mail_mcp.imap_client.MailBox") as MB:
        with MailAccount(cfg).connect() as mb:
            pass
    MB.return_value.xoauth2.assert_called_once_with("a@outlook.com", "TOK", initial_folder="INBOX")
    MB.return_value.login.assert_not_called()
