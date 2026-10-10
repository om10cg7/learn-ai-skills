"""note貼り付け用.html のコピー用スクリプトを、clipboard API が使えない環境でも動くように差し替える。

md2note_html.py が作ったページの copyText は navigator.clipboard だけに頼っている。
https 以外（共有フォルダ、簡易ビューアなど）では navigator.clipboard が無く、タイトルとタグのコピーが失敗する。
そこで textarea と execCommand('copy') の予備経路を足す。
"""
import re
import sys
from pathlib import Path

NEW_JS = r"""function done(m){var e=document.getElementById('msg');e.textContent=m;setTimeout(function(){e.textContent=''},2500)}
function fallbackCopy(t){var a=document.createElement('textarea');a.value=t;a.setAttribute('readonly','');a.style.position='fixed';a.style.top='0';a.style.opacity='0';document.body.appendChild(a);a.select();var ok=false;try{ok=document.execCommand('copy')}catch(e){}document.body.removeChild(a);done(ok?'コピーしました':'失敗。範囲選択してCtrl+Cしてください')}
function copyText(id){var t=document.getElementById(id).innerText;if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t).then(function(){done('コピーしました')},function(){fallbackCopy(t)})}else{fallbackCopy(t)}}
function copyRich(id){var el=document.getElementById(id);var r=document.createRange();r.selectNodeContents(el);var s=getSelection();s.removeAllRanges();s.addRange(r);var ok=false;try{ok=document.execCommand('copy')}catch(e){}s.removeAllRanges();done(ok?'本文をコピーしました':'失敗。範囲選択してCtrl+Cしてください')}"""


def main(path: str) -> None:
    p = Path(path)
    html = p.read_text(encoding="utf-8")
    patched, n = re.subn(r"<script>.*?</script>", lambda m: "<script>\n" + NEW_JS + "\n</script>", html, count=1, flags=re.S)
    if n != 1:
        raise SystemExit("script タグが見つかりません")
    p.write_text(patched, encoding="utf-8")
    print("patched:", p)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "note貼り付け用.html")
