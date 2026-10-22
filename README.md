# Paper-trading bots

GitHub Actions checks these bots during US market hours on weekdays. GitHub may delay scheduled runs, so the five-minute schedule is not an exact-time guarantee.

- **AAPL crossover bot:** uses a 20-day/50-day moving-average crossover and trades one share at most once per session.
- **MSFT market-filtered trend bot:** uses the same crossover, but only buys while SPY is above its 200-day moving average. It sells on a bearish MSFT crossover or when SPY falls below its 200-day average. It trades one share at most once per session and evaluates completed daily bars.

Both bots use Alpaca paper trading. The workflow requires the repository secrets `ALPACA_API_KEY` and `ALPACA_SECRET_KEY`. To pause both bots, disable the **Trading bot** workflow in the repository's Actions tab.
