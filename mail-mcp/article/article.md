さくらのVPS、Gmail、outlook.com。私のメールは、3つのアカウントに分かれています。AIにメールを見てもらおうとすると、アカウントごとに別の設定が要ります。

この記事では、3つをまとめて管理できる自作のMCPサーバー「mail-mcp」の作り方と、実際にハマったところをまとめます。フォルダ名も認証方法もアカウントごとに違い、つなぐだけで4回つまずきました。

## 🤔 なぜ複数のメールアカウントをまとめたいか

私のメールは、用途ごとに3つのアカウントに分かれています。さくらのVPSで作った独自ドメインのメール、Gmail、outlook.comです。

アカウントが分かれていると、AIに頼むときも、アカウントごとにツールを入れて、設定して、呼び分けることになります。

そこで、1つのMCPサーバーを窓口にして、「今日届いたメールを全部見せて」と一度で頼める形にしたいと考えました。

## 🛠 mail-mcpとは？

GitHubで公開している、複数のメールアカウントをまとめて管理するための自作ツールです。IMAPでメールを読むMCPサーバーで、本体のコードは約900行（Python）です。

https://github.com/om10cg7/learn-ai-skills/tree/main/mail-mcp

2026年11月時点の内容です。ツールは11個あります。

**読む**
- アカウント一覧、フォルダ一覧、検索、本文の取得
- 検索は、アカウントを指定しなければ全アカウントを横断する
- 1つのアカウントが失敗しても、残りの結果は返す

**下書き**
- 返信の下書き、新規の下書き、一覧、削除
- 下書きは、各アカウントの下書きフォルダに保存する

**整理**
- 既読にする、フォルダを移す、ゴミ箱へ移す

アカウントごとに、下書きとゴミ箱のフォルダ名が違います。サーバーが自動で見分けるので、AIには同じ言い方で頼めます。実際に接続を確かめたときの結果は、次のとおりです。

- さくらのVPS: `INBOX.Draft` と `INBOX.Trash`
- Gmail: `[Gmail]/下書き` と `[Gmail]/ゴミ箱`
- outlook.com: `Drafts` と `Deleted`

**送信機能は付けていません**

AIが誤ってメールを送る事故と、受信メールの中の指示にAIが従う事故を避けるためです。実際に、さくらのアドレスには、国税庁や還付金などをかたる不審に見えるメールが、1日で7通届きました。

- 送信機能（SMTP）は作っていない。保存するのは下書きまで
- 削除は、ゴミ箱へ移すだけ。完全に消す機能はない

自作のツールなので、使うときは自己責任でお願いします。

## 🚀 導入手順

### 環境

- OS: Windows 11
- Docker Desktop（Docker 29.8.2）
- Python 3.12、MCP Python SDK 2.x（コンテナの中で動きます）
- つないだクライアント: Antigravity CLI（`agy`）

### 1. リポジトリを取得して、ビルドする

```powershell
git clone https://github.com/om10cg7/learn-ai-skills.git
cd learn-ai-skills\mail-mcp
copy .env.example .env
copy config\accounts.example.yaml config\accounts.yaml
docker compose build
```

`.env` と `config\accounts.yaml` は、Gitに入れない設定になっています。パスワードは、`accounts.yaml` ではなく `.env` に書きます。

### 2. 3つのアカウントを設定する

アカウントごとに、認証の方法が違います。

**さくらのVPS（パスワード）**
- IMAPの993番ポートを、パケットフィルターとOSのファイアウォールの両方で開ける
- パスワードは、`.env` の `SAKURA_PASSWORD` に書く

**Gmail（アプリパスワード）**
- 2段階認証を有効にして、アプリパスワードを発行する
- ふだんのパスワードは、IMAPでは使えない

**outlook.com（OAuth2）**
- MicrosoftのEntra IDに、アプリを登録する
- サポートするアカウントの種類は「個人用アカウントのみ」にして、公開クライアントフローを許可する
- 手順書にあった「APIのアクセス許可の追加」は、不要だった（ログイン時の同意で付与された）

outlook.comだけは、初回にログインが要ります。

```powershell
docker compose run --rm mail-mcp auth outlook
```

画面に出たURLをブラウザで開き、表示されたコードを入力します。「ログイン成功」と出れば完了です。

### 3. 接続を確認する

```powershell
docker compose run --rm mail-mcp check
```

アカウントごとに、次のような行が出れば成功です。

```text
OK   sakura   フォルダ 5 件 / 下書き=INBOX.Draft / ゴミ箱=INBOX.Trash
```

3つとも「OK」になってから、次に進みます。

### 4. クライアントに登録する

