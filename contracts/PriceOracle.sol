// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract PriceOracle {

    address public proxyOracle;

    modifier onlyProxy() {
        require(msg.sender == proxyOracle, "Not authorized");
        _;
    }

    struct PriceData {
        string ipfsCid;
        string priceJson;
        uint256 timestamp;
    }

    mapping(uint256 => PriceData) public rounds;
    uint256 public latestRoundId;

    constructor(address _proxyOracle) {
        proxyOracle = _proxyOracle;
    }

    function submitRound(
        uint256 roundId,
        string calldata priceJson,
        string calldata ipfsCid
    ) external onlyProxy {
        rounds[roundId] = PriceData({
            ipfsCid: ipfsCid,
            priceJson: priceJson,
            timestamp: block.timestamp
        });

        latestRoundId = roundId;
    }

    function getLatestRound()
        external
        view
        returns (string memory, uint256)
    {
        PriceData memory p = rounds[latestRoundId];
        return (p.priceJson, p.timestamp);
    }
    
    function getRound(uint256 roundId)
        external
        view
        returns (string memory, uint256)
    {
        PriceData memory p = rounds[roundId];
        return (p.priceJson, p.timestamp);
    }
}