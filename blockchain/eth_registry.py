"""
Ethereum BLETrustRegistry interface.

Wraps the deployed BLETrustRegistry.sol contract on Sepolia testnet.
Provides three operations used by the main pipeline:
  - is_trusted(mac_str)  -> bool       (read-only, free)
  - log_anomaly(mac_str, risk_level, reason) -> tx_hash  (emits on-chain event)
  - register_device(mac_str, name)     -> tx_hash  (admin-only)

Configuration via environment variables (put these in a .env file):
  ETH_RPC_URL       - Infura/Alchemy endpoint, e.g. https://sepolia.infura.io/v3/YOUR_KEY
  CONTRACT_ADDRESS  - deployed contract address on Sepolia
  ETH_PRIVATE_KEY   - hex private key for signing transactions (keep secret!)

If ETH_RPC_URL or CONTRACT_ADDRESS are unset, the module silently disables itself
so the rest of the pipeline still works without Ethereum configured.
"""

import os
import json
import binascii
import logging

log = logging.getLogger(__name__)

# ── Optional dependency ───────────────────────────────────────────────────────
try:
    from web3 import Web3
    from web3.middleware import ExtraDataToPOAMiddleware
    _WEB3_AVAILABLE = True
except ImportError:
    _WEB3_AVAILABLE = False

# ── ABI path ──────────────────────────────────────────────────────────────────
_ABI_PATH = os.path.join(
    os.path.dirname(__file__), '..', 'contracts', 'BLETrustRegistry_abi.json'
)


def _load_abi() -> list:
    with open(_ABI_PATH, 'r') as f:
        return json.load(f)


def _mac_to_bytes6(mac_str: str) -> bytes:
    """
    Convert 'AA:BB:CC:DD:EE:FF' or 'AABBCCDDEEFF' to a 6-byte bytes object.
    Raises ValueError for malformed MACs.
    """
    clean = mac_str.replace(':', '').replace('-', '').upper()
    if len(clean) != 12:
        raise ValueError(f"Invalid MAC address: {mac_str!r}")
    return binascii.unhexlify(clean)


class EthRegistry:
    """
    Thin wrapper around the deployed BLETrustRegistry contract.

    Usage:
        reg = EthRegistry()
        if reg.enabled:
            trusted = reg.is_trusted('AA:BB:CC:DD:EE:FF')
    """

    def __init__(self):
        self.enabled = False
        self._w3 = None
        self._contract = None
        self._account = None

        if not _WEB3_AVAILABLE:
            log.warning("[ETH] web3 not installed. Run: pip install web3")
            return

        rpc_url  = os.getenv('ETH_RPC_URL', '').strip()
        contract = os.getenv('CONTRACT_ADDRESS', '').strip()

        if not rpc_url or not contract:
            log.info("[ETH] ETH_RPC_URL or CONTRACT_ADDRESS not set. "
                     "Ethereum layer disabled.")
            return

        try:
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            # Inject PoA middleware for Sepolia (uses clique consensus)
            w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

            if not w3.is_connected():
                log.warning("[ETH] Could not connect to RPC: %s", rpc_url)
                return

            abi = _load_abi()
            self._contract = w3.eth.contract(
                address=Web3.to_checksum_address(contract),
                abi=abi,
            )
            self._w3 = w3

            # Load signing account if private key is available
            pk = os.getenv('ETH_PRIVATE_KEY', '').strip()
            if pk:
                self._account = w3.eth.account.from_key(pk)

            self.enabled = True
            log.info("[ETH] Connected to Sepolia. Contract: %s", contract[:10] + '...')

        except Exception as exc:
            log.warning("[ETH] Ethereum init failed: %s", exc)

    # ── Public API ────────────────────────────────────────────────────────────

    def is_trusted(self, mac_str: str) -> bool:
        """
        Read-only call - no gas needed.
        Returns True if the MAC is whitelisted on-chain, False otherwise.
        Returns False (safe default) if Ethereum is disabled or call fails.
        """
        if not self.enabled:
            return False
        try:
            mac6 = _mac_to_bytes6(mac_str)
            return self._contract.functions.isTrusted(mac6).call()
        except Exception as exc:
            log.warning("[ETH] isTrusted(%s) failed: %s", mac_str, exc)
            return False

    def log_anomaly(self, mac_str: str, risk_level: str, reason: str) -> str | None:
        """
        Emit AnomalyLogged event on-chain.
        Requires ETH_PRIVATE_KEY to sign the transaction.
        Returns tx hash string or None on failure.
        """
        if not self.enabled or not self._account:
            return None
        try:
            mac6   = _mac_to_bytes6(mac_str)
            w3     = self._w3
            nonce  = w3.eth.get_transaction_count(self._account.address)
            tx     = self._contract.functions.logAnomaly(
                mac6, risk_level[:16], reason[:128]
            ).build_transaction({
                'from':     self._account.address,
                'nonce':    nonce,
                'gas':      80_000,
                'gasPrice': w3.eth.gas_price,
            })
            signed = self._account.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            log.info("[ETH] logAnomaly tx: 0x%s", tx_hash.hex())
            return '0x' + tx_hash.hex()
        except Exception as exc:
            log.warning("[ETH] logAnomaly(%s) failed: %s", mac_str, exc)
            return None

    def register_device(self, mac_str: str, name: str) -> str | None:
        """
        Whitelist a device on-chain (admin function).
        Requires ETH_PRIVATE_KEY to be the contract admin.
        Returns tx hash string or None on failure.
        """
        if not self.enabled or not self._account:
            log.warning("[ETH] Cannot register: ETH_PRIVATE_KEY not set.")
            return None
        try:
            mac6   = _mac_to_bytes6(mac_str)
            w3     = self._w3
            nonce  = w3.eth.get_transaction_count(self._account.address)
            tx     = self._contract.functions.registerDevice(
                mac6, name[:64]
            ).build_transaction({
                'from':     self._account.address,
                'nonce':    nonce,
                'gas':      120_000,
                'gasPrice': w3.eth.gas_price,
            })
            signed  = self._account.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            log.info("[ETH] registerDevice tx: 0x%s", tx_hash.hex())
            return '0x' + tx_hash.hex()
        except Exception as exc:
            log.warning("[ETH] registerDevice(%s) failed: %s", mac_str, exc)
            return None

    def revoke_device(self, mac_str: str) -> str | None:
        """
        Revoke a previously trusted device on-chain (admin function).
        Returns tx hash string or None on failure.
        """
        if not self.enabled or not self._account:
            return None
        try:
            mac6   = _mac_to_bytes6(mac_str)
            w3     = self._w3
            nonce  = w3.eth.get_transaction_count(self._account.address)
            tx     = self._contract.functions.revokeDevice(mac6).build_transaction({
                'from':     self._account.address,
                'nonce':    nonce,
                'gas':      60_000,
                'gasPrice': w3.eth.gas_price,
            })
            signed  = self._account.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            log.info("[ETH] revokeDevice tx: 0x%s", tx_hash.hex())
            return '0x' + tx_hash.hex()
        except Exception as exc:
            log.warning("[ETH] revokeDevice(%s) failed: %s", mac_str, exc)
            return None

    def get_device(self, mac_str: str) -> dict | None:
        """
        Fetch device info dict from the contract.
        Returns None if Ethereum is disabled or call fails.
        """
        if not self.enabled:
            return None
        try:
            mac6 = _mac_to_bytes6(mac_str)
            name, trusted, reg_at, rev_at = (
                self._contract.functions.getDevice(mac6).call()
            )
            return {
                'name':          name,
                'trusted':       trusted,
                'registered_at': reg_at,
                'revoked_at':    rev_at,
            }
        except Exception as exc:
            log.warning("[ETH] getDevice(%s) failed: %s", mac_str, exc)
            return None


