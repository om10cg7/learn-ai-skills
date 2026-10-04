#!/usr/bin/env python3
"""body.html から、noteエディタに貼り付けるJavaScriptを作って標準出力に出す。

使い方:
  python make_paste_js.py body.html > paste.js

出力のJSは、editor.note.com の編集画面で実行する。
  - 本文の .ProseMirror を全選択 → paste イベントで置き換える（何度実行しても重複しない）
  - 戻り値: { expected: {...}, actual: {...}, ok: true/false }
    expected は body.html の数、actual は編集欄に入った数
"""
import json
import re
import sys

body = open(sys.argv[1], encoding='utf-8').read()
expected = {
    'h2': len(re.findall(r'<h2>', body)),
    'h3': len(re.findall(r'<h3>', body)),
    'pre': len(re.findall(r'<pre>', body)),
    'blockquote': len(re.findall(r'<blockquote>', body)),
}

js = f"""const html = {json.dumps(body, ensure_ascii=False)};
const expected = {json.dumps(expected)};
const el = document.querySelector('.ProseMirror');
if (!el) throw new Error('本文エディタ(.ProseMirror)が見つかりません。編集画面を開いていますか');
el.focus();
document.execCommand('selectAll');
const dt = new DataTransfer();
dt.setData('text/html', html);
dt.setData('text/plain', html.replace(/<[^>]+>/g, ''));
el.dispatchEvent(new ClipboardEvent('paste', {{clipboardData: dt, bubbles: true, cancelable: true}}));
await new Promise(r => setTimeout(r, 500));
const actual = {{
  h2: el.querySelectorAll('h2').length,
  h3: el.querySelectorAll('h3').length,
  pre: el.querySelectorAll('pre').length,
  blockquote: el.querySelectorAll('blockquote').length,
}};
({{expected, actual, ok: JSON.stringify(expected) === JSON.stringify(actual)}})
"""
sys.stdout.write(js)
