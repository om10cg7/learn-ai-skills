"""設定の読み込み。

- アカウント定義は accounts.yaml（パスは環境変数 MAIL_MCP_CONFIG、既定 /config/accounts.yaml）
- パスワード本体は YAML に書かず、password_env で指定した環境変数から読む
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator


class FolderOverride(BaseModel):
    """SPECIAL-USE で自動判別できないサーバー向けの手動指定。null なら自動判別。"""

    drafts: str | None = None
    trash: str | None = None


class AccountConfig(BaseModel):
    name: str = Field(description="ツール呼び出しで使う短い識別子（例: sakura, gmail, outlook）")
    display_name: str = Field(description="From に使う表示名")
    email: str
    imap_host: str
    imap_port: int = 993
    username: str
    auth: Literal["password", "oauth2"] = "password"
    password_env: str | None = Field(default=None, description="パスワードを格納した環境変数名（auth=password）")
    # --- auth=oauth2 のとき ---
    oauth2_provider: Literal["microsoft", "google"] | None = None
    oauth2_client_id: str | None = None
    oauth2_client_secret_env: str | None = Field(default=None, description="google のみ。シークレットを格納した環境変数名")
    oauth2_authority: str | None = Field(default=None, description="microsoft のみ。既定は個人アカウント用 consumers")
    token_file: str | None = Field(default=None, description="既定 /tokens/<name>.json")
    signature: str = Field(default="", description="下書き末尾に自動付与する署名（空なら付けない）")
    folders: FolderOverride = Field(default_factory=FolderOverride)
    ssl_ca_file: str | None = Field(default=None, description="自己署名証明書を信頼する場合の CA ファイルパス")
    ssl_verify: bool = Field(default=True, description="False で証明書検証を無効化（ローカルの GreenMail 専用。本番では使わない）")
    timeout: int = 30

    @field_validator("name")
    @classmethod
    def _name_is_simple(cls, v: str) -> str:
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("name は英数字・ハイフン・アンダースコアのみ")
        return v

    @model_validator(mode="after")
    def _oauth2_fields(self):
        if self.auth == "oauth2":
            if not self.oauth2_provider or not self.oauth2_client_id:
                raise ValueError(f"[{self.name}] auth=oauth2 には oauth2_provider と oauth2_client_id が必要です")
            if self.oauth2_provider == "google" and not self.oauth2_client_secret_env:
                raise ValueError(f"[{self.name}] google の OAuth2 には oauth2_client_secret_env が必要です")
        elif not self.password_env:
            raise ValueError(f"[{self.name}] auth=password には password_env が必要です")
        return self

    def password(self) -> str:
        if self.auth != "password":
            raise ValueError(f"[{self.name}] auth={self.auth} ではパスワードは使いません")
        if not self.password_env:
            raise ValueError(f"[{self.name}] password_env が設定されていません")
        value = os.environ.get(self.password_env)
        if not value:
            raise ValueError(f"[{self.name}] 環境変数 {self.password_env} が空です（.env を確認）")
        return value


class Settings(BaseModel):
    accounts: list[AccountConfig]
    default_days: int = Field(default=7, description="search_emails の既定の遡り日数")
    default_unread_only: bool = True
    default_limit: int = Field(default=20, description="1 回の検索で返す最大件数")
    body_max_chars: int = Field(default=8000, description="get_email で返す本文の上限文字数")

    @field_validator("accounts")
    @classmethod
    def _unique_names(cls, v: list[AccountConfig]) -> list[AccountConfig]:
        names = [a.name for a in v]
        if len(names) != len(set(names)):
            raise ValueError("accounts の name が重複しています")
        if not v:
            raise ValueError("accounts が 1 件もありません")
        return v

    def get_account(self, name: str) -> AccountConfig:
        for a in self.accounts:
            if a.name == name:
                return a
        raise KeyError(f"アカウント '{name}' は存在しません。有効: {[a.name for a in self.accounts]}")


def load_settings(path: str | os.PathLike | None = None) -> Settings:
    p = Path(path or os.environ.get("MAIL_MCP_CONFIG", "/config/accounts.yaml"))
    if not p.exists():
        raise FileNotFoundError(f"設定ファイルが見つかりません: {p}")
    with p.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return Settings.model_validate(data)
