from __future__ import annotations
import math, os, secrets, uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from bitcoinlib.keys import verify_message

app = FastAPI(title="Bitcoin Recovery Vault", version="0.3.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://127.0.0.1:3000", "http://localhost:3000", "http://127.0.0.1:8088", "http://localhost:8088"], allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])
audit_log: list[dict[str, Any]] = []
challenges: dict[str, dict[str, Any]] = {}

def audit(event: str, **data: Any) -> None:
    audit_log.append({"ts": datetime.now(timezone.utc).isoformat(), "event": event, **data})

def research_score(inactivity_days: int, tx_count: int) -> int:
    days = max(0, inactivity_days)
    txs = max(0, tx_count)
    age = 100 * (1 - math.exp(-days / 730))
    penalty = min(20, math.log1p(txs) * 3)
    return round(max(0, min(100, age - penalty)))

class PublicAddressData(BaseModel):
    address: str
    valid: bool
    tx_count: int = 0
    funded_sats: int = 0
    spent_sats: int = 0
    balance_sats: int = 0
    latest_confirmed_block_time: int | None = None
    source: str
    as_of: str

class BitcoinDataProvider(Protocol):
    async def get_address(self, address: str) -> PublicAddressData: ...

class MempoolSpaceProvider:
    def __init__(self, base_url: str = "https://mempool.space/api"):
        self.base_url = base_url.rstrip("/")

    async def get_address(self, address: str) -> PublicAddressData:
        timeout = httpx.Timeout(12.0)
        headers = {"User-Agent": "Bitcoin-Recovery-Vault/0.3"}
        async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
            vr = await client.get(f"{self.base_url}/v1/validate-address/{address}")
            if vr.status_code == 429:
                raise HTTPException(503, "Public provider rate limit reached")
            if vr.status_code >= 400:
                raise HTTPException(502, "Address validation provider error")
            valid = bool(vr.json().get("isvalid"))
            now = datetime.now(timezone.utc).isoformat()
            if not valid:
                return PublicAddressData(address=address, valid=False, source="mempool.space", as_of=now)

            ar = await client.get(f"{self.base_url}/address/{address}")
            if ar.status_code == 429:
                raise HTTPException(503, "Public provider rate limit reached")
            if ar.status_code >= 400:
                raise HTTPException(502, "Address provider error")
            data = ar.json()
            chain = data.get("chain_stats", {})
            tx_count = int(chain.get("tx_count", 0))
            funded = int(chain.get("funded_txo_sum", 0))
            spent = int(chain.get("spent_txo_sum", 0))

            latest_time = None
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

            return PublicAddressData(
                address=address, valid=True, tx_count=tx_count,
                funded_sats=funded, spent_sats=spent,
                balance_sats=funded-spent,
                latest_confirmed_block_time=latest_time,
                source="mempool.space", as_of=now,
            )

def get_provider() -> BitcoinDataProvider:
    return MempoolSpaceProvider(os.getenv("BITCOIN_API_BASE", "https://mempool.space/api"))

class AnalyzeRequest(BaseModel):
    address: str = Field(min_length=14, max_length=90)
    inactivity_days: int = Field(ge=0, le=50000)
    tx_count: int = Field(ge=0, le=10_000_000)
    balance_btc: float = Field(ge=0)

class ChallengeRequest(BaseModel):
    address: str = Field(min_length=14, max_length=90)

class VerifyRequest(BaseModel):
    challenge_id: str
    signature: str
    address: str

@app.get("/health")
def health():
    return {"status":"ok","version":"0.3.0","non_custodial":True,"fund_transfers":False,"private_key_storage":False}

@app.post("/analyze-address")
def analyze_address(req: AnalyzeRequest):
    score = research_score(req.inactivity_days, req.tx_count)
    audit("address_analyzed", address=req.address, score=score)
    return {"address":req.address,"dormancy_score":score,"research_signal_only":True,
            "ownership_status":"unknown",
            "warning":"Dormancy is not proof that funds are lost, abandoned, or ownerless."}

@app.get("/public/address/{address}", response_model=PublicAddressData)
async def public_address(address: str):
    data = await get_provider().get_address(address)
    audit("public_address_fetched", address=address, source=data.source, valid=data.valid)
    return data
@app.post("/ownership/challenge")
def create_challenge(req: ChallengeRequest):
    cid = str(uuid.uuid4())
    nonce = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(minutes=15)
    text = f"Bitcoin Recovery Vault ownership proof\nAddress: {req.address}\nNonce: {nonce}\nChallenge: {cid}"
    challenges[cid] = {"address": req.address, "text": text, "expires": expires, "used": False}
    audit("ownership_challenge_created", address=req.address, challenge_id=cid)
    return {"challenge_id":cid,"message_to_sign":text,"expires_at":expires.isoformat(),
            "warning":"Sign only with your wallet. Never send a seed phrase or private key."}

@app.post("/ownership/verify")
def verify_ownership(req: VerifyRequest):
    ch = challenges.get(req.challenge_id)
    if not ch: raise HTTPException(404, "Challenge not found")
    if ch["used"]: raise HTTPException(409, "Challenge already used")
    if datetime.now(timezone.utc) > ch["expires"]: raise HTTPException(410, "Challenge expired")
    if ch["address"] != req.address: raise HTTPException(400, "Address mismatch")
    try:
        valid = bool(verify_message(ch["text"], req.signature, req.address))
    except Exception:
        valid = False
    ch["used"] = True
    result = "verified" if valid else "invalid_signature"
    audit("ownership_verification_attempted", address=req.address, result=result)
    if not valid:
        raise HTTPException(400, "Invalid signature for this address and challenge")
    return {"verified": True, "address": req.address, "challenge_id": req.challenge_id}

@app.get("/audit")
def get_audit():
    return {"events": audit_log[-100:], "contains_private_keys": False}

@app.post("/transfer")
def transfer_disabled():
    raise HTTPException(403, "Fund transfers are disabled in the non-custodial MVP.")