import pandas as pd
from .portfolio import Portfolio, Position

def apply_costs(price: float, fee_rate: float, slippage_rate: float, side: str) -> float:
    """
    side='buy' => pay worse price (price * (1+slip)), fee on notional
    side='sell' => receive worse price (price * (1-slip)), fee on notional
    Returns execution price after slippage (fee handled separately).
    """
    if side == "buy":
        return price * (1.0 + slippage_rate)
    if side == "sell":
        return price * (1.0 - slippage_rate)
    raise ValueError("side must be 'buy' or 'sell'")

def run_backtest_btc_mvp(
    df: pd.DataFrame,
    regime: pd.Series,
    fee_rate: float,
    slippage_rate: float,
    initial_capital: float,
    risk_per_trade: float,
    stop_atr_mult: float,
):
    """
    Single-asset BTC MVP:
    - Entry signal (evaluated on day t close):
        regime[t] == True
        close[t] > hh_prev[t]
        mom[t] > 0
        atr[t] is not NaN
      Execute at next day open (t+1 open)
    - Initial stop: entry - stop_atr_mult * atr[t]  (ATR from signal day)
    - Exit:
        1) stop hit intraday: if low[t] <= stop_price -> exit at stop_price (worst-case fill w/ slippage/fees)
        2) regime turns OFF (on day t close) -> exit next open
    - Position sizing: risk_per_trade * equity / (entry - stop)
      One position at a time.
    """
    portfolio = Portfolio(cash=initial_capital, position=Position())
    trades = []

    equity_curve = []
    dates = df.index

    pending_entry = False
    pending_exit = False
    pending_stop = None
    pending_entry_atr = None
    pending_signal_date = None

    for i in range(len(dates)):
        dt = dates[i]
        row = df.iloc[i]

        open_p = float(row["open"])
        high_p = float(row["high"])
        low_p = float(row["low"])
        close_p = float(row["close"])

        # 1) Execute pending exit at today's open
        if pending_exit and portfolio.is_in_market:
            exec_px = apply_costs(open_p, fee_rate, slippage_rate, side="sell")
            notional = portfolio.position.qty * exec_px
            fee = notional * fee_rate
            portfolio.cash += notional - fee

            trades[-1]["exit_date"] = dt
            trades[-1]["exit_price"] = exec_px
            trades[-1]["exit_fee"] = fee
            trades[-1]["exit_reason"] = "regime_off"

            portfolio.position = Position()
            pending_exit = False

        # 2) Stop logic (intraday) for open position
        if portfolio.is_in_market:
            stop_price = portfolio.position.stop_price
            if low_p <= stop_price:
                # exit at stop price (then apply slippage/fees as sell)
                exec_px = apply_costs(stop_price, fee_rate, slippage_rate, side="sell")
                notional = portfolio.position.qty * exec_px
                fee = notional * fee_rate
                portfolio.cash += notional - fee

                trades[-1]["exit_date"] = dt
                trades[-1]["exit_price"] = exec_px
                trades[-1]["exit_fee"] = fee
                trades[-1]["exit_reason"] = "stop"

                portfolio.position = Position()
                pending_exit = False  # in case it was set
            # else: remain in market

        # 3) Execute pending entry at today's open (if flat)
        if pending_entry and (not portfolio.is_in_market):
            # Determine stop from ATR measured at signal day
            stop_price = open_p - stop_atr_mult * float(pending_entry_atr)
            if stop_price <= 0:
                pending_entry = False
            else:
                exec_px = apply_costs(open_p, fee_rate, slippage_rate, side="buy")

                # Position sizing by risk
                eq = portfolio.equity(mark_price=exec_px)
                risk_cash = eq * risk_per_trade
                per_unit_risk = max(exec_px - stop_price, 1e-12)
                qty = risk_cash / per_unit_risk

                # Ensure we can afford (spot, no leverage in MVP)
                notional = qty * exec_px
                fee = notional * fee_rate
                total_cost = notional + fee

                if total_cost <= portfolio.cash and qty > 0:
                    portfolio.cash -= total_cost
                    portfolio.position = Position(
                        qty=qty,
                        entry_price=exec_px,
                        entry_date=dt,
                        stop_price=stop_price,
                    )
                    trades.append({
                        "entry_date": dt,
                        "entry_price": exec_px,
                        "entry_fee": fee,
                        "signal_date": pending_signal_date,
                        "qty": qty,
                        "stop_price": stop_price,
                        "exit_date": None,
                        "exit_price": None,
                        "exit_fee": None,
                        "exit_reason": None,
                    })

                pending_entry = False

        # 4) Generate signals at end of day (for next day)
        # Avoid generating if last bar (no next open to execute)
        if i < len(dates) - 1:
            # If in market: check regime OFF to exit next open
            if portfolio.is_in_market and (not bool(regime.loc[dt])):
                pending_exit = True

            # If flat: check entry conditions
            if (not portfolio.is_in_market) and (not pending_entry):
                hh_prev = row.get("hh_prev", None)
                mom = row.get("mom", None)
                atr_val = row.get("atr", None)

                cond = (
                    bool(regime.loc[dt]) and
                    (hh_prev is not None) and
                    (mom is not None) and
                    (atr_val is not None) and
                    pd.notna(hh_prev) and pd.notna(mom) and pd.notna(atr_val) and
                    (close_p > float(hh_prev)) and
                    (float(mom) > 0.0)
                )
                if cond:
                    pending_entry = True
                    pending_entry_atr = float(atr_val)
                    pending_signal_date = dt

        equity_curve.append({"date": dt, "equity": portfolio.equity(mark_price=close_p)})

    eq_df = pd.DataFrame(equity_curve).set_index("date")
    trades_df = pd.DataFrame(trades)

    # Compute PnL per trade (simple)
    if not trades_df.empty:
        trades_df["pnl"] = (
            trades_df["qty"] * trades_df["exit_price"]
            - trades_df["exit_fee"]
            - (trades_df["qty"] * trades_df["entry_price"] + trades_df["entry_fee"])
        )
    return eq_df, trades_df
