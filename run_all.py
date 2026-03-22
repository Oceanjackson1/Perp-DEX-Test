#!/usr/bin/env python3
"""
Perp DEX API Benchmark Runner
Runs all benchmark tests sequentially and generates a report.

Usage:
    python run_all.py                          # Full run (~2-3 hours)
    python run_all.py --skip ws_stability      # Skip 1hr stability test (~20 min)
    python run_all.py --platform hyperliquid   # Single platform
    python run_all.py --quick                  # Quick mode (fewer samples, shorter durations)
"""

import asyncio
import argparse
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent


def run_benchmark(script: str, args: list[str] = None):
    """Run a benchmark script as a subprocess."""
    cmd = [sys.executable, str(PROJECT_ROOT / "benchmarks" / script)]
    if args:
        cmd.extend(args)

    print(f"\n{'#'*60}")
    print(f"  Running: {script}")
    print(f"  Command: {' '.join(cmd)}")
    print(f"{'#'*60}\n")

    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    if result.returncode != 0:
        print(f"\n  WARNING: {script} exited with code {result.returncode}")
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Perp DEX API Benchmark Runner")
    parser.add_argument("--platform", default="all", help="Platform filter")
    parser.add_argument("--skip", nargs="*", default=[], help="Tests to skip (rest, ws_orderbook, order_roundtrip, rate_limit, batch, ws_stability)")
    parser.add_argument("--quick", action="store_true", help="Quick mode: fewer samples, shorter durations")
    args = parser.parse_args()

    platform_args = ["--platform", args.platform]

    start = time.time()
    print(f"\n{'='*60}")
    print(f"  Perp DEX API Benchmark Suite")
    print(f"  Platform: {args.platform}")
    print(f"  Skip: {args.skip or 'none'}")
    print(f"  Quick mode: {args.quick}")
    print(f"  Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    tests_run = 0
    tests_failed = 0

    # Test 1: REST Latency
    if "rest" not in args.skip:
        extra = ["--samples", "30"] if args.quick else []
        rc = run_benchmark("rest_latency.py", platform_args + extra)
        tests_run += 1
        if rc != 0:
            tests_failed += 1

    # Test 2: WS Orderbook
    if "ws_orderbook" not in args.skip:
        extra = ["--duration", "15"] if args.quick else []
        rc = run_benchmark("ws_orderbook.py", platform_args + extra)
        tests_run += 1
        if rc != 0:
            tests_failed += 1

    # Test 3: Order Roundtrip
    if "order_roundtrip" not in args.skip:
        extra = ["--rounds", "5"] if args.quick else []
        rc = run_benchmark("order_roundtrip.py", platform_args + extra)
        tests_run += 1
        if rc != 0:
            tests_failed += 1

    # Test 4: Rate Limit Probe
    if "rate_limit" not in args.skip:
        rc = run_benchmark("rate_limit_probe.py", platform_args)
        tests_run += 1
        if rc != 0:
            tests_failed += 1

    # Test 5: Batch Throughput
    if "batch" not in args.skip:
        rc = run_benchmark("batch_throughput.py", platform_args)
        tests_run += 1
        if rc != 0:
            tests_failed += 1

    # Test 6: WS Stability
    if "ws_stability" not in args.skip:
        extra = ["--duration", "5"] if args.quick else []
        rc = run_benchmark("ws_stability.py", platform_args + extra)
        tests_run += 1
        if rc != 0:
            tests_failed += 1

    # Generate Report
    print(f"\n{'#'*60}")
    print(f"  Generating report...")
    print(f"{'#'*60}\n")
    run_benchmark("report_generator.py")

    elapsed = time.time() - start
    elapsed_min = elapsed / 60

    print(f"\n{'='*60}")
    print(f"  Benchmark Suite Complete")
    print(f"  Tests run: {tests_run}, Failed: {tests_failed}")
    print(f"  Total time: {elapsed_min:.1f} minutes")
    print(f"  Results: results/")
    print(f"  Report: benchmark_report_{time.strftime('%Y%m%d')}.md")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
