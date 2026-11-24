Claude Code の公式プラグインは、数が多すぎて選べません。マーケットプレイスには315個も並んでいて、どれを入れればいいのか、入れたら重くならないのか、手が止まります。

この記事では、公式マーケットプレイス「claude-plugins-official」から3つを選び、私の PC で実際に動かした結果をまとめます。動いたものと、確認できなかったものを分けて書きます。

## 🤔 なぜ公式プラグインを試したいか

Claude Code を毎日使っていると、同じ作業が何度も出てきます。コミットを作る、危ない操作を止める、使いすぎたトークンを見直す、といった作業です。

自分でスキルやフックを書く前に、公式に用意されたものがあるなら、それを使うほうが早いはずです。ただ、入れる前に中身が分からないと、試す気になれません。

前回までは、スキルを1つ試す記事を書いてきました。今回はその続きで、公式のプラグインをまとめて見る回です。

https://note.com/om10cg72/n/n62928ada43f4

## 🛠 claude-plugins-official とは？

GitHub で公開されている、Anthropic のプラグインのディレクトリです。Claude Code の `/plugin` から探して入れられます。

**構成**
- plugins：Anthropic が作っているもの（code-review、frontend-design、各言語の LSP など）
- external_plugins：外部の提供者のもの（github、linear、asana、playwright など）

**数**
- 私の PC にあるコピーには、315個が載っていました
- カテゴリで多いのは、development が123個、productivity が69個、database が39個です

2026年10月時点の手元のコピーに基づきます。

注意点があります。README には「信頼できるものだけを入れてください。Anthropic は中身を保証しません」と書かれています。入れる前に、そのプラグインの中身を見ておくのが安全です。

https://github.com/anthropics/claude-plugins-official

## 🚀 導入手順

### 環境

- OS：Windows 11 Pro
- Claude Code：2.1.251
- Node.js：24.18.0
- Python：3.14.7

2026年10月26日に試しました。

### 1. 公式マーケットプレイスを確認する

私の環境では、最初から登録されていました。次のコマンドで確かめられます。

```powershell
claude plugin marketplace list
```

`claude-plugins-official` が `Source: GitHub (anthropics/claude-plugins-official)` と出れば登録済みです。

### 2. 入れる前に、重さを見る

プラグインは、入れると常に少しトークンを使います。`claude plugin details` で、その見込みを確かめられます。この表示は、入れた後のプラグインに対して出ました。

```powershell
claude plugin details hookify@claude-plugins-official
```

私の環境で出た値は、次のとおりです。数字は推定値です。

- session-report：常時 約46トークン
- commit-commands：常時 約71トークン
- hookify：常時 約218トークン

hookify が一番重いのは、スキルが5つ、エージェントが1つ、フックが4つと、中身が多いためです。それでも、毎回の消費としては小さい値でした。

### 3. 3つを入れる

```powershell
claude plugin install session-report@claude-plugins-official
claude plugin install hookify@claude-plugins-official
claude plugin install commit-commands@claude-plugins-official
```

3つとも `Successfully installed plugin`（scope: user）と出て、エラーなく入りました。

## ⚠️ ハマったところ

### `claude -p` で試したら、認証エラーになった

commit-commands を試すために、使い捨てのリポジトリを作り、`claude -p "/commit-commands:commit"` を実行しました。すると、次のエラーで止まりました。

```text
Failed to authenticate: OAuth session expired and could not be refreshed
```

原因は、確かめていません。Claude Code の画面の中から、別の `claude` を起動したことが関係している可能性があります。

回避策として、使い捨ての git worktree を作り、その中でスキルを呼び出す方法にしました。結果は、次の節に書きます。

### hookify のフックは `python3` を呼ぶ

hookify のフックの設定を見ると、実行するコマンドが `python3` になっていました。私の PC では、Microsoft Store 版の `python3` が使えたので、そのまま動きました。

Python が入っていない Windows では、動かない可能性があります。この点は、試していません。

## 💻 実際に試してみる

### session-report：使ったトークンの内訳が出た

Claude Code の履歴（`~/.claude/projects`）を読んで、使用量を集計するプラグインです。

本来は、HTML のレポートを作るスキルです。今回は、中の集計スクリプトを直接動かして、数字のほうを確かめました。HTML の生成までは試していません。

```powershell
node analyze-sessions.mjs --json --since 7d > session-report.json
```

直近7日分で、約7秒で終わりました。出てきた数字は次のとおりです。

- セッション数：31
- API 呼び出し：2,037回
- キャッシュ率：93.7%
- サブエージェントの呼び出し：56回

JSON には、プロジェクトごと、スキルごと、日ごとの内訳も入っていました。「どのプロジェクトで使いすぎたか」を後から見るのに使えそうです。

### hookify：危険なコマンドを止めるルールが動いた

