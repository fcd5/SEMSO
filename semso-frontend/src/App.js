import { useEffect, useState } from "react";
import { ethers } from "ethers";
import "./App.css";

const RPC_URL = "https://eth-sepolia.g.alchemy.com/v2/Iyy-VWcTVTCf9LlLNfFzH";
const CONTRACT_ADDRESS = "0xf1d53bD2D95EDf0EE8A794348c56129D3EACA7D5";

const ABI = [
  "function getLatestRound() view returns (string, uint256)",
  "function getRound(uint256) view returns (string, uint256)",
  "function latestRoundId() view returns (uint256)"
];

function App() {
  const [latestPrices, setLatestPrices] = useState({});
  const [latestTime, setLatestTime] = useState("");

  const [historyPrices, setHistoryPrices] = useState({});
  const [historyTime, setHistoryTime] = useState("");

  const [selectedDate, setSelectedDate] = useState("");

  const [walletAddress, setWalletAddress] = useState(null);

  const [alertCoin, setAlertCoin] = useState("BTC");
  const [alertPrice, setAlertPrice] = useState("");
  const [alertEmail, setAlertEmail] = useState("");
  const [alertType, setAlertType] = useState("BUY");

  const [tradeHistory, setTradeHistory] = useState([]);

  const provider = new ethers.JsonRpcProvider(RPC_URL);
  const contract = new ethers.Contract(CONTRACT_ADDRESS, ABI, provider);
  function getTaiwanNow() {
  const now = new Date();
  // 取得台灣時區字串 YYYY-MM-DDTHH:mm
  const taiwanStr = now.toLocaleString("sv-SE", { timeZone: "Asia/Taipei" }).replace(" ", "T").slice(0,16);
  return taiwanStr;
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    loadLatest();
    }, []);

  async function loadTradeHistory(addr) {
  const wallet = (addr || walletAddress)?.toLowerCase(); // ✅ 統一轉小寫

  if (!wallet) {
    alert("請先連接錢包");
    return;
  }

  try {
    console.log("Fetching trades for:", wallet);
    const res = await fetch(`http://127.0.0.1:5000/trades/${wallet}`);
    const data = await res.json();
    console.log("Trade API response:", data);
    setTradeHistory(data);
  } catch (err) {
    console.error(err);
    alert("無法取得交易紀錄");
  }
}
  
  async function handleCreateAlert() {
    if (!alertPrice || !alertEmail) {
      alert("請輸入價格與 Email");
      return;
    }

    const payload = {
      wallet: walletAddress?.toLowerCase(),
      coin: alertCoin,
      price: Number(alertPrice),
      email: alertEmail,
      type: alertType
    };

    try {
      const res = await fetch("http://127.0.0.1:5000/alerts", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      const data = await res.json();

      if (res.ok) {
        alert("提醒建立成功！");
        setAlertPrice("");
        setAlertEmail("");
      } else {
      alert(data.error);
      }

    } catch (err) {
      console.error(err);
      alert("建立提醒失敗");
    }
  }

  
  // connectWallet 改成這樣
async function connectWallet() {
  if (!window.ethereum) {
    alert("Please install MetaMask");
    return;
  }

  try {
    const provider = new ethers.BrowserProvider(window.ethereum);

    // ✅ 先撤銷舊授權，強制跳出 MetaMask 視窗
    try {
      await provider.send("wallet_revokePermissions", [
        { eth_accounts: {} }
      ]);
    } catch (e) {
      // 部分舊版 MetaMask 不支援，忽略錯誤
    }

    const accounts = await provider.send("eth_requestAccounts", []);
    const addr = accounts[0].address ? accounts[0].address : accounts[0];

    setWalletAddress(addr);

    // ✅ 直接傳 addr，不依賴 walletAddress state
    loadTradeHistory(addr);

    console.log("Connected wallet:", addr);

  } catch (err) {
    console.error(err);
  }
}

  async function loadLatest() {
    const [priceJson, timestamp] = await contract.getLatestRound();
    if (!priceJson) return;

    const data = JSON.parse(priceJson);
    setLatestPrices(data);
    setLatestTime(new Date(Number(timestamp) * 1000).toLocaleString());
  }

  async function searchByDate() {
  if (!selectedDate) return;

  const userTs = Math.floor(new Date(selectedDate).getTime() / 1000);
  const latest = await contract.latestRoundId();

  for (let i = Number(latest); i >= 1; i--) {
    const [priceJson, ts] = await contract.getRound(i);

    // ⭐ 防止空 round
    if (!priceJson || priceJson.trim() === "") {
      continue;
    }

    if (Number(ts) <= userTs) {
      try {
        const data = JSON.parse(priceJson);
        setHistoryPrices(data);
        setHistoryTime(
          new Date(Number(ts) * 1000).toLocaleString()
        );
        return;
      } catch (err) {
        console.error("JSON parse error:", err);
        continue;
      }
    }
  }

  alert("找不到符合時間的歷史資料");
}

function disconnectWallet() {
  setWalletAddress(null);
  setTradeHistory([]); 
}


return (
  <>
    {/* 主容器 */}
    <div className="container">
      <h1>🔮 SEMSO Crypto Oracle</h1>
      <div style={{ position: "absolute", top: "20px", right: "25px" }}>
        {!walletAddress ? (
          <button onClick={connectWallet}>
            登入
          </button>
        ) : (
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: "12px" }}>
              已登入：{walletAddress.slice(0,6)}...{walletAddress.slice(-4)}
            </div>
            <button onClick={disconnectWallet}>
              登出
            </button>
          </div>
        )}
      </div>
      
      <div style={{ marginBottom: "20px", textAlign: "center" }}>
        <input
          type="datetime-local"
          value={selectedDate}
          max={getTaiwanNow()}
          onChange={(e) => setSelectedDate(e.target.value)}
        />
        <button onClick={searchByDate} style={{ marginLeft: "10px" }}>
          Search History
        </button>
      </div>

      <div className="grid">
        {/* 最新價格 */}
        <div>
          <h2>📍 Latest Price</h2>
          <p>Time: {latestTime}</p>
          <PriceTable prices={latestPrices} />
        </div>

        {/* 歷史價格 */}
        <div>
          <h2>📜 Historical Price</h2>
          <p>Time: {historyTime || "Not selected"}</p>
          <PriceTable prices={historyPrices} />
        </div>
      </div>

      {walletAddress && (
        <div style={{
          position: "fixed",
          bottom: "0px",
          left: "0",
          width: "100%",
          background: "rgba(0,0,0,0.6)",
          padding: "20px",
          display: "flex",
          justifyContent: "center",
          gap: "10px",
          alignItems: "center",
          flexWrap: "wrap",
          zIndex: 1000
        }}>
          {/* 幣種選擇 */}
          <select
            value={alertCoin}
            onChange={(e) => setAlertCoin(e.target.value)}
            style={{ padding: "8px", borderRadius: "6px" }}
          >
            {["BTC","ETH","SOL","BNB"].map((coin) => (
              <option key={coin} value={coin}>{coin}</option>
            ))}
          </select>

          {/* 目標價格 */}
          <input
            type="number"
            placeholder="輸入目標價格"
            value={alertPrice}
            onChange={(e) => setAlertPrice(e.target.value)}
            style={{ padding: "8px", borderRadius: "6px", width: "120px" }}
          />

          {/* Email */}
          <input
            type="email"
            placeholder="輸入 Email"
            value={alertEmail}
            onChange={(e) => setAlertEmail(e.target.value)}
            style={{ padding: "8px", borderRadius: "6px", width: "180px" }}
          />

          {/* 買 / 賣 */}
          <select
            value={alertType}
            onChange={(e) => setAlertType(e.target.value)}
            style={{ padding: "8px", borderRadius: "6px" }}
          >
            <option value="BUY">買入提醒 </option>
            <option value="SELL">賣出提醒 </option>
          </select>

          {/* 建立提醒按鈕 */}
          <button
            onClick={() => handleCreateAlert()}
            style={{
              padding: "8px 16px",
              borderRadius: "6px",
              cursor: "pointer"
            }}
          >
            建立提醒
          </button>
        </div>
      )}
    </div>

    {/* 右側固定交易紀錄 */}
    <div className="trade-panel" style={{
      position: "fixed",
      top: "100px",      // 調整垂直位置
      right: "50px",     // 調整水平位置
      width: "490px",    // 調整寬度
      maxHeight: "70vh", // 高度不要超過畫面
      overflowY: "auto", // 滾動
      background: "rgba(0, 0, 0, 0.4)",
      border: "1px solid #ccc",
      padding: "10px",
      borderRadius: "8px",
      zIndex: 9999
    }}>
      <h2>💹 My Trade History</h2>
      <button onClick={() => loadTradeHistory()}>載入交易紀錄</button>

      <table style={{ marginTop: "10px", width: "100%" }}>
        <thead>
          <tr>
            <th>Coin</th>
            <th>Type</th>
            <th>Price</th>
            <th>Time</th>
            <th>是否觸發過</th>
          </tr>
        </thead>
        <tbody>
          {tradeHistory.length === 0 ? (
            <tr>
              <td colSpan="4">沒有交易紀錄</td>
            </tr>
          ) : (
            tradeHistory.map((trade, idx) => (
              <tr key={idx}>
                <td>{trade.coin}</td>
                <td>{trade.type}</td>
                <td>{trade.price}</td>
                <td>{new Date(trade.time).toLocaleString()}</td>
                <td>{trade.triggered ? "是" : "否"}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  </>
  );
}
export default App;

function PriceTable({ prices }) {
  return (
    <table>
      <thead>
        <tr>
          <th>Coin</th>
          <th>Price (USD)</th>
        </tr>
      </thead>
      <tbody>
        {["BTC", "ETH", "SOL", "BNB"].map((coin) => (
          <tr key={coin}>
            <td className="coin">{coin}</td>
            <td className="price">
              {prices[coin]?.median_price ?? "-"}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
