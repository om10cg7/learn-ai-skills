#!/usr/bin/env python3
"""画像に埋め込まれた来歴情報（C2PA）から、AI生成の記録を調べる。

使い方:
  python c2pa_check.py 見出し画像.jpg

分かること: 署名者、「生成AIによる作成」の記録、SynthID（電子透かし）の記録。
分からないこと: 具体的なモデル名。記録に無ければ「不明」と伝える。
記録が無い画像は「AI生成ではない」という意味ではない。
"""
import re
import sys

data = open(sys.argv[1], 'rb').read()
head = data[:200000]

if b'c2pa' not in head:
    print('C2PAの来歴情報: なし（AI生成かどうかは、この記録からは判断できません）')
    sys.exit(0)

texts = [m.group().decode('ascii', 'ignore') for m in re.finditer(rb'[\x20-\x7e]{6,}', head)]
joined = '\n'.join(texts)

signers = sorted(set(re.findall(r'(Google LLC|OpenAI|Adobe[^\n]{0,20}|Microsoft[^\n]{0,20}|Midjourney[^\n]{0,10})', joined)))
print('C2PAの来歴情報: あり')
print('署名者の候補:', ', '.join(signers) if signers else '読み取れず')
for pattern, label in [
    (r'(Created by [A-Za-z ]+?)\.', '作成の記録'),
    (r'(trainedAlgorithmicMedia)', 'AI生成の区分'),
    (r'(Applied imperceptible SynthID watermark)', '電子透かし'),
]:
    m = re.search(pattern, joined)
    if m:
        print(f'{label}:', m.group(1))
print('モデル名:', '記録なし（不明）' if not re.search(r'(Gemini|Imagen|DALL|Firefly|Midjourney|Stable)', joined) else '記録あり')