「こういう操作は止めてほしい」というルールを、Markdown のファイルで書いておくプラグインです。内部では、Claude Code のフックとして動きます。

同梱の例にある、`rm -rf` を止めるルールを使いました。ルールのファイルは、こういう形です。

```markdown
---
name: block-dangerous-rm
enabled: true
event: bash
pattern: rm\s+-rf
action: block
---

⚠️ Dangerous rm command detected!
```

これをプロジェクトの `.claude/` に置き、フックのスクリプトに Bash コマンドの入力を渡しました。結果は次のとおりです。

- `rm -rf /tmp/x` を渡すと、deny（拒否）と警告文が返ってきた
- `ls` を渡すと、何も返さずに通った

止めるべきものだけが止まりました。

ただし、これはスクリプトを単体で動かした確認です。Claude Code のセッションの中で、フックが実際に発火する場面までは確認していません。

### commit-commands：コミットは問題なく作れた

`/commit-commands:commit` で、変更内容から1つのコミットを作るプラグインです。ほかに `commit-push-pr` と `clean_gone` があります。

使い捨ての作業コピーで、ファイルを1つ作ってからスキルを呼び出しました。結果は次のとおりです。

- エラーも、許可の確認も出なかった
- スキルは、git status、git diff、直近のログを渡してきた
- そのうえで、`git add` と `git commit` を1回の呼び出しで実行した
- 作られたコミットメッセージは、英語の1行タイトルだった

このスキルは、「ほかの作業はせず、コミットだけ作る」と指示されています。メッセージが簡潔なのは、そのためだと思います。日本語で書かせたいときは、指示を足す必要がありそうです。

`commit-push-pr` と `clean_gone` は、試していません。

## 📚 公式マーケットプレイスの全プラグイン一覧

手元のコピー（2026年10月26日時点）に載っていた315個を、カテゴリごとに並べます。名前は `marketplace.json` の `name` です。

件数の多い development と productivity は、用途ごとに小分けしました。小分けは、私が説明文を見て分けたもので、公式の分類ではありません。

概要は、各プラグインの説明文（英語）を、私が日本語に短くまとめたものです。実際の機能は、各プラグインのページで確認してください。

プラグインの中にあるスキルまでは、数えていません。入れるときは、`名前@claude-plugins-official` の形で指定します。

### development（123個）

**言語サーバー（コード解析）（13個）**

- **clangd-lsp**：C/C++ の言語サーバー（clangd）によるコード解析
- **csharp-lsp**：C# の言語サーバーによるコード解析
- **gopls-lsp**：Go の言語サーバー（gopls）によるコード解析とリファクタリング
- **jdtls-lsp**：Java の言語サーバー（Eclipse JDT.LS）によるコード解析
- **kotlin-lsp**：Kotlin の言語サーバーによるコード解析
- **liquid-lsp**：Shopify Liquid テンプレート向けの言語サーバー連携
- **lua-lsp**：Lua の言語サーバーによるコード解析
- **php-lsp**：PHP の言語サーバー（Intelephense）によるコード解析
- **pyright-lsp**：Python の言語サーバー（Pyright）による型チェックとコード解析
- **ruby-lsp**：Ruby の言語サーバーによるコード解析
- **rust-analyzer-lsp**：Rust の言語サーバーによるコード解析
- **swift-lsp**：Swift の言語サーバー（SourceKit-LSP）によるコード解析
- **typescript-lsp**：TypeScript / JavaScript の言語サーバーによるコード解析

**Claude Code の開発と拡張（25個）**

- **agent-sdk-dev**：Claude Agent SDK を使った開発キット
- **chrome-devtools-mcp**：動作中の Chrome を操作、検査。性能トレース、ネットワーク、コンソールの確認
- **code-modernization**：古いコードベースを、評価、マップ化、業務ルール抽出、計画の順で近代化
- **context7**：Context7 の MCP サーバーで、最新のライブラリドキュメントを検索
- **fakechat**：チャンネル通知の流れを試すための、ローカルホストの簡易チャット
- **feature-dev**：コード探索、設計、レビュー用のエージェントを使った機能開発ワークフロー
- **frontend-design**：AI らしくない、完成度の高いフロントエンドを作る
- **gitkraken**：コミット、ブランチ、PR、Issue などの Git 情報を Claude に渡す
- **greptile**：GitHub / GitLab 向けの AI コードレビュー。PR のコメントを確認、解決
- **lumen**：コードベースを索引化して、ローカルで意味検索する MCP サーバー
- **mattpocock-skills**：Matt Pocock のエンジニアリング用スキル集（仕様、TDD、コードレビュー、ドメイン設計など）
- **mcp-apps**：MCP Apps SDK で MCP アプリを作るスキル
- **mcp-server-dev**：Claude と連携する MCP サーバーの設計、構築ガイド
- **mcp-tunnels**：Anthropic の MCP トンネル経由で、プライベートな MCP サーバーに接続
- **microsoft-docs**：Azure、.NET、Windows などの Microsoft 公式ドキュメントを参照
- **modern-web-guidance**：最新の Web のベストプラクティスをエージェントに教える
- **playground**：ビジュアル操作とプレビュー付きの、単一ファイルの HTML プレイグラウンドを作る
- **plugin-dev**：Claude Code プラグインを開発するツールキット（フック、MCP、コマンド、エージェント）
- **qodo**：Qodo のコード理解、コーディング規約、コードレビューを利用
- **qodo-standards**：Qodo のルール探索と規約管理（任意）
- **ralph-loop**：同じ作業を、前回の結果を見ながら完了まで繰り返す「Ralph Wiggum」手法
- **serena**：言語サーバー連携で、コードの理解、リファクタリング提案、ナビゲーションを行う MCP サーバー
- **skill-creator**：スキルの作成、改善、性能測定
- **sourcegraph**：コード検索、参照の追跡、リファクタリングの影響分析
- **superpowers**：ブレインストーミング、サブエージェント開発、体系的なデバッグ、TDD を教える

