const hre = require("hardhat");

async function main() {
  const contractAddress = "0xa83FC29A3c2852FC8ab61a4de728864d04171A97";

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