"""Moving average crossover bot for an Alpaca paper account.

Run once per day (e.g. after market close or before open):
    python bot.py
"""
import os
import sys

import yfinance as yf
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

import config


def get_signal():
    """Return 'buy', 'sell', or None based on a crossover between the last two days."""
    data = yf.download(config.SYMBOL, period=f"{config.LOOKBACK_DAYS}d",
                       interval="1d", progress=False, auto_adjust=True)
    if data.empty:
        raise RuntimeError(f"No price data returned for {config.SYMBOL}")

    close = data["Close"].squeeze()  # newer yfinance returns a one-column frame
    short_ma = close.rolling(config.SHORT_MA).mean()
    long_ma = close.rolling(config.LONG_MA).mean()

    prev_diff = short_ma.iloc[-2] - long_ma.iloc[-2]
    curr_diff = short_ma.iloc[-1] - long_ma.iloc[-1]

    print(f"{config.SYMBOL} close={close.iloc[-1]:.2f}  "
          f"{config.SHORT_MA}MA={short_ma.iloc[-1]:.2f}  "
          f"{config.LONG_MA}MA={long_ma.iloc[-1]:.2f}")

    if prev_diff <= 0 < curr_diff:
        return "buy"    # short MA crossed above long MA
    if prev_diff >= 0 > curr_diff:
        return "sell"   # short MA crossed below long MA
    return None


def current_qty(client):
    try:
        return float(client.get_open_position(config.SYMBOL).qty)
    except Exception:
        return 0.0  # no open position


def main():
    load_dotenv()
    key, secret = os.getenv("ALPACA_API_KEY"), os.getenv("ALPACA_SECRET_KEY")
    if not key or not secret or "your_" in key:
        sys.exit("Set ALPACA_API_KEY and ALPACA_SECRET_KEY in .env first.")

    client = TradingClient(key, secret, paper=True)  # paper trading only

    signal = get_signal()
    if signal is None:
        print("No crossover today. Nothing to do.")
        return

    held = current_qty(client)
    if signal == "buy" and held > 0:
        print("Buy signal, but already holding. Skipping.")
        return
    if signal == "sell" and held < config.TRADE_QTY:
        print("Sell signal, but not holding enough shares (shorting is off). Skipping.")
        return

    side = OrderSide.BUY if signal == "buy" else OrderSide.SELL
    order = client.submit_order(MarketOrderRequest(
        symbol=config.SYMBOL, qty=config.TRADE_QTY,
        side=side, time_in_force=TimeInForce.DAY))
    print(f"Placed {signal.upper()} order for {config.TRADE_QTY} {config.SYMBOL}: {order.id}")
    return True


if __name__ == "__main__":
    main()