**AWS（9個）**

- **aws-agents**：AWS 上で AI エージェントを構築、デプロイ、運用するスキル（Bedrock AgentCore など）
- **aws-agents-for-devsecops**：AWS の DevOps / セキュリティエージェントで、障害調査、脆弱性スキャン、ペネトレーションテストを実施
- **aws-amplify**：AWS Amplify Gen 2 でフルスタックアプリを作る手順（認証、データ、ストレージ、API、Lambda）
- **aws-core**：AWS 上のアプリ開発、デプロイ、運用。IaC の作成や基本サービスの利用
- **aws-data-analytics**：S3 Tables、Glue、Athena を使ったデータレイク、分析、ETL
- **aws-serverless**：AWS のサーバーレスアプリの設計、構築、デプロイ、テスト、デバッグ
- **aws-startup-advisor**：スタートアップ向けの AWS 構成、コスト、セキュリティの助言
- **migration-to-aws**：Google Cloud などから AWS への移行を、コードと請求データから計画
- **sagemaker-ai**：Amazon SageMaker AI で、AI モデルを構築、学習、デプロイ

**決済（8個）**

- **airwallex-dev**：Airwallex の決済連携（チェックアウト、カード入力、請求）のコードを生成
- **circle-skills**：USDC 決済、クロスチェーン送金、ウォレット、スマートコントラクトのスキル
- **mercadopago**：Mercado Pago の決済連携ツールキット
- **paypal**：PayPal の決済、定期課金、請求書、紛争対応の連携
- **rc**：RevenueCat のプロジェクト、商品、オファリングを Claude Code から設定
- **revenuecat**：RevenueCat のプロジェクト、商品、オファリングを Claude Code から設定
- **stripe**：Stripe 開発用プラグイン
- **sumup**：SumUp の決済連携（カードリーダー、オンライン決済）

**SAP・Oracle・業務基盤（15個）**

- **agentforce-adlc**：Agentforce エージェントの作成からデプロイ、テスト、最適化までの開発ライフサイクルを支援
- **cds-mcp**：SAP CAP プロジェクトの開発支援。CDS モデルとドキュメントを検索
- **forge-skills**：Atlassian Forge のアプリ作成、デプロイ、Rovo 向けコネクタの構築
- **netsuite-suitecloud**：NetSuite SuiteCloud の開発（SuiteScript、SDF など）
- **oracle-ai-data-platform-workbench-databricks-migrator**：Databricks から Oracle AI Data Platform への移行を自然言語で実行
- **oracle-ai-data-platform-workbench-engineer-agent**：Oracle AI Data Platform の Spark / Delta レイクハウスを自然言語で操作する、37 スキルのエージェント
- **oracle-ai-data-platform-workbench-spark-connectors**：Oracle AI Data Platform 用の Spark コネクタ 18 種
- **salesforce-development**：Salesforce のアプリとエージェント開発（メタデータ、Apex、デプロイなど）
- **sap-cds-mcp**：SAP CAP プロジェクトの開発支援（cds-mcp と同系統）
- **sap-fiori-mcp-server**：SAP Fiori アプリの開発、変更を支援する MCP サーバー
- **sap-mdk-server**：SAP Mobile Development Kit のアプリ開発を支援する MCP サーバー
- **servicenow-sdk**：ServiceNow アプリを Fluent SDK で作成、編集、デプロイ
- **ui5**：SAPUI5 / OpenUI5 のプロジェクト作成、検証、API ドキュメント、リンター
- **ui5-modernization**：SAPUI5 / OpenUI5 アプリの近代化ツールキット
- **ui5-typescript-conversion**：UI5 プロジェクトを JavaScript から TypeScript に変換

**AI・データ（25個）**

