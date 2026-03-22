#!/usr/bin/env python3
"""
Benchmark 5: Batch Operation Throughput
Compares single-order vs batch-order placement latency.
Only runs on platforms with testnet funds AND batch support.

Note: With $0 budget (Plan A), this test is largely placeholder.
Actual batch testing requires funded accounts on platforms that
support batch operations (Hyperliquid, Lighter, Paradex, Aster).
"""

import asyncio
import json
import time
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "platforms.json"
RESULTS_DIR = PROJECT_ROOT / "results"


def load_platforms():
    with open(CONFIG_PATH) as f:
        return json.load(f)


async def run_all(platform_filter: str = "all"):
    platforms = load_platforms()
    RESULTS_DIR.mkdir(exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  Batch Operation Throughput Test")
    print(f"  Note: Requires funded testnet accounts with batch API support")
    print(f"{'='*60}\n")

    all_results = []

    for pid, cfg in platforms.items():
        if platform_filter != "all" and pid not in platform_filter.split(","):
            continue

        caps = cfg.get("capabilities", {})
        display_name = cfg["display_name"]

        if not caps.get("has_batch"):
            reason = "NO_BATCH_SUPPORT"
        elif not caps.get("has_testnet_funds"):
            reason = "NO_TESTNET_FUNDS"
        else:
            reason = "SDK_NOT_IMPLEMENTED"

        all_results.append({
            "platform": pid,
            "display_name": display_name,
            "batch_throughput": reason,
        })
        print(f"  [{display_name}] {reason}")

    combined_path = RESULTS_DIR / "all_batch_throughput.json"
    with open(combined_path, "w") as f:
        json.dump({
            "test": "batch_throughput",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "note": "Plan A ($0 budget): batch throughput tests require funded accounts. "
                    "Platforms with batch support: Hyperliquid, Lighter, Paradex, Aster, trade[XYZ].",
            "results": all_results,
        }, f, indent=2, ensure_ascii=False)

    print(f"\n  Results saved to {RESULTS_DIR}/")
    print(f"  NOTE: To run actual batch tests, fund the test wallet and re-run with --funded")


def main():
    parser = argparse.ArgumentParser(description="Batch Operation Throughput Test")
    parser.add_argument("--platform", default="all")
    args = parser.parse_args()
    asyncio.run(run_all(args.platform))


if __name__ == "__main__":
    main()
