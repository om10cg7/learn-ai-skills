# mail-mcp 引き継ぎ資料（仕様 v1 / 2026-10-28）

## 1. 目的
Claude の Gmail/Outlook 連携 MCP のように、**IMAP に対応した自前のメール MCP サーバー**を作る。
Claude（Desktop / Code）と Gemini（CLI / Antigravity CLI）の両方から同じサーバーを使う。

## 2. 決定事項（ユーザーとの質疑で確定）

| 項目 | 決定 | 理由・補足 |
|---|---|---|
| 接続アカウント | さくらの VPS、Gmail、outlook.com（個人） | 3 アカウント |
| 利用クライアント | Claude Desktop、Gemini CLI / Antigravity CLI | いずれも stdio。HTTP 化は不要 |
| サーバー稼働場所 | 使用する Windows 11 PC の Docker | `docker run -i` で stdio を中継 |
| 送信 | **なし（下書き作成のみ、送信は手動）** | 誤送信・プロンプトインジェクション対策。SMTP 不要 |
| 下書きの保存先 | サーバーの下書きフォルダ（IMAP APPEND） | メールソフトで開いて確認・編集・送信できる |
| 整理操作 | 既読／未読、フォルダ移動、削除 | 削除は**ゴミ箱移動のみ**、完全削除なし |
| 複数アカウント | 横断検索（`account` 省略で全件） | 1 アカウント失敗でも他は返す |
| 検索の既定範囲 | 未読・直近 7 日 | AI が読む量の上限。`accounts.yaml` で変更可 |
| 返信下書き | 引用あり・署名自動・テキスト形式のみ | 署名はアカウントごとに設定 |
| Gmail 認証 | まずアプリパスワード → 後で OAuth2 | OAuth2 の仕組みは outlook.com と共用 |
| outlook.com 認証 | OAuth2（Entra ID アプリ登録、デバイスコードフロー） | 基本認証は廃止済み。v0.2 で実装 |
| 添付ファイル | 一覧のみ（中身取得は保留） | |

## 3. 技術スタック
Python 3.12 / MCP Python SDK 2.x（`MCPServer`）/ imap-tools / pydantic / PyYAML / uv /
Docker Compose / GreenMail（テスト用メールサーバー）/ pytest / MCP Inspector

## 4. ツール仕様

| ツール | 引数 | 動作 |
|---|---|---|
| `list_accounts` | — | 設定済みアカウント一覧 |
| `list_folders` | account | フォルダ一覧。下書き・ゴミ箱の判別結果を `special` に表示 |
| `search_emails` | account?, folder, unread_only?, days?, from_address?, subject?, text?, limit? | ヘッダのみ取得、既読にしない。日本語検索は charset=UTF-8 |
| `get_email` | account, uid, folder, max_chars? | 本文（HTML のみなら簡易テキスト化）・添付一覧。既読にしない |
| `create_reply_draft` | account, uid, body, folder, reply_all, include_quote | Re:・引用・署名・In-Reply-To/References を自動付与し下書きフォルダへ保存 |
| `create_draft` | account, to[], subject, body, cc[] | 新規下書き |
| `list_drafts` | account?, limit | 下書き一覧 |
| `delete_draft` | account, uid | 下書きを削除（完全削除。下書きのみ許可） |
| `mark_as_read` | account, uids[], folder, read | フラグ操作 |
| `move_email` | account, uids[], destination, folder | フォルダ移動 |
| `delete_email` | account, uids[], folder | ゴミ箱へ移動 |

### 特殊フォルダの判別順
1. `accounts.yaml` の `folders.drafts` / `folders.trash`
2. IMAP SPECIAL-USE 属性（`\Drafts`, `\Trash`）
3. よくある名前（`Drafts`, `下書き`, `[Gmail]/下書き`, `INBOX.Drafts`, `削除済みアイテム` など）

### 返信下書きの仕様
- 宛先は Reply-To があればそれ、なければ From。`reply_all=true` で元 To/Cc を Cc に（自分と重複は除外）
- 件名: 既に Re:/RE:/返信: 等が付いていればそのまま、なければ `Re: ` を付与
- 本文: ユーザー本文 → 空行 → `YYYY/MM/DD HH:MM、名前 <addr> wrote:` → `> ` 引用 → `-- ` 署名
- `References` = 元 References + 元 Message-ID

## 5. 指摘事項・注意点（開発時に必ず確認）

