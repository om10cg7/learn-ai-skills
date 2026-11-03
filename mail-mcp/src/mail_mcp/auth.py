"""OAuth2（XOAUTH2）認証。

初回だけ対話ログインが必要（`mail-mcp auth <account>`）。取得したリフレッシュトークンを token_file に保存し、
以降サーバーはユーザーの操作なしでアクセストークンを更新する。

- microsoft: MSAL のデバイスコードフロー。ブラウザのないコンテナ内でも URL とコードを表示するだけで済む。
  Entra ID で「公開クライアント」のアプリ登録が必要（client_id のみ、シークレット不要）。
- google: ループバック方式。コンテナ内で一時 HTTP サーバーを立て、ユーザーが表示された URL をブラウザで開く。
  `docker compose run -p 8765:8765 ...` のようにポートを通す必要がある。Google Cloud で「デスクトップアプリ」の
  OAuth クライアント（client_id + client_secret）が必要。
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

from .config import AccountConfig

log = logging.getLogger(__name__)

MS_SCOPES = ["https://outlook.office.com/IMAP.AccessAsUser.All"]  # offline_access は MSAL が自動付与
MS_AUTHORITY = "https://login.microsoftonline.com/consumers"  # 個人アカウント。職場アカウントなら common / テナントID
GOOGLE_SCOPES = ["https://mail.google.com/"]
GOOGLE_LOOPBACK_PORT = int(os.environ.get("MAIL_MCP_OAUTH_PORT", "8765"))


def _say(msg: str) -> None:
    """対話ログイン時のユーザー向け表示。stdio サーバーの通信を汚さないよう stderr へ。"""
    print(msg, file=sys.stderr, flush=True)


def token_path(cfg: AccountConfig) -> Path:
    return Path(cfg.token_file or f"/tokens/{cfg.name}.json")


# ============================ Microsoft ============================

def _msal_app(cfg: AccountConfig):
    import msal

    cache = msal.SerializableTokenCache()
    p = token_path(cfg)
    if p.exists():
        cache.deserialize(p.read_text(encoding="utf-8"))
    app = msal.PublicClientApplication(cfg.oauth2_client_id, authority=cfg.oauth2_authority or MS_AUTHORITY, token_cache=cache)
    return app, cache


def _msal_save(cfg: AccountConfig, cache) -> None:
    if cache.has_state_changed:
        p = token_path(cfg)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(cache.serialize(), encoding="utf-8")
        os.chmod(p, 0o600)


def microsoft_login(cfg: AccountConfig) -> None:
    app, cache = _msal_app(cfg)
    flow = app.initiate_device_flow(scopes=MS_SCOPES)
    if "user_code" not in flow:
        raise RuntimeError(f"デバイスコードフローを開始できません: {flow.get('error_description', flow)}")
    _say("\n" + flow["message"] + "\n")  # 「https://microsoft.com/devicelogin を開いてコード XXXX を入力」
    result = app.acquire_token_by_device_flow(flow)
    if "access_token" not in result:
        raise RuntimeError(f"認証失敗: {result.get('error_description', result)}")
    _msal_save(cfg, cache)
    _say(f"[{cfg.name}] ログイン成功。トークンを {token_path(cfg)} に保存しました。")


def microsoft_access_token(cfg: AccountConfig) -> str:
    app, cache = _msal_app(cfg)
    accounts = app.get_accounts()
    if not accounts:
        raise RuntimeError(f"[{cfg.name}] 未ログインです。`mail-mcp auth {cfg.name}` を実行してください")
    result = app.acquire_token_silent(MS_SCOPES, account=accounts[0])
    if not result or "access_token" not in result:
        raise RuntimeError(f"[{cfg.name}] トークン更新に失敗。`mail-mcp auth {cfg.name}` で再ログインしてください")
    _msal_save(cfg, cache)
    return result["access_token"]


# ============================ Google ============================

def _google_client_config(cfg: AccountConfig) -> dict:
    secret = os.environ.get(cfg.oauth2_client_secret_env or "", "")
    if not secret:
        raise ValueError(f"[{cfg.name}] oauth2_client_secret_env の環境変数が空です")
    return {
        "installed": {
            "client_id": cfg.oauth2_client_id,
            "client_secret": secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }


def google_login(cfg: AccountConfig) -> None:
    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_config(_google_client_config(cfg), scopes=GOOGLE_SCOPES)
    _say(f"\nブラウザで表示される URL を開いてください（コンテナのポート {GOOGLE_LOOPBACK_PORT} を公開していること）。\n")
    creds = flow.run_local_server(
        host="localhost", bind_addr="0.0.0.0", port=GOOGLE_LOOPBACK_PORT, open_browser=False,
        authorization_prompt_message="▶ この URL を開く: {url}",
        success_message="認証完了。このウィンドウは閉じて構いません。",
    )
    p = token_path(cfg)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(creds.to_json(), encoding="utf-8")
    os.chmod(p, 0o600)
    _say(f"[{cfg.name}] ログイン成功。トークンを {p} に保存しました。")


def google_access_token(cfg: AccountConfig) -> str:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    p = token_path(cfg)
    if not p.exists():
        raise RuntimeError(f"[{cfg.name}] 未ログインです。`mail-mcp auth {cfg.name}` を実行してください")
    creds = Credentials.from_authorized_user_info(json.loads(p.read_text(encoding="utf-8")), GOOGLE_SCOPES)
    if not creds.valid:
        if not creds.refresh_token:
            raise RuntimeError(f"[{cfg.name}] リフレッシュトークンがありません。`mail-mcp auth {cfg.name}` で再ログインしてください")
        creds.refresh(Request())
        p.write_text(creds.to_json(), encoding="utf-8")
    return creds.token


# ============================ 共通 ============================

PROVIDERS = {
    "microsoft": (microsoft_login, microsoft_access_token),
    "google": (google_login, google_access_token),
}


def interactive_login(cfg: AccountConfig) -> None:
    if cfg.auth != "oauth2":
        raise ValueError(f"[{cfg.name}] auth が oauth2 ではありません")
    PROVIDERS[cfg.oauth2_provider][0](cfg)


def access_token(cfg: AccountConfig) -> str:
    return PROVIDERS[cfg.oauth2_provider][1](cfg)
