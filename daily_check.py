"""One crossover check. GitHub Actions runs this every 30 minutes on weekdays.

- Market closed (nights, weekends, holidays): does nothing.
- Market open: runs the bot, unless it already traded this symbol today
  (max one trade per day, so it can't buy and sell on the same day).
"""
import os

from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.enums import QueryOrderStatus

import bot
import config


def main():
    load_dotenv()  # no .env on GitHub; keys come from repository secrets instead
    client = TradingClient(os.getenv("ALPACA_API_KEY"), os.getenv("ALPACA_SECRET_KEY"), paper=True)
    clock = client.get_clock()

    if not clock.is_open:
        print(f"Market closed (next open {clock.next_open}). Not trading.")
        return

    # Today's session started at this morning's open (9:30 ET).
    session_start = clock.timestamp.replace(hour=9, minute=30, second=0, microsecond=0)
    todays_orders = client.get_orders(GetOrdersRequest(
        status=QueryOrderStatus.ALL, symbols=[config.SYMBOL], after=session_start))
    if todays_orders:
        print(f"Already traded {config.SYMBOL} today. Not trading again until tomorrow.")
        return

    print("Market open. Running crossover check.")
    bot.main()


if __name__ == "__main__":
    main()
