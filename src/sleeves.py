from __future__ import annotations

import os
import pandas as pd
import numpy as np

from .backtest_multi import run_backtest_multi_mvp
from .config import Config
from .universe import load_crypto_monthly_schedule, symbols_for_date


CRYPTO_UNIVERSE_PATH = "data/universe/crypto_monthly.csv"


def _split_symbols(symbols, crypto_symbols: tuple[str, ...]):
    crypto_set = set(crypto_symbols)
    core = []
    sat = []
    for s in symbols:
        (sat if s in crypto_set else core).append(s)
    return core, sat


def _subset_panel(panel, symbols):
    return {s: panel[s] for s in symbols if s in panel}


def _align_equity(eq_df, idx, init_val: float) -> pd.Series:
    if eq_df is None or eq_df.empty:
        return pd.Series(index=idx, data=float(init_val))

    s = eq_df["equity"].astype(float).reindex(idx)
    if pd.isna(s.iloc[0]):
        s.iloc[0] = float(init_val)

    s = s.ffill()
    s = s.fillna(float(init_val))
    return s


def _sum_equity(eq_core, eq_sat, init_core: float, init_sat: float) -> pd.DataFrame:
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


def _run(panel, cfg: Config, capital_weight: float, allowed_symbols_fn=None):

    return run_backtest_multi_mvp(
        panel=panel,
        fee_rate=cfg.fee_rate,
        slippage_rate=cfg.slippage_rate,
        initial_capital=cfg.initial_capital * capital_weight,
        risk_per_trade=cfg.risk_per_trade,
        risk_cap_total=cfg.risk_cap_total,
        max_positions=cfg.max_positions,
        breakout_days=cfg.breakout_days,
        mom_days=cfg.mom_days,
        atr_days=cfg.atr_days,
        stop_atr_mult=cfg.stop_atr_mult,
        regime_ma_weeks=cfg.regime_ma_weeks,
        regime_slope_weeks=cfg.regime_slope_weeks,
        regime_use_slope=bool(cfg.regime_use_slope),
        allowed_symbols_fn=allowed_symbols_fn,
    )


def _annualized_vol(eq_df):
    if eq_df is None or eq_df.empty:
        return 0.0

    r = eq_df["equity"].pct_change().dropna()
    if len(r) == 0:
        return 0.0

    return float(r.std() * np.sqrt(252))


def run_backtest_core_satellite(panel, cfg: Config, symbols):

    core_syms, sat_syms = _split_symbols(symbols, cfg.crypto_symbols)

    sched = None
    if os.path.exists(CRYPTO_UNIVERSE_PATH):
        sched = load_crypto_monthly_schedule(CRYPTO_UNIVERSE_PATH)

    def sat_allowed(dt):
        if sched is None:
            return set(sat_syms)
        return symbols_for_date(dt, sched)

    # ---- FIRST PASS (measure vol) ----

    eq_core_0 = None
    if core_syms:
        core_panel = _subset_panel(panel, core_syms)
        eq_core_0, tr_core_0 = _run(core_panel, cfg, cfg.core_weight)

    eq_sat_0 = None
    if sat_syms:
        sat_panel = _subset_panel(panel, sat_syms)
        eq_sat_0, tr_sat_0 = _run(sat_panel, cfg, cfg.sat_weight, sat_allowed)

    vol_core = _annualized_vol(eq_core_0)
    vol_sat = _annualized_vol(eq_sat_0)

    # ---- VOL SCALING ----

    core_w = cfg.core_weight
    sat_w = cfg.sat_weight

    if vol_core > 0 and vol_sat > 0:

        inv_core = 1.0 / vol_core
        inv_sat = 1.0 / vol_sat

        s = inv_core + inv_sat

        core_w = inv_core / s
        sat_w = inv_sat / s

    # ---- SECOND PASS (final backtest) ----

    eq_core = None
    tr_core = None

    if core_syms:
        core_panel = _subset_panel(panel, core_syms)
        eq_core, tr_core = _run(core_panel, cfg, core_w)
        tr_core = tr_core.copy()
        tr_core["sleeve"] = "core"

    eq_sat = None
    tr_sat = None

    if sat_syms:
        sat_panel = _subset_panel(panel, sat_syms)
        eq_sat, tr_sat = _run(sat_panel, cfg, sat_w, sat_allowed)
        tr_sat = tr_sat.copy()
        tr_sat["sleeve"] = "sat"

    init_core = cfg.initial_capital * core_w
    init_sat = cfg.initial_capital * sat_w

    eq_total = _sum_equity(eq_core, eq_sat, init_core, init_sat)

    trades = []
    if tr_core is not None and not tr_core.empty:
        trades.append(tr_core)

    if tr_sat is not None and not tr_sat.empty:
        trades.append(tr_sat)

    tr_total = pd.concat(trades, ignore_index=True) if trades else pd.DataFrame()

    return eq_total, tr_total, eq_core, eq_sat