- **amd-skills**：AMD の検証済みスキル集。Ryzen AI でのローカル AI 実行や、Instinct GPU での LLM 提供など
- **astronomer-data-agents**：Apache Airflow と Astronomer 向けのデータエンジニアリング。DAG 作成、障害調査、リネージ追跡など
- **atomic-agents**：Atomic Agents フレームワークで AI エージェントを作るための開発ワークフロー
- **boltz**：Boltz による構造予測、分子やタンパク質のスクリーニング、バインダー設計
- **codspeed**：CodSpeed のベンチマーク、フレームグラフ、性能比較を Claude に渡す
- **confidence**：Confidence のフィーチャーフラグ、実験、移行ツールを Claude Code から利用
- **data**：Airflow と Astronomer 向けのデータエンジニアリング（astronomer-data-agents と同系統）
- **data-agent-kit**：Google Cloud のデータエンジニア向けスキル集
- **datarobot-agent-skills**：DataRobot の AI/ML ワークフロー（学習、デプロイ、予測、監視など）
- **deepeval**：AI アプリに DeepEval の評価、トレース、データセットを追加
- **dominodatalab**：Domino Data Lab の機能（ワークスペース、ジョブ、モデルのデプロイ、実験追跡など）
- **firecrawl**：Firecrawl で Web をスクレイピング、クロールして、Markdown や構造化データに変換
- **huggingface-skills**：オープンソースの AI モデル、データセット、Spaces を使う、学習、評価する
- **idmp-plugin**：TDengine IDMP 向けのスキル（探索、スキーマ確認、安全な運用作業）
- **nvidia-skills**：GPU 高速化、CUDA、AI、ロボティクスなど、NVIDIA 関連のスキルを探す
- **outputai**：Output.ai のワークフロー開発ツールキット（専門エージェント 5 種とスキル）
- **pixeltable**：Pixeltable でマルチモーダル AI アプリを作る
- **pydantic-ai**：Pydantic AI の最新パターンと注意点を踏まえたコードを書く
- **rill**：Rill（BI プラットフォーム）のプロジェクト開発とクエリ
- **setup-agent-analytics**：コードベース内の AI エージェントに、Pendo Agent Analytics を組み込む
- **setup-mcp-agent-analytics**：MCP サーバーに、Pendo の SDK を組み込んで、ツール呼び出しを分析
- **snowflake-cortex-code**：Snowflake 関連の指示を Cortex Code に振り分けて実行
- **streaming-skills-plugin**：Kafka、Flink、Schema Registry など、ストリーミング開発のスキル
- **tavily**：Tavily の検索、抽出、クロール API でリアルタイムの Web データを使う
- **togetherai-skills**：Together AI の推論、学習、埋め込み、音声、動画、画像などのスキル

**CI/CD・インフラ（4個）**

- **buildkite**：Buildkite のパイプライン、移行、CLI、API を扱う公式スキル
- **mergify**：Mergify CLI でマージキュー、スタック PR、不安定なテストの管理など
- **teamcity-cli**：TeamCity の CI/CD を CLI で操作（ビルド、ログ、ジョブ、キュー）
- **terraform**：Terraform MCP サーバー。IaC の自動化と操作

**Web・アプリ開発（24個）**

- **apollo-skills**：Apollo GraphQL（Client、Server、Federation、Router など）向けのスキル集
- **appwrite**：Appwrite の SDK スキル、MCP サーバー、デプロイ用コマンド
- **base44**：Base44 のフルスタックアプリを CLI と SDK で作ってデプロイ
- **catalyst-by-zoho**：Zoho Catalyst（サーバーレスのクラウド基盤）の公式プラグイン
- **ckeditor**：CKEditor 5 を JavaScript プロジェクトに導入、設定、統合
- **expo**：Expo と React Native のアプリを作る、デプロイ、更新、デバッグする公式スキル
- **laravel-boost**：Laravel 開発支援の MCP サーバー（Artisan、Eloquent、ルーティングなど）
- **liquid-skills**：Shopify テーマ向けの Liquid の基礎、コーディング規約、アクセシビリティ
- **lovable**：Lovable のアプリを Claude Code から作成、改善、デプロイ、管理
- **mintlify**：Mintlify でドキュメントサイトを作る、MDX への変換
- **netlify-skills**：Netlify の機能（Functions、Blobs、フォーム、デプロイなど）のスキル集
- **postman**：Postman の設定、モック、CI での検証、エンドポイント監視
- **preset-cli-skills**：Preset の sup CLI を使う、シェル、スクリプト、CI/CD 向けスキル
- **qt-development-skills**：Qt の C++ / QML のコードレビュー、記述、ドキュメント化
- **quarkus-agent**：Quarkus アプリの作成、管理のための MCP サーバー
- **resend**：Resend でメールを送受信するためのスキル（API、CLI、React Email など）
- **sanity**：Sanity のコンテンツ操作、GROQ クエリ、スキーマ設計
- **scandit-sdk**：Scandit のバーコード読み取り、ID 取得の SDK を組み込むスキル
- **shopify-ai-toolkit**：Shopify 開発用の 18 スキル（ドキュメント検索、API スキーマ、コード検証など）
- **twilio-developer-kit**：Twilio の SMS、音声、WhatsApp などを使うときの手順書
- **unity**：Unity 公式プラグイン。ゲーム開発、収益化、性能最適化のスキル
- **unreal-engine-skills-for-claude-code**：MCP 経由で Unreal Editor を操作する（アクター、ブループリント、マテリアルなど）
- **wix**：Wix のサイトとアプリを作成、管理、デプロイ
- **zoom-plugin**：Zoom の API、SDK、Webhook、ボットの連携を計画、構築、デバッグ

