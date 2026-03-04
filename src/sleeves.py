from __future__ import annotations

from dataclasses import replace
from typing import Iterable

import pandas as pd

from .backtest_multi import run_backtest_multi_mvp
from .config import Config


def _split_symbols(symbols: Iterable[str], crypto_symbols: tuple[str, ...]) -> tuple[list[str], list[str]]:
    crypto_set = set(crypto_symbols)
    core_syms: list[str] = []
    sat_syms: list[str] = []
    for s in symbols:
        (sat_syms if s in crypto_set else core_syms).append(s)
    return core_syms, sat_syms


def _sum_equity(eq_a: pd.DataFrame | None, eq_b: pd.DataFrame | None) -> pd.DataFrame:
    """
    Equity curves are expected to contain an 'equity' column indexed by datetime.
    We align on the intersection of indices to avoid accidental forward-fill lookahead.
    """
    if eq_a is None and eq_b is None:
        return pd.DataFrame(columns=["equity"])
    if eq_a is None:
        return eq_b.copy()
    if eq_b is None:
        return eq_a.copy()

    a = eq_a.copy()
    b = eq_b.copy()
    common_idx = a.index.intersection(b.index)
    a = a.loc[common_idx]
    b = b.loc[common_idx]

    out = pd.DataFrame(index=common_idx)
    out["equity"] = a["equity"].astype(float).values + b["equity"].astype(float).values
    return out


def run_backtest_core_satellite(panel, cfg: Config, symbols: list[str]):
    """
    Run two sleeves:
    - CORE: non-crypto symbols, capital = core_weight * initial_capital
    - SAT : crypto symbols,     capital = sat_weight * initial_capital

    Each sleeve gets its own risk budget scaled by its weight.
    Returns:
      eq_total_df with column 'equity'
      trades_df with added 'sleeve' column
    """
    core_syms, sat_syms = _split_symbols(symbols, cfg.crypto_symbols)

    eq_core = None
    tr_core = None
    if core_syms:
        cfg_core = replace(
            cfg,
            initial_capital=cfg.initial_capital * cfg.core_weight,
            risk_cap_total=cfg.risk_cap_total * cfg.core_weight,
        )
        eq_core, tr_core = run_backtest_multi_mvp(panel, cfg_core, core_syms)
        tr_core = tr_core.copy()
        tr_core["sleeve"] = "core"

    eq_sat = None
    tr_sat = None
    if sat_syms:
        cfg_sat = replace(
            cfg,
            initial_capital=cfg.initial_capital * cfg.sat_weight,
            risk_cap_total=cfg.risk_cap_total * cfg.sat_weight,
        )
        eq_sat, tr_sat = run_backtest_multi_mvp(panel, cfg_sat, sat_syms)
        tr_sat = tr_sat.copy()
        tr_sat["sleeve"] = "sat"

    eq_total = _sum_equity(eq_core, eq_sat)

    trades = []
    if tr_core is not None and len(tr_core) > 0:
        trades.append(tr_core)
    if tr_sat is not None and len(tr_sat) > 0:
        trades.append(tr_sat)
    tr_total = pd.concat(trades, ignore_index=True) if trades else pd.DataFrame()

    return eq_total, tr_total
