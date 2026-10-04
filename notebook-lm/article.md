NotebookLM（現 Gemini Notebook）に資料をためていても、要約や質問のたびにブラウザを開くのは手間です。Claude Code から直接呼べれば、開発の流れを止めずに済みます。

この記事では、MCP サーバー兼 CLI の「notebooklm-mcp-cli」をインストールし、自分のノート「自動化テスト」を400文字以内で要約させるまでをまとめます。Windows でのログインに一度失敗したので、その回避策も書いておきます。

## 🤔 なぜ NotebookLM を Claude Code から呼びたいか

NotebookLM には、株の情報番組の文字起こしを Google ドキュメントにしてためています。月ごとにソースを足して、要約や質問に使っています。

ただ、毎回ブラウザで開いて質問を打つのは地味に面倒です。Claude Code から「このノートを要約して」と頼めれば、結果をそのままファイルにしたり、次の処理につないだりできます。

前回は Claude Code に Gemini をつなぎました。今回はその NotebookLM 版です。

https://note.com/om10cg72/n/nab5f7d184e50

## 🛠 notebooklm-mcp-cli とは？

GitHub で公開されている、NotebookLM を外から操作するためのツールです。1つのパッケージに、MCP サーバー（notebooklm-mcp）と CLI（nlm）の両方が入っています。

MCP のツールは53個あり、ブラウザでできる操作はほぼ Claude Code から実行できます。

**基本操作**
- ノートブックの一覧・作成・名前変更・削除
- ソースの追加（URL、テキスト、ローカルファイル、Google Drive）と、AI によるソースの要約
- ノートブックへの質問（引用付き）。チャット履歴の Markdown / JSON エクスポートも可能

**コンテンツ生成（Studio）**
- 音声解説、動画解説、レポート、クイズ、フラッシュカード、マインドマップ、スライド、インフォグラフィックなど
- 生成物のダウンロードと、Google Docs / Sheets へのエクスポート

**リサーチ・整理・自動化**
- Web / Drive の調査（Deep Research を含む）と、見つかったソースの取り込み
- タグ付け、複数ノートブックを横断した質問、一括操作
- 複数手順をまとめて実行するパイプライン機能（ingest-and-podcast など）

2026年10月時点の README に基づきます。リポジトリは「jacob-bd/gemini-notebook-mcp-cli」に改名されていますが、パッケージ名は notebooklm-mcp-cli のままです。

注意点として、README には「非公開の内部 API を使っている」「ブラウザの Cookie を取り出して認証する」「Google の利用規約に沿っていない可能性がある」と明記されています。個人の実験用途として、自己責任で使ってください。

## 🚀 導入手順

### 環境

- OS：Windows 11 Pro
- Claude Code：2.1.251
- uv：0.12.23
- notebooklm-mcp-cli：0.15.1

### 1. uv を入れる

README の推奨インストール方法は uv です。私の環境には入っていなかったので、公式のインストーラーで入れました。

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

C:\Users\ユーザー名\.local\bin に入ります。開いているターミナルには PATH が反映されないので、ターミナルを開き直してください。

### 2. notebooklm-mcp-cli を入れる

```powershell
uv tool install notebooklm-mcp-cli
```

最後に「Installed 2 executables: nlm, notebooklm-mcp」と出れば成功です。

### 3. Google アカウントでログインする

```powershell
nlm login
```

Chrome が立ち上がるので、NotebookLM を使っている Google アカウントでサインインします。ただし、私の環境ではここでつまずきました。詳しくは後述の「ハマったところ」で書きます。

### 4. Claude Code に MCP を登録する

```powershell
nlm setup add claude-code
```

ユーザー全体（user scope）の設定に追加されます。確認はいつものコマンドです。

```powershell
claude mcp list
```

次のように出れば登録できています。

```
gemini-notebook-mcp: C:\Users\ユーザー名\.local\bin\notebooklm-mcp.EXE  - √ Connected
```

なお、MCP のツールは Claude Code を再起動するまで読み込まれません。

## ⚠️ ハマったところ

### ログイン成功と出るのに使えない

nlm login を実行すると、「Successfully authenticated!」と出て終わりました。ところが、ノートの一覧を取ろうとするとこうなります。

```
✗ Authentication Error
  Authentication expired. Run 'nlm login' in your terminal to re-authenticate.
```

ログイン時の表示をよく見ると、取れた Cookie が1個だけでした。

```
✓ Successfully authenticated!
  Cookies: 1 extracted
  CSRF Token: No (will be auto-extracted)
```

--clear を付けてブラウザのプロファイルを作り直しても、結果は同じでした。

### 原因は「URL だけでログイン判定」していること

インストールされたソースを Claude に読んでもらったところ、ログインできたかどうかを、開いているページの URL（ホスト名）だけで判定していました。

