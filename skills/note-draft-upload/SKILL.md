---
name: note-draft-upload
description: 書き上がったnote記事（article.md）を、note.comの下書きに入れるところまで行う。タイトル入力、本文の貼り付け（見出し・コードブロック・引用を保つ）、見出し画像のアップロード、下書き保存、保存後の検証まで。「noteに下書き保存して」「noteに入れて」「見出し画像を入れて」と言われたときに使う。記事を書く工程は anthropic-skills:note-article と note-tech-article の担当で、このスキルはその後工程。公開は絶対にしない。
---

# note 下書きアップロード

書き上がった `article.md` を note の下書きに入れる。公開はしない。

記事の執筆は `anthropic-skills:note-article`（書式ルールとリンター）と `note-tech-article`（リポジトリで裏取り）の担当。先にそちらで原稿を仕上げ、このスキルはその続きで使う。

## 守ること

- **「公開に進む」ボタンには触れない。** 公開、ハッシュタグ入力、有料設定はユーザー本人がやる。
- ログインやパスワードの入力はしない。未ログインなら、ユーザーにログインを頼んで待つ。
- 各操作は、ボタンの座標ではなく要素の参照（ref）で押す。作業中にウィンドウの大きさが変わり、座標がずれたことがある。
- 「変更が保存されていません」の確認が出たら、`force` で消さない。先に「下書き保存」を押す。

## 準備するもの

- `article.md`（1行目に `# タイトル` を書かない原稿）
- タイトル文字列
- 見出し画像のパス（任意。無ければ下の「見出し画像を探す」）

## 手順

### 1. 原稿を検査する

`anthropic-skills:note-article` の `scripts/check_note.py` を実行する。エラーが出たら直してから進む。警告（見出し数など）は、ユーザーの過去記事と照らして判断する。

### 2. HTMLに変換する

```bash
python scripts/md2note_html.py article.md --body-out body.html --page-out note貼り付け用.html --title "タイトル" --tags "タグ1,タグ2"
```

- `body.html` は貼り付け用の本文。
- `note貼り付け用.html` は、ユーザーが手で貼るときのコピー用ページ（任意）。
- note の引用ブロックは1段落しか入らない。変換は、引用内の複数行を1段落にまとめ、箇条書きは「・」にする。この処理を手で直さない。

### 3. 下書きを開いてタイトルを入れる

ブラウザは、ユーザー本人のChrome（Claude in Chrome）を優先する。組み込みブラウザは、noteに未ログインのことがある。

1. `https://note.com/notes/new` を開く。ログイン画面なら、ユーザーに頼む。
2. 編集画面（`editor.note.com/notes/<id>/edit/`）が出たら、タイトル欄をクリックして入力する。
3. このときのURLの `<id>` を控える。下書きのIDになる。

### 4. 本文を貼り付ける

```bash
python scripts/make_paste_js.py body.html > paste.js
```

`paste.js` の中身を、ページのJavaScript実行ツールで実行する。本文の `.ProseMirror` を全選択して、貼り付けのイベントを送る。何度実行しても重複しない。

戻り値の `expected` と `actual` を比べる。見出し(h2/h3)、コードブロック(pre)、引用(blockquote)の数が一致すれば成功。

### 5. 見出し画像を入れる

`references/eyecatch_upload.md` に従う。要点は、ファイル選択画面を開かずに、入力欄へファイルを渡すこと。

画像が無い場合は、`references/image_source.md` の場所から探す。AI生成の画像なら、`scripts/c2pa_check.py` で来歴を調べ、結果をユーザーに伝える。

### 6. 保存して検証する

1. 「下書き保存」を押す。
2. **別のブラウザ（または別タブ）で同じ下書きを開き直して**確かめる。保存の表示だけでは信用しない。
   - 見出し画像が、1280×670で登録されているか
   - 見出し・コードブロックの数が、手順4の値と同じか
3. 一致しなければ、原因を調べて、もう一度保存する。

### 7. 報告する

次を一覧で渡す。

- 下書きのURL
- 確認した数字（見出し、コードブロック、画像サイズ）
- ユーザーが手でやること: ハッシュタグ、AI生成の表示の要否、プレビューの確認、公開

## 参照

- `references/eyecatch_upload.md` — 見出し画像を入れる手順
- `references/image_source.md` — 見出し画像の保存場所（環境ごとの設定）
- `references/gotchas.md` — 今までの失敗と回避策
- `scripts/md2note_html.py` — マークダウンをnote向けHTMLに変換
- `scripts/make_paste_js.py` — 貼り付け用JavaScriptを作る
- `scripts/c2pa_check.py` — 画像の来歴（AI生成の記録）を調べる