### productivity（69個）

**Claude Code の補助（13個）**

- **claude-code-setup**：コードベースを分析して、Claude Code の自動化（フック、スキルなど）を提案
- **claude-md-management**：CLAUDE.md の品質確認、改善、学びの記録
- **code-review**：複数のエージェントで PR を自動レビューし、誤検知を減らす
- **code-simplifier**：最近変更したコードを、機能を保ったまま簡潔にするエージェント
- **coderabbit**：CodeRabbit による外部視点のコードレビュー（40 以上の静的解析を統合）
- **commit-commands**：コミット、プッシュ、PR 作成のコマンド
- **cwc-makers**：Code with Claude Makers の Cardputer を、1 コマンドでセットアップ
- **desktop-commander**：ターミナル、プロセス、ファイル操作の MCP サーバー（PDF、Excel なども対応）
- **hookify**：会話の傾向や指示から、望ましくない動作を防ぐフックを作る
- **pr-review-toolkit**：コメント、テスト、エラー処理、型設計などを見る PR レビュー用エージェント群
- **project-artifact**：プロジェクトの状況ページを作って、claude.ai 上で公開
- **receipts**：Claude Code で何をしたかをまとめる、個人向けの成果レポート
- **session-report**：Claude Code の使用量（トークン、キャッシュ、サブエージェントなど）の HTML レポートを作る

**開発・仕事のツール連携（20個）**

- **airtable**：Airtable をエージェントのデータベース、業務基盤として使う
- **asana**：Asana のタスクとプロジェクトを管理
- **atlassian**：Jira と Confluence の課題、ドキュメントを検索、作成
- **atlassian-twg-cli**：Atlassian の Teamwork Graph CLI。Jira、Confluence、Bitbucket の情報を横断して扱う
- **box**：Box のファイル検索、整理、共有、Box AI への質問
- **carbone-skill**：Carbone のテンプレート記法の公式リファレンス
- **circleback**：Circleback の会議、メール、予定を検索
- **discord**：Discord との連携ブリッジ（アクセス制御つき）
- **dropbox**：Dropbox のファイルを検索、整理、共有
- **exa**：Exa AI による Web 検索、深い調査、内容の抽出
- **github**：GitHub 公式 MCP サーバー。Issue、PR、リポジトリの管理
- **gitlab**：GitLab のリポジトリ、マージリクエスト、CI/CD、Issue の管理
- **imessage**：iMessage との連携ブリッジ（アクセス制御つき）
- **linear**：Linear の課題とプロジェクトを管理
- **notion**：Notion のページ、データベース、ナレッジを検索、更新
- **save-to-spotify**：音声エピソードを作って、Spotify に保存
- **slack**：Slack のメッセージ、チャンネル、スレッドを検索、参照
- **telegram**：Telegram との連携ブリッジ（アクセス制御つき）
- **youdotcom-agent-skills**：You.com による Web 検索、引用つきの調査、内容の抽出
- **zapier**：Zapier 経由で、8,000 以上のアプリを操作

**営業・マーケティング（18個）**

- **activecampaign**：ActiveCampaign のマーケティング自動化、CRM、メール配信を操作
- **amazon-selling-partner**：Amazon セラーセントラルと連携し、売上、在庫、出品状況を確認
- **apollo**：Apollo.io で見込み客の検索、情報補完、営業分析
- **clay**：Clay の CLI やテーブル、GTM データベースを操作
- **hubspot-sales**：HubSpot の営業業務（取り込み、優先順位づけなど）を Claude から実行
- **hunter**：業務用メールアドレスの検索と検証、企業情報の補完
- **intercom**：Intercom の会話、顧客サポートの傾向、連絡先を検索
- **leadfeeder**：サイト訪問者の情報から、見込み客を調べ、日次レポートを作る
- **lusha**：Lusha の B2B データで、見込み客リストを作る
- **monday-crm**：monday CRM を自然言語で操作（パイプライン作成、案件の要約など）
- **pendo-analytics**：Pendo のプロダクト分析（アカウント状況、機能の利用状況など）
- **pendo-guides**：Pendo のアプリ内ガイドを、HTML/CSS/JS で作る
- **pendo-orchestrate**：Pendo Orchestrate のメールジャーニーを作成、編集
- **shippo**：Shippo 経由で、配送業者の料金比較と出荷を行う
- **spotify-ads-api**：Spotify の広告キャンペーンを、自然言語で管理
- **vibe-prospecting**：B2B の企業、連絡先データを、検索、補完、書き出し
- **windsor-ai**：Windsor.ai 経由で、325 以上のビジネスデータを照会
- **zoominfo**：ZoomInfo で、企業と連絡先の検索、見込み客の補完

