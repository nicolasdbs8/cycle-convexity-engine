from __future__ import annotations

import pandas as pd
from typing import Iterable

from .backtest_multi import run_backtest_multi_mvp
from .config import Config


def _split_symbols(symbols: Iterable[str], crypto_symbols: tuple[str, ...]):
    crypto_set = set(crypto_symbols)
    core = []
    sat = []

    for s in symbols:
        if s in crypto_set:
            sat.append(s)
        else:
            core.append(s)

    return core, sat


def _subset_panel(panel, symbols):
    return {s: panel[s] for s in symbols if s in panel}


def _align_equity(eq_df, idx, init_val: float) -> pd.Series:
    if eq_df is None or eq_df.empty:
        s = pd.Series(index=idx, data=float(init_val))
        return s

    s = eq_df["equity"].astype(float).reindex(idx)

    # If the sleeve starts later, treat equity as flat at init_val until it exists
    if pd.isna(s.iloc[0]):
        s.iloc[0] = float(init_val)

    s = s.ffill()
    s = s.fillna(float(init_val))
    return s


def _sum_equity(eq_core, eq_sat, init_core: float, init_sat: float) -> pd.DataFrame:
    # Union of calendars, not intersection
    idx = None
    if eq_core is not None and not eq_core.empty:
        idx = eq_core.index if idx is None else idx.union(eq_core.index)
    if eq_sat is not None and not eq_sat.empty:
        idx = eq_sat.index if idx is None else idx.union(eq_sat.index)

    if idx is None:
        return pd.DataFrame(columns=["equity"])

    idx = idx.sort_values()
    s_core = _align_equity(eq_core, idx, init_core)
    s_sat = _align_equity(eq_sat, idx, init_sat)

    out = pd.DataFrame(index=idx)
    out["equity"] = s_core.values + s_sat.values
    return out


def _run(panel, cfg: Config, capital_weight):

    return run_backtest_multi_mvp(
        panel=panel,
        fee_rate=cfg.fee_rate,
        slippage_rate=cfg.slippage_rate,
        initial_capital=cfg.initial_capital * capital_weight,
        risk_per_trade=cfg.risk_per_trade,
        risk_cap_total=cfg.risk_cap_total * capital_weight,
        max_positions=cfg.max_positions,
        breakout_days=cfg.breakout_days,
        mom_days=cfg.mom_days,
        atr_days=cfg.atr_days,
        stop_atr_mult=cfg.stop_atr_mult,
        regime_ma_weeks=cfg.regime_ma_weeks,
        regime_slope_weeks=cfg.regime_slope_weeks,
        regime_use_slope=bool(cfg.regime_use_slope),
    )


def run_backtest_core_satellite(panel, cfg: Config, symbols):

    core_syms, sat_syms = _split_symbols(symbols, cfg.crypto_symbols)

    eq_core = None
    tr_core = None

    if core_syms:
        core_panel = _subset_panel(panel, core_syms)
        eq_core, tr_core = _run(core_panel, cfg, cfg.core_weight)
        tr_core["sleeve"] = "core"

    eq_sat = None
    tr_sat = None

    if sat_syms:
        sat_panel = _subset_panel(panel, sat_syms)
        eq_sat, tr_sat = _run(sat_panel, cfg, cfg.sat_weight)
        tr_sat["sleeve"] = "sat"

    init_core = cfg.initial_capital * cfg.core_weight
    init_sat = cfg.initial_capital * cfg.sat_weight
    eq_total = _sum_equity(eq_core, eq_sat, init_core, init_sat)

    trades = []

    if tr_core is not None and not tr_core.empty:
        trades.append(tr_core)

    if tr_sat is not None and not tr_sat.empty:
        trades.append(tr_sat)

    tr_total = pd.concat(trades, ignore_index=True) if trades else pd.DataFrame()

    return eq_total, tr_total
