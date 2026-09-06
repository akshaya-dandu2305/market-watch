import yfinance as yf


def get_stock_data(symbol: str):
    ticker = yf.Ticker(symbol)

    history = ticker.history(
        period="1mo",
        auto_adjust=False
    )

    if history.empty:
        raise ValueError(
            f"No market data found for {symbol}"
        )

    history = history.dropna(
        subset=["Close"]
    )

    if history.empty:
        raise ValueError(
            f"No valid price data found for {symbol}"
        )

    latest = history.iloc[-1]

    price = float(latest["Close"])
    volume = float(latest["Volume"])

    previous_close = None

    if len(history) >= 2:
        previous_close = float(
            history.iloc[-2]["Close"]
        )

    change = None
    change_percent = None

    if previous_close and previous_close != 0:
        change = price - previous_close

        change_percent = (
            change / previous_close
        ) * 100

    recent_volumes = history["Volume"].dropna()

    if len(recent_volumes) > 1:
        average_volume = float(
            recent_volumes.iloc[:-1].mean()
        )
    else:
        average_volume = volume

    if average_volume > 0:
        volume_ratio = (
            volume / average_volume
        )
    else:
        volume_ratio = 1

    returns = (
        history["Close"]
        .pct_change()
        .dropna()
    )

    if len(returns) > 0:
        typical_move = (
            returns.abs().mean() * 100
        )
    else:
        typical_move = 0

    if (
        typical_move > 0
        and change_percent is not None
    ):
        unusual_ratio = (
            abs(change_percent)
            / typical_move
        )
    else:
        unusual_ratio = 1

    # ---------------------------------------------------------
    # Recent price history for the mini chart
    # ---------------------------------------------------------

    price_history = []

    for index, row in history.iterrows():

        price_history.append({
            "date": str(index.date()),
            "price": round(
                float(row["Close"]),
                2
            ),
        })

    return {
        "symbol": symbol.upper(),

        "price": round(
            price,
            2
        ),

        "previous_close": (
            round(
                previous_close,
                2
            )
            if previous_close is not None
            else None
        ),

        "change": (
            round(
                change,
                2
            )
            if change is not None
            else None
        ),

        "change_percent": (
            round(
                change_percent,
                2
            )
            if change_percent is not None
            else None
        ),

        "day_high": round(
            float(latest["High"]),
            2
        ),

        "day_low": round(
            float(latest["Low"]),
            2
        ),

        "volume": int(
            volume
        ),

        "average_volume": int(
            average_volume
        ),

        "volume_ratio": round(
            volume_ratio,
            2
        ),

        "typical_daily_move": round(
            typical_move,
            2
        ),

        "unusual_ratio": round(
            unusual_ratio,
            2
        ),

        "data_date": str(
            history.index[-1].date()
        ),

        "data_status": "latest_available",

        "price_history": price_history,
    }
