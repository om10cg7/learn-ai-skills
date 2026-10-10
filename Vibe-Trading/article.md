AI に投資のバックテストを任せられる OSS が話題になっています。ただ、どこまで本当に動くのかは、自分で触ってみないと分かりません。

この記事では、HKUDS の「Vibe-Trading」を Python の仮想環境に入れ、MCP サーバーとして Claude Code に登録して、日本株でファクター検証とバックテストを動かした記録をまとめます。LLM の API キーは設定していません。結果を先に言うと、ほぼ「効かなかった」です。

## 🤔 なぜ Vibe-Trading を試したいか

前回は、TradingView の MCP サーバーを使って、日本株の株価を Claude Code から取るところまでやりました。

https://note.com/om10cg72/n/nebd65a86ecfb

次に気になったのは、取れた数字で戦略が通用するのかどうかです。Vibe-Trading は「自然言語で指示すると、AI が指標を選んでバックテストまで回す」と紹介されていて、460 種類以上のファクターが入っているとも聞きました。

その紹介が本当なのか、日本株で確かめてみます。

## 🛠 Vibe-Trading とは？

GitHub の HKUDS/Vibe-Trading で公開されている、金融リサーチ用のエージェント基盤です。ライセンスは MIT です。

今回触ったのは、次の 3 つです。

**MCP サーバー**

pip で入る vibe-trading-mcp が、Claude Code にツールを公開します。ツールの数は 74 個でした（私の環境で数えた数です）。

**ファクター（Alpha Zoo）**

同梱のファクターは 462 個で、Claude Code から読み込むと 462 個すべて成功しました。日本株で使うときは、自分で価格データを渡して計算する必要があります。

**バックテスト**

config.json と signal_engine.py を用意して実行します。ブートストラップとウォークフォワードの検証も、設定で付けられます。

試していないものもあります。自然言語で戦略を作るエージェントは、LLM の API キーが必要なので見送りました。シャドウアカウント、トレード履歴の診断、メッセージアプリへの通知、証券口座につながるツール（trading_account など）も使っていません。

2026年10月時点の README と、インストールしたパッケージの中身に基づきます。

一つ注意があります。README には、公式を名乗る X アカウントやトークンは公式のものではないので、買ったりウォレットをつないだりしないように、という警告が載っています。投資系のプロジェクトは、偽物に気をつけたほうがよさそうです。

## 🚀 導入手順

### 環境

- OS：Windows 11 Pro
- Claude Code：2.1.251
- Python：3.11.9
- vibe-trading-ai：0.1.16
- yfinance：1.7.0（vibe-trading-ai と一緒に入ったもの）

README の前提は Python 3.11 以上です。

### 1. 仮想環境を作る

作業用のフォルダで、仮想環境を作ります。パッケージが多いので、システムの Python を汚さないようにしました。

```powershell
python -m venv .venv
```

### 2. vibe-trading-ai を入れる

```powershell
.\.venv\Scripts\python.exe -m pip install vibe-trading-ai
```

最後に「Successfully installed ... vibe-trading-ai-0.1.16」と出れば成功です。pandas、scipy、langchain など、100 個を超えるパッケージが一緒に入りました。

MCP サーバーの実行ファイルは、.venv\Scripts の中に vibe-trading-mcp.exe として入ります。

### 3. Claude Code に MCP を登録する

```powershell
claude mcp add --scope project vibe-trading -- "C:\...\Vibe-Trading\.venv\Scripts\vibe-trading-mcp.exe"
```

`--scope project` を付けると、そのフォルダを開いたときだけ使えます。登録内容は .mcp.json に書かれますが、私の PC のパスが入るので、.gitignore に入れました。

登録しても、Claude Code を再起動するまでツールは読み込まれません。前回と同じです。

## ⚠️ ハマったところ

### 日本株の銘柄検索が使えない

search_symbol に「トヨタ自動車 7203」を渡すと、候補が 0 件になりました。

```
"yahoo": "skipped: non-ASCII query is not supported by this source"
"eastmoney": "eastmoney search failed: Expecting value: line 1 column 1 (char 0)"
```

日本語は Yahoo 側が対応しておらず、Eastmoney は JSON が返りませんでした。英語の「Toyota Motor 7203」でも、候補は 0 件でした。銘柄コードは、7203.T のように自分で書く必要があります。

### source を指定しないと、日本株の日足が取れない

