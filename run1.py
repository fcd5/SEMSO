import time
import requests
from env import OracleEnv
from RL import DoubleDQN

PROXY = "http://127.0.0.1:5000"
NODE_ID = 1

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

        payload = {
            "round_id": rid,
            "node_id": NODE_ID,
            "exchange": env.sources[action],
            "prices": prices
        }

        res = requests.post(f"{PROXY}/submit", json=payload, timeout=3)
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
