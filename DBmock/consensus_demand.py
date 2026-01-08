"""
Consensus demand store (mock DB) for ALL planned forecasts (not just approved).

This persists to a JSON file so Streamlit can show a table of:
- planned forecasts
- whether approval route was taken
- approval status (pending/approved/rejected/not_required)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


_STORE_PATH = Path(__file__).resolve().parent / "consensus_demand_store.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _key(row: Dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row.get("sku_id", "")),
        str(row.get("customer_id", "")),
        str(row.get("location_id", "")),
        str(row.get("as_of_date", "")),
    )


def load_consensus_demands() -> List[Dict[str, Any]]:
    if not _STORE_PATH.exists():
        return []
    try:
        rows = json.loads(_STORE_PATH.read_text())
        if not isinstance(rows, list):
            return []

        # Normalize: if percent stored as fraction, fix it.
        normalized: List[Dict[str, Any]] = []
        for r in rows:
            row = dict(r)
            tbp = row.get("total_boost_percent")
            tbf = row.get("total_boost_fraction")
            if tbf is None and isinstance(tbp, (int, float)) and -1.0 <= float(tbp) <= 1.0:
                frac = float(tbp)
                row["total_boost_fraction"] = frac
                row["total_boost_percent"] = round(frac * 100.0, 2)
            normalized.append(row)

        # Dedupe by key keeping latest updated_at
        latest: Dict[tuple[str, str, str, str], Dict[str, Any]] = {}
        for row in normalized:
            k = _key(row)
            existing = latest.get(k)
            if existing is None:
                latest[k] = row
                continue
            if str(row.get("updated_at", "")) >= str(existing.get("updated_at", "")):
                latest[k] = row

        return sorted(
            latest.values(),
            key=lambda x: (
                str(x.get("as_of_date", "")),
                str(x.get("location_id", "")),
                str(x.get("customer_id", "")),
                str(x.get("sku_id", "")),
            ),
        )
    except Exception:
        return []


def upsert_consensus_demand(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Upsert a record by (sku_id, customer_id, location_id, as_of_date).
    """
    rows = load_consensus_demands()
    row = dict(record)
    row.setdefault("created_at", _now_iso())
    row["updated_at"] = _now_iso()

    k = _key(row)
    replaced = False
    for i, existing in enumerate(rows):
        if _key(existing) == k:
            # preserve created_at if present
            row["created_at"] = existing.get("created_at", row["created_at"])
            rows[i] = row
            replaced = True
            break
    if not replaced:
        rows.append(row)

    _STORE_PATH.write_text(json.dumps(rows, indent=2))
    return row


def set_consensus_approval_status(
    *,
    sku_id: str,
    customer_id: str,
    location_id: str,
    as_of_date: str,
    approval_status: str,
) -> Optional[Dict[str, Any]]:
    """
    Update only the approval_status field for an existing record.
    """
    rows = load_consensus_demands()
    target_key = (sku_id, customer_id, location_id, as_of_date)
    updated_row: Optional[Dict[str, Any]] = None
    for i, row in enumerate(rows):
        if _key(row) == target_key:
            row = dict(row)
            row["approval_status"] = approval_status
            row["updated_at"] = _now_iso()
            rows[i] = row
            updated_row = row
            break
    if updated_row is None:
        return None
    _STORE_PATH.write_text(json.dumps(rows, indent=2))
    return updated_row


def clear_consensus_demands() -> None:
    if _STORE_PATH.exists():
        _STORE_PATH.unlink()


