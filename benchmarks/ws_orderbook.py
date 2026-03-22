#!/usr/bin/env python3
"""
Benchmark 2: WebSocket Orderbook Push Latency
Subscribes to each platform's orderbook channel for 60 seconds,
measures push intervals and server-to-client latency where available.
"""

import asyncio
import json
import time
import argparse
import statistics
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "platforms.json"
RESULTS_DIR = PROJECT_ROOT / "results"

DURATION_SEC = 60


def load_platforms():
    with open(CONFIG_PATH) as f:
        return json.load(f)


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


async def benchmark_native_ws(platform_id: str, config: dict) -> dict:
    """Benchmark platforms using native WebSocket protocol."""
    import websockets
    import websockets.exceptions

    display_name = config["display_name"]
    ws_url = config.get("ws_url")
    ws_config = config.get("orderbook_ws", {})
    subscribe_msg = ws_config.get("subscribe_msg") if ws_config else None

    if not ws_url or not subscribe_msg:
        return {"status": "NOT_SUPPORTED", "reason": "No WS URL or subscribe message"}

    print(f"  [{display_name}] Connecting to {ws_url}")

    timestamps = []
    server_timestamps = []
    message_count = 0

    extra_headers = {"User-Agent": "PerpDEX-Benchmark/1.0"}
    extensions = None
    if config.get("capabilities", {}).get("ws_requires_deflate"):
        import websockets.extensions.permessage_deflate as deflate
        extensions = [deflate.ClientPerMessageDeflateFactory()]

    try:
        async with websockets.connect(
            ws_url,
            additional_headers=extra_headers,
            extensions=extensions,
            ping_interval=20,
            ping_timeout=10,
            close_timeout=5,
            open_timeout=10,
        ) as ws:
            # Send subscribe message
            if ws_config.get("type") == "stream_url":
                pass  # Binance-style: already subscribed via URL
            else:
                await ws.send(json.dumps(subscribe_msg))
                print(f"  [{display_name}] Subscribed, collecting for {DURATION_SEC}s...")

            start_time = time.time()
            while time.time() - start_time < DURATION_SEC:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=5)
                    recv_time = time.perf_counter()
                    timestamps.append(recv_time)
                    message_count += 1

                    # Try to extract server timestamp
                    try:
                        data = json.loads(msg)
                        # Common timestamp fields
                        for key in ["T", "t", "timestamp", "ts", "time", "E", "server_time"]:
                            if key in data:
                                server_ts = data[key]
                                if isinstance(server_ts, (int, float)):
                                    # Normalize to seconds
                                    if server_ts > 1e12:
                                        server_ts = server_ts / 1000  # ms to s
                                    if server_ts > 1e9:
                                        client_time = time.time()
                                        delta_ms = (client_time - server_ts) * 1000
                                        if -5000 < delta_ms < 5000:  # Sanity check
                                            server_timestamps.append(delta_ms)
                                break
                    except (json.JSONDecodeError, TypeError, KeyError):
                        pass

                except asyncio.TimeoutError:
                    continue
                except websockets.exceptions.ConnectionClosed:
                    print(f"  [{display_name}] Connection closed unexpectedly")
                    break

    except Exception as e:
        print(f"  [{display_name}] ERROR: {e}")
        return {"status": "ERROR", "error": str(e)}

    if len(timestamps) < 2:
        return {"status": "INSUFFICIENT_DATA", "messages": message_count}

    # Calculate intervals between consecutive messages
    intervals = [(timestamps[i] - timestamps[i - 1]) * 1000 for i in range(1, len(timestamps))]

    result = {
        "status": "OK",
        "ws_url": ws_url,
        "duration_sec": DURATION_SEC,
        "total_messages": message_count,
        "messages_per_sec": round(message_count / DURATION_SEC, 2),
        "interval_p50_ms": round(percentile(intervals, 50), 2),
        "interval_p95_ms": round(percentile(intervals, 95), 2),
        "interval_mean_ms": round(statistics.mean(intervals), 2),
        "interval_min_ms": round(min(intervals), 2),
        "interval_max_ms": round(max(intervals), 2),
    }

    if server_timestamps:
        result["server_to_client_p50_ms"] = round(percentile(server_timestamps, 50), 2)
        result["server_to_client_p95_ms"] = round(percentile(server_timestamps, 95), 2)
        result["server_to_client_samples"] = len(server_timestamps)
    else:
        result["server_to_client_p50_ms"] = None

    print(f"  [{display_name}] {message_count} msgs in {DURATION_SEC}s "
          f"({result['messages_per_sec']}/s), interval p50={result['interval_p50_ms']}ms")
    return result