get_market_data に 7203.T を渡すと、source の既定値（auto）ではエラーになりました。

```
No data returned for any requested symbol: 7203.T
```

source に yahoo を指定すると、243 行の日足が取れました。7203.JP という書き方では取れません。米国株の AAPL.US は、auto のままで取れています。

### alpha_bench は日本株で使えない

ファクターをまとめて評価する alpha_bench は、universe に指定できるのが sp500、csi300、btc-usdt の 3 つだけでした。Alpha Zoo の各ファクターの対応市場も、米国、中国、香港、暗号資産で、日本株は入っていません。

README に日本株の記載がなかった理由は、これだと思います。

回避策として、Alpha Zoo の計算関数を Python から呼び、日本株の価格データに自分で当てました。

### MCP 経由の backtest だけ失敗する

backtest ツールを呼ぶと、3 回とも失敗しました。

```
akshare failed for 6594.T: ('Connection aborted.', RemoteDisconnected(...))
Exception: api init error.
```

ログの表面だけ見ると、Tushare のトークンがなくて落ちたように見えます。ところが、同じ run_dir に対して backtest/runner.py を直接実行すると、最後まで成功しました。

run_dir ごとのログ（logs/runner_stderr.txt）を読むと、本当のエラーは別にありました。

```
curl: (77) error adding trust anchors from locations:
CAfile: C:\Users\ユーザー名\...\certifi\cacert.pem
```

SSL の証明書ファイルを開けず、Yahoo への接続が失敗していたのです。失敗した銘柄が akshare、Tushare にフォールバックして、最後に Tushare のトークン要求で落ちていました。

原因は、インストール先のパスに日本語が入っていることでした。backtest ツールは、子プロセスを PYTHONUTF8=1 で起動します。この条件だと、日本語を含むパスにある証明書ファイルを、curl が開けなくなります。次の順に試して確かめました。

- PYTHONUTF8=1 だけを付けると、7203.T が 0 行になり失敗する
- PYTHONUTF8=0 にすると、成功する
- PYTHONUTF8=1 のままでも、証明書を英数字だけのパスに置いて環境変数 CURL_CA_BUNDLE で指すと、成功する

直接実行で成功したのは、私が PYTHONUTF8 を設定していなかったからです。

直し方は、証明書を英数字だけのパスにコピーして、.mcp.json で指すことです。

```powershell
.\.venv\Scripts\python.exe -c "import certifi, shutil, os; os.makedirs(r'C:\Users\Public\ca_test', exist_ok=True); shutil.copy(certifi.where(), r'C:\Users\Public\ca_test\cacert.pem')"
```

```json
"env": {
  "CURL_CA_BUNDLE": "C:\\Users\\Public\\ca_test\\cacert.pem"
}
```

Claude Code を再起動したあと、MCP 経由の backtest が成功しました。

ただし、certifi が更新されるとコピーは古くなります。長く使うなら、仮想環境そのものを英数字だけのパスに作るほうが確実です。私の環境では、そこまではやっていません。

### factor_analysis は、翌日のリターンを自分で作る必要がある

factor_analysis は、ファクターとリターンの CSV を渡すと、IC と分位グループ別の成績を返します。ソースを読むと、内部で日付をずらす処理がありませんでした。そのため、リターンの CSV は「その日のファクターで、そのあとに得られるリターン」にしておく必要があります。

もう 1 つあります。20 日先のリターンを毎日の値として渡すと、グループ別の最終資産が数十億倍という値になりました。重なった期間を毎日かけ合わせているためです。20 日先の結果は、IC だけを見ることにしました。

## 💻 日本株で試してみる

### Claude Code を再起動して、ツールを確認する

再起動したあと、Claude Code に vibe-trading のツール一覧を見せてもらいました。

> vibe-trading の MCP ツール一覧を見せて

返ってきたのは 74 個のツールです。このうち、バックテスト、ファクター分析、Alpha Zoo、データ取得系を今回使います。

### Alpha Zoo を確認する

> alpha_zoo の health を見て

Claude Code は alpha_zoo を呼び、`loaded: 462, failed: 0` と返ってきました。同梱ファクターの 462 個が、すべて読み込めています。

### 日本株でファクターを検証する

時価総額の大きい日本株 30 銘柄（私が選んだものです）の調整後終値を取り、Alpha Zoo から 3 つのファクターを計算しました。

