#!/usr/bin/env python3.11

import asyncio
import json
import re
import sys
from decimal import Decimal, ROUND_DOWN, ROUND_UP
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SDK_PATH = ROOT / ".pydeps311"
DEFAULT_WALLET_FILE = ROOT / "evm_wallet_20260320_165220.txt"

ADDRESS_PATTERN = re.compile(r"^Address:\s*(0x[a-fA-F0-9]{40})$")
PRIVATE_KEY_PATTERN = re.compile(r"^Private Key:\s*(0x[a-fA-F0-9]{64})$")

sys.path.insert(0, str(SDK_PATH))

from x10.perpetual.accounts import StarkPerpetualAccount  # noqa: E402
from x10.perpetual.configuration import TESTNET_CONFIG  # noqa: E402
from x10.perpetual.markets import MarketModel  # noqa: E402
from x10.perpetual.orders import OrderSide, OrderStatus, TimeInForce  # noqa: E402
from x10.perpetual.trading_client.trading_client import PerpetualTradingClient  # noqa: E402
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


def pick_market(markets: list[MarketModel]) -> MarketModel:
    active_markets = [
        market
        for market in markets
        if market.active and market.market_stats.bid_price > 0 and market.market_stats.ask_price > 0
    ]
    if not active_markets:
        raise ValueError("No active markets with non-zero bid/ask were returned.")

    for keyword in ("BTC", "ETH", "SOL"):
        for market in active_markets:
            if keyword in market.name.upper():
                return market

    return active_markets[0]


def build_safe_ioc_order(market: MarketModel) -> dict:
    bid = market.market_stats.bid_price
    ask = market.market_stats.ask_price
    tick = market.trading_config.min_price_change
    floor = market.trading_config.limit_price_floor
    cap = market.trading_config.limit_price_cap

    buy_candidate = max(floor, min(bid * Decimal("0.5"), ask - tick))
    buy_price = market.trading_config.round_price(buy_candidate, rounding_direction=ROUND_DOWN)
    if buy_price < ask:
        return {
            "side": OrderSide.BUY,
            "price": buy_price,
            "strategy": "IOC buy placed well below best ask to avoid execution and resting.",
        }

    sell_candidate = min(cap, max(ask * Decimal("1.5"), bid + tick))
    sell_price = market.trading_config.round_price(sell_candidate, rounding_direction=ROUND_UP)
    if sell_price > bid:
        return {
            "side": OrderSide.SELL,
            "price": sell_price,
            "strategy": "IOC sell placed well above best bid to avoid execution and resting.",
        }

    raise ValueError(f"Could not build a non-crossing IOC order for market {market.name}.")


