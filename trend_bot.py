"""Market-filtered moving-average trend bot for an Alpaca paper account."""
from zoneinfo import ZoneInfo

import yfinance as yf
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

import config

MARKET_SYMBOL = "SPY"
MARKET_MA = 200
SYMBOL = "MSFT"


def _daily_closes(symbol, current_time):
    data = yf.download(symbol, period="2y", interval="1d",
                       progress=False, auto_adjust=True)
    if data.empty or "Close" not in data:
        raise RuntimeError(f"No price data returned for {symbol}")

    close = data["Close"]
    if hasattr(close, "columns"):
        if symbol in close.columns:
            close = close[symbol]
        elif len(close.columns) == 1:
            close = close.iloc[:, 0]
        else:
            raise RuntimeError(f"Unexpected price data format for {symbol}")

    current_date = current_time.astimezone(
        ZoneInfo("America/New_York")).date()
    close = close.dropna()
    if len(close) and close.index[-1].date() == current_date:
        close = close.iloc[:-1]
    return close


def get_signal(current_time):
    """Return buy, sell, or None using completed daily bars only."""
    market_close = _daily_closes(MARKET_SYMBOL, current_time)
    symbol_close = _daily_closes(SYMBOL, current_time)

    if len(market_close) < MARKET_MA or len(symbol_close) < config.LONG_MA + 1:
        raise RuntimeError("Not enough completed daily price data for indicators")

    market_average = market_close.rolling(MARKET_MA).mean().iloc[-1]
    market_filter_ok = market_close.iloc[-1] > market_average

    short_ma = symbol_close.rolling(config.SHORT_MA).mean()
    long_ma = symbol_close.rolling(config.LONG_MA).mean()
    previous_diff = short_ma.iloc[-2] - long_ma.iloc[-2]
    current_diff = short_ma.iloc[-1] - long_ma.iloc[-1]

    print(
        f"{SYMBOL} close={symbol_close.iloc[-1]:.2f} "
        f"{config.SHORT_MA}MA={short_ma.iloc[-1]:.2f} "
        f"{config.LONG_MA}MA={long_ma.iloc[-1]:.2f}; "
        f"{MARKET_SYMBOL} close={market_close.iloc[-1]:.2f} "
        f"{MARKET_MA}MA={market_average:.2f} "
        f"filter={'on' if market_filter_ok else 'off'}"
    )

    if not market_filter_ok:
        return "sell"
    if previous_diff <= 0 < current_diff:
        return "buy"
    if previous_diff >= 0 > current_diff:
        return "sell"
    return None


def current_qty(client):
    positions = client.get_all_positions()
    for position in positions:
        if position.symbol == SYMBOL:
            return float(position.qty)
    return 0.0


def main(client, current_time):
    signal = get_signal(current_time)
    if signal is None:
        print("No crossover with the market filter on. Nothing to do.")
        return False

    held = current_qty(client)
    if signal == "buy" and held > 0:
        print("Buy signal, but already holding. Skipping.")
        return False
    if signal == "sell" and held < config.TRADE_QTY:
        print("Sell signal, but not holding enough shares. Skipping.")
        return False

    side = OrderSide.BUY if signal == "buy" else OrderSide.SELL
    order = client.submit_order(MarketOrderRequest(
        symbol=SYMBOL,
        qty=config.TRADE_QTY,
        side=side,
        time_in_force=TimeInForce.DAY,
    ))
    print(
        f"Placed paper {signal.upper()} order for {config.TRADE_QTY} "
        f"{SYMBOL}: {order.id}"
    )
    return True
