#!/usr/bin/env python3
"""
Benchmark 1: REST API Latency
Sends 100 requests to each platform's lightest public endpoint,
measures round-trip time, and computes p50/p95/p99/mean/min/max.
"""

import asyncio
import json
import time
import argparse
import statistics
from pathlib import Path
from typing import Optional

import aiohttp

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "platforms.json"
RESULTS_DIR = PROJECT_ROOT / "results"

WARMUP_COUNT = 5
DEFAULT_SAMPLE_COUNT = 100
INTERVAL_MS = 200  # ms between requests
SAMPLE_COUNT = DEFAULT_SAMPLE_COUNT


def load_platforms():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def percentile(data: list[float], p: float) -> float:
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * (p / 100)
    f = int(k)
    c = f + 1
    if c >= len(sorted_data):
        return sorted_data[f]
    return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])


async def measure_single_request(
    session: aiohttp.ClientSession,
    url: str,
    method: str,
    body: Optional[dict],
) -> tuple[float, int, Optional[str]]:
    """Returns (latency_ms, status_code, error_or_none)."""
    start = time.perf_counter()
    try:
        if method == "POST":
            async with session.post(url, json=body, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                await resp.read()
                elapsed = (time.perf_counter() - start) * 1000
                server_time = resp.headers.get("X-Server-Time") or resp.headers.get("Date")
                return elapsed, resp.status, None
        else:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                await resp.read()
                elapsed = (time.perf_counter() - start) * 1000
                return elapsed, resp.status, None
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        return elapsed, 0, str(e)


async def benchmark_platform(platform_id: str, config: dict) -> dict:
    """Run REST latency benchmark for a single platform."""
    display_name = config["display_name"]
    caps = config.get("capabilities", {})

    if not caps.get("has_public_rest", False):
        print(f"  [{display_name}] SKIP - no public REST API")
        return {
            "platform": platform_id,
            "display_name": display_name,
            "rest_latency": "NOT_SUPPORTED",
        }

    ping = config["ping_endpoint"]
    base_url = config.get("rest_testnet") or config["rest_base"]
    url = base_url.rstrip("/") + ping["path"]
    method = ping["method"]
    body = ping.get("body")

    print(f"  [{display_name}] Testing {method} {url}")

    latencies = []
    errors = []

    async with aiohttp.ClientSession(
        headers={"User-Agent": "PerpDEX-Benchmark/1.0"}
    ) as session:
        # Warmup
        for i in range(WARMUP_COUNT):
            await measure_single_request(session, url, method, body)
            await asyncio.sleep(INTERVAL_MS / 1000)

        # Actual measurements
        for i in range(SAMPLE_COUNT):
            latency_ms, status, error = await measure_single_request(session, url, method, body)
            if error:
                errors.append({"sample": i, "error": error, "latency_ms": round(latency_ms, 2)})
            elif status == 429:
                errors.append({"sample": i, "error": f"HTTP {status} rate limited", "latency_ms": round(latency_ms, 2)})
                # Slow down if rate limited
                await asyncio.sleep(2)
            elif status >= 400:
                errors.append({"sample": i, "error": f"HTTP {status}", "latency_ms": round(latency_ms, 2)})
            else:
                latencies.append(latency_ms)

            if (i + 1) % 25 == 0:
                print(f"    {i + 1}/{SAMPLE_COUNT} done")

            await asyncio.sleep(INTERVAL_MS / 1000)

    if not latencies:
        print(f"  [{display_name}] FAILED - no successful requests")
        return {
            "platform": platform_id,
            "display_name": display_name,
            "rest_latency": {
                "status": "FAILED",
                "endpoint": f"{method} {ping['path']}",
                "errors": errors[:10],
            },
        }

    result = {
        "platform": platform_id,
        "display_name": display_name,
        "rest_latency": {
            "endpoint": f"{method} {ping['path']}",
            "base_url": base_url,
            "samples": len(latencies),
            "errors": len(errors),
            "p50_ms": round(percentile(latencies, 50), 2),
            "p95_ms": round(percentile(latencies, 95), 2),
            "p99_ms": round(percentile(latencies, 99), 2),
            "mean_ms": round(statistics.mean(latencies), 2),
            "min_ms": round(min(latencies), 2),
            "max_ms": round(max(latencies), 2),
            "stdev_ms": round(statistics.stdev(latencies), 2) if len(latencies) > 1 else 0,
        },
    }

    p50 = result["rest_latency"]["p50_ms"]
    p99 = result["rest_latency"]["p99_ms"]
    print(f"  [{display_name}] p50={p50}ms  p99={p99}ms  ({len(latencies)} OK, {len(errors)} errors)")
    return result


async def run_all(platform_filter: Optional[str] = None, samples: int = DEFAULT_SAMPLE_COUNT):
    global SAMPLE_COUNT
    SAMPLE_COUNT = samples
    platforms = load_platforms()
    RESULTS_DIR.mkdir(exist_ok=True)

    targets = {}
    if platform_filter and platform_filter != "all":
        for pid in platform_filter.split(","):
            pid = pid.strip()
            if pid in platforms:
                targets[pid] = platforms[pid]
            else:
                print(f"  WARNING: unknown platform '{pid}'")
    else:
        targets = platforms

    print(f"\n{'='*60}")
    print(f"  REST Latency Benchmark — {len(targets)} platforms")
    print(f"  Samples: {SAMPLE_COUNT} per platform (+ {WARMUP_COUNT} warmup)")
    print(f"  Interval: {INTERVAL_MS}ms between requests")
    print(f"{'='*60}\n")

    all_results = []
    for pid, cfg in targets.items():
        result = await benchmark_platform(pid, cfg)
        all_results.append(result)

        # Save individual result
        out_path = RESULTS_DIR / f"{pid}_rest_latency.json"
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    # Save combined results
    combined_path = RESULTS_DIR / "all_rest_latency.json"
    with open(combined_path, "w") as f:
        json.dump({
            "test": "rest_latency",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "config": {
                "warmup": WARMUP_COUNT,
                "samples": SAMPLE_COUNT,
                "interval_ms": INTERVAL_MS,
            },
            "results": all_results,
        }, f, indent=2, ensure_ascii=False)

    # Print summary table
    print(f"\n{'='*60}")
    print(f"  Summary (sorted by p50)")
    print(f"{'='*60}")
    print(f"  {'Platform':<20} {'p50':>8} {'p95':>8} {'p99':>8} {'Samples':>8}")
    print(f"  {'-'*20} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")

    sortable = [r for r in all_results if isinstance(r.get("rest_latency"), dict) and "p50_ms" in r["rest_latency"]]
    sortable.sort(key=lambda r: r["rest_latency"]["p50_ms"])
    for r in sortable:
        rl = r["rest_latency"]
        print(f"  {r['display_name']:<20} {rl['p50_ms']:>7.1f} {rl['p95_ms']:>7.1f} {rl['p99_ms']:>7.1f} {rl['samples']:>8}")

    skipped = [r for r in all_results if not isinstance(r.get("rest_latency"), dict) or "p50_ms" not in r.get("rest_latency", {})]
    for r in skipped:
        status = r["rest_latency"] if isinstance(r["rest_latency"], str) else "FAILED"
        print(f"  {r['display_name']:<20} {'—':>8} {'—':>8} {'—':>8} {status:>8}")

    print(f"\n  Results saved to {RESULTS_DIR}/")


def main():
    parser = argparse.ArgumentParser(description="REST API Latency Benchmark")
    parser.add_argument("--platform", default="all", help="Platform ID or comma-separated list (default: all)")
    parser.add_argument("--samples", type=int, default=SAMPLE_COUNT, help="Number of samples per platform")
    args = parser.parse_args()

    asyncio.run(run_all(args.platform, args.samples))


if __name__ == "__main__":
    main()