**金融・会計・法務（18個）**

- **airwallex-agentos**：Airwallex のアカウント操作を、自然言語で実行
- **blackrock-advisor-center-plugin**：金融アドバイザー向けの BlackRock のスキル（ポートフォリオ確認、ファンド分析など）
- **carta-cap-table**：Carta の持ち株表、ストックオプション、評価額などを照会
- **carta-crm**：Carta CRM の投資家、企業、案件を、会話で検索、更新
- **carta-investors**：Carta の投資家データ、ベンチマーク、規制報告を照会
- **chronograph-gp**：プライベートキャピタルの GP 向けに、ポートフォリオ監視と評価、分析
- **chronograph-lp**：プライベートキャピタルの LP 向けに、ポートフォリオ監視と分析
- **gc-ai**：GC AI の法務ナレッジベースで、文書のアップロードとレビュー
- **govtribe**：政府調達の調査、入札判断、競合分析
- **intuit-quickbooks**：QuickBooks の財務状況、損益、キャッシュフローの確認
- **legalzoom**：ビジネスや個人向けの法務ツール（契約書のリスク確認など）
- **linq-alpha**：LinqAlpha による財務リサーチ（業績、予想など）
- **netsuite-ai-companion**：NetSuite AI Connector を使う AI 向けの、ツール選択や出力の指針
- **netsuite-finance-analyst**：NetSuite のデータで、財務報告、決算、差異分析などを実施
- **pigment**：Pigment のモデル、指標、ボードを自然言語で作る
- **vanguard-advisor-tools**：金融専門家向けに、ファンドや ETF の調査と比較
- **wingspan**：Wingspan で支払う業務委託先の確認、支払い記録
- **zocks-advisor**：金融アドバイザー向けのスキル 7 種（顧客の傾向、離反リスクなど）

### database（39個）

- **aiven**：PostgreSQL、Kafka、OpenSearch などのマネージドサービスを展開
- **alloydb**：AlloyDB for PostgreSQL の作成、接続、操作
- **alloydb-omni**：AlloyDB Omni の作成、接続、操作
- **altimate-code**：dbt とウェアハウスの作業を、専用 CLI エージェントに任せる
- **azure-cosmos-db-assistant**：Azure Cosmos DB のデータモデル、クエリ最適化、性能改善
- **azure-sql-developer**：ローカルのコンテナで動く Azure SQL Database 向けのスキル
- **bigdata-com**：Bigdata.com による金融リサーチと分析
- **bigquery-data-analytics**：BigQuery のデータへの接続、クエリ、分析
- **clickhouse**：ClickHouse Cloud に接続して、スキーマ確認や読み取り専用の SQL を実行
- **clickhouse-best-practices**：ClickHouse のスキーマ設計、クエリ最適化、取り込みの 28 のルール
- **cloud-sql-mysql**：Cloud SQL for MySQL への接続と操作
- **cloud-sql-postgresql**：Cloud SQL for PostgreSQL の作成、接続、操作
- **cloud-sql-sqlserver**：Cloud SQL for SQL Server への接続
- **cockroachdb**：CockroachDB のクラスターに接続して、スキーマ確認や SQL の最適化
- **convex**：Convex 公式プラグイン（スキル、コード作成用サブエージェントなど）
- **databases-on-aws**：AWS のデータベース群に関する助言（スキーマ設計、クエリ、移行）
- **databricks**：Databricks の CLI、Apps、ジョブ、パイプラインなどのスキル
- **datahub-skills**：DataHub の開発と操作（カタログ検索、メタデータ補完、リネージ追跡など）
- **dataproc**：Dataproc のクラスターとジョブの管理
- **dataverse**：Microsoft Dataverse の構築、分析、管理
- **duckdb-skills**：DuckDB でデータファイルの読み取り、クエリ、ドキュメント検索
- **firebase**：Firebase の Firestore、認証、Functions、ホスティングなどを管理
- **firestore-native**：Firestore のデータベースとドキュメントへの接続と操作
- **informatica-for-claude-platform**：Informatica のカタログで、テーブルや用語を探す
- **knowledge-catalog**：データと AI の資産を探索、管理、監視、統制
- **looker**：Looker に接続して、LookML でデータを扱う
- **mongodb**：MongoDB 公式プラグイン。接続、データ探索、クエリ最適化
- **mongodb-atlas**：Atlas のマネージド MCP サーバー経由で、MongoDB Atlas に接続
- **neon**：Neon のプロジェクトとデータベースを管理
- **oracledb**：Oracle Database への接続、クエリ、操作
- **pinecone**：Pinecone のベクトルインデックスの管理と検索
- **planetscale**：PlanetScale の組織、データベース、ブランチ、スキーマを扱う MCP サーバー
- **qdrant-skills**：Qdrant のベクトル検索（スケーリング、性能、監視など）
- **redis-development**：Redis のデータ構造、ベクトル検索、キャッシュ、性能のベストプラクティス
- **sap-hana-cli**：SAP HANA の 150 以上のツール（クエリ、インポート、データ品質確認など）
- **spanner**：Spanner のデータを自然言語で操作
- **supabase**：Supabase のデータベース、認証、ストレージ、リアルタイムを操作
- **vsql-extension-builder**：VillageSQL（MySQL）の拡張機能を、7 段階で作る
- **zilliz**：Zilliz Cloud の管理（クラスター、スキーマ、ベクトル検索など 14 スキル）

