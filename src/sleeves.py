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
CORE_UNIVERSE_PATH = "data/universe/core_monthly.csv"

# Core: top-N trends (mensuel via momentum)
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


def _core_allowed_from_panel(panel: Dict[str, pd.DataFrame], core_syms: List[str], cfg: Config) -> Callable[[pd.Timestamp], Optional[set]]:
    """
    Variante "no-file": sélection top-N sur momentum calculé à la volée.
    IMPORTANT: si pas de mom dispo à dt -> retourne None (=> pas de filtre ce jour-là).
    """
    sig_panel: Dict[str, pd.DataFrame] = {}
    for s in core_syms:
        if s not in panel:
            continue
        sig_panel[s] = build_signals(panel[s], cfg.breakout_days, cfg.mom_days, cfg.atr_days)

    def allowed(dt: pd.Timestamp) -> Optional[set]:
        moms = []
        for s, df in sig_panel.items():
            if dt not in df.index:
                continue
            m = df.loc[dt].get("mom", np.nan)
            if pd.notna(m):
                moms.append((s, float(m)))

        if not moms:
            return None  # <-- clé: None = pas de filtre
        moms.sort(key=lambda x: x[1], reverse=True)
        return {s for s, _ in moms[:CORE_TOP_N]}

    return allowed


def _core_allowed_from_schedule(core_syms: List[str], core_sched) -> Callable[[pd.Timestamp], Optional[set]]:
    """
    Variante "file": utilise core_monthly.csv (month,symbols).
    Si schedule vide -> retourne None (pas de filtre).
    """
    core_set = set(core_syms)

    def allowed(dt: pd.Timestamp) -> Optional[set]:
        if not core_sched:
            return None
        pick = set(symbols_for_date(dt, core_sched)).intersection(core_set)
        # si schedule existe mais mois vide -> filtre vide = no trades core ce mois
        return pick

    return allowed


def _sat_allowed_from_schedule(sat_syms: List[str], crypto_sched) -> Callable[[pd.Timestamp], Optional[set]]:
    sat_set = set(sat_syms)

    def allowed(dt: pd.Timestamp) -> Optional[set]:
        if not crypto_sched:
            return None  # pas de schedule => pas de filtre
        pick = set(symbols_for_date(dt, crypto_sched)).intersection(sat_set)
        return pick

    return allowed


def _run(
    panel: Dict[str, pd.DataFrame],
    cfg: Config,
    capital_weight: float,
    allowed_symbols_fn: Optional[Callable[[pd.Timestamp], Optional[set]]] = None,
    vol_target_annual: Optional[float] = None,
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
        vol_target_annual=vol_target_annual,
        vol_window_days=cfg.vol_window_days,
        vol_scaler_min=cfg.vol_scaler_min,
        vol_scaler_max=cfg.vol_scaler_max,
    )


def run_backtest_core_satellite(panel: Dict[str, pd.DataFrame], cfg: Config, symbols: List[str]):
    core_syms, sat_syms = _split_symbols(symbols, cfg.crypto_symbols)

    # --- schedules (robustes: si fichier vide -> {})
    crypto_sched = {}
    if os.path.exists(CRYPTO_UNIVERSE_PATH):
        crypto_sched = load_crypto_monthly_schedule(CRYPTO_UNIVERSE_PATH)

    core_sched = {}
    if os.path.exists(CORE_UNIVERSE_PATH):
        core_sched = load_crypto_monthly_schedule(CORE_UNIVERSE_PATH)

    # --- allowed fns
    # Core: si schedule core existe (non vide) -> on l’utilise ; sinon fallback panel-momentum
    core_allowed: Optional[Callable[[pd.Timestamp], Optional[set]]] = None
    if core_syms:
        if core_sched:
            core_allowed = _core_allowed_from_schedule(core_syms, core_sched)
        else:
            core_allowed = _core_allowed_from_panel(panel, core_syms, cfg)

    sat_allowed: Optional[Callable[[pd.Timestamp], Optional[set]]] = None
    if sat_syms:
        if crypto_sched:
            sat_allowed = _sat_allowed_from_schedule(sat_syms, crypto_sched)
        else:
            sat_allowed = None  # pas de schedule => pas de filtre

    eq_core = tr_core = None
    if core_syms:
        core_panel = _subset_panel(panel, core_syms)
        eq_core, tr_core = _run(
            core_panel,
            cfg,
            cfg.core_weight,
            allowed_symbols_fn=core_allowed,
            vol_target_annual=cfg.core_target_vol_annual,
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
            vol_target_annual=cfg.sat_target_vol_annual,
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

    # Portfolio vol targeting (si activé via cfg.*)
    ret = eq_total["equity"].pct_change()
    vol = ret.rolling(30).std() * np.sqrt(252)

    target = float(getattr(cfg, "portfolio_target_vol_annual", 0.0) or 0.0)
    if target > 0:
        scaler = target / vol
        scaler = scaler.clip(float(cfg.vol_scaler_min), float(cfg.vol_scaler_max))
        ret_adj = ret * scaler.shift(1)
        eq_total["equity"] = (1 + ret_adj.fillna(0)).cumprod() * float(eq_total["equity"].iloc[0])

    return eq_total, tr_total, eq_core, eq_sat
