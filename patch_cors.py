from pathlib import Path

p = Path(r"J:\Bitcoin-Recovery-Vault-v0.3\backend\main.py")
s = p.read_text(encoding="utf-8")

if "CORSMiddleware" not in s:
    s = s.replace(
        "from fastapi import FastAPI, HTTPException",
        "from fastapi import FastAPI, HTTPException\nfrom fastapi.middleware.cors import CORSMiddleware",
    )

marker = 'app = FastAPI(title="Bitcoin Recovery Vault", version="0.3.0")'
if "allow_origins" not in s:
    cors = marker + '\napp.add_middleware(\n    CORSMiddleware,\n    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],\n    allow_credentials=False,\n    allow_methods=["GET", "POST"],\n    allow_headers=["*"],\n)'
    s = s.replace(marker, cors)

p.write_text(s, encoding="utf-8")
print("cors-added")
