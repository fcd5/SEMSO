import requests
import json

PINATA_API_KEY = "7b8d1d3dc44da1ca5845"
PINATA_SECRET_API_KEY = "0dc4c91c0b54d989c6f331a94e88669558e0c075afaafd4f3537991f520fdea4"

PINATA_URL = "https://api.pinata.cloud/pinning/pinJSONToIPFS"

def upload_to_ipfs(data: dict) -> str:
    headers = {
        "Content-Type": "application/json",
        "pinata_api_key": PINATA_API_KEY,
        "pinata_secret_api_key": PINATA_SECRET_API_KEY
    }

    payload = {
        "pinataContent": data,
        "pinataMetadata": {
            "name": f"round-{data.get('round_id')}"
        }
    }

    r = requests.post(PINATA_URL, headers=headers, data=json.dumps(payload))
    r.raise_for_status()

    cid = r.json()["IpfsHash"]
    print("[Pinata] uploaded, CID =", cid)
    return cid