ホストが notebooklm.google.com ならログイン済みとみなし、すぐに Cookie を取りにいきます。未ログインの状態でもこのホストのページが表示されると、サインインする前に Cookie を取って終わってしまう、というのが私の推測です（コードを読んでの推測で、確定ではありません）。

### 回避策：自分で起動した Chrome から取らせる

nlm login には、外部のブラウザから Cookie を取るモードがあります。これを使いました。

まず、デバッグ用のポートを開けて Chrome を起動します。

```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=18800 --user-data-dir="$env:USERPROFILE\.notebooklm-mcp-cli\manual-chrome" https://notebooklm.google.com/
```

開いた Chrome で手動でサインインし、ノートの一覧が表示されるまで待ちます。そのうえで、この Chrome から Cookie を取らせます。

```powershell
nlm login --provider openclaw --cdp-url http://127.0.0.1:18800 --force
```

今度は Cookie が54個取れ、アカウント名も表示されました。

```
✓ Successfully authenticated!
  Provider: openclaw
  Cookies: 54 extracted
  CSRF Token: Yes
```

--provider openclaw は本来、OpenClaw というツールが管理するブラウザ向けのオプションです。ただ、中身はデバッグポートにつなぐだけなので、普通の Chrome でも使えました。

## 💻 「自動化テスト」を400文字以内で要約させる

### Claude Code を再起動する

MCP を登録しただけでは、Claude Code にツールは読み込まれません。Claude のデスクトップアプリを一度終了して、起動し直しました。

再起動後は、notebook_list や notebook_query など、NotebookLM 用のツールが Claude Code から呼べるようになっていました。

### ノートを確認する

Claude Code が notebook_list を呼ぶと、ノートの一覧が返ってきました。その中に「自動化テスト」があり、ソースは3件でした。中身は、2026年9月の株の情報番組3本を文字起こしした Google ドキュメントです。

### 要約を頼む

Claude Code にはこう指示しました。

> 自動化テストのノートを400文字以内で要約して

Claude Code は notebook_query を呼び、次の質問を NotebookLM に投げました。

```
このノートの内容を400文字以内で要約してください
```

返ってきた回答は次の通りです（引用番号はそのまま載せています）。

> 本ノートは、2026年9月時点の株式市場・マクロ経済動向と投資戦略に関する3つの専門チャンネルの解説をまとめたものです。
> 資金の流れ、米長期金利（5%超）、原油高が及ぼす市場影響が共通テーマです [1-3]。
> ・伊木ヒロシ: 米国株から日本株や実物資産への資金移動を分析し、金利上昇下での個別株選定や金・暗号通貨での資産保全を推奨 [4-6]。
> ・戸松信博: 円安・日銀動向、AI株（マイクロン決算等）の変動、ビットコイン等の需給、財務分析（PER・PBR・ROE）の基本を解説 [7-11]。
> ・江守哲: 「9月効果」や中間選挙のアノマリー、マグニフィセント7の選別、金やエネルギー株を活用したリスクヘッジと買増戦略を提示 [12-15]。

文字数は、引用番号と記号を除くと299文字でした。400文字以内という指示は守られています。

回答の最後には「さらに詳しく深掘りしましょうか？」という提案文も付いていました。これを含めた全体は439文字なので、文字数を厳密に使いたいときは、提案文を除いて数える必要があります。

返ってくるのは JSON で、引用番号ごとに、どのソースのどの部分から取ったかも入っています。ブラウザ版と同じく、どの番組の話かを後から追えます。

### 再起動前は CLI で動いた

実は、再起動する前にも一度、同じ指示を出しています。このときはまだ MCP のツールが読み込まれていなかったため、Claude Code は同梱の CLI（nlm）を代わりに呼びました。

```powershell
nlm notebook query <ノートID> "このノートの内容を400文字以内で要約してください" --new-conversation
```

こちらは約34秒で、383文字（引用番号などを除くと323文字）の要約が返ってきました。MCP 経由の所要時間は計っていないので、速さの比較はできていません。

なお README によると、CLI や MCP から投げた質問も NotebookLM のチャット履歴に残るそうです（ブラウザでの確認はまだしていません）。

## 📝 まとめ

- インストールは uv で1コマンド。Claude Code への登録も nlm setup add claude-code の1コマンド
- Windows では nlm login が「成功」と出ても Cookie が1個しか取れず、使えないことがあった
- その場合は、デバッグポート付きで起動した Chrome に手動でサインインし、--provider openclaw --cdp-url で Cookie を取らせると通った
- 登録後は Claude Code（アプリ）の再起動が必要。再起動すると、MCP の notebook_query 経由で「自動化テスト」を400文字以内で要約できた
- 再起動前でも、Claude Code が CLI（nlm）を呼べば同じことができた

👉 次回は、毎月の文字起こしを新しいソースとして追加し、要約まで流せるか試します。

※動作確認は Windows 11 / 個人の Google アカウントでの結果です。このツールは非公式で、内部 API の変更で動かなくなる可能性があります。
