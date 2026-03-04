import json
import pandas as pd
from typing import Dict, List, Tuple

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
) -> Tuple[pd.DataFrame, pd.DataFrame]:

    # Build signals+regime per symbol
    sym_data = {}
    sym_regime = {}
    for sym, df in panel.items():
        df2 = build_signals(df, breakout_days, mom_days, atr_days)
        reg = compute_weekly_regime(df2, regime_ma_weeks, regime_slope_weeks, use_slope=regime_use_slope)
        sym_data[sym] = df2
        sym_regime[sym] = reg

    # --- DEBUG STATS (safe, no behavior change) ---
    stats = {}
    for sym in sym_data.keys():
        d = sym_data[sym]
        r = sym_regime[sym].astype(bool)

        hh_ok = int(d["hh_prev"].notna().sum()) if "hh_prev" in d.columns else 0
        mom_ok = int(d["mom"].notna().sum()) if "mom" in d.columns else 0
        atr_ok = int(d["atr"].notna().sum()) if "atr" in d.columns else 0
        reg_true = int(r.sum())

        cond_ok = 0
        if all(c in d.columns for c in ["close", "hh_prev", "mom", "atr"]):
            c = (
                r
                & d["hh_prev"].notna()
                & d["mom"].notna()
                & d["atr"].notna()
                & (d["close"] > d["hh_prev"])
                & (d["mom"] > 0.0)
            )
            cond_ok = int(c.sum())

        stats[sym] = {
            "rows": int(len(d)),
            "start": str(d.index.min().date()) if len(d) else None,
            "end": str(d.index.max().date()) if len(d) else None,
            "hh_prev_notna": hh_ok,
            "mom_notna": mom_ok,
            "atr_notna": atr_ok,
            "regime_true_days": reg_true,
            "signal_cond_days": cond_ok,
        }

    print("[debug] per_symbol_stats=" + json.dumps(stats))
    # --- END DEBUG STATS ---

    # Common trading calendar: intersection to avoid missing bars
    common_idx = None
    for sym, df2 in sym_data.items():
        common_idx = df2.index if common_idx is None else common_idx.intersection(df2.index)
    common_idx = common_idx.sort_values()

    pf = PortfolioMulti(cash=initial_capital)
    equity_curve: List[dict] = []
    trades: List[dict] = []

    # pending orders keyed by symbol
    pending_entry = {}  # sym -> dict(signal_date, atr_at_signal)
    pending_exit = set()  # symbols to exit next open

    for i, dt in enumerate(common_idx):
        # marks at close for equity curve
        marks_close = {sym: float(sym_data[sym].loc[dt, "close"]) for sym in sym_data.keys()}
        eq_now = pf.equity(marks_close)

        # 1) execute exits at open
        for sym in list(pending_exit):
            if pf.has(sym):
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
                    "exit_reason": "regime_off",
                    "qty": pos.qty,
                    "stop_price": pos.stop_price,
                })
            pending_exit.discard(sym)

        # 2) stop intraday
        for sym in list(pf.positions.keys()):
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
                pending_exit.discard(sym)

        # 3) execute entries at open (if signaled prev day)
        for sym, pe in list(pending_entry.items()):
            if pf.has(sym):
                pending_entry.pop(sym, None)
                continue

            o = float(sym_data[sym].loc[dt, "open"])
            exec_px = apply_costs(o, fee_rate, slippage_rate, "buy")
            stop_price = o - stop_atr_mult * float(pe["atr"])
            if stop_price <= 0:
                pending_entry.pop(sym, None)
                continue

            # risk sizing
            marks = {s: float(sym_data[s].loc[dt, "open"]) for s in sym_data.keys()}
            eq_open = pf.equity(marks)
            print("[debug] entry_try", sym, "dt", str(dt.date()), "eq_open", eq_open, "cash", pf.cash)
            risk_cash = eq_open * risk_per_trade
            per_unit_risk = max(exec_px - stop_price, 1e-12)
            qty = risk_cash / per_unit_risk

            notional = qty * exec_px
            fee = notional * fee_rate
            stop_risk_cash = qty * max(0.0, exec_px - stop_price)

            # global risk budget gate
            budget = risk_cap_total * eq_open
            if (pf.total_stop_risk() + stop_risk_cash) <= budget and pf.can_open(sym, max_positions):
                ok = pf.open_long(sym, qty, exec_px, dt, stop_price, fee)
                if ok:
                    # entry trade record will be completed on exit
                    pass

            pending_entry.pop(sym, None)

        # 4) generate signals (EOD) for next bar
        if i < len(common_idx) - 1:
            for sym in sym_data.keys():
                row = sym_data[sym].loc[dt]
                close_p = float(row["close"])

                # regime off -> exit next open
                if pf.has(sym) and (not bool(sym_regime[sym].loc[dt])):
                    pending_exit.add(sym)

                # entry if flat + no pending
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

        equity_curve.append({"date": dt, "equity": eq_now})

    eq_df = pd.DataFrame(equity_curve).set_index("date")
    trades_df = pd.DataFrame(trades)

    if not trades_df.empty:
        trades_df["pnl"] = (
            trades_df["qty"] * trades_df["exit_price"]
            - trades_df["exit_fee"]
            - (trades_df["qty"] * trades_df["entry_price"] + trades_df["entry_fee"])
        )
    return eq_df, trades_df
