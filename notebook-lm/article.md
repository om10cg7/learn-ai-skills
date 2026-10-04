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

Claude にインストールされたソースを読んでもらったところ、ログインできたかどうかを、開いているページの URL（ホスト名）だけで判定していました。

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

まず、ノートが見えるかを確認しました。

```powershell
nlm notebook list
```

一覧の中に「自動化テスト」があり、ソースは3件でした。中身は、2026年9月の株の情報番組3本を文字起こしした Google ドキュメントです。

Claude Code にはこう指示しました。

> 自動化テストのノートを400文字以内で要約して

Claude Code が実行したのは、次のコマンドです。

```powershell
nlm notebook query <ノートID> "このノートの内容を400文字以内で要約してください" --new-conversation
```

約34秒で、次の回答が返ってきました（引用番号はそのまま載せています）。

> 本ノートは、2026年9月の米国株・日本株市場動向や投資戦略を扱った3つのコンテンツの要約です。
>
> 1. 伊木ヒロシ: 原油高や米10年債利回り5%等のマクロ環境下で「お金の移動」を重視し[1, 2]、個別株の厳選や金・仮想通貨・不動産への資産保全的な分散投資を提言[2-5]。
> 2. 戸松信博: 米長期金利高や日米の為替政策・日銀動向を分析[6, 7]。AI株の強さ、金・ビットコインの動向、ROEやPBR等による財務分析を解説[8-10]。
> 3. 江守哲: 9月のアノマリーや調整リスク、金利・原油の影響を説明[11, 12]。マグニフィセント7の選別や、金・エネルギー・現金を交えた段階的リスク管理を提言[13-15]。
>
> 共通して、原油・金利・為替などのマクロ指標から資金流出入を読み解く重要性が強調されています[2, 6, 12]。

文字数を数えると、引用番号込みで383文字、引用番号を除くと323文字でした。400文字以内という指示は守られています。

回答の最後には「さらに詳しく比較・深掘りしましょうか？」という提案も付いていました。ここまで含めると452文字なので、文字数を厳密に使いたい場合は削る必要があります。

返ってくるのは JSON で、引用番号ごとにどのソースから取ったかも入っています。ブラウザ版と同じく、どの番組の話かを後から追えるのは便利です。

なお README によると、CLI や MCP から投げた質問も NotebookLM のチャット履歴に残るそうです（ブラウザでの確認はまだしていません）。

### MCP ではなく CLI 経由になった理由

今回は MCP 登録の直後で、Claude Code を再起動しないまま指示を出しました。そのため MCP のツールが読み込まれておらず、Claude Code は同梱の CLI（nlm）を代わりに呼びました。

再起動すれば、MCP の notebook_query ツール経由で同じことができるはずです。こちらはまだ試していません（未検証）。結果だけ見れば、CLI 経由でも Claude Code から NotebookLM を使えることは確認できました。

## 📝 まとめ

- インストールは uv で1コマンド。Claude Code への登録も nlm setup add claude-code の1コマンド
- Windows では nlm login が「成功」と出ても Cookie が1個しか取れず、使えないことがあった
- その場合は、デバッグポート付きで起動した Chrome に手動でサインインし、--provider openclaw --cdp-url で Cookie を取らせると通った
- 「自動化テスト」を400文字以内で要約させると、約34秒で引用付きの要約が返ってきた（本文383文字）
- MCP のツールは Claude Code の再起動後に使える。再起動前でも CLI 経由なら動く

👉 次回は、Claude Code を再起動して MCP 経由で同じ指示を出してみます。あわせて、毎月の文字起こしをソースに追加して要約するところまで自動化できるか試します。

※動作確認は Windows 11 / 個人の Google アカウントでの結果です。このツールは非公式で、内部 API の変更で動かなくなる可能性があります。