Antigravity CLIには、次のコマンドで登録しました。`<フォルダ>` は、`mail-mcp` を置いた場所です。

```powershell
agy mcp add mail -- docker run -i --rm -e TZ=Asia/Tokyo --env-file <フォルダ>\.env -v <フォルダ>\config:/config:ro -v <フォルダ>\tokens:/tokens mail-mcp:latest
```

パスに空白や日本語が入っていても、設定ファイルには、引数ごとに正しく分かれて保存されました。

Claude Desktopにも同じ内容を書けますが、設定ファイルの場所に注意が要ります（次の節で書きます）。再起動するまで、設定は読み込まれません。

## ⚠️ ハマったところ

### Claude Desktopに「mail」が出ない

設定ファイルに `mcpServers` を書いて再起動したのに、ツールの一覧にメールが出ませんでした。

原因は、設定ファイルの場所の取り違えです。私の環境はWindowsのストア版で、似たフォルダが2つあります。アプリが実際に読んでいたのは、最初に書いた場所とは別のフォルダでした。

```text
C:\Users\<ユーザー名>\AppData\Local\Claude-Data\claude_<ID>\claude_desktop_config.json
```

私は、アプリが自動で書き込む設定が入っているほうが、実際に使われているファイルだと判断し、そこに `mcpServers` を足しました。足したあとの画面での確認は、まだ終わっていません。

### docker composeでは動くのに、docker runだとさくらだけ失敗する

`check` は3つともOKだったのに、`docker run` で起動すると、さくらだけログインに失敗しました。

```text
MailboxLoginError: Response status "OK" expected, but "NO" received. Data: [b'Login failed.']
```

原因は、`.env` の `SAKURA_PASSWORD=` の直後にあった、半角スペース1つです。`docker compose` は無視しますが、`docker run --env-file` は、そのまま渡していました。

スペースを消して直りました。クライアントは `docker run` で起動するため、`check` が通っても、この違いには気づけません。

### テスト用サーバーで、本文の取得が失敗する

テスト用のメールサーバー（GreenMail）に対して、メール本文の取得が失敗しました。

```text
imaplib.IMAP4.error: UID command error: BAD [b'Search command not supported']
```

原因は、検索のたびに文字コードを指定していたことです。GreenMailは、その指定を受け付けません。英数字だけの検索では文字コードを指定せず、日本語を含むときだけ `UTF-8` を指定するように直しました。本文の取得は、検索をやめて、UIDで直接取るようにしました。

### outlook.comのログインが「AADSTS70016」で失敗する

デバイスコードでのログインが、次のエラーで2回失敗しました。

```text
AADSTS70016: The provided request has not yet been authorized by the user. The user must input their code.
```

原因は、コードの期限切れです。私の環境では、コードを出してから約15分で切れました。コードを出したあと、ブラウザを開くのが間に合っていませんでした。

先にブラウザを開いて、すぐ入力できる状態でコードを出すと、3回目で通りました。

## 💻 実際に使ってみる

### 再起動して、確認する

`agy` に登録したあと、次のように頼みました。

> mail の list_accounts を実行して

Antigravity CLIは `list_accounts` を呼び、設定した3つのアカウントを返しました。

- `sakura`
- `gmail`
- `outlook`

### 全アカウントを横断して検索する

アカウントを指定せずに、検索を実行しました。3つすべてから、結果が返りました。

今日（2026年11月3日）届いたメールの件名は、3アカウントを合わせて、24件を一覧にできました。内訳は次のとおりです。

- さくら: 7件
- Gmail: 10件
- outlook.com: 7件

なお、この横断検索は、動作確認用に自作したスクリプトで行いました。Antigravity CLIの会話から呼ぶ形では、`list_accounts` だけ確かめています。

### まだ確かめていないこと

- Claude Desktopの画面から呼び出す確認は、終わっていません
- 検索にかかる時間は、計っていないので、他の方法と比較できません

## 📝 まとめ

- 複数のメールアカウントを、1つのMCPサーバーで、同じ頼み方で扱えるようになった
- アカウントごとに違う下書きとゴミ箱のフォルダ名は、サーバーが自動で見分ける
- 送信機能は付けず、下書きの保存とゴミ箱への移動までに絞った
- outlook.comは、OAuth2の登録とデバイスコードでのログインで、APIの許可を足さずにつながった
- `check` が通っても `docker run` で失敗することがあるので、起動と同じ方法で確かめる

👉 次回は、Gmailをアプリパスワードから、OAuth2に切り替えます。

※ 2026年11月時点の内容です。私の環境（Windows 11）での結果で、自作のツールです。Claude Desktopの画面からの確認は、終わっていません。
