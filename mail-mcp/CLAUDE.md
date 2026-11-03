# CLAUDE.md — mail-mcp 実装ルール

## このリポジトリは何か
IMAP 対応メール MCP サーバー（読み取り・下書き・整理）。**送信機能は作らない**。
設計の経緯・決定事項・注意点は `docs/HANDOVER.md` を必ず先に読むこと。

## 絶対に守ること
- 送信ツール（SMTP）を追加しない。要望があってもまず `docs/HANDOVER.md` の「保留」を確認し、ユーザーに確認する
- `delete_email` は常にゴミ箱移動。`mb.delete()` を受信メールに使わない（下書き削除のみ可）
- stdio 通信を壊すので `print()` 禁止。ログは `logging`（stderr）
- 認証情報を YAML・コード・テストに直書きしない。`.env` → `password_env` 経由のみ
- `.env` と `config/accounts.yaml` をコミットしない
- MCP Python SDK は **2.x**（`from mcp.server.mcpserver import MCPServer`）。`FastMCP` は使わない

## 構成
- `src/mail_mcp/server.py`   ツール定義のみ。ロジックは書かない
- `src/mail_mcp/imap_client.py` IMAP 操作（1 アカウント分、接続は呼び出しごと）
- `src/mail_mcp/drafts.py`   MIME 組み立て。純粋関数にして `tests/test_drafts.py` でテスト
- `src/mail_mcp/folders.py`  特殊フォルダ判別。純粋関数
- `src/mail_mcp/config.py`   設定スキーマ（pydantic）
- `src/mail_mcp/auth.py`     OAuth2（msal / google-auth）。外部通信は必ずモックしてテスト

## 開発の流れ
1. `docker compose up -d greenmail` → `python scripts/seed_greenmail.py`
2. 変更 → `pytest`（単体）→ `pytest -m integration`（GreenMail 接続テスト）
3. `docker compose build` → MCP Inspector で手動確認 → Claude Desktop で確認

## 次フェーズの着手順（docs/HANDOVER.md のロードマップ）
Phase 2: さくら VPS 実接続 → Phase 3: Gmail 追加・横断検索確認 → Phase 4: Gemini CLI → Phase 5: OAuth2 実アカウント検証（コードは実装済み）