### 安全
- 受信メール本文の指示（「転送して」「全員に返信して」等）に AI が従う危険がある。送信機能を持たないことが最大の対策。サーバーの `instructions` でも明示済み
- 将来 HTTP 化・外部公開する場合は**認証を付けてから**公開する（無認証公開は誰でもメールを読める）
- 認証情報はコード・YAML に書かず `.env`。`.env` と `accounts.yaml` は Git 管理外

### IMAP の制約
- 下書きの「編集」は IMAP にない。`update_draft` を作る場合は**新規保存 → 旧削除**の順（逆だと失敗時に消える）
- SMTP で送っても送信済みフォルダに入らないサーバーが多い（送信を作る場合は `\Sent` への APPEND が必要）
- 日本語は `email.message.EmailMessage` を使い UTF-8 で統一（旧 `MIMEText` は使わない）

### アカウント別
- **さくらの VPS**（自前の Postfix + Dovecot 想定）
  - 993 番をコントロールパネルのパケットフィルターと OS のファイアウォール両方で許可
  - Let's Encrypt の正式証明書を推奨。自己署名なら `ssl_ca_file` に CA を指定（`ssl_verify: false` は本番で使わない）
  - Dovecot の `special_use` 設定を確認（`doveconf -n | grep -A3 mailbox`）。無ければ `folders.*` で手動指定
- **Gmail**：2 段階認証を有効にしてアプリパスワードを発行。フォルダは `[Gmail]/下書き`、`[Gmail]/ゴミ箱`（SPECIAL-USE で自動判別される）
- **outlook.com**：基本認証廃止のため OAuth2 必須。Entra ID のアプリ登録は「個人用 Microsoft アカウントのみ」「パブリック クライアント フロー許可」「Office 365 Exchange Online の IMAP.AccessAsUser.All」。authority は `consumers`（職場アカウントなら `oauth2_authority` で変更）
- **OAuth2 共通**：トークンファイルはパスワード同等の機密。`tokens/` は Git 管理外、ファイル権限 600。Gmail 側は OAuth 同意画面が「テスト」状態だとリフレッシュトークンが 7 日で失効する仕様があるため、長期運用するなら同意画面を「本番」にする

### Windows 11
- `.gitattributes` で改行 LF 統一済み（CRLF だとコンテナ内のスクリプトが動かない）
- WSL2 のメモリが膨らむ場合は `%UserProfile%\.wslconfig` で上限設定
- `compose.yaml` 内のパスは相対（`./config`）。Claude Desktop 設定の `args` は絶対パス（`C:\\dev\\...`）

## 6. v0.1 の状態（検証済み範囲）
- 単体テスト 12 件通過
- **Dovecot 2.3.21（さくら VPS と同系統）に対する統合テスト 3 件通過**（SPECIAL-USE 自動判別、返信下書き保存→一覧→削除、ゴミ箱移動）
- **MCP クライアントから stdio 経由で全 11 ツールの E2E 確認済み**（`scripts/e2e_check.py`）
- 日本語の件名・差出人名・本文・引用・署名が正しく往復することを確認
- **未検証**: `docker compose build`（Docker のない環境で作成）、GreenMail、Gmail、outlook.com
- **OAuth2（v0.2 で追加）**: Microsoft はデバイスコードフロー、Google はループバック方式。`mail-mcp auth <account>` で初回ログイン、トークンは `/tokens/<name>.json`。単体テスト（外部通信はモック）で接続経路（XOAUTH2 呼び出し、トークン更新、保存）は検証済みだが、**実アカウントでのログインは未検証**。Entra ID / Google Cloud の設定手順は README 参照
- CLI: `mail-mcp`（サーバー）/ `mail-mcp auth <account>`（OAuth2 初回ログイン）/ `mail-mcp check`（全アカウント接続確認）
- タイムゾーンはコンテナに `TZ=Asia/Tokyo` を渡す（Dockerfile / compose.yaml 設定済み）。Claude Desktop 等から `docker run` する場合は `-e TZ=Asia/Tokyo` を追加

## 7. ロードマップ
1. ✅ v0.1: 受信・下書き・整理
2. `docker compose build` → GreenMail で `pytest -m integration` と `scripts/e2e_check.py` → MCP Inspector 確認
3. さくら VPS 実接続（`list_folders` で証明書・フォルダ判別を確認）→ Claude Desktop 登録
4. Gmail 追加 → 横断検索の動作確認
5. Gemini CLI / Antigravity CLI 登録
6. OAuth2 の実アカウント検証（outlook.com でログイン → `check` が OK になること → Gmail も切り替え）
7. 保留: 添付本文取得、HTML 下書き、`update_draft`、送信、Streamable HTTP 化
