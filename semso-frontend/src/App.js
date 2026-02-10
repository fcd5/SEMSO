import { useEffect, useState } from "react";
import { ethers } from "ethers";
import "./App.css";

const RPC_URL = "https://eth-sepolia.g.alchemy.com/v2/Iyy-VWcTVTCf9LlLNfFzH";
const CONTRACT_ADDRESS = "0xa83FC29A3c2852FC8ab61a4de728864d04171A97";

const ABI = [
  "function getLatestRound() view returns (string, uint256)"
];

function App() {
  const [prices, setPrices] = useState({});
  const [updateTime, setUpdateTime] = useState("");

  useEffect(() => {
    async function loadLatestPrice() {
      try {
        const provider = new ethers.JsonRpcProvider(RPC_URL);
        const contract = new ethers.Contract(
          CONTRACT_ADDRESS,
          ABI,
          provider
        );

        const [priceJson, timestamp] =
          await contract.getLatestRound();

        if (!priceJson || priceJson.length === 0) {
          console.warn("No price data on chain yet");
          return;
        }

        const data = JSON.parse(priceJson);
        setPrices(data);

        setUpdateTime(
          new Date(Number(timestamp) * 1000).toLocaleString()
        );
      } catch (err) {
        console.error("Failed to load price:", err);
      }
    }

    loadLatestPrice();
  }, []);

  return (
    <div className="container">
      <h1>🔮 SEMSO Crypto Oracle</h1>
      <p className="time">Last Update: {updateTime}</p>

      <table>
        <thead>
          <tr>
            <th>Cryptocurrency</th>
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
    </div>
  );
}

export default App;