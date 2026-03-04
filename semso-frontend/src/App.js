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

  const provider = new ethers.JsonRpcProvider(RPC_URL);
  const contract = new ethers.Contract(CONTRACT_ADDRESS, ABI, provider);
  function getTaiwanNow() {
  const now = new Date();
  // 取得台灣時區字串 YYYY-MM-DDTHH:mm
  const taiwanStr = now.toLocaleString("sv-SE", { timeZone: "Asia/Taipei" }).replace(" ", "T").slice(0,16);
  return taiwanStr;
  }
  useEffect(() => {
    loadLatest();
  }, []);

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

  return (
    <div className="container">
      <h1>🔮 SEMSO Crypto Oracle</h1>

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
    </div>
  );
}

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

export default App;