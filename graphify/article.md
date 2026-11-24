自分のアプリのコードを Claude Code に読ませるたびに、grep やファイルの総当たりで、トークンも時間もかかるのが気になっていました。

この記事では、コードを知識グラフにする「Graphify」を入れて、自作のバスマップアプリ（194ファイル）を解析するところまでをまとめます。API キーは要らず、`Settings` クラスを変えたときの影響範囲を、grep なしで洗い出せました。

## 🤔 なぜ Graphify を試したいか

Claude Code に「この関数を変えると、どこに影響する？」と聞くと、まず grep とファイルの読み込みが何十回も走ります。結果が出る前に、時間とトークンが減っていきます。

Graphify は、コードを解析して、ファイル・関数・クラスのつながりをグラフにしてくれるツールです。そのグラフを先に見れば、読むべきファイルを絞れるはずだと考えました。

解析の対象は、自作の広島バスマップです。アプリ自体は、前に記事にしています。

https://note.com/om10cg72/n/n7f5c18dd7d46

今回は、Graphify の使い方を一通り試すことが目的です。成果物を作る記事ではなく、学習の記録です。

## 🛠 Graphify とは？

コードベースを解析して、知識グラフにするツールです。PyPI で公開されていて、`pip` か `uv` で入れます。

**解析でできること**
- コードの解析は、ローカルの tree-sitter（構文木）だけで行う。LLM を使わないので、API キーは要らない
- つながりが多いノード（神ノード）のランキングと、意外な依存を `GRAPH_REPORT.md` にまとめる
- `graph.html` で、コミュニティごとに色分けしたグラフを見られる
- Obsidian 用のノートを出力できる

**グラフを調べるコマンド**
- `graphify explain "名前"`：ノードとつながりの説明
- `graphify path "A" "B"`：2つのノードの最短経路

この節は、`graphify --help` の表示と、解説記事に基づきます。バージョンは 0.9.101 です。

注意点が1つあります。パッケージ名は `graphifyy`（末尾の y が 2 つ）で、実行コマンドは `graphify`（y が 1 つ）です。間違えやすいので、気をつけてください。

## 🚀 導入手順

**環境**

- OS：Windows 11 Pro
- Claude Code：2.1.251
- uv：0.12.23
- Python：3.11.9
- Graphify：0.9.101

**1. Graphify を入れる**

```powershell
uv tool install graphifyy
graphify --version
```

「graphify 0.9.101」と出れば成功です。実行ファイルは `graphify` と `graphify-mcp` の2つが入りました。

**2. Claude Code にスキルを登録する**

```powershell
graphify install
```

`~/.claude/skills/graphify/` にスキルが作られ、Claude Code で `/graphify` が使えるようになります。

**3. プロジェクトを解析する**

解説記事では、Claude Code の中で `/graphify . --code-only --obsidian` を打つ方法が紹介されています。今回は、同じ解析を CLI から実行しました。

```powershell
cd （プロジェクトのフォルダ）
graphify update .
graphify export obsidian --dir graphify-out/obsidian
```

`graphify update .` が、コードだけを解析するコマンドです。`.gitignore` に書いてある `.venv` や `.env` は、対象から外れました。

スキル経由の `/graphify` は、まだ試していません。

## ⚠️ ハマったところ

**グローバルの CLAUDE.md に、3行が足されていた**

`graphify install` は、スキルを作るだけではありませんでした。`~/.claude/CLAUDE.md` の末尾にも、次のような3行を自動で書き足していました。

```markdown
# graphify
- **graphify** (`~/.claude/skills/graphify/SKILL.md`) - any input to knowledge graph. Trigger: `/graphify`
When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.
```

既存の記述は変わっていませんでした。ただ、グローバル設定に触られるので、インストールのあとに中身を見ておくことをおすすめします。

**経路を調べると「経路なし」になる**

`graphify path "Settings" "create_web_app()"` を実行すると、こう出ました。