### monitoring（22個）

- **amplitude**：Amplitude の計測、チャート分析、ダッシュボード作成
- **dash0**：Claude Code のセッションを、OpenTelemetry のトレースとして記録
- **datadog**：Datadog のログ、メトリクス、トレース、ダッシュボードを照会
- **dynatrace**：Dynatrace の DQL、監視、ログ分析、問題調査のスキル
- **fullstory**：Fullstory の行動分析とセッションリプレイを照会
- **grafana-assistant**：Grafana Assistant のアプリと CLI のスキル
- **grafana-cloud-mcp**：Grafana Cloud のホスト型 MCP サーバー
- **grafana-mcp**：Grafana のダッシュボード、データソース、アラート、インシデントを扱う MCP サーバー
- **honeycomb**：Honeycomb の可観測性（クエリ、障害調査、SLO など）
- **incident-io**：incident.io でインシデント対応、オンコール確認、振り返り
- **langfuse**：Langfuse（LLM のトレースとプロンプト管理）のスキル
- **langfuse-observability**：Claude Code のトレースを Langfuse に送る
- **logfire**：Python アプリに Logfire の可観測性を追加
- **logrocket**：LogRocket のセッションリプレイや指標を自然言語で照会
- **mlflow**：MLflow で AI エージェントのトレース、評価、改善
- **newrelic**：New Relic の APM、クラウドコスト、Kubernetes の調査
- **noibu**：ECサイトの顧客体験の問題と、収益への影響を確認
- **pagerduty**：PagerDuty のリスクスコアとインシデント照合で、コードの質と安全性を高める
- **posthog**：PostHog の分析、フィーチャーフラグ、実験、エラー追跡
- **rootly**：インシデント管理（デプロイの安全性、対応、オンコール、振り返り）
- **sentry**：Sentry のエラー報告、スタックトレース、Issue の検索
- **sentry-cli**：Sentry CLI を使うスキル

### security（18個）

- **42crunch-api-security-testing**：OpenAPI 仕様を監査して、API の脆弱性を検出
- **auth0**：Auth0 でログイン、SSO、MFA、アクセス制御を追加
- **claude-security**：自分のコードの脆弱性を、セッション内で詳しくスキャン
- **crowdsec**：CrowdSec の導入、設定、運用、デバッグ
- **crowdstrike-falcon-foundry**：CrowdStrike Falcon Foundry 向けの、セキュリティアプリ開発スキル
- **crowdstrike-falcon-fusion**：CrowdStrike Falcon Fusion のワークフローを作る、デプロイ、実行
- **duende-skills**：Duende の OAuth/OIDC、IdentityServer などの開発スキル
- **jfrog**：JFrog Platform（Artifactory、セキュリティ検出結果など）を使う
- **security-guidance**：Claude が書いたコードのセキュリティレビュー（パターン警告、差分レビューなど）
- **semgrep**：Semgrep で、脆弱性をリアルタイムに検出
- **sonarqube**：SonarQube のコード品質とセキュリティの規則を適用
- **sonatype-guide**：依存関係の脆弱性とサプライチェーンを分析
- **stackhawk-api**：StackHawk の API で、セキュリティ状況と検出結果を確認
- **stackhawk-hawkscan**：HawkScan（DAST）の設定、実行、結果の解釈
- **vanta**：Vanta のセキュリティとコンプライアンスの情報に接続
- **vanta-mcp-plugin**：Vanta のセキュリティとコンプライアンスの情報に接続（vanta と同系統）
- **workos**：WorkOS の AuthKit、SSO、Directory Sync、RBAC などのスキル
- **zscaler**：Zscaler のクラウドセキュリティ（ZPA、ZIA、ZDX など）を管理

