"""GreenMail にテストメールを投入する（SMTP 3025 番、認証なし）。

使い方: python scripts/seed_greenmail.py [host]
"""
import smtplib
import sys
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
samples = [
    ("山田 太郎 <yamada@example.jp>", "打ち合わせ日程のご相談", "田中様\n\n来週の打ち合わせですが、火曜か水曜はいかがでしょうか。\n\n山田"),
    ("佐藤 花子 <sato@example.jp>", "見積書送付の件", "お世話になっております。\n見積書を添付いたしました。ご確認ください。\n\n佐藤"),
    ("newsletter@example.com", "Weekly Digest", "This week's top stories..."),
]
with smtplib.SMTP(host, 3025) as s:
    for from_, subject, body in samples:
        m = EmailMessage()
        m["From"], m["To"], m["Subject"] = from_, "test@localhost", subject
        m["Date"], m["Message-ID"] = formatdate(localtime=True), make_msgid(domain="example.jp")
        m.set_content(body, charset="utf-8")
        s.send_message(m)
        print("sent:", subject)
