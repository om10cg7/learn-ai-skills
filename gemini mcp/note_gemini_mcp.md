Claude Code で開発していると、すぐにトークンの制限がかかります。有料プランに入っているのに、作業の途中で止まるのはつらいところです。

そこで、ソースを書く作業を Gemini に任せる構成を試しました。この記事では、MCP サーバー「gemini-mcp-tool」を Claude Code に追加する手順と、Windows でハマった点をまとめます。Claude Code を使っていて、制限に困っている人向けです。

## 🤔 なぜ Gemini に書かせようと思ったか

私は Claude と Gemini の両方の有料プランに入っています。使い分けは次の通りです。

- Claude：プログラム開発
- Gemini：調べ物や文章など、一般的な用途

困っているのは Claude 側です。開発では、コードの読み込み、修正、実行、エラーの確認と、やり取りが何往復も続きます。そのぶんトークンの消費が早く、作業の途中で制限にかかります。

一方の Gemini は、一般的な用途にしか使っていないので、枠がほとんど余っています。それならソースを書く部分は Gemini に任せて、Claude は指示と確認に回せばいいのではないか。これが今回試した理由です。

Claude Code から Gemini を呼べるようにするのが、MCP サーバーの gemini-mcp-tool です。

## 🛠 gemini-mcp-tool とは？

npm で配布されている MCP サーバーで、インストール作業はほぼ要りません。

提供されるツールは4つです。

- `ask-gemini`：ファイルや質問を Gemini に投げる。コードを書かせるのはこれ
- `sandbox-test`：コードをサンドボックスで実行して確かめる
- `Ping`：接続確認
- `Help`：CLI 情報の表示

ファイルは `@src/main.js` のように `@` で指定して渡します。ディレクトリ全体なら `@.` です。

> 2026年10月時点の GitHub の README に基づきます。Gemini CLI は2026年6月18日に提供終了になっていて、バックエンドは Antigravity CLI（`agy`）に切り替わっています。ネットの古い記事は Gemini CLI 前提のものが多いので注意してください。

## 🚀 導入手順

### 環境

- OS：Windows 11
- Node.js：v24.18.0 / npm 11.16.0
- Claude Code：2.1.251

### 1. MCP を追加する

次のコマンドで、ユーザー全体（`-s user`）の設定に追加します。

```bash
claude mcp add -s user --transport stdio gemini -- npx -y gemini-mcp-tool
```

`-s user` を付けると、どのプロジェクトでも使えます。特定のプロジェクトだけで使うなら `-s project` にします。

### 2. 追加できたか確認する

```bash
claude mcp list
```

次のように表示されれば成功です。

```
gemini: npx -y gemini-mcp-tool - √ Connected
```

### 3. バックエンドの CLI を入れてサインインする

README によると、Antigravity CLI（`agy`）をインストールして、一度サインインしておく必要があります。`Connected` と出ても、これが無いと Gemini は動きません。MCP サーバー自体は起動できているだけだからです。

Windows のインストールは、公式ドキュメントにある PowerShell の1行です。

```powershell
irm https://antigravity.google/cli/install.ps1 | iex
```

途中で `ERROR: logging before google.Init` と赤字が出ますが、中身は Info ログで失敗ではありません。最後に `binary placed successfully` と出れば成功です。

ただし、インストール直後は開いているターミナルに PATH が反映されず、`agy` が見つからないと言われます。ターミナルを開き直せば通ります。Claude のデスクトップアプリも、再起動するまで古い PATH のままでした。

その後、新しいターミナルで `agy` を起動し、Google アカウントでサインインします。私の環境では Google AI Pro のアカウントで利用でき、初期モデルは Gemini 3.8 Flash (High) でした。

## ⚠️ ハマったところ

### PowerShell だと `-y` が怒られる

PowerShell でそのまま実行したら、こうなりました。

```
error: unknown option '-y'
```

原因は `--` が PowerShell に解釈されて、claude コマンドに届いていなかったことです（Windows PowerShell 5.1 で確認）。

`--` は「ここから先は起動するコマンドの引数」という区切りです。これが消えると、`-y` が claude mcp add のオプション扱いになります。

対処は cmd 経由で実行することでした。

```bash
cmd /c "claude mcp add -s user --transport stdio gemini -- npx -y gemini-mcp-tool"
```

Git Bash で実行する方法でも通るはずですが、こちらは試していません（未検証）。

### Connected でも使えるとは限らない

`claude mcp list` の `Connected` は、MCP サーバーのプロセスが起動して応答したという意味です。Gemini 側の認証まで見ているわけではありません。最初に `Ping` で疎通を、次に小さな `ask-gemini` で実際に返事が来るかを確認するのが安全です。

## 💻 Gemini にプログラムを書かせる

まず `Ping` を呼びました。これはサーバーの応答確認なので、返ってきても Gemini に届いたとは限りません。次に `ask-gemini` で、小さな関数を書かせました。

```
Pythonで、CSVファイルのパスを受け取り、各列の平均値を辞書で返す関数 column_means(path) を書いてください。標準ライブラリのみ使用、数値でない列は無視、コードのみ出力してください。
```

返ってきたのは、`csv.DictReader` で読み込み、列ごとに `float` へ変換できるかを見て、変換できない値が1つでもある列を除外するコードでした。

```python
import csv

def column_means(path):
    with open(path, mode='r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return {}

        col_values = {field: [] for field in reader.fieldnames}
        for row in reader:
            for k in reader.fieldnames:
                col_values[k].append(row.get(k))

    result = {}
    for col, vals in col_values.items():
        nums = []
        is_numeric = True
        for v in vals:
            if v is None or v.strip() == '':
                continue
            try:
                nums.append(float(v))
            except ValueError:
                is_numeric = False
                break
        if is_numeric and nums:
            result[col] = sum(nums) / len(nums)

    return result
```

Claude が次のテスト用 CSV で実行して確認しました。

```
name,price,qty,note
A,100,2,x
B,200,,y
C,300,4,1
```

結果は `{'price': 200.0, 'qty': 3.0}` でした。文字だけの `name` と、数値と文字が混ざった `note` は除外され、`qty` の空欄は平均の計算から外れています。意図どおりの動きです。

なお、ツールの説明には既定モデルが `gemini-2.5-pro` と書かれていますが、バックエンドが `agy` に切り替わっているため、実際にどのモデルが答えたかは確認できていません。

役割分担は、Gemini が実装の下書きを書き、Claude が実行して確かめる形です。

ただし、今回は小さな関数1つだけです。Claude のトークン消費がどれだけ減ったかは、まだ測っていないので言えません。

## 📝 まとめ

- 追加は1コマンド。ただし Windows の PowerShell では `--` が消えるので cmd 経由にする
- `Connected` はサーバーが起動しただけ。Gemini 側のサインインが別途必要
- 古い記事の Gemini CLI 前提の手順は、いまはそのまま通らない可能性が高い
- `agy` を入れてサインインし、アプリを再起動すれば、`ask-gemini` で実際にコードが返ってきた

👉 次回は、既存のプロジェクトを `@` で渡して、もっと大きな実装を任せます。Claude のトークン消費が実際に減るかも見てみます。

---
※動作確認は Windows 11 / Google AI Pro アカウントでの結果です。無料アカウントで使えるかは確認していません。
