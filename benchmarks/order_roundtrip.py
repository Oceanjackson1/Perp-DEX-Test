#!/usr/bin/env python3
"""
Benchmark 3: Order Round-trip Latency
Places a far-from-market limit order, waits for confirmation,
cancels it, and measures the full cycle. Only runs on platforms
with testnet funds available.

Supported platforms: Extended (x10) testnet
"""

import asyncio
import json
import time
import argparse
import statistics
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "platforms.json"
RESULTS_DIR = PROJECT_ROOT / "results"
WALLET_FILE = PROJECT_ROOT / "evm_wallet_20260320_165220.txt"

ROUNDS = 20


def load_platforms():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def load_wallet():
    """Load test wallet from file."""
    if not WALLET_FILE.exists():
        return None, None
    text = WALLET_FILE.read_text()
    address = None
    private_key = None
    for line in text.strip().split("\n"):
        if "Address:" in line:
            address = line.split("Address:")[1].strip()
        elif "Private Key:" in line:
            private_key = line.split("Private Key:")[1].strip()
    return address, private_key


def percentile(data: list[float], p: float) -> float:
    if not data:
        return 0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * (p / 100)
    f = int(k)
    c = f + 1
    if c >= len(sorted_data):
        return sorted_data[f]
    return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])


async def test_extended_roundtrip() -> dict:
    """Test order round-trip on Extended (x10) testnet using their SDK."""
    try:
        import sys
        sys.path.insert(0, str(PROJECT_ROOT / ".pydeps311" / "lib" / "python3.11" / "site-packages"))
        from x10.perpetual.accounts import StarkPerpetualAccount
        from x10.perpetual.configuration import TESTNET_CONFIG
        from x10.perpetual.orders import OrderSide, OrderType
    except ImportError:
        return {
            "platform": "extended",
            "display_name": "Extended (x10)",
            "order_roundtrip": {
                "status": "SDK_NOT_AVAILABLE",
                "note": "x10-perpetual SDK not installed. Run: pip install x10-perpetual",
            },
        }

    address, private_key = load_wallet()
    if not private_key:
        return {
            "platform": "extended",
            "display_name": "Extended (x10)",
            "order_roundtrip": {"status": "NO_WALLET", "note": "Wallet file not found"},
        }

    print(f"  [Extended] Testing order round-trip on testnet ({ROUNDS} rounds)")

    place_latencies = []
    cancel_latencies = []
    errors = []

    try:
        account = StarkPerpetualAccount(
            vault=0,
            private_key=private_key,
            config=TESTNET_CONFIG,
        )

        for i in range(ROUNDS):
            # Place a far-from-market buy limit order (price = $1, won't fill)
            place_start = time.perf_counter()
            try:
                order = await account.place_order(
                    market="BTC-USD",
                    side=OrderSide.BUY,
                    order_type=OrderType.LIMIT,
                    price=1.0,  # Far below market
                    size=0.001,  # Minimum size
                )
                place_elapsed = (time.perf_counter() - place_start) * 1000
                place_latencies.append(place_elapsed)

                # Cancel the order
                cancel_start = time.perf_counter()
                await account.cancel_order(order_id=order.id)
                cancel_elapsed = (time.perf_counter() - cancel_start) * 1000
                cancel_latencies.append(cancel_elapsed)

                if (i + 1) % 5 == 0:
                    print(f"    {i + 1}/{ROUNDS}: place={place_elapsed:.0f}ms cancel={cancel_elapsed:.0f}ms")

            except Exception as e:
                place_elapsed = (time.perf_counter() - place_start) * 1000
                errors.append({"round": i, "error": str(e), "elapsed_ms": round(place_elapsed, 2)})
                print(f"    {i + 1}/{ROUNDS}: ERROR - {e}")

            await asyncio.sleep(0.5)

    except Exception as e:
        return {
            "platform": "extended",
            "display_name": "Extended (x10)",
            "order_roundtrip": {"status": "SETUP_ERROR", "error": str(e)},
        }

    result = {"platform": "extended", "display_name": "Extended (x10)"}

    if place_latencies:
        result["order_roundtrip"] = {
            "status": "OK",
            "network": "testnet",
            "rounds": ROUNDS,
            "successful": len(place_latencies),
            "errors": len(errors),
            "place_order": {
                "p50_ms": round(percentile(place_latencies, 50), 2),
                "p95_ms": round(percentile(place_latencies, 95), 2),
                "mean_ms": round(statistics.mean(place_latencies), 2),
            },
            "cancel_order": {
                "p50_ms": round(percentile(cancel_latencies, 50), 2),
                "p95_ms": round(percentile(cancel_latencies, 95), 2),
                "mean_ms": round(statistics.mean(cancel_latencies), 2),
            },
            "full_roundtrip": {
                "p50_ms": round(percentile([p + c for p, c in zip(place_latencies, cancel_latencies)], 50), 2),
                "p95_ms": round(percentile([p + c for p, c in zip(place_latencies, cancel_latencies)], 95), 2),
                "mean_ms": round(statistics.mean([p + c for p, c in zip(place_latencies, cancel_latencies)]), 2),
            },
        }
        print(f"  [Extended] Place p50={result['order_roundtrip']['place_order']['p50_ms']}ms "
              f"Cancel p50={result['order_roundtrip']['cancel_order']['p50_ms']}ms")
    else:
        result["order_roundtrip"] = {"status": "ALL_FAILED", "errors": errors}

    return result


async def run_all(platform_filter: str = "all", rounds: int = ROUNDS):
    global ROUNDS
    ROUNDS = rounds
    RESULTS_DIR.mkdir(exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  Order Round-trip Latency Test")
    print(f"  Rounds: {ROUNDS} per platform")
    print(f"  Note: Only platforms with testnet funds are tested")
    print(f"{'='*60}\n")

    # Currently only Extended testnet has a proven write-path with SDK
    all_results = []

    testable = {
        "extended": test_extended_roundtrip,
    }

    for pid, test_fn in testable.items():
        if platform_filter != "all" and pid not in platform_filter.split(","):
            continue
        result = await test_fn()
        all_results.append(result)

        out_path = RESULTS_DIR / f"{pid}_order_roundtrip.json"
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    # Mark untestable platforms
    platforms = load_platforms()
    for pid, cfg in platforms.items():
        if pid not in [r["platform"] for r in all_results]:
            if platform_filter != "all" and pid not in platform_filter.split(","):
                continue
            caps = cfg.get("capabilities", {})
            if not caps.get("has_testnet_funds") or not caps.get("has_order_api"):
                reason = "NO_TESTNET_FUNDS" if not caps.get("has_testnet_funds") else "NO_ORDER_API"
            else:
                reason = "SDK_NOT_IMPLEMENTED"
            all_results.append({
                "platform": pid,
                "display_name": cfg["display_name"],
                "order_roundtrip": reason,
            })

    combined_path = RESULTS_DIR / "all_order_roundtrip.json"
    with open(combined_path, "w") as f:
        json.dump({
            "test": "order_roundtrip",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "rounds": ROUNDS,
            "results": all_results,
        }, f, indent=2, ensure_ascii=False)

    print(f"\n  Results saved to {RESULTS_DIR}/")


def main():
    parser = argparse.ArgumentParser(description="Order Round-trip Latency Test")
    parser.add_argument("--platform", default="all")
    parser.add_argument("--rounds", type=int, default=ROUNDS)
    args = parser.parse_args()

    asyncio.run(run_all(args.platform, args.rounds))


if __name__ == "__main__":
    main()
