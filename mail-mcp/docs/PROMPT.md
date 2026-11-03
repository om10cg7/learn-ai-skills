# Claude Code への引き継ぎプロンプト

別 PC で ZIP を展開し、そのフォルダで Claude Code を起動して、以下をそのまま貼り付ける。
（`CLAUDE.md` はリポジトリ直下にあるので自動で読まれる）

---

## 初回プロンプト（Phase 2〜4 を進める）

```
このリポジトリは、IMAP 対応のメール MCP サーバー「mail-mcp」v0.2 です。
別の環境で設計・実装・テスト（単体 17 件、Dovecot 統合 3 件、stdio E2E）まで完了した状態で引き継いでいます。

まず次を読んで、設計の経緯・決定事項・注意点を把握してください。
- CLAUDE.md（実装ルール。必ず守ること）
- docs/HANDOVER.md（仕様 v1 の決定事項、ツール仕様、指摘事項、ロードマップ）
- README.md（セットアップと登録手順）

把握できたら、docs/HANDOVER.md の「7. ロードマップ」の 2 から順に進めてください。

【環境】
- Windows 11、PowerShell、Docker Desktop（WSL2）
- このリポジトリは C:\dev\mail-mcp に置いてある

【進め方】
1. まず `pytest` を実行して、単体テスト 17 件が通ることを確認
2. `docker compose build` を実行。失敗したらエラーを見て Dockerfile を直す（uv + python:3.12-slim 構成）
3. `docker compose up -d greenmail` → `python scripts\seed_greenmail.py` → `pytest -m integration` → `scripts\e2e_check.py` で GreenMail に対する動作確認
4. config\accounts.yaml を作るよう私に促し、さくらの VPS のアカウントを設定したら
   `docker compose run --rm mail-mcp check` が OK になるまで接続を確認
   （証明書エラー・フォルダ判別エラーが出た場合の対処は HANDOVER.md 5 章）
5. Claude Desktop の設定（README の JSON）を %APPDATA%\Claude\claude_desktop_config.json に追加
6. Gmail（アプリパスワード）を追加して横断検索を確認
7. Gemini CLI / Antigravity CLI に登録

【絶対に守ること】
- 送信機能（SMTP）は作らない。要望があっても私に確認する
- delete_email は常にゴミ箱移動。完全削除にしない
- print() 禁止。ログは stderr
- .env、config/accounts.yaml、tokens/ を絶対にコミットしない
- MCP Python SDK は 2.x（MCPServer）。FastMCP に書き換えない

各ステップが終わるごとに、何を確認して何が OK だったかを短く報告してください。
私の操作（パスワード入力、設定ファイル記入、Claude Desktop 再起動など）が必要なところで止めて、
具体的に何をすればいいかを指示してください。
```

---

## Phase 5 プロンプト（outlook.com の OAuth2 検証、Phase 2〜4 が終わってから）

```
Phase 2〜4 が完了しました。次は outlook.com の OAuth2 接続を検証します。
OAuth2 のコードは src/mail_mcp/auth.py に実装済みですが、実アカウントでのログインは未検証です。

1. README の「OAuth2 の初回ログイン」の Entra ID 手順を、私が画面で迷わないように一つずつ案内してください
2. config/accounts.yaml に outlook アカウント（auth: oauth2, oauth2_provider: microsoft）を追加
3. `docker compose run --rm mail-mcp auth outlook` を実行し、表示された URL とコードでログイン
4. `docker compose run --rm mail-mcp check` で OK を確認
5. エラーが出たら、MSAL のエラー内容を読んで auth.py または Entra ID の設定を修正

成功したら、Gmail も同じ手順で OAuth2（oauth2_provider: google）に切り替えてください。
```

---

## トラブル時の追加プロンプト例

```
`docker compose run --rm mail-mcp check` で次のエラーが出ました。原因と直し方を教えてください。
（エラーをここに貼る）
```

```
Claude Desktop のツール一覧に mail が出ません。
%APPDATA%\Claude\logs\mcp-server-mail.log を確認して原因を特定してください。
```
