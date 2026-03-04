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

# ---- Core ranking (recommended)
CORE_TOP_N = 3

# --- Vol scaling settings ---
USE_VOL_SCALING = True
VOL_WINDOW_DAYS = 30
CORE_TARGET_VOL_ANN = 0.10
SAT_TARGET_VOL_ANN = 0.20
SCALER_MIN = 0.25
SCALER_MAX = 2.0


def _split_symbols(symbols: List[str], crypto_symbols: tuple[str, ...]) -> Tuple[List[str], List[str]]:
    crypto = set(crypto_symbols)
    core, sat = [], []
    for s in symbols:
        (sat if s in crypto else core).append(s)
    return core, sat


def _subset_panel(panel: Dict[str, pd.DataFrame], symbols: List[str]) -> Dict[str, pd.DataFrame]:
    return {s: panel[s] for s in symbols if s in panel}


def _align_equity(eq_df: Optional[pd.DataFrame], idx: pd.DatetimeIndex, init_val: float) -> pd.Series:
    """
    Reindex equity to idx, forward-fill, and GUARANTEE first value is init_val (no NaN).
    """
    if eq_df is None or eq_df.empty:
        return pd.Series(index=idx, data=float(init_val))

    s = eq_df["equity"].astype(float).reindex(idx)

    # if first is NaN, set to init
    if pd.isna(s.iloc[0]):
        s.iloc[0] = float(init_val)

    s = s.ffill().fillna(float(init_val))
    return s


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


def _build_proxy_returns(
    panel: Dict[str, pd.DataFrame],
    symbols: List[str],
    allowed_symbols_fn: Optional[Callable[[pd.Timestamp], set]] = None,
) -> pd.Series:
    """
    Equal-weight proxy returns (close-to-close) for vol scaling.
    No lookahead; robust to missing bars.
    """
    if not symbols:
        return pd.Series(dtype=float)

    all_idx = None
    for s in symbols:
        if s not in panel:
            continue
        all_idx = panel[s].index if all_idx is None else all_idx.union(panel[s].index)
    if all_idx is None or len(all_idx) == 0:
        return pd.Series(dtype=float)

    cal = all_idx.sort_values()
    last_close: Dict[str, float] = {}
    out = []

    for dt in cal:
        allowed = allowed_symbols_fn(dt) if allowed_symbols_fn is not None else None
        vals = []

        for s in symbols:
            if s not in panel:
                continue
            if allowed is not None and s not in allowed:
                continue
            df = panel[s]
            if dt not in df.index:
                continue

            c = float(df.loc[dt, "close"])
            if s in last_close:
                prev = float(last_close[s])
                if prev > 0:
                    vals.append((c / prev) - 1.0)
            last_close[s] = c

        out.append((dt, float(np.mean(vals)) if len(vals) > 0 else np.nan))

    return pd.Series({dt: r for dt, r in out}).sort_index()


def _rolling_ann_vol(ret_s: pd.Series, window: int) -> pd.Series:
    return ret_s.astype(float).rolling(window=window, min_periods=window).std() * np.sqrt(252.0)


def _make_risk_per_trade_fn(base_rpt: float, proxy_ret: pd.Series, target_vol_ann: float) -> Callable[[pd.Timestamp], float]:
    vol = _rolling_ann_vol(proxy_ret, VOL_WINDOW_DAYS)

    def fn(dt: pd.Timestamp) -> float:
        if not USE_VOL_SCALING:
            return float(base_rpt)

        v = vol.get(dt, np.nan)
        if v is None or (not np.isfinite(v)) or v <= 0:
            return float(base_rpt)

        scaler = float(target_vol_ann) / float(v)
        scaler = max(SCALER_MIN, min(SCALER_MAX, scaler))
        return float(base_rpt) * scaler

    return fn


def _core_allowed_builder(panel: Dict[str, pd.DataFrame], core_syms: List[str], cfg: Config) -> Callable[[pd.Timestamp], set]:
    """
    Core top-N momentum selection. We must precompute signals here,
    because the backtester builds signals internally (so raw panel has no 'mom').
    """
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


def _run(
    panel: Dict[str, pd.DataFrame],
    cfg: Config,
    capital_weight: float,
    allowed_symbols_fn: Optional[Callable[[pd.Timestamp], set]] = None,
    risk_per_trade_fn: Optional[Callable[[pd.Timestamp], float]] = None,
):
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
        risk_per_trade_fn=risk_per_trade_fn,
    )


def run_backtest_core_satellite(panel: Dict[str, pd.DataFrame], cfg: Config, symbols: List[str]):
    core_syms, sat_syms = _split_symbols(symbols, cfg.crypto_symbols)

    # --- sat monthly schedule (optional) ---
    sched = None
    if os.path.exists(CRYPTO_UNIVERSE_PATH):
        sched = load_crypto_monthly_schedule(CRYPTO_UNIVERSE_PATH)

    def sat_allowed(dt: pd.Timestamp) -> set:
        if sched is None:
            return set(sat_syms)
        return set(symbols_for_date(dt, sched)).intersection(set(sat_syms))

    # --- core top-N momentum ---
    core_allowed = _core_allowed_builder(panel, core_syms, cfg)

    # --- vol scaling (ex-ante rolling) ---
    core_proxy_ret = _build_proxy_returns(panel, core_syms, allowed_symbols_fn=None)
    sat_proxy_ret = _build_proxy_returns(panel, sat_syms, allowed_symbols_fn=sat_allowed)

    core_rpt_fn = _make_risk_per_trade_fn(cfg.risk_per_trade, core_proxy_ret, CORE_TARGET_VOL_ANN)
    sat_rpt_fn = _make_risk_per_trade_fn(cfg.risk_per_trade, sat_proxy_ret, SAT_TARGET_VOL_ANN)

    # --- run sleeves with FIXED capital weights (cfg.core_weight/cfg.sat_weight) ---
    eq_core = tr_core = None
    if core_syms:
        core_panel = _subset_panel(panel, core_syms)
        eq_core, tr_core = _run(
            core_panel,
            cfg,
            cfg.core_weight,
            allowed_symbols_fn=core_allowed,
            risk_per_trade_fn=core_rpt_fn,
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
            allowed_symbols_fn=sat_allowed,
            risk_per_trade_fn=sat_rpt_fn,
        )
        if tr_sat is not None and not tr_sat.empty:
            tr_sat = tr_sat.copy()
            tr_sat["sleeve"] = "sat"

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
