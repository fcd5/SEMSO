from web3 import Web3
import json

# =========================
# Hardhat local network
# =========================
RPC_URL = "https://eth-sepolia.g.alchemy.com/v2/Iyy-VWcTVTCf9LlLNfFzH"

# Hardhat account #0 (proxy oracle)
PRIVATE_KEY = "155fffa715d3131db62be0f4975f80e52b009fdceb6d75809476d9cabdb80b5f"
ACCOUNT_ADDRESS = "0xa7eE1aBCD7af18B0956877D0dc26a5bf0E0ad575"

# =========================
# Deployed contract info
# =========================
CONTRACT_ADDRESS = "0xa83FC29A3c2852FC8ab61a4de728864d04171A97"

with open("artifacts/contracts/PriceOracle.sol/PriceOracle.json") as f:
    abi = json.load(f)["abi"]

w3 = Web3(Web3.HTTPProvider(RPC_URL))
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)

def submit_price(round_id, price_data, ipfs_cid=""):
    # 🔴 一定要用 pending
    nonce = w3.eth.get_transaction_count(
        ACCOUNT_ADDRESS,
        "pending"
    )

    tx = contract.functions.submitRound(
        round_id,
        json.dumps(price_data),
        ipfs_cid
    ).build_transaction({
        "from": ACCOUNT_ADDRESS,
        "nonce": nonce,
        "gas": 500_000,  # 🔧 不用 3,000,000

        # ✅ EIP-1559（Sepolia 正解）
        "maxFeePerGas": w3.to_wei("3", "gwei"),
        "maxPriorityFeePerGas": w3.to_wei("1.5", "gwei"),
    })

    signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    print("[CHAIN] tx sent:", tx_hash.hex())