import hmac, hashlib, json

def sign_pgw_payload(secret_key: str, payload: dict) -> str:
    """
    Produce HMAC‑SHA256 signature of a JSON payload.
    """
    data = json.dumps(payload, separators=(',', ':'), sort_keys=True)
    return hmac.new(
        secret_key.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()
