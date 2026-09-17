from pathlib import Path
p=Path(r"J:\Bitcoin-Recovery-Vault-v0.3\backend\main.py")
s=p.read_text(encoding="utf-8")
s=s.replace('allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"]','allow_origins=["http://127.0.0.1:3000", "http://localhost:3000", "http://127.0.0.1:8088", "http://localhost:8088"]')
p.write_text(s,encoding="utf-8")
print("cors-8088-added")