async def fetch_order_state(client: PerpetualTradingClient, order_id: int, retries: int = 5) -> dict:
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            response = await client.account.get_order_by_id(order_id)
            return {
                "ok": True,
                "attempt": attempt,
                "order": response.data.model_dump(mode="json") if response.data is not None else None,
            }
        except Exception as exc:  # noqa: BLE001
            last_error = {
                "attempt": attempt,
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
            await asyncio.sleep(1)

    return {
        "ok": False,
        "error": last_error,
    }


async def run_probe(wallet_file: Path) -> dict:
    address, private_key = load_wallet(wallet_file)
    user_client = UserClient(TESTNET_CONFIG, lambda: private_key)
    trading_client = None

    results = {
        "wallet_address": address,
        "testnet_host": TESTNET_CONFIG.onboarding_url,
        "api_base_url": TESTNET_CONFIG.api_base_url,
    }

    try:
        accounts = await user_client.get_accounts()
        if not accounts:
            raise ValueError("No accounts returned by Extended testnet onboarding API.")

        onboarded_account = accounts[0]
        api_key = await user_client.create_account_api_key(
            onboarded_account.account,
            description="codex write probe",
        )

        results["account"] = {
            "id": onboarded_account.account.id,
            "account_index": onboarded_account.account.account_index,
            "status": onboarded_account.account.status,
            "l2_vault": onboarded_account.account.l2_vault,
            "l2_public_key": onboarded_account.l2_key_pair.public_hex,
        }
        results["api_key"] = redact_api_key(api_key)

        stark_account = StarkPerpetualAccount(
            vault=onboarded_account.account.l2_vault,
            private_key=onboarded_account.l2_key_pair.private_hex,
            public_key=onboarded_account.l2_key_pair.public_hex,
            api_key=api_key,
        )
        trading_client = PerpetualTradingClient(TESTNET_CONFIG, stark_account=stark_account)

        try:
            balance_before = await trading_client.account.get_balance()
            results["balance_before_claim"] = {
                "ok": True,
                "balance": balance_before.data.model_dump(mode="json") if balance_before.data is not None else None,
            }
        except Exception as exc:  # noqa: BLE001
            results["balance_before_claim"] = {
                "ok": False,
                "error_type": type(exc).__name__,
                "error": str(exc),
            }

        try:
            claim = await trading_client.testnet.claim_testing_funds()
            results["claim_testing_funds"] = {
                "ok": True,
                "response": claim.data.model_dump(mode="json") if claim.data is not None else None,
            }
            await asyncio.sleep(1)
        except Exception as exc:  # noqa: BLE001
            results["claim_testing_funds"] = {
                "ok": False,
                "error_type": type(exc).__name__,
                "error": str(exc),
            }

        try:
            balance_after_claim = await trading_client.account.get_balance()
            results["balance_after_claim"] = {
                "ok": True,
                "balance": balance_after_claim.data.model_dump(mode="json") if balance_after_claim.data is not None else None,
            }
        except Exception as exc:  # noqa: BLE001
            results["balance_after_claim"] = {
                "ok": False,
                "error_type": type(exc).__name__,
                "error": str(exc),
            }

        try:
            client_info = await trading_client.account.get_client()
            results["client_info_after_claim"] = {
                "ok": True,
                "client": client_info.data.model_dump(mode="json") if client_info.data is not None else None,
            }
        except Exception as exc:  # noqa: BLE001
            results["client_info_after_claim"] = {
                "ok": False,
                "error_type": type(exc).__name__,
                "error": str(exc),
            }

        markets_response = await trading_client.markets_info.get_markets()
        markets = markets_response.data or []
        selected_market = pick_market(markets)
        order_plan = build_safe_ioc_order(selected_market)
        order_qty = selected_market.trading_config.min_order_size

        results["selected_market"] = {
            "name": selected_market.name,
            "bid_price": str(selected_market.market_stats.bid_price),
            "ask_price": str(selected_market.market_stats.ask_price),
            "mark_price": str(selected_market.market_stats.mark_price),
            "min_order_size": str(selected_market.trading_config.min_order_size),
            "min_order_size_change": str(selected_market.trading_config.min_order_size_change),
            "min_price_change": str(selected_market.trading_config.min_price_change),
            "limit_price_floor": str(selected_market.trading_config.limit_price_floor),
            "limit_price_cap": str(selected_market.trading_config.limit_price_cap),
        }
        results["planned_probe_order"] = {
            "side": order_plan["side"],
            "qty": str(order_qty),
            "price": str(order_plan["price"]),
            "time_in_force": TimeInForce.IOC,
            "strategy": order_plan["strategy"],
        }

        placed_order_response = await trading_client.place_order(
            market_name=selected_market.name,
            amount_of_synthetic=order_qty,
            price=order_plan["price"],
            side=order_plan["side"],
            time_in_force=TimeInForce.IOC,
            external_id="codex-extended-write-probe",
        )
        placed_order = placed_order_response.data
        results["place_order"] = {
            "ok": True,
            "order": placed_order.model_dump(mode="json") if placed_order is not None else None,
        }

        if placed_order is not None:
            fetched_order = await fetch_order_state(trading_client, placed_order.id)
            results["fetch_order_state"] = fetched_order

            open_orders = await trading_client.account.get_open_orders(market_names=[selected_market.name])
            open_order_list = open_orders.data or []
            results["open_orders_after_probe"] = {
                "ok": True,
                "count": len(open_order_list),
                "orders": [order.model_dump(mode="json") for order in open_order_list],
            }

            active_statuses = {OrderStatus.NEW, OrderStatus.PARTIALLY_FILLED, OrderStatus.UNTRIGGERED}
            if fetched_order.get("ok") and fetched_order.get("order") is not None:
                order_status = fetched_order["order"].get("status")
                if order_status in active_statuses:
                    try:
                        await trading_client.orders.cancel_order(placed_order.id)
                        results["cleanup_cancel"] = {
                            "ok": True,
                            "order_id": placed_order.id,
                        }
                    except Exception as exc:  # noqa: BLE001
                        results["cleanup_cancel"] = {
                            "ok": False,
                            "order_id": placed_order.id,
                            "error_type": type(exc).__name__,
                            "error": str(exc),
                        }
        return results
    except Exception as exc:  # noqa: BLE001
        results["probe_error"] = {
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        return results
    finally:
        if trading_client is not None:
            await trading_client.info.close_session()
            await trading_client.testnet.close_session()
            await trading_client.close()
        await user_client.close_session()


def main() -> int:
    results = asyncio.run(run_probe(DEFAULT_WALLET_FILE))
    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