# ── Module-level singleton ────────────────────────────────────────────────────
# Instantiated once; if env vars are missing it just stays disabled.
_registry: EthRegistry | None = None


def get_registry() -> EthRegistry:
    global _registry
    if _registry is None:
        _registry = EthRegistry()
    return _registry


# ── Convenience functions for use in main.py ─────────────────────────────────

def eth_is_trusted(mac_str: str) -> bool:
    return get_registry().is_trusted(mac_str)


def eth_is_trusted_batch(mac_list: list[str]) -> dict[str, bool]:
    """
    Check multiple MACs in parallel (ThreadPoolExecutor).
    Returns {mac_str: trusted_bool} dict.
    Falls back to False for all MACs if Ethereum is disabled.

    Paper section XII: "queries can be parallelized using asyncio,
    reducing total cycle overhead from O(N) serial latency to
    near-constant time with concurrent RPC calls."
    """
    reg = get_registry()
    if not reg.enabled:
        return {mac: False for mac in mac_list}

    from concurrent.futures import ThreadPoolExecutor, as_completed

    results: dict[str, bool] = {}
    with ThreadPoolExecutor(max_workers=min(len(mac_list), 10)) as pool:
        future_to_mac = {pool.submit(reg.is_trusted, mac): mac
                         for mac in mac_list}
        for future in as_completed(future_to_mac):
            mac = future_to_mac[future]
            try:
                results[mac] = future.result()
            except Exception:
                results[mac] = False
    return results


def eth_log_anomaly(mac_str: str, risk_level: str, reason: str) -> str | None:
    return get_registry().log_anomaly(mac_str, risk_level, reason)


def eth_register_device(mac_str: str, name: str) -> str | None:
    return get_registry().register_device(mac_str, name)


def eth_enabled() -> bool:
    return get_registry().enabled


if __name__ == '__main__':
    import sys
    logging.basicConfig(level=logging.INFO)
    reg = get_registry()
    if not reg.enabled:
        print("Ethereum not configured. Set ETH_RPC_URL and CONTRACT_ADDRESS.")
        sys.exit(0)

    # Quick smoke test
    test_mac = 'AA:BB:CC:DD:EE:FF'
    print(f"isTrusted({test_mac}): {reg.is_trusted(test_mac)}")
    count_fn = reg._contract.functions.deviceCount().call()
    print(f"Total registered devices on-chain: {count_fn}")
