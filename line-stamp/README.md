# line-stamp

AI で作ったイラストを、LINE スタンプにして販売するまでの制作物と、note 記事の元データです。

- 静止画のスタンプ 16 枚（2026-11-11 に販売開始）
- 動くスタンプ 8 個（2026-11-13 に審査をリクエスト）

進捗、決定事項、作業ログは、Obsidian の Vault（`projects/line-stamp/`）にあります。

## フォルダ

```text
raw/        元のイラストのシート（AI で生成した画像）
tools/      切り出し・透過・白フチ・リサイズ、規格の検査
build/      静止画 16 枚の出力と、確認用の一覧
submit-16/  静止画の申請用 16 枚と main.png、tab.png
anim/       動くスタンプ（raw/ が元の画像、submit-8/ が申請用）
article/    note 記事の原稿とメモ、手順のスクリーンショット
prompts/    制作の記録（元画像のハッシュ、加工の手順）
```

## 静止画スタンプを作り直す

このフォルダで実行します。環境は Python 3.11、Pillow、numpy、scipy です。

```powershell
python tools/process.py
python tools/validate.py submit-16 --expect-count 16
```

## 公開しているもの

- 静止画スタンプ: https://line.me/S/sticker/37885826
- note の記事: https://note.com/om10cg72/n/n47cc37745ff8

## 注意

- 作り直せる ZIP（`*.zip`）は、Git に入れていません。
- `article/screenshots/` は、note の記事で使った画像だけを Git に入れています。
