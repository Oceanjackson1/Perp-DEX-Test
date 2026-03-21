#!/usr/bin/env python3.11

import asyncio
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SDK_PATH = ROOT / ".pydeps311"
DEFAULT_WALLET_FILE = ROOT / "evm_wallet_20260320_165220.txt"

ADDRESS_PATTERN = re.compile(r"^Address:\s*(0x[a-fA-F0-9]{40})$")
PRIVATE_KEY_PATTERN = re.compile(r"^Private Key:\s*(0x[a-fA-F0-9]{64})$")

sys.path.insert(0, str(SDK_PATH))

from x10.perpetual.configuration import TESTNET_CONFIG  # noqa: E402
from x10.perpetual.trading_client.account_module import AccountModule  # noqa: E402
from x10.perpetual.user_client.user_client import UserClient  # noqa: E402


def load_wallet(wallet_file: Path) -> tuple[str, str]:
    address = None
    private_key = None

    for raw_line in wallet_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        address_match = ADDRESS_PATTERN.match(line)
        if address_match:
            address = address_match.group(1)
            continue

        private_key_match = PRIVATE_KEY_PATTERN.match(line)
        if private_key_match:
            private_key = private_key_match.group(1)

    if not address or not private_key:
        raise ValueError(f"Could not parse wallet file: {wallet_file}")

    return address, private_key


def redact_api_key(api_key: str) -> dict:
    if len(api_key) <= 8:
        return {"prefix": api_key, "length": len(api_key)}
    return {"prefix": api_key[:8], "suffix": api_key[-4:], "length": len(api_key)}


async def run_probe(wallet_file: Path) -> dict:
    address, private_key = load_wallet(wallet_file)
    client = UserClient(TESTNET_CONFIG, lambda: private_key)
    results = {
        "wallet_address": address,
        "testnet_host": TESTNET_CONFIG.onboarding_url,
        "api_base_url": TESTNET_CONFIG.api_base_url,
    }

    onboarded_account = None
    fetched_accounts = []

    try:
        onboarded = await client.onboard()
        onboarded_account = onboarded.account
        results["onboard"] = {
            "ok": True,
            "account": onboarded.account.model_dump(mode="json"),
            "l2_public_key": onboarded.l2_key_pair.public_hex,
        }
    except Exception as exc:  # noqa: BLE001
        results["onboard"] = {
            "ok": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

    try:
        accounts = await client.get_accounts()
        fetched_accounts = accounts
        results["get_accounts"] = {
            "ok": True,
            "count": len(accounts),
            "accounts": [
                {
                    "account": account.account.model_dump(mode="json"),
                    "l2_public_key": account.l2_key_pair.public_hex,
                }
                for account in accounts
            ],
        }
    except Exception as exc:  # noqa: BLE001
        results["get_accounts"] = {
            "ok": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

    target_account = None
    if onboarded_account is not None:
        target_account = onboarded_account
    elif fetched_accounts:
        target_account = fetched_accounts[0].account

    if target_account is not None:
        try:
            api_key = await client.create_account_api_key(target_account, description="codex probe")
            results["create_account_api_key"] = {
                "ok": True,
                "api_key": redact_api_key(api_key),
                "account_id": target_account.id,
            }
        except Exception as exc:  # noqa: BLE001
            results["create_account_api_key"] = {
                "ok": False,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "account_id": target_account.id,
            }
    else:
        results["create_account_api_key"] = {
            "ok": False,
            "error_type": "NoAccountAvailable",
            "error": "No onboarded account was available for API key creation.",
        }

    if results["create_account_api_key"].get("ok"):
        account_module = AccountModule(TESTNET_CONFIG, api_key=api_key)
        try:
            account_response = await account_module.get_account()
            account_data = account_response.data
            results["private_get_account"] = {
                "ok": True,
                "account": account_data.model_dump(mode="json") if account_data is not None else None,
            }
        except Exception as exc:  # noqa: BLE001
            results["private_get_account"] = {
                "ok": False,
                "error_type": type(exc).__name__,
                "error": str(exc),
            }

        try:
            orders_response = await account_module.get_open_orders()
            orders = orders_response.data or []
            results["private_get_open_orders"] = {
                "ok": True,
                "count": len(orders),
            }
        except Exception as exc:  # noqa: BLE001
            results["private_get_open_orders"] = {
                "ok": False,
                "error_type": type(exc).__name__,
                "error": str(exc),
            }

        await account_module.close_session()

    await client.close_session()
    return results


def main() -> int:
    wallet_file = DEFAULT_WALLET_FILE
    results = asyncio.run(run_probe(wallet_file))
    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
