# 見出し画像を下書きに入れる

note の見出し画像は、ファイル選択画面が開くボタン経由でしか入れられない。その画面は Claude からは操作できない。そこで、画面を開かせずに、入力欄へファイルを直接渡す。

使うもの: Claude in Chrome（ユーザー本人のChrome）。組み込みブラウザにはファイルを渡すツールが無い。

## 前提

- 画像は JPEG / PNG / WebP。推奨サイズは 1280×670（2:1）。
- 16:9 の画像（1376×768 など）でも入る。切り取り画面で上下が少し切れる。タイトル文字が上端に近い画像は、切り取り位置を確認する。
- 合計10MB未満。

## 手順

### 1. 画像の追加メニューを開く

編集画面の上、タイトルの上にある「画像を追加」ボタンを、`find` で見つけて ref で押す。メニューが出て、「画像をアップロード」「記事にあう画像を選ぶ」などが並ぶ。

### 2. ファイル選択画面が開かないように細工する

ファイル入力欄は、「画像をアップロード」を押した瞬間に作られる。何もしないと、見えない選択画面が開いて止まる。先に次のJSを実行する。

```javascript
if (!window.__patched) {
  const orig = HTMLInputElement.prototype.click;
  HTMLInputElement.prototype.click = function () {
    if (this.type === 'file') {
      this.setAttribute('aria-label', '見出し画像ファイル入力');
      this.style.cssText = 'display:block;position:fixed;top:60px;left:10px;width:220px;height:30px;opacity:1;z-index:99999;background:#fff';
      if (!this.isConnected) document.body.appendChild(this);
      window.__fi = this;
      return;
    }
    return orig.apply(this, arguments);
  };
  window.__patched = true;
}
```

### 3. 「画像をアップロード」を押す

`find` で「画像をアップロード」のボタンを探し、ref で押す。選択画面は開かず、入力欄が画面に現れる。

### 4. ファイルを渡す

`find` で「見出し画像ファイル入力」（file）を探し、`file_upload` で画像のパスを渡す。

- 入力欄の id は `note-editor-eyecatch-input`、accept は `image/jpeg,image/png,image/webp`。

### 5. 切り取り画面で保存する

数秒後に「画像のサイズの変更」ダイアログが出る。

- 薄暗い上下が、切り取られる部分。タイトル文字や主役が、明るい範囲に入っているか確認する。
- 「保存」ボタンは、アクセシビリティツリー上でラベルが付いていないことがある。`read_page` でダイアログ（`role=dialog`）の中を見て、ラベルの無いボタンのうち、「キャンセル」の次のものを押す。
- **座標クリックは使わない。** ダイアログの表示中にウィンドウの大きさが変わり、座標がずれたことがある。

### 6. 保存する

画像が上に表示されたら、「下書き保存」を押す。保存の確認は、別のブラウザで開き直して、見出し画像が 1280×670 で入っているかを見る。

## うまくいかないとき

- 入力欄が見つからない → 手順2を実行したか、手順3で「画像をアップロード」を押したかを確認する。
- 保存後に「変更が保存されていません」の確認が出る → 「下書き保存」をもう一度押す。強制移動はしない。
- ダイアログが閉じない → 上の「保存」ボタンの見つけ方を使う。
