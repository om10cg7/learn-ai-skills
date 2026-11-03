# mail-mcp

IMAP 対応のメール MCP サーバー。**読み取り・下書き作成・整理**を行い、**送信機能は持たない**（下書きの送信はメールソフトで手動）。
Claude Desktop / Claude Code / Gemini CLI（Antigravity CLI）から stdio で利用。

## ツール一覧

| 分類 | ツール | 内容 |
|---|---|---|
| 読み取り | `list_accounts` | アカウント一覧 |
| | `list_folders` | フォルダ一覧（下書き・ゴミ箱の判別結果付き） |
| | `search_emails` | 検索。`account` 省略で全アカウント横断。既定は未読・直近 7 日 |
| | `get_email` | 本文・ヘッダ・添付一覧（既読にしない） |
| 下書き | `create_reply_draft` | 返信下書き（Re:・引用・署名・スレッド情報を自動付与） |
| | `create_draft` | 新規下書き |
| | `list_drafts` / `delete_draft` | 下書きの一覧・削除 |
| 整理 | `mark_as_read` | 既読／未読 |
| | `move_email` | フォルダ移動 |
| | `delete_email` | **ゴミ箱へ移動のみ**（完全削除なし） |

## セットアップ（Windows 11）

前提: Docker Desktop（WSL2 バックエンド）、Git。

```powershell
git clone <このリポジトリ> C:\dev\mail-mcp
cd C:\dev\mail-mcp
copy .env.example .env                              # パスワードを記入
copy config\accounts.example.yaml config\accounts.yaml   # アカウント情報を記入
docker compose build
docker compose run --rm mail-mcp check      # 全アカウントの接続・フォルダ判別を確認
```

`check` が全て `OK` になってから各クライアントに登録する。

### Claude Desktop に登録

`%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mail": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm", "-e", "TZ=Asia/Tokyo",
        "--env-file", "C:\\dev\\mail-mcp\\.env",
        "-v", "C:\\dev\\mail-mcp\\config:/config:ro",
        "-v", "C:\\dev\\mail-mcp\\tokens:/tokens",
        "mail-mcp:latest"
      ]
    }
  }
}
```

Claude Desktop を再起動すると、ツール一覧に `mail` が出る。

### Claude Code に登録

```powershell
claude mcp add mail -- docker run -i --rm -e TZ=Asia/Tokyo --env-file C:\dev\mail-mcp\.env -v C:\dev\mail-mcp\config:/config:ro -v C:\dev\mail-mcp\tokens:/tokens mail-mcp:latest
```

### Gemini CLI / Antigravity CLI に登録

```powershell
gemini mcp add mail docker -- run -i --rm -e TZ=Asia/Tokyo --env-file C:\dev\mail-mcp\.env -v C:\dev\mail-mcp\config:/config:ro -v C:\dev\mail-mcp\tokens:/tokens mail-mcp:latest
```

または `~\.gemini\settings.json` に:

```json
{
  "mcpServers": {
    "mail": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "TZ=Asia/Tokyo", "--env-file", "C:\\dev\\mail-mcp\\.env",
               "-v", "C:\\dev\\mail-mcp\\config:/config:ro", "-v", "C:\\dev\\mail-mcp\\tokens:/tokens", "mail-mcp:latest"]
    }
  }
}
```

（Antigravity CLI は設定ファイルの場所が異なる場合があるため、公式ドキュメントで確認）

## ローカルテスト（本物のアカウント不要）

```powershell
docker compose up -d greenmail                 # テスト用メールサーバー
python scripts\seed_greenmail.py               # テストメール 3 通を投入
copy config\accounts.greenmail.yaml config\accounts.yaml
docker compose run --rm mail-mcp               # 起動確認（Ctrl+C で終了）
```

MCP Inspector で対話的に試す:

```powershell
npx @modelcontextprotocol/inspector docker run -i --rm --env-file .env -v ${PWD}\config:/config:ro --network mail-mcp_default mail-mcp:latest
```

> GreenMail に Docker 内から接続する場合、`imap_host: greenmail` のまま `--network mail-mcp_default` を付ける。
> PC 側（Docker 外）の Python から接続する場合は `localhost` に変える。

## テスト

```powershell
uv venv; .venv\Scripts\activate
uv pip install -e ".[dev]"
pytest                    # 単体テスト
pytest -m integration     # GreenMail 接続テスト（起動していなければスキップ）
$env:MAIL_MCP_CONFIG="config\accounts.yaml"; python scripts\e2e_check.py   # 全ツールを stdio 経由で実行
```

`e2e_check.py` は先頭のメール 1 通を既読にしてゴミ箱へ移動するので、**テスト用アカウントで**実行する。

## アカウント別の注意

| アカウント | 認証 | 備考 |
|---|---|---|
| さくらの VPS | パスワード | 993 番をパケットフィルタと FW で許可。自己署名証明書なら `ssl_ca_file` に CA を指定 |
| Gmail | アプリパスワード | 2 段階認証を有効にして発行。Phase 6 で OAuth2 へ |
| outlook.com | OAuth2 | 下記「OAuth2 の初回ログイン」参照 |

## OAuth2 の初回ログイン（outlook.com、Gmail を OAuth2 にする場合）

一度ログインすればトークンが `tokens/<account>.json` に保存され、以後は自動更新される。

**outlook.com（Microsoft）**
1. [Entra 管理センター](https://entra.microsoft.com) → アプリの登録 → 新規登録。サポートされるアカウントの種類は「個人用 Microsoft アカウントのみ」、リダイレクト URI は空のまま
2. 「認証」→「パブリック クライアント フローを許可する」を **はい**
3. 「API のアクセス許可」→ Microsoft Graph ではなく **Office 365 Exchange Online** → 委任 → `IMAP.AccessAsUser.All` を追加
4. アプリケーション (クライアント) ID を `accounts.yaml` の `oauth2_client_id` に設定
5. `docker compose run --rm mail-mcp auth outlook` → 表示された URL をブラウザで開き、コードを入力してログイン

**Gmail（Google）**
1. [Google Cloud Console](https://console.cloud.google.com) → API とサービス → 認証情報 → OAuth クライアント ID → 種類「デスクトップ アプリ」
2. OAuth 同意画面でテストユーザーに自分の Gmail を追加（公開しない限り「テスト」のままでよい）
3. クライアント ID を `oauth2_client_id`、シークレットを `.env` の `GMAIL_OAUTH_CLIENT_SECRET` に設定
4. `docker compose run --rm -p 8765:8765 mail-mcp auth gmail` → 表示された URL をブラウザで開いてログイン（ブラウザが `localhost:8765` に戻ってきて完了）

## 設計上の安全策

- 送信ツールは存在しない（SMTP 未使用）
- 削除はゴミ箱移動のみ
- 受信メール内の指示に従わないよう、サーバーの `instructions` で AI に明示
- 認証情報は `.env` と `config/accounts.yaml` に分離し、どちらも Git 管理外
- stdio 通信を壊さないよう、ログは stderr のみ

## ロードマップ

1. ✅ 受信・下書き・整理（本リポジトリ v0.1）
2. さくら VPS → Gmail の順に実アカウント接続
3. Gemini CLI / Antigravity CLI 接続
4. OAuth2 対応（outlook.com、Gmail）
5. （保留）添付ファイル本文の取得、HTML 下書き、送信機能、Streamable HTTP 化
