#!/usr/bin/env python3
"""
Benchmark 4: Rate Limit Probe
Gradually increases request rate until first HTTP 429,
records the actual threshold and recovery time.
"""

import asyncio
import json
import time
import argparse
from pathlib import Path
from typing import Optional

import aiohttp

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "platforms.json"
RESULTS_DIR = PROJECT_ROOT / "results"


def load_platforms():
    with open(CONFIG_PATH) as f:
        return json.load(f)


async def probe_rate_limit(platform_id: str, config: dict) -> dict:
    """Probe rate limits by exponential ramp until first 429."""
    display_name = config["display_name"]
    caps = config.get("capabilities", {})

    if not caps.get("has_public_rest", False):
        print(f"  [{display_name}] SKIP - no public REST API")
        return {
            "platform": platform_id,
            "display_name": display_name,
            "rate_limit": "NOT_SUPPORTED",
        }

    ping = config["ping_endpoint"]
    base_url = config.get("rest_testnet") or config["rest_base"]
    url = base_url.rstrip("/") + ping["path"]
    method = ping["method"]
    body = ping.get("body")

    print(f"  [{display_name}] Probing {method} {url}")

    # Ramp schedule: requests per second, duration in seconds
    ramp_levels = [1, 2, 4, 8, 16, 32, 64]
    results_log = []
    first_429_rps = None
    first_429_time = None
    recovery_time_sec = None
    total_requests = 0
    total_429s = 0
    total_errors = 0

    async with aiohttp.ClientSession(
        headers={"User-Agent": "PerpDEX-Benchmark/1.0"}
    ) as session:
        for rps in ramp_levels:
            interval = 1.0 / rps
            duration = 10  # seconds at this level
            count = int(rps * duration)
            level_429s = 0
            level_errors = 0

            print(f"    Ramp: {rps} req/s for {duration}s ({count} requests)")

            for i in range(count):
                start = time.perf_counter()
                try:
                    if method == "POST":
                        async with session.post(url, json=body, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                            status = resp.status
                    else:
                        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                            status = resp.status

                    total_requests += 1

                    if status == 429:
                        level_429s += 1
                        total_429s += 1
                        if first_429_rps is None:
                            first_429_rps = rps
                            first_429_time = time.time()
                            print(f"    FIRST 429 at {rps} req/s (request #{total_requests})")

                    elif status == 418:
                        # IP banned (Binance-style)
                        print(f"    IP BANNED (418) at {rps} req/s — stopping immediately")
                        first_429_rps = first_429_rps or rps
                        results_log.append({
                            "rps": rps,
                            "requests": i + 1,
                            "status_429": level_429s,
                            "ip_banned": True,
                        })
                        break

                    elif status >= 400:
                        level_errors += 1
                        total_errors += 1

                except Exception as e:
                    total_errors += 1
                    level_errors += 1

                # Maintain target rate
                elapsed = time.perf_counter() - start
                sleep_time = interval - elapsed
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)

            results_log.append({
                "rps": rps,
                "requests": count,
                "status_429": level_429s,
                "other_errors": level_errors,
            })

            # If we hit 429, stop ramping and measure recovery
            if first_429_rps is not None:
                print(f"    Measuring recovery time...")
                # Wait and probe every 1s until we get a 200
                for wait in range(60):
                    await asyncio.sleep(1)
                    try:
                        if method == "POST":
                            async with session.post(url, json=body, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                                if resp.status == 200:
                                    recovery_time_sec = time.time() - first_429_time
                                    print(f"    Recovered after {recovery_time_sec:.1f}s")
                                    break
                        else:
                            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                                if resp.status == 200:
                                    recovery_time_sec = time.time() - first_429_time
                                    print(f"    Recovered after {recovery_time_sec:.1f}s")
                                    break
                    except Exception:
                        continue
                else:
                    recovery_time_sec = 60.0
                    print(f"    Recovery not detected within 60s")
                break

    result = {
        "platform": platform_id,
        "display_name": display_name,
        "rate_limit": {
            "endpoint": f"{method} {ping['path']}",
            "base_url": base_url,
            "method": "exponential_ramp",
            "ramp_levels_rps": ramp_levels,
            "total_requests": total_requests,
            "total_429s": total_429s,
            "total_errors": total_errors,
            "first_429_at_rps": first_429_rps,
            "recovery_time_sec": round(recovery_time_sec, 2) if recovery_time_sec else None,
            "ramp_log": results_log,
        },
    }

    if first_429_rps:
        print(f"  [{display_name}] Rate limited at {first_429_rps} req/s, "
              f"recovery {recovery_time_sec:.1f}s ({total_requests} total reqs)")
    else:
        print(f"  [{display_name}] No rate limit hit up to {ramp_levels[-1]} req/s "
              f"({total_requests} total reqs)")

    return result


async def run_all(platform_filter: Optional[str] = None):
    platforms = load_platforms()
    RESULTS_DIR.mkdir(exist_ok=True)

    targets = {}
    if platform_filter and platform_filter != "all":
        for pid in platform_filter.split(","):
            pid = pid.strip()
            if pid in platforms:
                targets[pid] = platforms[pid]
    else:
        targets = platforms

    print(f"\n{'='*60}")
    print(f"  Rate Limit Probe — {len(targets)} platforms")
    print(f"  Method: exponential ramp (1→2→4→8→16→32→64 req/s)")
    print(f"  Stop on first 429, then measure recovery")
    print(f"{'='*60}\n")

    all_results = []
    for pid, cfg in targets.items():
        result = await probe_rate_limit(pid, cfg)
        all_results.append(result)

        out_path = RESULTS_DIR / f"{pid}_rate_limit.json"
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        # Cool down between platforms
        await asyncio.sleep(3)

    # Save combined
    combined_path = RESULTS_DIR / "all_rate_limit.json"
    with open(combined_path, "w") as f:
        json.dump({
            "test": "rate_limit_probe",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "results": all_results,
        }, f, indent=2, ensure_ascii=False)

    # Summary
    print(f"\n{'='*60}")
    print(f"  Summary")
    print(f"{'='*60}")
    print(f"  {'Platform':<20} {'First 429':>12} {'Recovery':>10} {'Total Reqs':>12}")
    print(f"  {'-'*20} {'-'*12} {'-'*10} {'-'*12}")

    for r in all_results:
        rl = r.get("rate_limit", {})
        if isinstance(rl, str):
            print(f"  {r['display_name']:<20} {'—':>12} {'—':>10} {rl:>12}")
        else:
            f429 = f"{rl['first_429_at_rps']} req/s" if rl.get("first_429_at_rps") else "NOT HIT"
            rec = f"{rl['recovery_time_sec']}s" if rl.get("recovery_time_sec") else "—"
            print(f"  {r['display_name']:<20} {f429:>12} {rec:>10} {rl['total_requests']:>12}")

    print(f"\n  Results saved to {RESULTS_DIR}/")


def main():
    parser = argparse.ArgumentParser(description="Rate Limit Probe")
    parser.add_argument("--platform", default="all", help="Platform ID or comma-separated list")
    args = parser.parse_args()

    asyncio.run(run_all(args.platform))


if __name__ == "__main__":
    main()
