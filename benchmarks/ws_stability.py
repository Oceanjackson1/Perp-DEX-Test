#!/usr/bin/env python3
"""
Benchmark 6: WebSocket Connection Stability
Maintains a WebSocket connection for 1 hour, records disconnects,
total messages, and reconnection times.
"""

import asyncio
import json
import time
import argparse
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "platforms.json"
RESULTS_DIR = PROJECT_ROOT / "results"

DURATION_MIN = 60  # 1 hour default


def load_platforms():
    with open(CONFIG_PATH) as f:
        return json.load(f)


async def stability_test(platform_id: str, config: dict) -> dict:
    """Run WS stability test for a single platform."""
    import websockets
    import websockets.exceptions

    display_name = config["display_name"]
    caps = config.get("capabilities", {})

    if not caps.get("has_ws", False):
        return {"platform": platform_id, "display_name": display_name, "ws_stability": "NOT_SUPPORTED"}

    if caps.get("ws_is_socketio"):
        return {"platform": platform_id, "display_name": display_name, "ws_stability": "SOCKETIO_NOT_TESTED"}

    ws_url = config.get("ws_url")
    ws_config = config.get("orderbook_ws", {})
    subscribe_msg = ws_config.get("subscribe_msg") if ws_config else None

    if not ws_url:
        return {"platform": platform_id, "display_name": display_name, "ws_stability": "NO_WS_URL"}

    ws_type = ws_config.get("type", "native") if ws_config else "native"
    actual_url = ws_config.get("stream_url", ws_url) if ws_type == "stream_url" else ws_url

    print(f"  [{display_name}] Starting {DURATION_MIN}min stability test on {actual_url}")

    total_messages = 0
    disconnects = []
    reconnect_times = []
    start_time = time.time()
    end_time = start_time + DURATION_MIN * 60
    connection_num = 0

    extra_headers = {"User-Agent": "PerpDEX-Benchmark/1.0"}
    extensions = None
    if caps.get("ws_requires_deflate"):
        import websockets.extensions.permessage_deflate as deflate
        extensions = [deflate.ClientPerMessageDeflateFactory()]

    while time.time() < end_time:
        connection_num += 1
        connect_start = time.perf_counter()
        try:
            async with websockets.connect(
                actual_url,
                additional_headers=extra_headers,
                extensions=extensions,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=5,
                open_timeout=15,
            ) as ws:
                connect_elapsed = (time.perf_counter() - connect_start) * 1000

                if connection_num > 1:
                    reconnect_times.append(connect_elapsed)
                    print(f"    Reconnected #{connection_num} in {connect_elapsed:.0f}ms")

                # Subscribe
                if ws_type != "stream_url" and subscribe_msg:
                    await ws.send(json.dumps(subscribe_msg))

                # Receive loop
                while time.time() < end_time:
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=30)
                        total_messages += 1

                        # Progress report every 5 minutes
                        elapsed_min = (time.time() - start_time) / 60
                        if total_messages % 5000 == 0:
                            print(f"    [{display_name}] {elapsed_min:.1f}min: "
                                  f"{total_messages} msgs, {len(disconnects)} disconnects")

                    except asyncio.TimeoutError:
                        # No data for 30s — might be normal for low-activity markets
                        continue

        except websockets.exceptions.ConnectionClosed as e:
            disconnect_time = time.time() - start_time
            disconnects.append({
                "at_seconds": round(disconnect_time, 2),
                "reason": str(e),
                "connection_num": connection_num,
            })
            print(f"    [{display_name}] Disconnected at {disconnect_time:.0f}s: {e}")
            await asyncio.sleep(1)  # Brief pause before reconnect

        except Exception as e:
            disconnect_time = time.time() - start_time
            disconnects.append({
                "at_seconds": round(disconnect_time, 2),
                "reason": str(e),
                "connection_num": connection_num,
            })
            print(f"    [{display_name}] Error at {disconnect_time:.0f}s: {e}")
            await asyncio.sleep(2)

    actual_duration = (time.time() - start_time) / 60

    result = {
        "platform": platform_id,
        "display_name": display_name,
        "ws_stability": {
            "ws_url": actual_url,
            "target_duration_min": DURATION_MIN,
            "actual_duration_min": round(actual_duration, 2),
            "total_messages": total_messages,
            "messages_per_min": round(total_messages / max(actual_duration, 0.1), 1),
            "disconnects": len(disconnects),
            "disconnect_log": disconnects,
            "reconnect_times_ms": reconnect_times,
            "avg_reconnect_ms": round(sum(reconnect_times) / len(reconnect_times), 1) if reconnect_times else None,
            "total_connections": connection_num,
        },
    }

    print(f"  [{display_name}] Done: {total_messages} msgs, "
          f"{len(disconnects)} disconnects in {actual_duration:.1f}min")
    return result


async def run_all(platform_filter: Optional[str] = None, duration: int = DURATION_MIN):
    global DURATION_MIN
    DURATION_MIN = duration
    platforms = load_platforms()
    RESULTS_DIR.mkdir(exist_ok=True)

    targets = {}
    if platform_filter and platform_filter != "all":
        for pid in platform_filter.split(","):
            pid = pid.strip()
            if pid in platforms:
                targets[pid] = platforms[pid]
    else:
        targets = {k: v for k, v in platforms.items()
                   if v.get("capabilities", {}).get("has_ws", False)}

    print(f"\n{'='*60}")
    print(f"  WS Connection Stability Test — {len(targets)} platforms")
    print(f"  Duration: {DURATION_MIN} minutes per platform")
    print(f"  Total estimated time: ~{len(targets) * DURATION_MIN} minutes")
    print(f"{'='*60}\n")

    all_results = []
    for pid, cfg in targets.items():
        result = await stability_test(pid, cfg)
        all_results.append(result)

        out_path = RESULTS_DIR / f"{pid}_ws_stability.json"
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    # Save combined
    combined_path = RESULTS_DIR / "all_ws_stability.json"
    with open(combined_path, "w") as f:
        json.dump({
            "test": "ws_stability",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "duration_min": DURATION_MIN,
            "results": all_results,
        }, f, indent=2, ensure_ascii=False)

    # Summary
    print(f"\n{'='*60}")
    print(f"  Summary")
    print(f"{'='*60}")
    print(f"  {'Platform':<20} {'Messages':>10} {'Disconnects':>12} {'Duration':>10}")
    print(f"  {'-'*20} {'-'*10} {'-'*12} {'-'*10}")

    for r in all_results:
        ws = r.get("ws_stability", {})
        if isinstance(ws, str):
            print(f"  {r['display_name']:<20} {'—':>10} {'—':>12} {ws:>10}")
        else:
            print(f"  {r['display_name']:<20} {ws['total_messages']:>10} "
                  f"{ws['disconnects']:>12} {ws['actual_duration_min']:>9.1f}m")


def main():
    parser = argparse.ArgumentParser(description="WS Connection Stability Test")
    parser.add_argument("--platform", default="all", help="Platform ID or comma-separated list")
    parser.add_argument("--duration", type=int, default=DURATION_MIN, help="Duration in minutes (default: 60)")
    args = parser.parse_args()

    asyncio.run(run_all(args.platform, args.duration))


if __name__ == "__main__":
    main()
