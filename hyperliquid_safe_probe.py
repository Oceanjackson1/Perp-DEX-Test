#!/usr/bin/env python3.11

import json
import re
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SDK_PATH = ROOT / ".pydeps_hl"
DEFAULT_WALLET_FILE = ROOT / "evm_wallet_20260320_165220.txt"

ADDRESS_PATTERN = re.compile(r"^Address:\s*(0x[a-fA-F0-9]{40})$")
PRIVATE_KEY_PATTERN = re.compile(r"^Private Key:\s*(0x[a-fA-F0-9]{64})$")

sys.path.insert(0, str(SDK_PATH))

from eth_account import Account  # noqa: E402
from hyperliquid.exchange import Exchange  # noqa: E402
from hyperliquid.utils import constants  # noqa: E402
import requests  # noqa: E402


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


def try_call(fn):
    try:
        return {"ok": True, "result": fn()}
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }


def post_info(payload):
    response = requests.post(
        f"{constants.TESTNET_API_URL}/info",
        json=payload,
        timeout=30,
        headers={"Content-Type": "application/json", "User-Agent": "codex-hl-probe"},
    )
    return {
        "status_code": response.status_code,
        "json": response.json(),
    }


def main() -> int:
    address, private_key = load_wallet(DEFAULT_WALLET_FILE)
    wallet = Account.from_key(private_key)

    meta = post_info({"type": "meta"})["json"]
    exchange = Exchange(
        wallet,
        base_url=constants.TESTNET_API_URL,
        meta=meta,
        spot_meta={"universe": [], "tokens": []},
    )

    results = {
        "wallet_address": address,
        "base_url": constants.TESTNET_API_URL,
        "meta_probe": {
            "ok": True,
            "universe_count": len(meta.get("universe", [])),
        },
        "pre_state": try_call(lambda: post_info({"type": "clearinghouseState", "user": address})),
        "pre_open_orders": try_call(lambda: post_info({"type": "openOrders", "user": address})),
    }

    nonce = int(time.time() * 1000)
    results["noop"] = try_call(lambda: exchange.noop(nonce))

    # Intentionally use an IOC market-style order on a zero-balance wallet.
    # If auth/signing works, the expected outcome is a clean trading-layer rejection
    # such as insufficient margin, not an auth-format failure.
    results["market_open_btc_buy_0_001"] = try_call(lambda: exchange.market_open("BTC", True, 0.001, slippage=0.01))

    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
