"""MCP クライアントとして stdio でサーバーを起動し、全ツールを一通り呼ぶ動作確認スクリプト。
使い方: MAIL_MCP_CONFIG=config/accounts.yaml python scripts/e2e_check.py [account名]
注意: 最初に見つかったメール 1 通に対して 返信下書き作成 → 既読 → ゴミ箱移動 を行う（テスト用アカウントで実行すること）。
"""
import asyncio, json, os, sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    env = dict(os.environ)
    account = sys.argv[1] if len(sys.argv) > 1 else None
    async with stdio_client(StdioServerParameters(command="mail-mcp", env=env)) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            async def call(name, **a):
                res = await s.call_tool(name, a)
                out = res.structured_content or [c.text for c in res.content]
                print(f"== {name}", json.dumps(out, ensure_ascii=False)[:600]); return out
            accs = (await call("list_accounts"))["result"]
            account = account or accs[0]["name"]
            await call("list_folders", account=account)
            r = await call("search_emails", account=account, unread_only=False, days=0, limit=3)
            if not r["results"]:
                print("メールがありません"); return
            uid = r["results"][0]["uid"]
            await call("get_email", account=account, uid=uid)
            await call("create_reply_draft", account=account, uid=uid, body="（e2e_check による自動テスト下書き）")
            await call("list_drafts", account=account)
            await call("mark_as_read", account=account, uids=[uid])
            await call("delete_email", account=account, uids=[uid])
asyncio.run(main())
