from __future__ import annotations

import time
from typing import List, Optional

from utils.parse_timeframe import parse_timeframe


def _compute_sma(values: List[float], window: int) -> List[Optional[float]]:
    """Compute simple moving average, padding with None before first full window."""
    if window <= 1:
        return list(values)

    result: List[Optional[float]] = []
    running_sum = 0.0
    for i, value in enumerate(values):
        running_sum += value
        if i >= window:
            running_sum -= values[i - window]
        if i >= window - 1:
            result.append(running_sum / window)
        else:
            result.append(None)
    return result


def generate_candlestick_png(
    ccxt_exchange,
    symbol: str,
    timeframe: str = "1m",
    lookback_minutes: int = 60,
    theme: str = "dark",
    moving_averages: Optional[List[int]] = None,
    width: int = 800,
    height: int = 500,
    scale: int = 2,
) -> bytes:
    """
    Generate a candlestick PNG for the given symbol using ccxt OHLCV data.

    Args:
        ccxt_exchange: An instantiated ccxt exchange (e.g., base_exchange.exchange)
        symbol: Market symbol like "BTC/USDT"
        timeframe: ccxt timeframe string (e.g., "1m", "5m", "1h")
        lookback_minutes: How many minutes of history to visualize
        theme: "dark" or "light"
        moving_averages: List of window sizes for SMA lines
        width: Image width in pixels
        height: Image height in pixels
        scale: Pixel ratio multiplier for export

    Returns:
        PNG bytes
    """
    # Lazy import to avoid hard dependency when charts are disabled
    try:
        import plotly.graph_objects as go
        import plotly.io as pio  # noqa: F401  # ensure kaleido engine is available
    except Exception as e:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "Plotly (and kaleido) are required for chart generation. Install with: "
            "pip install plotly kaleido"
        ) from e

    if moving_averages is None:
        moving_averages = [7, 25]

    try:
        tf_minutes = parse_timeframe(timeframe)
    except Exception:
        # Fallback parsing for safety
        unit = timeframe[-1]
        num = int(timeframe[:-1])
        if unit == "m":
            tf_minutes = num
        elif unit == "h":
            tf_minutes = num * 60
        elif unit == "d":
            tf_minutes = num * 1440
        else:
            tf_minutes = 1

    # Add extra bars for MAs and chart context
    extra = (max(moving_averages) if moving_averages else 0) + 5
    approx_candles = int((lookback_minutes + tf_minutes - 1) // tf_minutes)
    limit = max(20, approx_candles + extra)

    since_ms = int((time.time() - lookback_minutes * 60) * 1000)

    try:
        ohlcv = ccxt_exchange.fetch_ohlcv(symbol, timeframe, since=since_ms, limit=limit)
    except Exception:
        # Retry without since if the exchange rejects it
        ohlcv = ccxt_exchange.fetch_ohlcv(symbol, timeframe, limit=limit)

    if not ohlcv or len(ohlcv) < 5:
        raise RuntimeError(f"Not enough OHLCV data for {symbol} {timeframe}")

    ts = [row[0] for row in ohlcv]
    opens = [float(row[1]) for row in ohlcv]
    highs = [float(row[2]) for row in ohlcv]
    lows = [float(row[3]) for row in ohlcv]
    closes = [float(row[4]) for row in ohlcv]

    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(
            x=ts,
            open=opens,
            high=highs,
            low=lows,
            close=closes,
            name=symbol,
            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",
        )
    )

    for window in moving_averages:
        if window and window > 1 and window <= len(closes):
            ma = _compute_sma(closes, window)
            fig.add_trace(
                go.Scatter(
                    x=ts,
                    y=ma,
                    mode="lines",
                    name=f"MA{window}",
                    line=dict(width=1.6),
                )
            )

    fig.update_layout(
        template="plotly_dark" if theme.lower() == "dark" else "plotly_white",
        title=dict(text=f"{symbol} ({timeframe}) - Recent Price", x=0.01, xanchor="left"),
        margin=dict(l=10, r=10, t=40, b=20),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(128,128,128,0.2)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(rangeslider_visible=False)

    try:
        return fig.to_image(format="png", width=width, height=height, scale=scale)
    except Exception as e:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "Plotly image export failed. Ensure 'kaleido' is installed."
        ) from e
