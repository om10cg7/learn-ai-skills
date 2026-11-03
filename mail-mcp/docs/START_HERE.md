# はじめに読むファイル

| ファイル | 内容 |
|---|---|
| `docs/PROMPT.md` | **Claude Code に貼るプロンプト**（初回・Phase 5・トラブル時） |
| `CLAUDE.md` | Claude Code が自動で読む実装ルール |
| `docs/HANDOVER.md` | 仕様 v1 の決定事項、ツール仕様、指摘事項・注意点、ロードマップ |
| `README.md` | セットアップ、Claude Desktop / Claude Code / Gemini CLI の登録手順、OAuth2 手順 |

## 手順

1. この ZIP を `C:\dev\mail-mcp` に展開
2. `copy .env.example .env`、`copy config\accounts.example.yaml config\accounts.yaml`
3. `C:\dev\mail-mcp` で Claude Code を起動し、`docs/PROMPT.md` の「初回プロンプト」を貼る
4. Claude Code の指示に従って、パスワード記入・Claude Desktop 再起動などを行う

## 現在の状態（2026-11-02 時点、v0.2）

- 実装済み: 読み取り・下書き・整理の 11 ツール、3 アカウント横断、OAuth2（Microsoft / Google）、CLI（auth / check）
- 検証済み: 単体 17 件、Dovecot 2.3.21 統合 3 件、stdio 経由 E2E
- 未検証: Docker ビルド、さくら VPS・Gmail・outlook.com の実接続、Claude Desktop / Gemini CLI 登録
