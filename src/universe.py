from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import pandas as pd


MonthlySchedule = Dict[pd.Timestamp, List[str]]


def load_crypto_monthly_schedule(path: str) -> MonthlySchedule:
    """
    CSV attendu:
      month,symbols
    où:
      - month: YYYY-MM-DD (début de mois)
      - symbols: "BTC,ETH,SOL" (string)
    Retour:
      dict {Timestamp(month)->[symbols]}
    Robustesse:
      - si fichier absent / vide (0 octet) / illisible -> retourne {}
    """
    try:
        df = pd.read_csv(path)
    except FileNotFoundError:
        return {}
    except pd.errors.EmptyDataError:
        # Fichier 0 octet -> pas de schedule disponible
        return {}

    if df.empty:
        return {}

    # Tolérance: "date" ou "month"
    if "month" in df.columns:
        month_col = "month"
    elif "date" in df.columns:
        month_col = "date"
    else:
        raise ValueError(f"{path}: missing 'month' (or 'date') column")

    if "symbols" not in df.columns:
        raise ValueError(f"{path}: missing 'symbols' column")

    out: MonthlySchedule = {}
    for _, row in df.iterrows():
        m = pd.to_datetime(row[month_col], utc=False).normalize()
        raw = str(row["symbols"]) if pd.notna(row["symbols"]) else ""
        syms = [s.strip() for s in raw.split(",") if s.strip()]
        out[m] = syms

    return out


def symbols_for_date(dt: pd.Timestamp, sched: MonthlySchedule) -> List[str]:
    """
    Renvoie la liste de symboles active pour le mois de dt.
    Si pas trouvé -> [].
    """
    if not sched:
        return []

    d = pd.Timestamp(dt).normalize()
    # On prend le "month start"
    month = pd.Timestamp(year=d.year, month=d.month, day=1)
    return list(sched.get(month, []))
