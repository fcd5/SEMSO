import numpy as np
import requests


class OracleEnv:
    def __init__(self):
        self.sources = ["Binance", "Kraken", "Coinbase", "KuCoin", "Bybit"]
        self.symbols = ["BTC", "ETH", "SOL", "BNB"]
        self.state_clip = 200
        self.timeout = 5
        self.reset()

    def reset(self):
        self.state = np.zeros(len(self.sources))
        return self.state.copy()

    def update_state(self, action, reward):
    # 整體衰減（避免無限累積）
        self.state = self.state * 0.9
    # 根據 reward 更新
        self.state[action] += reward
        return self.state.copy()
    

    def fetch_prices(self, action):
        source = self.sources[action]
        prices = {}

        for sym in self.symbols:
            try:
                if source == "Binance":
                    prices[sym] = self._binance(sym)
                elif source == "Kraken":
                    prices[sym] = self._kraken(sym)
                elif source == "Coinbase":
                    prices[sym] = self._coinbase(sym)
                elif source == "KuCoin":
                    prices[sym] = self._kucoin(sym)
                elif source == "Bybit":
                    prices[sym] = self._bybit(sym)
            except Exception:
                prices[sym] = None

        return prices

    def _binance(self, sym):
        r = requests.get(
            "https://api.binance.com/api/v3/ticker/price",
            params={"symbol": f"{sym}USDT"},
            timeout=self.timeout
        )
        return float(r.json()["price"])

    def _kraken(self, sym):
        pair = {"BTC": "XXBTZUSD", "ETH": "XETHZUSD", "SOL": "SOLUSD", "BNB": "BNBUSD"}[sym]
        r = requests.get(
            "https://api.kraken.com/0/public/Ticker",
            params={"pair": pair},
            timeout=self.timeout
        )
        data = r.json()["result"]
        return float(list(data.values())[0]["c"][0])

    def _coinbase(self, sym):
        r = requests.get(
            f"https://api.coinbase.com/v2/prices/{sym}-USD/spot",
            timeout=self.timeout
        )
        return float(r.json()["data"]["amount"])

    def _kucoin(self, sym):
        r = requests.get(
            "https://api.kucoin.com/api/v1/market/orderbook/level1",
            params={"symbol": f"{sym}-USDT"},
            timeout=self.timeout
        )
        return float(r.json()["data"]["price"])

    def _bybit(self, sym):
        r = requests.get(
            "https://api.bybit.com/v5/market/tickers",
            params={"category": "spot", "symbol": f"{sym}USDT"},
            timeout=self.timeout
        )
        return float(r.json()["result"]["list"][0]["lastPrice"])
