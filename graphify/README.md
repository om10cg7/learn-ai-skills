# Graphify 学習ノート

Graphify × Claude Code × Obsidian 実践導入ガイド。
Graphify をローカルに導入し、Claude Code のトークン消費を抑えながらプロジェクト全体の構造を把握・操作する手順。

このフォルダは Graphify の勉強だけに使う。

## 1. インストール

PyPI 上のパッケージ名は `graphifyy`（末尾の y が 2 つ）、実行コマンド名は `graphify`（y が 1 つ）。

```bash
# uv（推奨: 依存関係が孤立し、PATH も自動管理）
uv tool install graphifyy

# pip
pip install graphifyy
```

```bash
graphify --version
```

## 2. Claude Code へのスキル登録

```bash
graphify install
```

`~/.claude/skills/` 配下に Graphify のスキル定義（`SKILL.md` など）が生成され、`/graphify` が使えるようになる。

## 3. プロジェクトの知識グラフ化（+ Obsidian 出力）

```bash
cd /path/to/your-project
claude
```

Claude Code で次を入力する。

```text
/graphify . --code-only --obsidian
```

- `--code-only`: ローカルの tree-sitter（抽象構文木）だけで解析する。API トークン消費は 0 で、数秒で終わる
- `--obsidian`: 解析結果を `[[Wikiリンク]]` 付きの Markdown 群として出力する
- 設計書（Markdown や PDF）も意味解析させたい場合は `--code-only` を外し、`/graphify . --obsidian` を実行する

実行後、プロジェクト直下に `graphify-out/` が生成される。

## 4. 便利さを確かめる 3 ステップ

### ① 急所を一発で把握

`graphify-out/GRAPH_REPORT.md` を開く。

- God nodes（神ノード）: 最も多くのモジュールから依存されている、変更時の影響が大きいコア機能のランキング
- Surprising connections（意外なつながり）: 直感では見落としがちなモジュール間の隠れた依存パス

### ② ブラウザと Obsidian で俯瞰

- `graphify-out/graph.html` をブラウザで開くと、コミュニティごとに色分けされた全体マップを見られる
- Obsidian で `graphify-out/`（またはその中の Wiki フォルダ）を Vault として開く。既存の Vault に取り込んでもよい。グラフビューで自分のメモとコード構造をリンクさせられる

### ③ 生ファイルを読ませずに影響調査

```text
graphifyのグラフを使って、[クラス名/関数名] を変更した際の影響範囲と呼び出し経路（path）を特定して。
不要な生ファイルのRead/Grepは最小限に抑えて回答して。
```

`grep` や総当たりのファイルオープンが発生せず、`graph.json` の経路解析と必要最小限のファイルだけで答えるため、トークン消費と応答時間が減る。

## 5. 日常運用の自動化

### コミット時の自動差分更新

```bash
graphify hook install
```

Git Hook が登録され、コミット時に差分だけを再解析（`graphify update .`）する。

### CLAUDE.md への探索ルール追加

プロジェクトの `CLAUDE.md` に追記すると、Claude Code が grep や総当たり探索に戻るのを防げる。

```markdown
## コードベース探索ルール
- 全体構造の把握や影響範囲の調査を行う際は、初手で Grep や Read を多用しないこと。
- 必ず先に `graphify-out/graph.json` または Graphify のクエリツールを参照し、対象の依存経路を絞り込んでから該当ファイルのみを開くこと。
```

## 学習メモ

（試した結果・気づきをここに書く）
