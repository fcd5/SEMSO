const hre = require("hardhat");

async function main() {
  const ethers = hre.ethers;

  const proxyOracleAddress = "0xa7eE1aBCD7af18B0956877D0dc26a5bf0E0ad575"; 

  const PriceOracle = await ethers.getContractFactory("PriceOracle");
  const priceOracle = await PriceOracle.deploy(proxyOracleAddress);

  await priceOracle.waitForDeployment();

  console.log(
    "PriceOracle deployed to:",
    await priceOracle.getAddress()
  );
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});