// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * BLETrustRegistry
 * On-chain whitelist for trusted BLE/Classic-BT devices.
 * Deployed on Sepolia testnet.
 *
 * Defense layer 1 of 3:
 *   Ethereum registry (this) -> Duplicate MAC detector -> AI ensemble
 */
contract BLETrustRegistry {

    // ---------------------------------------------------------------
    // Types
    // ---------------------------------------------------------------

    struct DeviceInfo {
        string  name;
        bool    trusted;
        uint256 registeredAt;
        uint256 revokedAt;
    }

    // ---------------------------------------------------------------
    // State
    // ---------------------------------------------------------------

    address public admin;

    // mac6 = 6-byte MAC packed into bytes6, e.g. AA:BB:CC:DD:EE:FF -> 0xAABBCCDDEEFF
    mapping(bytes6 => DeviceInfo) private registry;
    bytes6[] private allMacs;

    // ---------------------------------------------------------------
    // Events
    // ---------------------------------------------------------------

    event DeviceRegistered(bytes6 indexed mac, string name, uint256 timestamp);
    event DeviceRevoked(bytes6 indexed mac, uint256 timestamp);
    event AnomalyLogged(bytes6 indexed mac, string riskLevel, string reason, uint256 timestamp);

    // ---------------------------------------------------------------
    // Modifiers
    // ---------------------------------------------------------------

    modifier onlyAdmin() {
        require(msg.sender == admin, "BLETrustRegistry: caller is not admin");
        _;
    }

    // ---------------------------------------------------------------
    // Constructor
    // ---------------------------------------------------------------

    constructor() {
        admin = msg.sender;
    }

    // ---------------------------------------------------------------
    // Admin functions
    // ---------------------------------------------------------------

    /**
     * Register a device as trusted.
     * @param mac   6-byte packed MAC address (e.g. 0xAABBCCDDEEFF)
     * @param name  Human-readable device name
     */
    function registerDevice(bytes6 mac, string calldata name) external onlyAdmin {
        require(mac != bytes6(0), "BLETrustRegistry: zero MAC");
        if (!registry[mac].trusted && registry[mac].registeredAt == 0) {
            allMacs.push(mac);
        }
        registry[mac] = DeviceInfo({
            name:         name,
            trusted:      true,
            registeredAt: block.timestamp,
            revokedAt:    0
        });
        emit DeviceRegistered(mac, name, block.timestamp);
    }

    /**
     * Revoke a previously trusted device.
     * @param mac  6-byte packed MAC address
     */
    function revokeDevice(bytes6 mac) external onlyAdmin {
        require(registry[mac].trusted, "BLETrustRegistry: device not trusted");
        registry[mac].trusted   = false;
        registry[mac].revokedAt = block.timestamp;
        emit DeviceRevoked(mac, block.timestamp);
    }

    /**
     * Log an anomaly detected by the local AI/rule engine on-chain.
     * Non-admin callers allowed so the scanner node can log without holding admin key.
     * @param mac       6-byte packed MAC address
     * @param riskLevel "LOW" | "MEDIUM" | "HIGH"
     * @param reason    Short human-readable reason string
     */
    function logAnomaly(
        bytes6 mac,
        string calldata riskLevel,
        string calldata reason
    ) external {
        emit AnomalyLogged(mac, riskLevel, reason, block.timestamp);
    }

    /**
     * Transfer admin rights to a new address.
     */
    function transferAdmin(address newAdmin) external onlyAdmin {
        require(newAdmin != address(0), "BLETrustRegistry: zero address");
        admin = newAdmin;
    }

    // ---------------------------------------------------------------
    // View functions
    // ---------------------------------------------------------------

    /**
     * Check whether a device is currently trusted.
     * @param mac  6-byte packed MAC address
     */
    function isTrusted(bytes6 mac) external view returns (bool) {
        return registry[mac].trusted;
    }

    /**
     * Return full device info.
     */
    function getDevice(bytes6 mac) external view returns (
        string memory name,
        bool trusted,
        uint256 registeredAt,
        uint256 revokedAt
    ) {
        DeviceInfo storage d = registry[mac];
        return (d.name, d.trusted, d.registeredAt, d.revokedAt);
    }

    /**
     * Return total number of MACs ever registered (including revoked).
     */
    function deviceCount() external view returns (uint256) {
        return allMacs.length;
    }
}
