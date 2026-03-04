import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Callable, Optional

from .portfolio_multi import PortfolioMulti
from .backtest import apply_costs
from .strategy import build_signals
from .regime import compute_weekly_regime


def run_backtest_multi_mvp(
    panel: Dict[str, pd.DataFrame],
    fee_rate: float,
    slippage_rate: float,
    initial_capital: float,
    risk_per_trade: float,
    risk_cap_total: float,
    max_positions: int,
    breakout_days: int,
    mom_days: int,
    atr_days: int,
    stop_atr_mult: float,
    regime_ma_weeks: int,
    regime_slope_weeks: int,
    regime_use_slope: bool,
    allowed_symbols_fn: Optional[Callable[[pd.Timestamp], set]] = None,
    risk_per_trade_fn: Optional[Callable[[pd.Timestamp], float]] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Multi-asset backtest (long-only breakout) with:
      - next-open execution
      - fees + slippage
      - ATR stop
      - weekly MA regime filter
      - global risk cap (sum stop-risk)
      - max_positions
      - optional universe constraint via allowed_symbols_fn(dt)->set(symbols)
      - optional dynamic risk via risk_per_trade_fn(dt)->float

    Robust calendar handling:
      - uses UNION of all timestamps across symbols
      - only trades a symbol on dates where it has a bar
      - marks equity using last known close for symbols without a bar on dt (e.g., ETFs on weekends)
    """

    # Build signals+regime per symbol
    sym_data: Dict[str, pd.DataFrame] = {}
    sym_regime: Dict[str, pd.Series] = {}

    for sym, df in panel.items():
        df2 = build_signals(df, breakout_days, mom_days, atr_days)
        reg = compute_weekly_regime(
            df2,
            regime_ma_weeks,
            regime_slope_weeks,
            use_slope=regime_use_slope,
        )
        sym_data[sym] = df2
        sym_regime[sym] = reg

    # Master calendar: UNION of all indices
    all_idx = None
    for _, df2 in sym_data.items():
        all_idx = df2.index if all_idx is None else all_idx.union(df2.index)
    if all_idx is None or len(all_idx) == 0:
        return pd.DataFrame(columns=["equity"]), pd.DataFrame()

    calendar = all_idx.sort_values()

    def has_bar(sym: str, dt: pd.Timestamp) -> bool:
        return dt in sym_data[sym].index

    # Last known close price per symbol (for marking)
    last_close: Dict[str, float] = {}
    for sym, df2 in sym_data.items():
        last_close[sym] = float(df2["close"].iloc[0])

    pf = PortfolioMulti(cash=initial_capital)
    equity_curve: List[dict] = []
    trades: List[dict] = []

    pending_entry = {}        # sym -> dict(signal_date, atr)
    pending_exit_reason = {}  # sym -> reason string

    for dt in calendar:
        allowed = allowed_symbols_fn(dt) if allowed_symbols_fn is not None else None

        # update last close
        for sym in sym_data.keys():
            if has_bar(sym, dt):
                last_close[sym] = float(sym_data[sym].loc[dt, "close"])

        marks_close = {sym: float(last_close[sym]) for sym in sym_data.keys()}
        eq_now = pf.equity(marks_close)

        # dynamic risk for today (clamped)
        rpt = float(risk_per_trade_fn(dt)) if risk_per_trade_fn is not None else float(risk_per_trade)
        if not np.isfinite(rpt):
            rpt = float(risk_per_trade)
        rpt = max(0.0, min(0.10, rpt))  # hard clamp safety

        # forced exits if universe drops
        if allowed is not None:
            for sym in list(pf.positions.keys()):
                if sym not in allowed and sym not in pending_exit_reason:
                    pending_exit_reason[sym] = "universe_exit"

        # 1) execute exits at open
        for sym in list(pending_exit_reason.keys()):
            reason = pending_exit_reason.get(sym, "exit")
            if not pf.has(sym):
                pending_exit_reason.pop(sym, None)
                continue
            if not has_bar(sym, dt):
                continue

            o = float(sym_data[sym].loc[dt, "open"])
            exec_px = apply_costs(o, fee_rate, slippage_rate, "sell")
            notional = pf.positions[sym].qty * exec_px
            fee = notional * fee_rate
            pos = pf.close_long(sym, exec_px, dt, fee)

            trades.append({
                "symbol": sym,
                "entry_date": pos.entry_date,
                "entry_price": pos.entry_price,
                "entry_fee": pos.entry_fee,
                "exit_date": dt,
                "exit_price": exec_px,
                "exit_fee": fee,
                "exit_reason": reason,
                "qty": pos.qty,
                "stop_price": pos.stop_price,
            })
            pending_exit_reason.pop(sym, None)

        # 2) stop intraday
        for sym in list(pf.positions.keys()):
            if not has_bar(sym, dt):
                continue
            low = float(sym_data[sym].loc[dt, "low"])
            stop = pf.positions[sym].stop_price
            if low <= stop:
                exec_px = apply_costs(stop, fee_rate, slippage_rate, "sell")
                notional = pf.positions[sym].qty * exec_px
                fee = notional * fee_rate
                pos = pf.close_long(sym, exec_px, dt, fee)

                trades.append({
                    "symbol": sym,
                    "entry_date": pos.entry_date,
                    "entry_price": pos.entry_price,
                    "entry_fee": pos.entry_fee,
                    "exit_date": dt,
                    "exit_price": exec_px,
                    "exit_fee": fee,
                    "exit_reason": "stop",
                    "qty": pos.qty,
                    "stop_price": pos.stop_price,
                })
                pending_exit_reason.pop(sym, None)

        # 3) execute entries at open
        for sym, pe in list(pending_entry.items()):
            if allowed is not None and sym not in allowed:
                pending_entry.pop(sym, None)
                continue
            if pf.has(sym):
                pending_entry.pop(sym, None)
                continue
            if not has_bar(sym, dt):
                continue

            o = float(sym_data[sym].loc[dt, "open"])
            exec_px = apply_costs(o, fee_rate, slippage_rate, "buy")
            stop_price = o - stop_atr_mult * float(pe["atr"])
            if stop_price <= 0:
                pending_entry.pop(sym, None)
                continue

            eq_open = eq_now
            risk_cash = eq_open * rpt
            per_unit_risk = max(exec_px - stop_price, 1e-12)
            qty = risk_cash / per_unit_risk

            # cash cap (no leverage)
            max_qty_cash = pf.cash / (exec_px * (1.0 + fee_rate))
            qty = min(qty, max_qty_cash)
            if qty <= 0:
                pending_entry.pop(sym, None)
                continue

            notional = qty * exec_px
            fee = notional * fee_rate
            stop_risk_cash = qty * max(0.0, exec_px - stop_price)

            budget = risk_cap_total * eq_open
            if (pf.total_stop_risk() + stop_risk_cash) <= budget and pf.can_open(sym, max_positions):
                pf.open_long(sym, qty, exec_px, dt, stop_price, fee)

            pending_entry.pop(sym, None)

        # 4) EOD signals
        for sym in sym_data.keys():
            if not has_bar(sym, dt):
                continue
            if allowed is not None and sym not in allowed:
                continue

            row = sym_data[sym].loc[dt]
            close_p = float(row["close"])

            if pf.has(sym) and (not bool(sym_regime[sym].loc[dt])):
                if sym not in pending_exit_reason:
                    pending_exit_reason[sym] = "regime_off"

            if (not pf.has(sym)) and (sym not in pending_entry):
                hh_prev = row.get("hh_prev", None)
                mom = row.get("mom", None)
                atr_v = row.get("atr", None)
                cond = (
                    bool(sym_regime[sym].loc[dt]) and
                    pd.notna(hh_prev) and pd.notna(mom) and pd.notna(atr_v) and
                    (close_p > float(hh_prev)) and
                    (float(mom) > 0.0)
                )
                if cond:
                    pending_entry[sym] = {"signal_date": dt, "atr": float(atr_v)}

        equity_curve.append({"date": dt, "equity": float(eq_now)})

    eq_df = pd.DataFrame(equity_curve).set_index("date")
    trades_df = pd.DataFrame(trades)

    if not trades_df.empty:
        trades_df["pnl"] = (
            trades_df["qty"] * trades_df["exit_price"]
            - trades_df["exit_fee"]
            - (trades_df["qty"] * trades_df["entry_price"] + trades_df["entry_fee"])
        )

    return eq_df, trades_df