### deployment（9個）

- **azure**：Azure MCP サーバーと専用スキルで、Azure に詳しくする
- **cloudflare**：Cloudflare の Workers、Durable Objects、Wrangler などのスキル
- **deploy-on-aws**：AWS へのデプロイ（構成の提案、コスト見積もり、IaC）
- **google-cloud-storage**：Google Cloud Storage のバケットとオブジェクトを管理
- **hostinger**：Hostinger のサービスを、デプロイ、管理、監視
- **railway**：Railway のアプリ、データベース、インフラをデプロイ、管理
- **render**：Render のアプリをデプロイ、デバッグ、監視
- **valtown**：Val Town で構築とデプロイ
- **vercel**：Vercel のデプロイ、ビルド状況、ログ、ドメインを管理

### design（8個）

- **adobe-for-creativity**：Adobe のクリエイティブ機能で、画像編集やデザインの自動化
- **canva**：Canva のデザインを作成、編集、レビュー、リサイズ
- **figma**：Figma のデザインファイルやデザイントークンを参照して、コードに変換
- **hyperframes**：HTML を書いて動画を書き出す（HeyGen）
- **miro**：Miro のボードを読み、図を作る
- **runway-api**：Runway の API で、動画、画像、音声を生成
- **superdesign**：Superdesign のキャンバスで、UI とマーケティング画像をデザイン
- **ui-theme-designer**：UI テーマデザイナー向けのスキル

### automation（3個）

- **browser-use**：Claude に実際のブラウザを持たせる
- **synthflow**：Synthflow の音声エージェントに接続して、通話を確認
- **zyte-web-data**：Zyte API による Web スクレイピングと Scrapy のスパイダー生成

### learning（3個）

- **explanatory-output-style**：実装の選択理由やコードの傾向を説明する出力スタイル
- **learn-with-coursera**：学びたいことに合わせて、Coursera の講座を提案
- **learning-output-style**：判断が必要な場面で、コードの記述を求める学習モード

### location（2個）

- **amazon-location-service**：Amazon Location Service で地図、場所検索、ルート検索を追加
- **mapbox**：Mapbox のスキルと MCP サーバーで、位置情報アプリを作る

### testing（2個）

- **growthbook**：GrowthBook のフィーチャーフラグと実験のスキル
- **playwright**：Microsoft 製のブラウザ自動化と E2E テスト用 MCP サーバー

### math（2個）

- **math-olympiad**：競技数学の問題を、反証を重ねる検証付きで解く
- **math-proof**：難しい数学の問題を解いて、proof.md に証明をまとめる

### migration（1個）

- **aws-transform**：コードベースの AWS への移行、近代化（.NET、COBOL、VMware など）

### その他（14個）

- **ai-plugins**：Endor Labs で、サプライチェーンのリスクをスキャン、修正
- **aikido**：Aikido による SAST、シークレット、IaC の脆弱性検出
- **atlan**：Atlan のデータカタログを、自然言語で検索、管理
- **brightdata-plugin**：Bright Data による Web スクレイピングと検索
- **build-with-wordpress**：WordPress のサイトとアプリを作る
- **cloudinary**：Cloudinary のメディアの管理、変換、最適化
- **data-engineering**：ウェアハウス探索、パイプライン作成、Airflow 連携
- **fastly-agent-toolkit**：Fastly の開発ツールとスキル
- **fiftyone**：データセットとコンピュータビジョンのモデルを作る
- **nightvision**：NightVision（DAST と API 探索）のスキル
- **nimble**：Nimble による Web の検索、抽出、クロール
- **postiz**：SNS の投稿予約、メディアのアップロード、分析（28 以上のプラットフォーム）
- **prisma**：Prisma の Postgres 管理、マイグレーション、SQL 実行
- **remember**：会話を要約して日次ログにまとめる、連続的な記憶

## 📝 まとめ

- 公式マーケットプレイスは、私の PC に最初から登録されていて、315個が載っていた
- `claude plugin details` で、入れた後の常時トークンが分かる。今回の3つは約46〜218トークンだった
- session-report は、直近7日分の使用量を約7秒で集計できた。HTML の生成は未確認
- hookify は、`rm -rf` だけを止めるルールが動いた。セッション内での発火は未確認
- commit-commands は、worktree の中でエラーなく1コミットを作れた。`claude -p` では認証エラーになった

入れる作業は1行で済みました。つまずいたのは、プラグインの中身ではなく、動かす環境のほうです。

👉 次回は、code-review や security-guidance など、別のプラグインを試します。

※Windows 11 Pro、Claude Code 2.1.251 での検証結果です。プラグインの内容は更新されることがあります。数字は2026年10月26日時点のもので、導入は各プラグインの内容を確認したうえで、ご自身の責任でお願いします。
