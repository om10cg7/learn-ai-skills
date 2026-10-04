#!/usr/bin/env python3
"""note向けマークダウンを、noteエディタに貼れるHTMLに変換する。

使い方:
  python md2note_html.py article.md --body-out body.html \
      [--page-out note貼り付け用.html --title "タイトル" --tags "a,b,c"]

note特有の制約:
  - 見出しは h2 / h3 のみ
  - 引用ブロックは1段落しか入らない → 引用内の複数行は <br> で1段落にまとめる
  - 引用内の箇条書き（- ）は「・」に置き換える
  - URLだけの行は、リンク段落にする（noteがカード化する）
"""
import argparse
import html
import re


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', r'<a href="\2">\1</a>', s)
    return s


def quote_block(lines):
    parts = []
    for l in lines:
        l = re.sub(r'^> ?', '', l).strip()
        if not l:
            continue
        l = re.sub(r'^- ', '・', l)
        parts.append(inline(l))
    return '<blockquote><p>' + '<br>'.join(parts) + '</p></blockquote>'


def blocks(lines):
    out = []
    i = 0
    while i < len(lines):
        l = lines[i]
        if not l.strip():
            i += 1
            continue
        if l.startswith('```'):
            j = i + 1
            code = []
            while j < len(lines) and not lines[j].startswith('```'):
                code.append(lines[j])
                j += 1
            out.append('<pre><code>' + html.escape('\n'.join(code), quote=False) + '</code></pre>')
            i = j + 1
            continue
        if l.startswith('### '):
            out.append('<h3>' + inline(l[4:]) + '</h3>')
            i += 1
            continue
        if l.startswith('## '):
            out.append('<h2>' + inline(l[3:]) + '</h2>')
            i += 1
            continue
        if l.startswith('>'):
            q = []
            while i < len(lines) and lines[i].startswith('>'):
                q.append(lines[i])
                i += 1
            out.append(quote_block(q))
            continue
        if re.match(r'^- ', l):
            items = []
            while i < len(lines) and re.match(r'^- ', lines[i]):
                items.append('<li>' + inline(lines[i][2:]) + '</li>')
                i += 1
            out.append('<ul>' + ''.join(items) + '</ul>')
            continue
        if re.match(r'^\d+\. ', l):
            items = []
            while i < len(lines) and re.match(r'^\d+\. ', lines[i]):
                items.append('<li>' + inline(re.sub(r'^\d+\. ', '', lines[i])) + '</li>')
                i += 1
            out.append('<ol>' + ''.join(items) + '</ol>')
            continue
        if re.match(r'^https?://\S+$', l.strip()):
            u = l.strip()
            out.append(f'<p><a href="{u}">{u}</a></p>')
            i += 1
            continue
        p = [l]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r'^(#|```|>|- |\d+\. |https?://)', lines[i]):
            p.append(lines[i])
            i += 1
        out.append('<p>' + '<br>'.join(inline(x) for x in p) + '</p>')
    return out


PAGE = '''<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>note貼り付け用</title>
<style>
body{{font-family:"Yu Gothic",Meiryo,sans-serif;max-width:760px;margin:24px auto;padding:0 16px;line-height:1.9;color:#222}}
.panel{{background:#f4f6f8;border:1px solid #d8dde2;border-radius:8px;padding:12px 16px;margin-bottom:20px}}
.panel h4{{margin:0 0 6px;font-size:14px}}
button{{font-size:14px;padding:6px 14px;border:1px solid #888;border-radius:6px;background:#fff;cursor:pointer;margin-right:6px}}
#msg{{color:#0a7d33;font-size:13px;margin-left:6px}}
pre{{background:#f6f8fa;padding:12px;overflow-x:auto;border-radius:6px}}
blockquote{{border-left:4px solid #ccc;margin-left:0;padding-left:14px;color:#444}}
</style>
</head>
<body>
<div class="panel"><h4>1. タイトル</h4><div id="title">{title}</div>
<p><button onclick="copyText('title')">タイトルをコピー</button><span id="msg"></span></p></div>
<div class="panel"><h4>2. 本文</h4>
<p><button onclick="copyRich('article')">本文をコピー</button> 下の本文を範囲選択してコピーしても同じです。</p></div>
<div class="panel"><h4>3. ハッシュタグ</h4><div id="tags">{tags}</div>
<p><button onclick="copyText('tags')">タグをコピー</button></p></div>
<hr>
<div id="article">
{body}
</div>
<script>
function done(m){{var e=document.getElementById('msg');e.textContent=m;setTimeout(function(){{e.textContent=''}},2500)}}
function copyText(id){{navigator.clipboard.writeText(document.getElementById(id).innerText).then(function(){{done('コピーしました')}})}}
function copyRich(id){{var el=document.getElementById(id);var r=document.createRange();r.selectNodeContents(el);var s=getSelection();s.removeAllRanges();s.addRange(r);var ok=document.execCommand('copy');s.removeAllRanges();done(ok?'本文をコピーしました':'失敗。範囲選択してCtrl+Cしてください')}}
</script>
</body>
</html>
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('--body-out', required=True)
    ap.add_argument('--page-out')
    ap.add_argument('--title', default='')
    ap.add_argument('--tags', default='')
    a = ap.parse_args()

    body = '\n'.join(blocks(open(a.src, encoding='utf-8').read().split('\n')))
    open(a.body_out, 'w', encoding='utf-8').write(body)
    if a.page_out:
        tags = ' '.join('#' + t.strip() for t in a.tags.split(',') if t.strip())
        page = PAGE.format(title=html.escape(a.title), tags=html.escape(tags), body=body)
        open(a.page_out, 'w', encoding='utf-8').write(page)
    print('body:', len(body), 'chars',
          '| h2', body.count('<h2>'), '| h3', body.count('<h3>'),
          '| pre', body.count('<pre>'), '| blockquote', body.count('<blockquote>'))


if __name__ == '__main__':
    main()
