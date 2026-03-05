import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Callable, Optional

from .portfolio_multi import PortfolioMulti
from .backtest import apply_costs
from .strategy import build_signals
from .regime import compute_weekly_regime


def _rolling_ann_vol(ret_s: pd.Series, window: int) -> float:
    """Return latest rolling annualized vol (sqrt(252) * std) or NaN."""
    if ret_s is None or len(ret_s) < window:
        return float("nan")
    v = ret_s.iloc[-window:].astype(float).std(ddof=0) * np.sqrt(252.0)
    return float(v)


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
    # Optional dynamic risk budget (kept for compatibility; sleeves can pass None)
    risk_per_trade_fn: Optional[Callable[[pd.Timestamp], float]] = None,
    # Portfolio volatility targeting (applied as a scaler to risk budgets)
    vol_target_annual: Optional[float] = None,
    vol_window_days: int = 30,
    vol_scaler_min: float = 0.25,
    vol_scaler_max: float = 1.0,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Multi-asset backtest (long-only breakout) with:
      - next-open execution
      - fees + slippage
      - ATR stop (fixed at entry)
      - weekly MA regime filter
      - global risk cap (sum stop-risk)
      - max_positions
      - optional universe constraint via allowed_symbols_fn(dt)->set(symbols)

    IMPORTANT (anti-lookahead):
      - sizing uses EQUITY AT OPEN computed from *previous known close* marks
      - signals are computed on close (EOD) and queued for next available open
      - equity curve is marked on close (EOD)

    Robust calendar handling:
      - UNION of all timestamps across symbols
      - trades a symbol only on dates where it has a bar
      - marks equity using last known close for symbols without a bar on dt (e.g., ETFs on weekends)
    """

    # Build signals+regime per symbol
    sym_data: Dict[str, pd.DataFrame] = {}
    sym_regime: Dict[str, pd.Series] = {}

    for sym, df in panel.items():
        df2 = build_signals(df, breakout_days, mom_days, atr_days, exit_ll_days=50)
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

    # Last known close price per symbol (known at the NEXT open)
    last_close: Dict[str, float] = {}
    for sym, df2 in sym_data.items():
        last_close[sym] = float(df2["close"].iloc[0])

    pf = PortfolioMulti(cash=float(initial_capital))
    equity_curve: List[dict] = []
    trades: List[dict] = []

    pending_entry: Dict[str, dict] = {}        # sym -> dict(signal_date, atr)
    pending_exit_reason: Dict[str, str] = {}   # sym -> reason

    # For realized-vol targeting we use *close-to-close* portfolio returns
    eq_close_hist: List[float] = []
    ret_hist: List[float] = []

    for dt in calendar:
        allowed = allowed_symbols_fn(dt) if allowed_symbols_fn is not None else None

        # ---- OPEN STATE (known info at the open) ----
        marks_prevclose = {sym: float(last_close[sym]) for sym in sym_data.keys()}
        eq_open = float(pf.equity(marks_prevclose))

        # Realized-vol scaler (based only on PAST close-to-close returns)
        vol_scaler = 1.0
        if vol_target_annual is not None and vol_window_days > 0:
            v = _rolling_ann_vol(pd.Series(ret_hist), vol_window_days)
            if np.isfinite(v) and v > 0:
                vol_scaler = float(vol_target_annual) / float(v)
                vol_scaler = max(float(vol_scaler_min), min(float(vol_scaler_max), vol_scaler))

        # If universe says a held symbol is no longer allowed, schedule exit
        if allowed is not None:
            for sym in list(pf.positions.keys()):
                if sym not in allowed and sym not in pending_exit_reason:
                    pending_exit_reason[sym] = "universe_exit"

        # 1) Execute exits at open (only if the symbol has a bar today)
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

        # 2) Stop intraday (only if symbol has a bar today)
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

        # 3) Execute entries at open (only if symbol has a bar today)
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

            rpt = float(risk_per_trade_fn(dt)) if risk_per_trade_fn is not None else float(risk_per_trade)
            rpt_eff = rpt * float(vol_scaler)
            cap_eff = float(risk_cap_total) * float(vol_scaler)

            n = max(len(pf.positions) +1, 1)
            risk_cash = eq_open * rpt_eff / np.sqrt(n)
            per_unit_risk = max(exec_px - stop_price, 1e-12)
            qty = risk_cash / per_unit_risk

            # CASH CAP (no leverage)
            max_qty_cash = pf.cash / (exec_px * (1.0 + fee_rate))
            if qty > max_qty_cash:
                qty = max_qty_cash
            if qty <= 0:
                pending_entry.pop(sym, None)
                continue

            notional = qty * exec_px
            fee = notional * fee_rate
            stop_risk_cash = qty * max(0.0, exec_px - stop_price)

            budget = cap_eff * eq_open
            if (pf.total_stop_risk() + stop_risk_cash) <= budget and pf.can_open(sym, max_positions):
                pf.open_long(sym, qty, exec_px, dt, stop_price, fee)

            pending_entry.pop(sym, None)

        # ---- CLOSE STATE (EOD data becomes known now) ----
        for sym in sym_data.keys():
            if has_bar(sym, dt):
                last_close[sym] = float(sym_data[sym].loc[dt, "close"])

        marks_close = {sym: float(last_close[sym]) for sym in sym_data.keys()}
        eq_close = float(pf.equity(marks_close))

        if len(eq_close_hist) > 0:
            prev = float(eq_close_hist[-1])
            if prev > 0:
                ret_hist.append((eq_close / prev) - 1.0)
        eq_close_hist.append(eq_close)

        # 4) Generate signals (EOD)
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

            # Donchian exit (trend break): close < LL_prev => exit next open
            if pf.has(sym):
                ll_prev = row.get("ll_prev", None)
                if pd.notna(ll_prev) and (close_p < float(ll_prev)):
                    if sym not in pending_exit_reason:
                        pending_exit_reason[sym] = "donchian_ll"

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

        equity_curve.append({"date": dt, "equity": float(eq_close)})

    eq_df = pd.DataFrame(equity_curve).set_index("date")
    trades_df = pd.DataFrame(trades)

    if not trades_df.empty:
        trades_df["pnl"] = (
            trades_df["qty"] * trades_df["exit_price"]
            - trades_df["exit_fee"]
            - (trades_df["qty"] * trades_df["entry_price"] + trades_df["entry_fee"])
        )

    return eq_df, trades_df
