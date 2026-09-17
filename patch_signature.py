from pathlib import Path
p=Path(r'J:\Bitcoin-Recovery-Vault-v0.3\backend\main.py')
s=p.read_text(encoding='utf-8')
s=s.replace('from pydantic import BaseModel, Field', 'from pydantic import BaseModel, Field\nfrom bitcoinlib.keys import verify_message')
old='''    ch["used"] = True\n    audit("ownership_verification_attempted", address=req.address, result="fail_closed")\n    raise HTTPException(501, "Signature verifier not installed; verification fails closed")'''
new='''    try:\n        valid = bool(verify_message(ch["text"], req.signature, req.address))\n    except Exception:\n        valid = False\n    ch["used"] = True\n    result = "verified" if valid else "invalid_signature"\n    audit("ownership_verification_attempted", address=req.address, result=result)\n    if not valid:\n        raise HTTPException(400, "Invalid signature for this address and challenge")\n    return {"verified": True, "address": req.address, "challenge_id": req.challenge_id}'''
if old not in s: raise SystemExit('old verify block not found')
s=s.replace(old,new)
p.write_text(s,encoding='utf-8')
print('signature-verifier-added')