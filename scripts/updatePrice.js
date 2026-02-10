const hre = require("hardhat");

async function main() {
  // 🔴 換成你部署出來的合約地址
  const ORACLE_ADDRESS = "0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0";

  // 取得合約實例
  const oracle = await hre.ethers.getContractAt(
    "PriceOracle",
    ORACLE_ADDRESS
  );

  // 呼叫合約 function（送交易）
  const tx = await oracle.updatePrice(30000);
  await tx.wait();

  console.log("Price updated on-chain!");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});