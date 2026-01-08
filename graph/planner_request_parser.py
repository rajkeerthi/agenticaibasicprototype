"""
Natural-language planner request -> structured parameters.

We keep this very constrained and safe:
- The LLM only produces a small JSON object with agreed fields.
- If the LLM is unavailable/fails, we fall back to conservative defaults.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from prototype2_demand_supply.agents.llm import build_reasoning_client
from dateutil import parser as date_parser


@dataclass(frozen=True)
class PlannerRunParams:
    customer_id: str = "BLINKIT"
    location_id: str = "BANGALORE"
    as_of_date: str = "2026-01-01"
    scope: str = "single"  # "single" | "all_relevant"
    sku_id: str = "AUTO"  # when scope == single
    abc_class: str = "A"
    xyz_classes: List[str] = None  # type: ignore[assignment]
    upper_threshold: float = 0.30
    lower_threshold: float = -0.20
    needs_clarification: bool = False
    clarification_questions: List[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.xyz_classes is None:
            object.__setattr__(self, "xyz_classes", ["Y", "Z"])
        if self.clarification_questions is None:
            object.__setattr__(self, "clarification_questions", [])

    def to_state(self, *, user_query: str) -> Dict[str, Any]:
        return {
            "sku_id": self.sku_id,
            "customer_id": self.customer_id,
            "location_id": self.location_id,
            "as_of_date": self.as_of_date,
            "upper_threshold": self.upper_threshold,
            "lower_threshold": self.lower_threshold,
            "user_query": user_query,
            # multi-sku selectors
            "scope": self.scope,
            "abc_class": self.abc_class,
            "xyz_classes": list(self.xyz_classes),
        }


_SKU_ALIASES: Dict[str, str] = {
    "PONDS": "PONDS_SUPER_LIGHT_GEL_100G",
    "POND": "PONDS_SUPER_LIGHT_GEL_100G",
    "PONDS SUPER LIGHT GEL": "PONDS_SUPER_LIGHT_GEL_100G",
    "DOVE": "DOVE_HAIR_FALL_RESCUE_650ML",
    "DOVE HAIR FALL": "DOVE_HAIR_FALL_RESCUE_650ML",
}

def _mentioned_customer(text: str) -> bool:
    t = (text or "").upper()
    return ("BLINKIT" in t) or ("ZEPTO" in t)


def _mentioned_location(text: str) -> bool:
    t = (text or "").upper()
    return "BANGALORE" in t


def _mentioned_scope_all(text: str) -> bool:
    t = (text or "").upper()
    return ("ALL" in t) or ("A/Y" in t) or ("A-Y" in t) or ("A Y" in t)


def _infer_sku_from_text(text: str) -> str:
    t = (text or "").upper()
    for sku in ["PONDS_SUPER_LIGHT_GEL_100G", "DOVE_HAIR_FALL_RESCUE_650ML"]:
        if sku in t:
            return sku
    for k in sorted(_SKU_ALIASES.keys(), key=len, reverse=True):
        if k in t:
            return _SKU_ALIASES[k]
    return "AUTO"


def _infer_date_from_text(text: str, default_year: int = 2026) -> Optional[str]:
    if not text:
        return None
    m = re.search(r"(20\d{2}-\d{2}-\d{2})", text)
    if m:
        return m.group(1)
    try:
        dt = date_parser.parse(
            text,
            fuzzy=True,
            default=datetime(default_year, 1, 1),
            dayfirst=True,
        )
        # Guard: only accept if the user query actually contains a month name or a day number.
        # (Prevents accidentally returning the default date for generic queries.)
        if not re.search(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b", text.lower()) and not re.search(
            r"\b\d{1,2}\b|\b\d{1,2}(st|nd|rd|th)\b", text.lower()
        ):
            return None
        return dt.date().isoformat()
    except Exception:
        return None


def _clarification_questions(missing: List[str]) -> List[str]:
    qs: List[str] = []
    if "sku_id" in missing:
        qs.append("Which product/SKU should I run this for? (e.g., PONDS_SUPER_LIGHT_GEL_100G)")
    if "customer_id" in missing:
        qs.append("Which customer? (BLINKIT or ZEPTO)")
    if "location_id" in missing:
        qs.append("Which location/DC? (e.g., BANGALORE)")
    if "as_of_date" in missing:
        qs.append("Which date should I use? (e.g., 2026-01-02 or '2nd Jan 2026')")
    return qs


def _fallback_parse(user_query: str) -> PlannerRunParams:
    """
    Minimal regex-based fallback.
    """
    q = user_query.upper()
    sku_id = _infer_sku_from_text(user_query)
    inferred_date = _infer_date_from_text(user_query)
    scope_all = _mentioned_scope_all(user_query)
    scope = "all_relevant" if scope_all else "single"

    # Only treat customer/location/date as "known" if user explicitly provided them.
    customer_known = _mentioned_customer(user_query)
    location_known = _mentioned_location(user_query)
    date_known = inferred_date is not None

    customer = "BLINKIT" if "BLINKIT" in q else ("ZEPTO" if "ZEPTO" in q else "BLINKIT")
    location = "BANGALORE" if "BANGALORE" in q else "BANGALORE"
    as_of_date = inferred_date or "2026-01-01"

    missing: List[str] = []
    if not scope_all and (not sku_id or sku_id == "AUTO"):
        missing.append("sku_id")
    if not customer_known:
        missing.append("customer_id")
    if not location_known:
        missing.append("location_id")
    if not date_known:
        missing.append("as_of_date")

    needs_clarification = len(missing) > 0
    questions = _clarification_questions(missing) if needs_clarification else []

    return PlannerRunParams(
        customer_id=customer,
        location_id=location,
        as_of_date=as_of_date,
        scope=scope,
        sku_id=("AUTO" if scope_all else sku_id),
        needs_clarification=needs_clarification,
        clarification_questions=questions,
    )


async def parse_planner_request(user_query: str) -> PlannerRunParams:
    """
    Uses Gemini/OpenAI reasoning client (Gemini preferred) to parse the query into parameters.
    """
    inferred_sku = _infer_sku_from_text(user_query)
    inferred_date = _infer_date_from_text(user_query)
    client = build_reasoning_client(prefer="google")
    if client is None:
        return _fallback_parse(user_query)

    system = (
        "You are a demand planning request parser. "
        "Return ONLY valid JSON with the specified schema; no extra text."
    )
    schema_hint = {
        "customer_id": "BLINKIT|ZEPTO",
        "location_id": "BANGALORE",
        "as_of_date": "YYYY-MM-DD",
        "scope": "single|all_relevant",
        "sku_id": "SKU_ID or AUTO",
        "abc_class": "A|B|C",
        "xyz_classes": ["Y", "Z"],
        "upper_threshold": 0.30,
        "lower_threshold": -0.20,
        "needs_clarification": "true|false",
        "clarification_questions": ["question1", "question2"],
    }
    user = (
        f"User request:\n{user_query}\n\n"
        f"Deterministic hints (use if consistent): sku_hint={inferred_sku}, date_hint={inferred_date}\n\n"
        f"Schema:\n{schema_hint}\n\n"
        "Rules:\n"
        "- If the user asks for all relevant SKUs (e.g., 'all A/Y'), set scope=all_relevant and sku_id=AUTO.\n"
        "- If SKU is explicitly mentioned, set scope=single and sku_id to that.\n"
        "- Do NOT silently assume missing customer/location/date. If any is missing/unclear, set needs_clarification=true and ask follow-up questions.\n"
        "- If date is written like '2nd jan', convert to YYYY-MM-DD (default year 2026 unless user says otherwise).\n"
        "- Keep defaults only for thresholds/abc/xyz.\n"
        "Return ONLY JSON."
    )
    try:
        raw = await client.generate(system=system, user=user)
        data = json.loads(raw)

        customer_id = str(data.get("customer_id") or "").upper().strip()
        location_id = str(data.get("location_id") or "").upper().strip()
        as_of_date = str(data.get("as_of_date") or "").strip()
        scope = str(data.get("scope") or "single").strip()
        sku_id = str(data.get("sku_id") or "").upper().strip()

        if not sku_id:
            sku_id = inferred_sku
        if not as_of_date:
            as_of_date = inferred_date or ""

        # IMPORTANT: Do not silently accept LLM defaults for required fields.
        # Require explicit user mention (or confident inference) before we proceed.
        missing: List[str] = []
        scope_all = _mentioned_scope_all(user_query) or (scope == "all_relevant")

        if not scope_all and (not sku_id or sku_id == "AUTO"):
            missing.append("sku_id")
        if not _mentioned_customer(user_query):
            missing.append("customer_id")
        if not _mentioned_location(user_query):
            missing.append("location_id")
        # Only accept date if we could infer it or it is strict ISO.
        if not inferred_date and not re.match(r"^20\d{2}-\d{2}-\d{2}$", as_of_date or ""):
            missing.append("as_of_date")

        needs_clarification = bool(data.get("needs_clarification")) or (len(missing) > 0)
        questions = list(data.get("clarification_questions") or [])
        if needs_clarification and not questions:
            questions = _clarification_questions(missing)

        return PlannerRunParams(
            customer_id=customer_id or "BLINKIT",
            location_id=location_id or "BANGALORE",
            as_of_date=(inferred_date or as_of_date or "2026-01-01"),
            scope=("all_relevant" if scope_all else scope),
            sku_id=("AUTO" if scope_all else (sku_id or "AUTO")),
            abc_class=str(data.get("abc_class", "A")).upper(),
            xyz_classes=[str(x).upper() for x in (data.get("xyz_classes") or ["Y", "Z"])],
            upper_threshold=float(data.get("upper_threshold", 0.30)),
            lower_threshold=float(data.get("lower_threshold", -0.20)),
            needs_clarification=needs_clarification,
            clarification_questions=questions,
        )
    except Exception:
        return _fallback_parse(user_query)



