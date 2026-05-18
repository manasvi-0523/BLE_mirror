"""
Admin script: register trusted BLE devices on-chain.

Usage:
    python contracts/register_device.py AA:BB:CC:DD:EE:FF "My Laptop"
    python contracts/register_device.py --revoke AA:BB:CC:DD:EE:FF
    python contracts/register_device.py --list

Required environment variables (put in .env and use python-dotenv, or export manually):
    ETH_RPC_URL       - e.g. https://sepolia.infura.io/v3/YOUR_PROJECT_ID
    CONTRACT_ADDRESS  - deployed contract address on Sepolia
    ETH_PRIVATE_KEY   - hex private key of the admin account (no 0x prefix needed)

How to deploy the contract (one-time):
    1. Open https://remix.ethereum.org
    2. Create contracts/BLETrustRegistry.sol, paste the Solidity code
    3. Compile with Solidity 0.8.19
    4. Deploy to Sepolia via MetaMask (Injected Web3 provider)
    5. Copy the deployed contract address into ETH_CONTRACT_ADDRESS env var
    6. Get free Sepolia ETH from: https://sepoliafaucet.com or https://faucet.quicknode.com/ethereum/sepolia
"""

import argparse
import os
import sys

# Allow running from project root or contracts/ dir
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Load .env if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, rely on shell env vars

from blockchain.eth_registry import get_registry


def cmd_register(mac: str, name: str):
    reg = get_registry()
    if not reg.enabled:
        print("[ERROR] Ethereum not configured.")
        print("        Set ETH_RPC_URL, CONTRACT_ADDRESS, and ETH_PRIVATE_KEY.")
        sys.exit(1)
    print(f"[ETH] Registering {mac!r} as {name!r} on-chain...")
    tx = reg.register_device(mac, name)
    if tx:
        print(f"[ETH] Transaction submitted: {tx}")
        print(f"      View on Etherscan: https://sepolia.etherscan.io/tx/{tx}")
    else:
        print("[ERROR] Transaction failed. Check logs.")
        sys.exit(1)


def cmd_revoke(mac: str):
    reg = get_registry()
    if not reg.enabled:
        print("[ERROR] Ethereum not configured.")
        sys.exit(1)
    print(f"[ETH] Revoking {mac!r} on-chain...")
    tx = reg.revoke_device(mac)
    if tx:
        print(f"[ETH] Transaction submitted: {tx}")
        print(f"      View on Etherscan: https://sepolia.etherscan.io/tx/{tx}")
    else:
        print("[ERROR] Transaction failed. Check logs.")
        sys.exit(1)


def cmd_check(mac: str):
    reg = get_registry()
    if not reg.enabled:
        print("[ERROR] Ethereum not configured.")
        sys.exit(1)
    trusted = reg.is_trusted(mac)
    info    = reg.get_device(mac)
    print(f"\nMAC:     {mac}")
    print(f"Trusted: {trusted}")
    if info:
        print(f"Name:    {info['name'] or '(not registered)'}")
        if info['registered_at']:
            from datetime import datetime
            ts = datetime.utcfromtimestamp(info['registered_at'])
            print(f"Registered: {ts.strftime('%Y-%m-%d %H:%M UTC')}")
        if info['revoked_at']:
            from datetime import datetime
            ts = datetime.utcfromtimestamp(info['revoked_at'])
            print(f"Revoked:    {ts.strftime('%Y-%m-%d %H:%M UTC')}")
    print()


def cmd_status():
    reg = get_registry()
    if not reg.enabled:
        print("[ETH] Status: OFFLINE")
        print("      Missing environment variables:")
        for var in ('ETH_RPC_URL', 'CONTRACT_ADDRESS', 'ETH_PRIVATE_KEY'):
            val = os.getenv(var, '')
            status = 'SET' if val else 'NOT SET'
            print(f"        {var}: {status}")
        return
    contract = os.getenv('CONTRACT_ADDRESS', '')
    print("[ETH] Status: CONNECTED")
    print(f"      Contract: {contract}")
    count = reg._contract.functions.deviceCount().call()
    print(f"      Registered device MACs: {count}")
    admin = reg._contract.functions.admin().call()
    print(f"      Admin address: {admin}")
    signer = reg._account.address if reg._account else 'NOT SET'
    print(f"      Signer (ETH_PRIVATE_KEY): {signer}")
    if reg._account and reg._account.address.lower() != admin.lower():
        print("      [WARN] Signer is NOT the contract admin - write calls will fail")


def main():
    parser = argparse.ArgumentParser(
        description="Admin tool for the on-chain BLE trust registry"
    )
    subparsers = parser.add_subparsers(dest='cmd')

    reg_p = subparsers.add_parser(
        'register', help='Whitelist a device on-chain')
    reg_p.add_argument('mac',  help='MAC address, e.g. AA:BB:CC:DD:EE:FF')
    reg_p.add_argument('name', help='Human-readable device name')

    rev_p = subparsers.add_parser(
        'revoke', help='Revoke a trusted device on-chain')
    rev_p.add_argument('mac', help='MAC address to revoke')

    chk_p = subparsers.add_parser(
        'check', help='Check trust status of a MAC address')
    chk_p.add_argument('mac', help='MAC address to check')

    subparsers.add_parser(
        'status', help='Show Ethereum connection status and contract info')

    args = parser.parse_args()

    if args.cmd == 'register':
        cmd_register(args.mac, args.name)
    elif args.cmd == 'revoke':
        cmd_revoke(args.mac)
    elif args.cmd == 'check':
        cmd_check(args.mac)
    elif args.cmd == 'status':
        cmd_status()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