```text
No directed path found between 'Settings' and 'create_web_app()'. Re-run with --undirected to search ignoring edge direction.
```

原因は、辺の向きです。このグラフでは、依存する側から `Settings` へ向かう向きで辺が張られています。`Settings` から `create_web_app()` へ向かう経路は、ありません。

`--undirected` を付けるか、始点と終点を逆にすれば、経路が見つかるはずです。ここは、出力のメッセージに従っただけで、付け直しての実行は試していません。

**SQL ファイルが解析されなかった**

SQL ファイル2つは、グラフに入りませんでした。SQL を解析するパッケージ（`tree_sitter_sql`）が入っていない、という警告が出ました。ほかに、シンボルがゼロだったファイルが6つあります。

## 💻 実際に解析してみる

**結果を見る**

対象は194ファイルで、解析は API を使わずに終わりました。

- ノード：3,904、エッジ：8,376、コミュニティ：215
- エッジの91%は、コードから直接読み取ったもの（EXTRACTED）
- 残りの9%（756本）は推論したもの（INFERRED）。平均の確信度は0.92
- 出力：`GRAPH_REPORT.md`、`graph.html`、`graph.json`、Obsidian 用の4,119ノートと `graph.canvas`

`graph.html` は、PC の既定のブラウザで開きました。アプリ内のブラウザでは、ローカルのファイルを開けませんでした。

**神ノードを見る**

`GRAPH_REPORT.md` の神ノードの上位5つです。

1. `Settings`（117エッジ）：設定クラス
2. `未決事項`（91）：設計書の項目
3. `standard()`（77）
4. `create_web_app()`（74）
5. `page()`（71）

設定を持つ `Settings` が1位でした。自分でも「いろんな所から参照されている」と思っていた場所なので、納得です。

2位の `未決事項` は、コードではなく設計書の見出しです。`docs/` の Markdown も、見出しなどの構造がノードに入っていました。コードの核を探すときには、ノイズになります。

「意外なつながり」の欄では、設計書の見出しと、対応するコードがつながっていました。たとえば、設計書の「新しい設定値（`Settings` に足す）」の節が、コードの `Settings` につながっています。

**Settings を変えたら何に影響するか**

次のコマンドで、`Settings` の影響範囲を調べました。

```powershell
graphify explain "Settings"
```

grep も、ソースの読み込みもしていません。出力は117本の接続で、ファイルごとにまとめると、こうなりました。

- 本体コード：`web.py`（`create_web_app()`）、`worker.py`（`Worker`）、`bootstrap.py`、`db.py`、`static_updater.py`、`testing.py`
- テスト：10ファイル前後。設定の既定値を直接調べるテストは、最初に確認したい
- ドキュメント：設計書の `regions.md`

この調査は、Claude Code に頼んだのではなく、私が `graphify` のコマンドを直接実行したものです。「Claude Code が grep に戻らずに、グラフを使うか」は、まだ確かめていません。

推論（INFERRED）の辺は、確信度が0.95でも推測です。実際にコードを変えるときは、ソースで確かめます。

## 📝 まとめ

- `uv tool install graphifyy` で入り、コマンド名は `graphify`（y が 1 つ）です
- `graphify install` は、グローバルの `CLAUDE.md` に3行を足します。入れたあとに中身を見ておくと安心です
- `graphify update .` は、API を使わずに、194ファイルを解析して3,904ノードのグラフを作りました
- 神ノードの1位は `Settings` で、`graphify explain` だけで影響範囲を洗い出せました
- 経路の検索は、辺の向きに注意が必要です。「経路なし」と出たら、`--undirected` を疑います

👉 次回は、Claude Code に影響調査を頼んで、grep に戻らないかを確かめます。

※ 2026年11月時点、Windows 11 で確認しました。Graphify は 0.9.101 です。解析に使ったアプリは自作のものです。Obsidian での表示と、`graphify hook install` は、まだ試していません。
