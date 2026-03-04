from flask import Flask, request, jsonify
import threading
import time
import statistics
from price_oracle_client import submit_price
from pinata_client import upload_to_ipfs
import json
from eth_account.messages import encode_defunct
from eth_account import Account

app = Flask(__name__)

# =========================
# SEMSO parameters
# =========================
T = 3                  # minimum number of submissions
K = 4                  # minimum source diversity
ROUND_TIME = 15
ROUND_GAP = 10

total_rounds = 0
total_success = 0

# =========================
# Security: source whitelist
# =========================
ALLOWED_SOURCES = ["Binance", "Kraken", "Coinbase", "KuCoin", "Bybit"]
ALLOWED_NODE_ADDRESSES = [
    "0xda0FE91eFc4B31Dc1C3023897E1A68BCBbfB8E82",
    "0xA1C9fd82Cb891B87Dc99EAf4854a993693cBDe71",
    "0x30fbc49A173B991041065e3c834895Aa882Fb854",
    "0x05786F0e4a3569B3179F0CDd812396042d5ecC78",
    "0xE9d2ADD1A04857395648a11b6042aDC5C5b4774d"
]
# =========================
# Global state
# =========================
state = {
    "round_id": 0,
    "round_status": {},      # rid -> OPEN / DONE
    "submissions": {},       # rid -> node_id -> data
    "round_rewards": {},     # rid -> node_id -> reward
    "final_price": {}        # rid -> aggregated price
}

lock = threading.Lock()

# =========================
# Round scheduler
# =========================
def round_loop():
    while True:
        with lock:
            state["round_id"] += 1
            rid = state["round_id"]
            state["round_status"][rid] = "OPEN"
            state["submissions"][rid] = {}
            print(f"\n[Proxy] ===== Round {rid} OPEN =====")

        time.sleep(ROUND_TIME)

        with lock:
            evaluate_round(rid)
            state["round_status"][rid] = "DONE"
            print(f"[Proxy] ===== Round {rid} DONE =====")
            print(f"[Proxy] Final price: {state['final_price'].get(rid)}")

        time.sleep(ROUND_GAP)

# =========================
# Core SEMSO evaluation
# =========================
def evaluate_round(rid):
    subs = state["submissions"].get(rid, {})
    rewards = {}

    print("\n[DEBUG] ===== EVALUATE ROUND", rid, "=====")
    print("[DEBUG] total submissions:", len(subs))

    if not subs:
        print("[DEBUG] FAIL: no submissions")
        state["round_rewards"][rid] = {}
        return

    exchanges = []
    illegal_sources = set()

    for nid, v in subs.items():
        ex = v["exchange"]
        exchanges.append(ex)

        if ex not in ALLOWED_SOURCES:
            illegal_sources.add(ex)

        print(f"[DEBUG] node {nid} -> exchange = {ex}")

    # =========================
    # Reward decision
    # =========================
    reward = 1

    if illegal_sources:
        reward = -1
    elif len(subs) < T:
        reward = -1
    else:
        unique_ex = set(exchanges)
        if len(unique_ex) < K:
            reward = -1

    # =========================
    # Assign rewards
    # =========================
    for nid in subs:
        rewards[nid] = reward

    state["round_rewards"][rid] = rewards

    # =========================
    # 🔹 IPFS upload（先做）
    # =========================
    ipfs_payload = {
        "round_id": rid,
        "T": T,
        "K": K,
        "submissions": subs,
        "reward": reward,
        "timestamp": int(time.time())
    }

    cid = upload_to_ipfs(ipfs_payload)
    state.setdefault("ipfs_cids", {})[rid] = cid

    # =========================
    # Aggregation & on-chain commit
    # =========================
    if reward == 1:
        aggregate_prices(rid, subs)

        # ⭐ 把 CID 包進鏈上資料
        state["final_price"][rid]["ipfs_cid"] = cid

        try:
            submit_to_blockchain(rid, state["final_price"][rid])
            print(f"[CHAIN] Round {rid} submitted successfully")
        except Exception as e:
            print(f"[CHAIN][ERROR] Round {rid} submit failed:", e)
    else:
        print(f"[CHAIN] Round {rid} NOT submitted (reward=0)")

    print(f"[DEBUG] FINAL reward = {reward}")
    # =========================
    # 成功率統計（安全版本）
    # =========================
    global total_rounds, total_success

    success = 1 if reward == 1 else 0

    total_rounds += 1
    total_success += success

    overall_rate = total_success / total_rounds

    print(f"[STATS] Overall success rate: {overall_rate:.3f}")
    print(f"[STATS] Total rounds: {total_rounds}, Total success: {total_success}")
    
    
# =========================
# Price aggregation
# =========================
def aggregate_prices(rid, subs):
    result = {}

    sample = next(iter(subs.values()), None)
    if not sample:
        return

    symbols = sample["prices"].keys()

    for sym in symbols:
        prices = []
        sources = []

        for v in subs.values():
            if sym in v["prices"]:
                prices.append(v["prices"][sym])
                sources.append(v["exchange"])

        if prices:
            result[sym] = {
                "median_price": statistics.median(prices),
                "sources": list(set(sources))
            }

    state["final_price"][rid] = result

def verify_signature(payload, signature, address):
    try:
        message = encode_defunct(text=json.dumps(payload))
        recovered = Account.recover_message(message, signature=signature)
        return recovered.lower() == address.lower()
    except:
        return False
    
# =========================
# Blockchain submission
# =========================
def submit_to_blockchain(rid, final_price):
    submit_price(rid, final_price)

# =========================
# API endpoints
# =========================
@app.route("/round")
def get_round():
    with lock:
        rid = state["round_id"]
        return jsonify({
            "round_id": rid,
            "status": state["round_status"].get(rid, "INIT")
        })

@app.route("/submit", methods=["POST"])
def submit():
    data = request.json
    payload = data["payload"]
    signature = data["signature"]
    address = data["address"]

    rid = payload["round_id"]
    nid = payload["node_id"]

    # 🔐 驗證 node 地址
    if address not in ALLOWED_NODE_ADDRESSES:
        return jsonify({"error": "unauthorized node"}), 403

    # 🔐 驗證簽章
    if not verify_signature(payload, signature, address):
        return jsonify({"error": "invalid signature"}), 403
    with lock:
        if state["round_status"].get(rid) != "OPEN":
            return jsonify({"error": "round not open"}), 400

        if nid in state["submissions"][rid]:
            return jsonify({"error": "already submitted"}), 400

        state["submissions"][rid][nid] = {
            "exchange": payload["exchange"],
            "prices": payload["prices"],
            "address": address
            }

        print(f"[Proxy] RECEIVE submit round={rid} node={nid}")

    return jsonify({"status": "ok"})

@app.route("/reward/<int:round_id>/<int:node_id>")
def get_reward(round_id, node_id):
    with lock:
        if state["round_status"].get(round_id) != "DONE":
            return jsonify({"status": "pending"})

        return jsonify({
            "reward": state["round_rewards"]
            .get(round_id, {})
            .get(node_id, 0)
        })

# =========================
# Entry point
# =========================
if __name__ == "__main__":
    threading.Thread(target=round_loop, daemon=True).start()
    app.run(port=5000)