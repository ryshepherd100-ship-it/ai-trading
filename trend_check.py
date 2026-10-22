"""One market-filtered trend check, run by the separate GitHub Actions workflow."""
import os
from datetime import timezone
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.enums import QueryOrderStatus

import trend_bot


def main():
    load_dotenv()
    key = os.getenv("ALPACA_API_KEY")
    secret = os.getenv("ALPACA_SECRET_KEY")
    if not key or not secret or "your_" in key:
        raise RuntimeError("Set ALPACA_API_KEY and ALPACA_SECRET_KEY in secrets.")

    client = TradingClient(key, secret, paper=True)
    clock = client.get_clock()
    if not clock.is_open:
        print(f"Market closed (next open {clock.next_open}). Not trading.")
        return

    eastern = clock.timestamp.astimezone(ZoneInfo("America/New_York"))
    session_start = eastern.replace(hour=9, minute=30, second=0, microsecond=0)
    session_start_utc = session_start.astimezone(timezone.utc)
    todays_orders = client.get_orders(GetOrdersRequest(
        status=QueryOrderStatus.ALL,
        symbols=[trend_bot.SYMBOL],
        after=session_start_utc,
    ))
    if todays_orders:
        print(
            f"Already placed an order for {trend_bot.SYMBOL} today. "
            "Not trading again until the next session."
        )
        return

    print("Market open. Running market-filtered trend check.")
    trend_bot.main(client, clock.timestamp)


if __name__ == "__main__":
    main()
