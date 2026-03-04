from __future__ import annotations

import os
from typing import Dict, List, Optional, Tuple, Callable

import numpy as np
import pandas as pd

from .backtest_multi import run_backtest_multi_mvp
from .config import Config
from .universe import load_crypto_monthly_schedule, symbols_for_date
from .strategy import build_signals

CRYPTO_UNIVERSE_PATH = "data/universe/crypto_monthly.csv"
CORE_TOP_N = 3


def _split_symbols(symbols: List[str], crypto_symbols: tuple[str, ...]) -> Tuple[List[str], List[str]]:
    crypto = set(crypto_symbols)
    core, sat = [], []
    for s in symbols:
        (sat if s in crypto else core).append(s)
    return core, sat


def _subset_panel(panel: Dict[str, pd.DataFrame], symbols: List[str]) -> Dict[str, pd.DataFrame]:
    return {s: panel[s] for s in symbols if s in panel}


def _align_equity(eq_df: Optional[pd.DataFrame], idx: pd.DatetimeIndex, init_val: float) -> pd.Series:
    """Align an equity curve onto idx and forward-fill. Guarantees first value init_val."""
    if eq_df is None or eq_df.empty:
        return pd.Series(index=idx, data=float(init_val))

    s = eq_df["equity"].astype(float).reindex(idx)
    if len(s) > 0 and pd.isna(s.iloc[0]):
        s.iloc[0] = float(init_val)
    return s.ffill().fillna(float(init_val))


def _sum_equity(
    eq_core: Optional[pd.DataFrame],
    eq_sat: Optional[pd.DataFrame],
    init_core: float,
    init_sat: float,
) -> pd.DataFrame:
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


def _core_allowed_builder(panel: Dict[str, pd.DataFrame], core_syms: List[str], cfg: Config) -> Callable[[pd.Timestamp], set]:
    """Top-N momentum filter for the CORE sleeve (computed on the same bars, no lookahead)."""
    sig_panel: Dict[str, pd.DataFrame] = {}
    for s in core_syms:
        if s not in panel:
            continue
        sig_panel[s] = build_signals(panel[s], cfg.breakout_days, cfg.mom_days, cfg.atr_days)

    def allowed(dt: pd.Timestamp) -> set:
        moms = []
        for s, df in sig_panel.items():
            if dt not in df.index:
                continue
            m = df.loc[dt].get("mom", np.nan)
            if pd.notna(m):
                moms.append((s, float(m)))

        if not moms:
            return set()

        moms.sort(key=lambda x: x[1], reverse=True)
        return {s for s, _ in moms[:CORE_TOP_N]}

    return allowed


def _apply_vol_target(eq_df: Optional[pd.DataFrame], target_vol_annual: Optional[float], cfg: Config) -> Optional[pd.DataFrame]:
    """Volatility targeting on an equity curve (close-to-close), no lookahead via shift(1).

    - Uses rolling std on pct_change() returns.
    - Annualization: * sqrt(252)
    - Clamp scaler to [cfg.vol_scaler_min, cfg.vol_scaler_max]
    - If target_vol_annual is None -> disabled (returns input).
    """
    if eq_df is None or eq_df.empty or target_vol_annual is None:
        return eq_df

    eq = eq_df["equity"].astype(float)
    if len(eq) < 3:
        return eq_df

    ret = eq.pct_change()
    vol = ret.rolling(int(cfg.vol_window_days)).std(ddof=0) * np.sqrt(252.0)

    scaler = (float(target_vol_annual) / vol)
    scaler = scaler.replace([np.inf, -np.inf], np.nan).fillna(1.0)
    scaler = scaler.clip(float(cfg.vol_scaler_min), float(cfg.vol_scaler_max))

    # no lookahead: scaler from information up to t-1 applies to return at t
    ret_adj = ret * scaler.shift(1).fillna(1.0)

    eq_out = (1.0 + ret_adj.fillna(0.0)).cumprod() * float(eq.iloc[0])

    out = eq_df.copy()
    out["equity"] = eq_out
    return out


def _run(
    panel: Dict[str, pd.DataFrame],
    cfg: Config,
    capital_weight: float,
    allowed_symbols_fn: Optional[Callable[[pd.Timestamp], set]] = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    return run_backtest_multi_mvp(
        panel=panel,
        fee_rate=cfg.fee_rate,
        slippage_rate=cfg.slippage_rate,
        initial_capital=cfg.initial_capital * float(capital_weight),
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


def run_backtest_core_satellite(panel: Dict[str, pd.DataFrame], cfg: Config, symbols: List[str]):
    core_syms, sat_syms = _split_symbols(symbols, cfg.crypto_symbols)

    sched = None
    if os.path.exists(CRYPTO_UNIVERSE_PATH):
        sched = load_crypto_monthly_schedule(CRYPTO_UNIVERSE_PATH)

    def sat_allowed(dt: pd.Timestamp) -> set:
        # If no schedule, allow all sat_syms (static candidate set)
        if sched is None:
            return set(sat_syms)
        # Otherwise: monthly Top-N list intersected with candidate set
        return set(symbols_for_date(dt, sched)).intersection(set(sat_syms))

    core_allowed = _core_allowed_builder(panel, core_syms, cfg)

    eq_core = tr_core = None
    if core_syms:
        core_panel = _subset_panel(panel, core_syms)
        eq_core, tr_core = _run(core_panel, cfg, cfg.core_weight, allowed_symbols_fn=core_allowed)
        if tr_core is not None and not tr_core.empty:
            tr_core = tr_core.copy()
            tr_core["sleeve"] = "core"

    eq_sat = tr_sat = None
    if sat_syms:
        sat_panel = _subset_panel(panel, sat_syms)
        eq_sat, tr_sat = _run(sat_panel, cfg, cfg.sat_weight, allowed_symbols_fn=sat_allowed)
        if tr_sat is not None and not tr_sat.empty:
            tr_sat = tr_sat.copy()
            tr_sat["sleeve"] = "sat"

    # Apply volatility targeting PER SLEEVE (recommended)
    eq_core = _apply_vol_target(eq_core, cfg.core_target_vol_annual, cfg)
    eq_sat = _apply_vol_target(eq_sat, cfg.sat_target_vol_annual, cfg)

    init_core = float(cfg.initial_capital) * float(cfg.core_weight)
    init_sat = float(cfg.initial_capital) * float(cfg.sat_weight)

    eq_total = _sum_equity(eq_core, eq_sat, init_core, init_sat)

    trades = []
    if tr_core is not None and not tr_core.empty:
        trades.append(tr_core)
    if tr_sat is not None and not tr_sat.empty:
        trades.append(tr_sat)
    tr_total = pd.concat(trades, ignore_index=True) if trades else pd.DataFrame()

    return eq_total, tr_total, eq_core, eq_sat