- academic_carhart_mom：12 か月前から 1 か月前までの騰落率（モメンタム）
- academic_high52w：52 週高値に対する現在値の位置
- academic_bab：低ベータ

これを factor_analysis にかけました。期間は 2020 年 1 月から 2026 年 10 月 1 日までです。

**翌日のリターンに対する IC（平均）と IR**

- モメンタム：IC 0.015、IR 0.049
- 52 週高値：IC 0.012、IR 0.040
- 低ベータ：IC 0.006、IR 0.017

**20 日先のリターンに対する IC（平均）と IR**

- モメンタム：IC 0.008、IR 0.025
- 52 週高値：IC 0.029、IR 0.099
- 低ベータ：IC -0.001、IR -0.003

IC は、ファクターの順位と実際のリターンの順位の相関です。一般には 0.03 を超えると、弱い信号があるとされます。52 週高値の 20 日先がかろうじて近いだけで、あとはほぼゼロでした。

「AI が良い指標を選んでくれる」というより、大型株の 30 銘柄では、既存の学術的なファクターがほとんど効かなかった、という結果です。

### バックテストを回す

> 52 週高値の上位 5 銘柄を毎月入れ替える戦略を、バックテストして

signal_engine.py は Claude Code が書きました。毎月の最初の営業日に、52 週高値に対する現在値の比が高い上位 5 銘柄を、等金額で持つ戦略です。比較用に、30 銘柄の等金額保有も同じ条件で回しました。

設定のポイントは次の 3 つです。

- 評価期間は 2020 年 1 月から。指標の計算に使う 252 日分は、評価に含めない
- 手数料は 0.1%（既定値のまま）
- 検証として、ブートストラップとウォークフォワードを付ける

結果は MCP 経由の backtest で出しました。

**52 週高値の上位 5 銘柄**

- 総リターン +260.0%、年率 21.7%
- Sharpe 1.02、最大ドローダウン -25.6%

**30 銘柄の等金額保有**

- 総リターン +276.0%、年率 22.5%
- Sharpe 1.12、最大ドローダウン -25.8%

戦略は、何もしない等金額保有に負けました。ファクター検証で IC がほぼゼロだった結果と、同じ向きです。

検証機能の結果も見ておきます。

ブートストラップによる Sharpe の 95% 信頼区間は、戦略が 0.22 から 1.80、等金額保有が 0.32 から 1.91 でした。幅が広すぎて、優れているとは言えません。

ウォークフォワードでは、戦略は 5 つの区間すべてがプラスでした。ただし、等金額保有も 5 区間すべてプラスなので、戦略が良い証拠にはなりません。

同じ設定で回し直すと、数字が少し変わりました。直接実行した最初の回は、戦略が +253.6%、等金額保有が +276.1% でした。

実行のたびに「OHLC validation: dropping N invalid bar(s)」の件数も違っていました。Yahoo から取るデータが毎回微妙に違うのだと思います（確かめてはいません）。

この記事の数字は、MCP 経由で実行した回のものです。結論は、どちらの回でも変わりませんでした。

計っていないこともあります。日本株の売買コストに合わせた手数料の検証は、やっていません。

## 📝 まとめ

- Vibe-Trading は、MCP で 74 個のツールを Claude Code に渡せる。LLM の API キーなしで、ファクター検証とバックテストまで動いた
- Alpha Zoo の 462 個は、すべて読み込めた。ただし対応市場に日本株はなく、自分で価格データを渡す必要がある
- 日本株は、銘柄コード（7203.T）を自分で書き、source に yahoo を指定すれば日足が取れる。銘柄検索は使えなかった
- 52 週高値の戦略は、等金額保有に負けた（+260.0% と +276.0%）。ファクターの IC も、ほぼゼロだった
- MCP 経由の backtest は、インストール先のパスに日本語が入っていると失敗した。証明書を英数字のパスに置き、CURL_CA_BUNDLE で指して直った

👉 次回は、alpha_bench を米国株（sp500）で動かして、日本株との違いを見ます。

※ Windows 11 での検証です。日本株への適用は、Vibe-Trading の想定された使い方ではありません。

※ 株価は 2026年10月1日までの Yahoo Finance の調整後終値です。30 銘柄は現在の大型株なので、生存者バイアスがあります。

※ 本記事は個人の見解であり、特定の銘柄の売買を推奨するものではありません。投資判断はご自身の責任でお願いします。
