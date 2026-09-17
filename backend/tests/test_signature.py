from bitcoinlib.keys import Key
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_real_message_signature_verification():
    key = Key()
    address = key.address()
    c = client.post('/ownership/challenge', json={'address': address})
    assert c.status_code == 200
    data = c.json()
    signature = key.sign_message(data['message_to_sign'])
    r = client.post('/ownership/verify', json={
        'challenge_id': data['challenge_id'],
        'signature': signature.as_base64(),
        'address': address,
    })
    assert r.status_code == 200
    assert r.json()['verified'] is True
