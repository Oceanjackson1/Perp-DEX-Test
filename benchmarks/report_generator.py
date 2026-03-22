#!/usr/bin/env python3
"""
Report Generator: Reads all JSON results from results/ directory
and produces a Chinese Markdown comparison report.
"""

import json
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
REPORT_PATH = PROJECT_ROOT / f"benchmark_report_{time.strftime('%Y%m%d')}.md"


def load_json(filename: str) -> dict | None:
    path = RESULTS_DIR / filename
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return None


def generate_report():
    rest = load_json("all_rest_latency.json")
    ws_ob = load_json("all_ws_orderbook.json")
    rate = load_json("all_rate_limit.json")
    order = load_json("all_order_roundtrip.json")
    batch = load_json("all_batch_throughput.json")
    ws_stab = load_json("all_ws_stability.json")

    lines = []
    lines.append("# Perp DEX API 性能实测基准报告\n")
    lines.append(f"**测试日期：** {time.strftime('%Y-%m-%d')}")
    lines.append(f"**测试环境：** macOS, Python 3.11, 网络位置未公开")
    lines.append(f"**方法论：** 自动化脚本实测，非文档数据\n")
    lines.append("---\n")

    # 1. REST Latency
    lines.append("## 一、REST API 延迟实测\n")
    lines.append("对每个平台最轻量的公共端点发送 100 次请求，统计往返延迟。\n")
    lines.append("| 排名 | 平台 | p50 (ms) | p95 (ms) | p99 (ms) | 均值 (ms) | 最小 | 最大 | 样本数 |")
    lines.append("|------|------|----------|----------|----------|-----------|------|------|--------|")

    if rest and "results" in rest:
        sortable = [r for r in rest["results"]
                    if isinstance(r.get("rest_latency"), dict) and "p50_ms" in r["rest_latency"]]
        sortable.sort(key=lambda r: r["rest_latency"]["p50_ms"])
        for i, r in enumerate(sortable, 1):
            rl = r["rest_latency"]
            lines.append(f"| {i} | **{r['display_name']}** | {rl['p50_ms']} | {rl['p95_ms']} | "
                        f"{rl['p99_ms']} | {rl['mean_ms']} | {rl['min_ms']} | {rl['max_ms']} | {rl['samples']} |")

        # Failed/skipped
        failed = [r for r in rest["results"]
                  if not isinstance(r.get("rest_latency"), dict) or "p50_ms" not in r.get("rest_latency", {})]
        for r in failed:
            status = r["rest_latency"] if isinstance(r["rest_latency"], str) else "FAILED"
            lines.append(f"| — | {r['display_name']} | — | — | — | — | — | — | {status} |")

    lines.append("")

    # 2. WS Orderbook
    lines.append("## 二、WebSocket 订单簿推送延迟实测\n")
    lines.append("订阅 BTC 订单簿频道 60 秒，统计推送间隔。\n")
    lines.append("| 排名 | 平台 | 间隔 p50 (ms) | 间隔 p95 (ms) | 消息/秒 | 总消息数 | 服务器→客户端 p50 |")
    lines.append("|------|------|--------------|--------------|---------|---------|-----------------|")

    if ws_ob and "results" in ws_ob:
        sortable = [r for r in ws_ob["results"]
                    if isinstance(r.get("ws_orderbook"), dict) and r["ws_orderbook"].get("status") == "OK"]
        sortable.sort(key=lambda r: r["ws_orderbook"]["interval_p50_ms"])
        for i, r in enumerate(sortable, 1):
            ws = r["ws_orderbook"]
            s2c = f"{ws['server_to_client_p50_ms']}ms" if ws.get("server_to_client_p50_ms") else "—"
            lines.append(f"| {i} | **{r['display_name']}** | {ws['interval_p50_ms']} | {ws['interval_p95_ms']} | "
                        f"{ws['messages_per_sec']} | {ws['total_messages']} | {s2c} |")

        skipped = [r for r in ws_ob["results"]
                   if not isinstance(r.get("ws_orderbook"), dict) or r["ws_orderbook"].get("status") != "OK"]
        for r in skipped:
            ws = r.get("ws_orderbook", {})
            status = ws if isinstance(ws, str) else ws.get("status", "UNKNOWN")
            lines.append(f"| — | {r['display_name']} | — | — | — | — | {status} |")

    lines.append("")

    # 3. Rate Limit
    lines.append("## 三、速率限制实测\n")
    lines.append("指数级加压 (1→2→4→8→16→32→64 req/s)，记录首次 HTTP 429 的速率和恢复时间。\n")
    lines.append("| 平台 | 首次 429 速率 | 恢复时间 | 总请求数 | 文档声称限制 |")
    lines.append("|------|-------------|---------|---------|------------|")

    if rate and "results" in rate:
        for r in rate["results"]:
            rl = r.get("rate_limit", {})
            if isinstance(rl, str):
                lines.append(f"| {r['display_name']} | — | — | — | {rl} |")
            else:
                f429 = f"{rl['first_429_at_rps']} req/s" if rl.get("first_429_at_rps") else "未触发 (≤64 req/s)"
                rec = f"{rl['recovery_time_sec']}s" if rl.get("recovery_time_sec") else "—"
                lines.append(f"| **{r['display_name']}** | {f429} | {rec} | {rl['total_requests']} | — |")

    lines.append("")

    # 4. Order Roundtrip
    lines.append("## 四、下单→撤单 Round-trip 延迟实测\n")
    lines.append("在有测试网资金的平台上，发送远离市价的限价单并立即撤单。\n")

    if order and "results" in order:
        tested = [r for r in order["results"]
                  if isinstance(r.get("order_roundtrip"), dict) and r["order_roundtrip"].get("status") == "OK"]
        if tested:
            lines.append("| 平台 | 下单 p50 (ms) | 下单 p95 | 撤单 p50 (ms) | 撤单 p95 | 全程 p50 | 成功次数 |")
            lines.append("|------|-------------|---------|-------------|---------|---------|---------|")
            for r in tested:
                rt = r["order_roundtrip"]
                lines.append(f"| **{r['display_name']}** | "
                            f"{rt['place_order']['p50_ms']} | {rt['place_order']['p95_ms']} | "
                            f"{rt['cancel_order']['p50_ms']} | {rt['cancel_order']['p95_ms']} | "
                            f"{rt['full_roundtrip']['p50_ms']} | {rt['successful']}/{rt['rounds']} |")

        not_tested = [r for r in order["results"]
                      if not isinstance(r.get("order_roundtrip"), dict) or r["order_roundtrip"].get("status") != "OK"]
        if not_tested:
            lines.append("\n**未测试平台（方案 A：$0 预算）：**\n")
            for r in not_tested:
                reason = r["order_roundtrip"] if isinstance(r["order_roundtrip"], str) else r["order_roundtrip"].get("status", "UNKNOWN")
                lines.append(f"- {r['display_name']}: `{reason}`")

    lines.append("")

    # 5. Batch Throughput
    lines.append("## 五、批量操作吞吐实测\n")
    lines.append("方案 A ($0 预算) 下，批量操作测试需要有资金的账户，暂未执行。\n")
    lines.append("**支持批量操作的平台：** Hyperliquid, Lighter, Paradex, Aster, trade[XYZ]\n")
    lines.append("*充值后可运行：`python benchmarks/batch_throughput.py --funded`*\n")

    # 6. WS Stability
    lines.append("## 六、WebSocket 连接稳定性实测\n")
    lines.append(f"持续连接并接收数据，记录断线次数和消息吞吐。\n")
    lines.append("| 平台 | 持续时间 (分钟) | 总消息数 | 消息/分钟 | 断线次数 | 平均重连 (ms) |")
    lines.append("|------|---------------|---------|----------|---------|-------------|")

    if ws_stab and "results" in ws_stab:
        sortable = [r for r in ws_stab["results"]
                    if isinstance(r.get("ws_stability"), dict)]
        sortable.sort(key=lambda r: -r["ws_stability"].get("total_messages", 0))
        for r in sortable:
            ws = r["ws_stability"]
            avg_rc = f"{ws['avg_reconnect_ms']}" if ws.get("avg_reconnect_ms") else "—"
            lines.append(f"| **{r['display_name']}** | {ws['actual_duration_min']} | "
                        f"{ws['total_messages']} | {ws['messages_per_min']} | "
                        f"{ws['disconnects']} | {avg_rc} |")

        skipped = [r for r in ws_stab["results"] if isinstance(r.get("ws_stability"), str)]
        for r in skipped:
            lines.append(f"| {r['display_name']} | — | — | — | — | {r['ws_stability']} |")

    lines.append("")

    # Conclusion
    lines.append("---\n")
    lines.append("## 测试方法说明\n")
    lines.append("- **REST 延迟：** 100 次请求 + 5 次预热，间隔 200ms，统计往返时间")
    lines.append("- **WS 推送：** 订阅 60 秒，统计消息到达间隔")
    lines.append("- **速率限制：** 指数加压 (1-64 req/s)，首次 429 即停")
    lines.append("- **下单测试：** 远离市价限价单，确保不成交，仅测量 API 响应速度")
    lines.append("- **WS 稳定性：** 持续连接并接收数据，记录断线和消息计数")
    lines.append("- 所有测试从同一网络位置执行，延迟包含网络传输时间")
    lines.append("- 结果反映客户端视角的真实体验，非服务端内部延迟\n")

    report_content = "\n".join(lines)
    with open(REPORT_PATH, "w") as f:
        f.write(report_content)

    print(f"\n  Report generated: {REPORT_PATH}")
    print(f"  Size: {len(report_content)} chars")


if __name__ == "__main__":
    generate_report()
