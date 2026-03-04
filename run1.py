import time
import requests
from env import OracleEnv
from RL import DoubleDQN
import os
import json
from dotenv import load_dotenv
from eth_account import Account
from eth_account.messages import encode_defunct

PROXY = "http://127.0.0.1:5000"
NODE_ID = 1
# 載入 .env
load_dotenv()

# 讀取 node1 的私鑰
PRIVATE_KEY = os.getenv("NODE1_PRIVATE_KEY")

if PRIVATE_KEY is None:
    raise Exception("NODE1_PRIVATE_KEY not found in .env")

# 取得 node 地址
NODE_ADDRESS = Account.from_key(PRIVATE_KEY).address

print("Node address:", NODE_ADDRESS)

env = OracleEnv()

RL = DoubleDQN(
    n_actions=len(env.sources),
    n_features=len(env.sources)
)

state = env.reset()
last_handled_round = -1

print("=== Oracle Node START ===")

while True:
    try:
        r = requests.get(f"{PROXY}/round", timeout=2).json()
        rid = r["round_id"]
        status = r["status"]

        if rid <= last_handled_round or status != "OPEN":
            time.sleep(0.5)
            continue

        action = RL.choose_action(state)
        prices = env.fetch_prices(action)
        print("Node1 Current state:", state)
        
        payload = {
            "round_id": rid,
            "node_id": NODE_ID,
            "exchange": env.sources[action],
            "prices": prices,
        }

# 🔐 簽章
        message = encode_defunct(text=json.dumps(payload))
        signed = Account.sign_message(message, PRIVATE_KEY)

        submission = {
            "payload": payload,
            "signature": signed.signature.hex(),
            "address": "0xda0FE91eFc4B31Dc1C3023897E1A68BCBbfB8E82"
        }

        res = requests.post(f"{PROXY}/submit", json=submission, timeout=3)
        if res.status_code != 200:
            time.sleep(0.5)
            continue

        last_handled_round = rid

        while True:
            rw = requests.get(
                f"{PROXY}/reward/{rid}/{NODE_ID}", timeout=2
            ).json()
            if rw.get("status") == "pending":
                time.sleep(0.5)
                continue
            reward = rw.get("reward", 0)
            break

        next_state = env.update_state(action, reward)

        RL.store_transition(state, action, reward, next_state)
        if RL.memory_counter > RL.batch_size:
            RL.learn()

        state = next_state
        time.sleep(0.5)

    except Exception as e:
        print("ERROR:", e)
        time.sleep(1)