async def benchmark_binance_style_ws(platform_id: str, config: dict) -> dict:
    """Benchmark Binance-style stream URL WebSockets (e.g., Aster)."""
    import websockets

    display_name = config["display_name"]
    ws_config = config.get("orderbook_ws", {})
    stream_url = ws_config.get("stream_url")

    if not stream_url:
        return {"status": "NOT_SUPPORTED", "reason": "No stream URL"}

    print(f"  [{display_name}] Connecting to {stream_url}")

    timestamps = []
    message_count = 0

    try:
        async with websockets.connect(
            stream_url,
            additional_headers={"User-Agent": "PerpDEX-Benchmark/1.0"},
            ping_interval=20,
            open_timeout=10,
        ) as ws:
            print(f"  [{display_name}] Connected, collecting for {DURATION_SEC}s...")
            start_time = time.time()
            while time.time() - start_time < DURATION_SEC:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=5)
                    timestamps.append(time.perf_counter())
                    message_count += 1
                except asyncio.TimeoutError:
                    continue
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}

    if len(timestamps) < 2:
        return {"status": "INSUFFICIENT_DATA", "messages": message_count}

    intervals = [(timestamps[i] - timestamps[i - 1]) * 1000 for i in range(1, len(timestamps))]

    return {
        "status": "OK",
        "ws_url": stream_url,
        "duration_sec": DURATION_SEC,
        "total_messages": message_count,
        "messages_per_sec": round(message_count / DURATION_SEC, 2),
        "interval_p50_ms": round(percentile(intervals, 50), 2),
        "interval_p95_ms": round(percentile(intervals, 95), 2),
        "interval_mean_ms": round(statistics.mean(intervals), 2),
        "interval_min_ms": round(min(intervals), 2),
        "interval_max_ms": round(max(intervals), 2),
        "server_to_client_p50_ms": None,
    }


async def benchmark_platform(platform_id: str, config: dict) -> dict:
    display_name = config["display_name"]
    caps = config.get("capabilities", {})

    if not caps.get("has_ws", False):
        print(f"  [{display_name}] SKIP - no WebSocket API")
        return {
            "platform": platform_id,
            "display_name": display_name,
            "ws_orderbook": "NOT_SUPPORTED",
        }

    if caps.get("ws_is_socketio"):
        print(f"  [{display_name}] SKIP - Socket.IO (not raw WS, needs separate client)")
        return {
            "platform": platform_id,
            "display_name": display_name,
            "ws_orderbook": "SOCKETIO_NOT_TESTED",
        }

    ws_config = config.get("orderbook_ws", {})
    ws_type = ws_config.get("type", "native") if ws_config else None

    if ws_type == "stream_url":
        result = await benchmark_binance_style_ws(platform_id, config)
    else:
        result = await benchmark_native_ws(platform_id, config)

    return {
        "platform": platform_id,
        "display_name": display_name,
        "ws_orderbook": result,
    }


async def run_all(platform_filter: Optional[str] = None, duration: int = DURATION_SEC):
    global DURATION_SEC
    DURATION_SEC = duration
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
    print(f"  WS Orderbook Push Latency — {len(targets)} platforms")
    print(f"  Duration: {DURATION_SEC}s per platform")
    print(f"{'='*60}\n")

    all_results = []
    for pid, cfg in targets.items():
        result = await benchmark_platform(pid, cfg)
        all_results.append(result)

        out_path = RESULTS_DIR / f"{pid}_ws_orderbook.json"
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    # Save combined
    combined_path = RESULTS_DIR / "all_ws_orderbook.json"
    with open(combined_path, "w") as f:
        json.dump({
            "test": "ws_orderbook",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "duration_sec": DURATION_SEC,
            "results": all_results,
        }, f, indent=2, ensure_ascii=False)

    # Summary
    print(f"\n{'='*60}")
    print(f"  Summary (sorted by interval p50)")
    print(f"{'='*60}")
    print(f"  {'Platform':<20} {'p50':>8} {'p95':>8} {'msg/s':>8} {'Total':>8}")
    print(f"  {'-'*20} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")

    sortable = [r for r in all_results if isinstance(r.get("ws_orderbook"), dict) and r["ws_orderbook"].get("status") == "OK"]
    sortable.sort(key=lambda r: r["ws_orderbook"]["interval_p50_ms"])
    for r in sortable:
        ws = r["ws_orderbook"]
        print(f"  {r['display_name']:<20} {ws['interval_p50_ms']:>7.1f} {ws['interval_p95_ms']:>7.1f} {ws['messages_per_sec']:>7.1f} {ws['total_messages']:>8}")

    skipped = [r for r in all_results if not isinstance(r.get("ws_orderbook"), dict) or r["ws_orderbook"].get("status") != "OK"]
    for r in skipped:
        ws = r.get("ws_orderbook", {})
        status = ws if isinstance(ws, str) else ws.get("status", "UNKNOWN")
        print(f"  {r['display_name']:<20} {'—':>8} {'—':>8} {'—':>8} {status:>8}")

    print(f"\n  Results saved to {RESULTS_DIR}/")


def main():
    parser = argparse.ArgumentParser(description="WS Orderbook Push Latency Benchmark")
    parser.add_argument("--platform", default="all", help="Platform ID or comma-separated list")
    parser.add_argument("--duration", type=int, default=DURATION_SEC, help="Duration in seconds (default: 60)")
    args = parser.parse_args()

    asyncio.run(run_all(args.platform, args.duration))


if __name__ == "__main__":
    main()
