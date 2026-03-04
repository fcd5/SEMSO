const hre = require("hardhat");

async function main() {
  const contractAddress = "0xf1d53bD2D95EDf0EE8A794348c56129D3EACA7D5";

  const [signer] = await hre.ethers.getSigners();

  const oracle = new hre.ethers.Contract(
    contractAddress,
    (await hre.artifacts.readArtifact("PriceOracle")).abi,
    signer
  );

  const roundId = 1; // 你目前要讀的 round

  const result = await oracle.getRound(roundId);

  console.log("📦 On-chain price JSON:", result[0]);
  console.log("⏱ Timestamp:", result[1].toString());
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});