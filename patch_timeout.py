from pathlib import Path

p = Path(r"J:\Bitcoin-Recovery-Vault-v0.3\backend\main.py")
s = p.read_text(encoding="utf-8")
old = '''            latest_time = None
            tr = await client.get(f"{self.base_url}/address/{address}/txs")
            if tr.status_code == 200:
                for tx in tr.json():
                    status = tx.get("status", {})
                    if status.get("confirmed") and status.get("block_time"):
                        latest_time = int(status["block_time"])
                        break
'''
new = '''            latest_time = None
            try:
                tr = await client.get(f"{self.base_url}/address/{address}/txs")
                if tr.status_code == 200:
                    for tx in tr.json():
                        status = tx.get("status", {})
                        if status.get("confirmed") and status.get("block_time"):
                            latest_time = int(status["block_time"])
                            break
            except httpx.TimeoutException:
                latest_time = None
'''
if old not in s:
    raise SystemExit("target block not found")
p.write_text(s.replace(old, new), encoding="utf-8")
print("timeout-fallback-added")
