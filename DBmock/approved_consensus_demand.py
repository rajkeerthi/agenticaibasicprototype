"""
Approved consensus demand store (mock DB).

We persist approvals to a JSON file so Streamlit can display a table and approvals
survive app reruns.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


_STORE_PATH = Path(__file__).resolve().parent / "approved_consensus_demand_store.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_approved_consensus_demands() -> List[Dict[str, Any]]:
    if not _STORE_PATH.exists():
        return []
    try:
        rows = json.loads(_STORE_PATH.read_text())
        # Normalize legacy rows where total_boost_percent accidentally stored as fraction (-0.3)
        # and dedupe by (sku_id, customer_id, location_id, as_of_date) keeping latest approved_at.
        normalized: List[Dict[str, Any]] = []
        for r in rows if isinstance(rows, list) else []:
            row = dict(r)
            tbp = row.get("total_boost_percent")
            tbf = row.get("total_boost_fraction")
            # If percent looks like a fraction and no explicit fraction is present, fix it.
            if tbf is None and isinstance(tbp, (int, float)) and -1.0 <= float(tbp) <= 1.0:
                frac = float(tbp)
                row["total_boost_fraction"] = frac
                row["total_boost_percent"] = round(frac * 100.0, 2)
            normalized.append(row)

        # Dedupe
        latest_by_key: Dict[tuple, Dict[str, Any]] = {}
        for row in normalized:
            key = (
                str(row.get("sku_id")),
                str(row.get("customer_id")),
                str(row.get("location_id")),
                str(row.get("as_of_date")),
            )
            existing = latest_by_key.get(key)
            if existing is None:
                latest_by_key[key] = row
                continue
            # Pick latest approved_at if possible; else keep the newer row.
            if str(row.get("approved_at", "")) >= str(existing.get("approved_at", "")):
                latest_by_key[key] = row

        # Stable-ish ordering for display
        return sorted(
            latest_by_key.values(),
            key=lambda x: (
                str(x.get("as_of_date", "")),
                str(x.get("location_id", "")),
                str(x.get("customer_id", "")),
                str(x.get("sku_id", "")),
            ),
        )
    except Exception:
        return []


def save_approved_consensus_demand(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Append an approved consensus demand record.

    Required keys (expected):
    - sku_id, customer_id, location_id, as_of_date
    - baseline_forecast, total_boost_percent, final_demand_forecast
    """
    rows = load_approved_consensus_demands()

    row = dict(record)
    row.setdefault("approved_at", _now_iso())

    # Upsert by (sku_id, customer_id, location_id, as_of_date)
    key = (
        str(row.get("sku_id")),
        str(row.get("customer_id")),
        str(row.get("location_id")),
        str(row.get("as_of_date")),
    )
    replaced = False
    for i, existing in enumerate(rows):
        ek = (
            str(existing.get("sku_id")),
            str(existing.get("customer_id")),
            str(existing.get("location_id")),
            str(existing.get("as_of_date")),
        )
        if ek == key:
            rows[i] = row
            replaced = True
            break
    if not replaced:
        rows.append(row)
    _STORE_PATH.write_text(json.dumps(rows, indent=2))
    return row


def clear_approved_consensus_demands() -> None:
    if _STORE_PATH.exists():
        _STORE_PATH.unlink()


