from __future__ import annotations
import os
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Callable

from .backtest_multi import run_backtest_multi_mvp
from .config import Config
from .universe import load_crypto_monthly_schedule, symbols_for_date

CRYPTO_UNIVERSE_PATH = "data/universe/crypto_monthly.csv"

# ---- ranking parameter
CORE_TOP_N = 3


def _split_symbols(symbols: List[str], crypto_symbols: tuple[str, ...]):
    crypto = set(crypto_symbols)
    core, sat = [], []
    for s in symbols:
        (sat if s in crypto else core).append(s)
    return core, sat


def _subset_panel(panel: Dict[str, pd.DataFrame], symbols: List[str]):
    return {s: panel[s] for s in symbols if s in panel}


def _core_allowed_builder(panel, core_syms):

    # union calendar
    idx = None
    for s in core_syms:
        if s in panel:
            idx = panel[s].index if idx is None else idx.union(panel[s].index)

    idx = idx.sort_values()

    def allowed(dt):

        moms = []

        for s in core_syms:

            if s not in panel:
                continue

            df = panel[s]

            if dt not in df.index:
                continue

            m = df.loc[dt]["mom"]

            if pd.notna(m):
                moms.append((s, float(m)))

        if not moms:
            return set()

        moms = sorted(moms, key=lambda x: x[1], reverse=True)

        return {s for s, _ in moms[:CORE_TOP_N]}

    return allowed


def _run(panel, cfg, weight, allowed_symbols_fn=None, risk_per_trade_fn=None):

    return run_backtest_multi_mvp(
        panel=panel,
        fee_rate=cfg.fee_rate,
        slippage_rate=cfg.slippage_rate,
        initial_capital=cfg.initial_capital * weight,
        risk_per_trade=cfg.risk_per_trade,
        risk_cap_total=cfg.risk_cap_total,
        max_positions=cfg.max_positions,
        breakout_days=cfg.breakout_days,
        mom_days=cfg.mom_days,
        atr_days=cfg.atr_days,
        stop_atr_mult=cfg.stop_atr_mult,
        regime_ma_weeks=cfg.regime_ma_weeks,
        regime_slope_weeks=cfg.regime_slope_weeks,
        regime_use_slope=cfg.regime_use_slope,
        allowed_symbols_fn=allowed_symbols_fn,
        risk_per_trade_fn=risk_per_trade_fn
    )


def run_backtest_core_satellite(panel: Dict[str, pd.DataFrame], cfg: Config, symbols: List[str]):

    core_syms, sat_syms = _split_symbols(symbols, cfg.crypto_symbols)

    # ---- crypto schedule
    sched = None

    if os.path.exists(CRYPTO_UNIVERSE_PATH):
        sched = load_crypto_monthly_schedule(CRYPTO_UNIVERSE_PATH)

    def sat_allowed(dt):

        if sched is None:
            return set(sat_syms)

        return set(symbols_for_date(dt, sched)).intersection(set(sat_syms))

    # ---- core ranking filter
    core_allowed = _core_allowed_builder(panel, core_syms)

    # ---- run sleeves
    eq_core = tr_core = None
    if core_syms:

        core_panel = _subset_panel(panel, core_syms)

        eq_core, tr_core = _run(
            core_panel,
            cfg,
            cfg.core_weight,
            allowed_symbols_fn=core_allowed
        )

        if tr_core is not None and not tr_core.empty:
            tr_core = tr_core.copy()
            tr_core["sleeve"] = "core"

    eq_sat = tr_sat = None
    if sat_syms:

        sat_panel = _subset_panel(panel, sat_syms)

        eq_sat, tr_sat = _run(
            sat_panel,
            cfg,
            cfg.sat_weight,
            allowed_symbols_fn=sat_allowed
        )

        if tr_sat is not None and not tr_sat.empty:
            tr_sat = tr_sat.copy()
            tr_sat["sleeve"] = "sat"

    # ---- merge equity curves
    idx = None

    if eq_core is not None:
        idx = eq_core.index if idx is None else idx.union(eq_core.index)

    if eq_sat is not None:
        idx = eq_sat.index if idx is None else idx.union(eq_sat.index)

    idx = idx.sort_values()

    core_eq = eq_core["equity"].reindex(idx).ffill() if eq_core is not None else 0
    sat_eq = eq_sat["equity"].reindex(idx).ffill() if eq_sat is not None else 0

    eq_total = pd.DataFrame(index=idx)
    eq_total["equity"] = core_eq + sat_eq

    # ---- merge trades
    trades = []

    if tr_core is not None:
        trades.append(tr_core)

    if tr_sat is not None:
        trades.append(tr_sat)

    tr_total = pd.concat(trades, ignore_index=True) if trades else pd.DataFrame()

    return eq_total, tr_total, eq_core, eq_sat
