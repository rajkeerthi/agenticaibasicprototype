"""
Demand/Supply agent tools for the prototype2_demand_supply project.

This file intentionally keeps the "tools" as plain Python callables so they can be:
- wrapped as AutoGen v0.4+ tools (FunctionTool) later, or
- used in LangGraph v1.0 via your preferred tool/node integration.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

try:
    # Local package imports (preferred when running as a module)
    from ..DBmock.productcustomerlocation_drivers import get_product_drivers
    from ..DBmock.productlocation_xyzabc import (
        find_skus_by_class,
        get_product_master_data,
        list_product_master_data,
    )
    from ..DBmock.demanddrivervalues import (
        DEFAULT_AS_OF_DATE,
        get_demand_driver_values,
        get_demand_driver_notes,
        get_demand_driver_scenario,
    )
except Exception:  # pragma: no cover
    # Fallback for ad-hoc execution where package context isn't set up.
    from prototype2_demand_supply.DBmock.productcustomerlocation_drivers import (  # type: ignore
        get_product_drivers,
    )
    from prototype2_demand_supply.DBmock.productlocation_xyzabc import (  # type: ignore
        find_skus_by_class,
        get_product_master_data,
        list_product_master_data,
    )
    from prototype2_demand_supply.DBmock.demanddrivervalues import (  # type: ignore
        DEFAULT_AS_OF_DATE,
        get_demand_driver_values,
        get_demand_driver_notes,
        get_demand_driver_scenario,
    )


def _norm_upper(value: str) -> str:
    return (value or "").strip().upper()


def _filter_drivers_by_category(drivers: Sequence[Dict[str, Any]], category: str) -> List[Dict[str, Any]]:
    return [d for d in drivers if d.get("category") == category]


def _safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_bool(value: Any) -> Optional[bool]:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        v = value.strip().lower()
        if v in {"true", "1", "yes", "y"}:
            return True
        if v in {"false", "0", "no", "n"}:
            return False
    return None


def _step_boost_from_intensity(intensity: float) -> float:
    """
    Step boost calculator (as requested) using if/elif.

    intensity is a rough "signal strength" score where:
    - <= 0 means no boost
    - higher means stronger boost
    Returns a boost fraction: 0.10 => +10%, 0.50 => +50%, 0.60 => 50%+
    """
    if intensity <= 0.0:
        return 0.0
    elif intensity <= 0.20:
        return 0.10
    elif intensity <= 0.40:
        return 0.20
    elif intensity <= 0.60:
        return 0.30
    elif intensity <= 0.80:
        return 0.40
    elif intensity <= 1.00:
        return 0.50
    else:
        return 0.60  # 50%+


def _step_boost_from_signed_score(score: float) -> float:
    """
    Step boost calculator supporting negative scenarios (min down to -30%).

    score is a rough "net signal" where:
    - negative => headwind
    - positive => tailwind
    Returns a boost fraction: -0.10 => -10%, -0.30 => -30%, 0.60 => 50%+
    """
    if score <= -1.00:
        return -0.30
    elif score <= -0.70:
        return -0.20
    elif score <= -0.35:
        return -0.10
    elif score < 0.35:
        return 0.0
    elif score < 0.60:
        return 0.10
    elif score < 0.80:
        return 0.20
    elif score < 1.00:
        return 0.30
    elif score < 1.20:
        return 0.40
    elif score < 1.40:
        return 0.50
    else:
        return 0.60  # 50%+


def _get_values(
    sku_id: str,
    customer_id: str,
    location_id: str,
    as_of_date: str,
) -> Dict[str, Any]:
    return get_demand_driver_values(
        sku_id=_norm_upper(sku_id),
        customer_id=_norm_upper(customer_id),
        location_id=_norm_upper(location_id),
        as_of_date=as_of_date,
    )


def _attach_values(
    drivers: Sequence[Dict[str, Any]],
    sku_id: str,
    customer_id: str,
    location_id: str,
    as_of_date: str,
    include_values: bool,
) -> List[Dict[str, Any]]:
    if not include_values:
        return [dict(d) for d in drivers]

    values = get_demand_driver_values(
        sku_id=_norm_upper(sku_id),
        customer_id=_norm_upper(customer_id),
        location_id=_norm_upper(location_id),
        as_of_date=as_of_date,
    )
    enriched: List[Dict[str, Any]] = []
    for d in drivers:
        dd = dict(d)
        dd["value"] = values.get(dd.get("driver_name"))
        dd["as_of_date"] = as_of_date
        dd["customer_id"] = _norm_upper(customer_id)
        dd["location_id"] = _norm_upper(location_id)
        enriched.append(dd)
    return enriched


# ======================================================================================
# 1) Consensus Demand Forecast Drivers (Statistical Baseline)
# ======================================================================================
def fetch_consensus_demand_driver(
    sku_id: str,
    customer_id: str = "BLINKIT",
    location_id: str = "BANGALORE",
    as_of_date: str = DEFAULT_AS_OF_DATE,
    include_values: bool = True,
) -> List[Dict[str, Any]]:
    """
    Tool 1: Fetch consensus demand driver(s) for a SKU.
    """
    drivers = get_product_drivers(_norm_upper(sku_id))
    subset = _filter_drivers_by_category(drivers, "Statistical Demand Forecast")
    return _attach_values(subset, sku_id, customer_id, location_id, as_of_date, include_values)


# ======================================================================================
# 2) Real Time Social Signals
# ======================================================================================
def fetch_social_signal_drivers(
    sku_id: str,
    customer_id: str = "BLINKIT",
    location_id: str = "BANGALORE",
    as_of_date: str = DEFAULT_AS_OF_DATE,
    include_values: bool = True,
) -> List[Dict[str, Any]]:
    """
    Tool 2: Fetch social signal drivers for a SKU.
    """
    drivers = get_product_drivers(_norm_upper(sku_id))
    subset = _filter_drivers_by_category(drivers, "Real Time Social Signals")
    return _attach_values(subset, sku_id, customer_id, location_id, as_of_date, include_values)


# ======================================================================================
# 3) Real Time Marketing Spend and Engagement Signals
# ======================================================================================
def fetch_marketing_spend_drivers(
    sku_id: str,
    customer_id: str = "BLINKIT",
    location_id: str = "BANGALORE",
    as_of_date: str = DEFAULT_AS_OF_DATE,
    include_values: bool = True,
) -> List[Dict[str, Any]]:
    """
    Tool 3: Fetch marketing spend/engagement drivers for a SKU.
    """
    drivers = get_product_drivers(_norm_upper(sku_id))
    subset = _filter_drivers_by_category(drivers, "Real Time Marketing Spend and Engagement Signals")
    return _attach_values(subset, sku_id, customer_id, location_id, as_of_date, include_values)


# ======================================================================================
# 4) Real Time Trade Promo Signals
# ======================================================================================
def fetch_trade_promo_drivers(
    sku_id: str,
    customer_id: str = "BLINKIT",
    location_id: str = "BANGALORE",
    as_of_date: str = DEFAULT_AS_OF_DATE,
    include_values: bool = True,
) -> List[Dict[str, Any]]:
    """
    Tool 4: Fetch trade promo drivers for a SKU.
    """
    drivers = get_product_drivers(_norm_upper(sku_id))
    subset = _filter_drivers_by_category(drivers, "Real Time Trade Promo Signals")
    return _attach_values(subset, sku_id, customer_id, location_id, as_of_date, include_values)


# ======================================================================================
# 5) Real Time Digital Shelf Analytics Signals
# ======================================================================================
def fetch_digital_shelf_drivers(
    sku_id: str,
    customer_id: str = "BLINKIT",
    location_id: str = "BANGALORE",
    as_of_date: str = DEFAULT_AS_OF_DATE,
    include_values: bool = True,
) -> List[Dict[str, Any]]:
    """
    Tool 5: Fetch digital shelf drivers for a SKU.
    """
    drivers = get_product_drivers(_norm_upper(sku_id))
    subset = _filter_drivers_by_category(drivers, "Real Time Digital Shelf Analytics Signals")
    return _attach_values(subset, sku_id, customer_id, location_id, as_of_date, include_values)


# ======================================================================================
# 6) Real Time Weather/Environment Signals
# ======================================================================================
def fetch_weather_environment_drivers(
    sku_id: str,
    customer_id: str = "BLINKIT",
    location_id: str = "BANGALORE",
    as_of_date: str = DEFAULT_AS_OF_DATE,
    include_values: bool = True,
) -> List[Dict[str, Any]]:
    """
    Tool 6: Fetch weather/environment drivers for a SKU.
    """
    drivers = get_product_drivers(_norm_upper(sku_id))
    subset = _filter_drivers_by_category(drivers, "Real Time Weather/Environment Signals")
    return _attach_values(subset, sku_id, customer_id, location_id, as_of_date, include_values)


# ======================================================================================
# 7) Real Time Competitor Data
# ======================================================================================
def fetch_competitor_data_drivers(
    sku_id: str,
    customer_id: str = "BLINKIT",
    location_id: str = "BANGALORE",
    as_of_date: str = DEFAULT_AS_OF_DATE,
    include_values: bool = True,
) -> List[Dict[str, Any]]:
    """
    Tool 7: Fetch competitor data drivers for a SKU.
    """
    drivers = get_product_drivers(_norm_upper(sku_id))
    subset = _filter_drivers_by_category(drivers, "Real Time Competitor Data")
    return _attach_values(subset, sku_id, customer_id, location_id, as_of_date, include_values)


# ======================================================================================
# 8) Real Time POS Data & Open Orders
# ======================================================================================
def fetch_pos_data_drivers(
    sku_id: str,
    customer_id: str = "BLINKIT",
    location_id: str = "BANGALORE",
    as_of_date: str = DEFAULT_AS_OF_DATE,
    include_values: bool = True,
) -> List[Dict[str, Any]]:
    """
    Tool 8: Fetch POS/open-orders drivers for a SKU.
    """
    drivers = get_product_drivers(_norm_upper(sku_id))
    subset = _filter_drivers_by_category(drivers, "Real Time POS Data & Open Orders")
    return _attach_values(subset, sku_id, customer_id, location_id, as_of_date, include_values)


# ======================================================================================
# 9) ABC/XYZ Class fetcher
# ======================================================================================
def fetch_abc_xyz_classification(
    sku_id: str,
    location_id: str = "BANGALORE",
) -> Optional[Dict[str, Any]]:
    """
    Tool 9: Fetch abc_class and xyz_class (and related master data) for a SKU at a location.
    """
    return get_product_master_data(_norm_upper(sku_id), _norm_upper(location_id))


def fetch_relevant_products_by_abc_xyz(
    location_id: str = "BANGALORE",
    abc_class: str = "A",
    xyz_classes: Sequence[str] = ("Y", "Z"),
) -> List[Dict[str, Any]]:
    """
    Micro-step 1 (Actor): fetch relevant products for planning.

    Returns a list of product master-data dicts filtered by ABC/XYZ classes.
    """
    location_id_u = _norm_upper(location_id)
    skus = find_skus_by_class(location_id_u, abc_class=abc_class, xyz_classes=xyz_classes)
    # Return full master-data rows when possible
    master_rows = {r["sku_id"]: r for r in list_product_master_data(location_id_u)}
    return [master_rows.get(sku, {"sku_id": sku, "location_id": location_id_u}) for sku in skus]


# ======================================================================================
# Demand boost calculators (step-based, if/elif)
# Note: POS drivers are intentionally excluded (not causal factor per request)
# ======================================================================================


def calculate_social_signal_demand_boost(
    sku_id: str,
    customer_id: str = "BLINKIT",
    location_id: str = "BANGALORE",
    as_of_date: str = DEFAULT_AS_OF_DATE,
) -> Dict[str, Any]:
    """
    Uses: Ingredient Trend Velocity, Brand Sentiment Score, Viral Hashtag Volume, Influencer Mention Count
    Returns a dict with boost_percent and supporting details.
    """
    values = _get_values(sku_id, customer_id, location_id, as_of_date)
    trend = _safe_float(values.get("Ingredient Trend Velocity"))  # typically 0..1 (WoW velocity)
    sentiment = _safe_float(values.get("Brand Sentiment Score"))  # 0..100
    hashtags = _safe_float(values.get("Viral Hashtag Volume"))  # mentions/day
    influencer = _safe_float(values.get("Influencer Mention Count"))  # mentions/day

    # Build a simple net score: tailwinds - headwinds
    tailwinds = 0.0
    headwinds = 0.0
    if trend is not None:
        if trend >= 0.30:
            tailwinds += 0.40
        elif trend >= 0.15:
            tailwinds += 0.25
        elif trend >= 0.05:
            tailwinds += 0.10
        elif trend <= -0.15:
            headwinds += 0.30
        elif trend <= -0.05:
            headwinds += 0.15
    if sentiment is not None:
        if sentiment >= 80:
            tailwinds += 0.30
        elif sentiment >= 70:
            tailwinds += 0.20
        elif sentiment >= 60:
            tailwinds += 0.10
        elif sentiment <= 40:
            headwinds += 0.35
        elif sentiment <= 50:
            headwinds += 0.20
    if hashtags is not None:
        if hashtags >= 2000:
            tailwinds += 0.25
        elif hashtags >= 1200:
            tailwinds += 0.15
        elif hashtags >= 600:
            tailwinds += 0.05
        elif hashtags < 200:
            headwinds += 0.10
    if influencer is not None:
        if influencer >= 30:
            tailwinds += 0.25
        elif influencer >= 15:
            tailwinds += 0.15
        elif influencer >= 5:
            tailwinds += 0.05
        elif influencer < 2:
            headwinds += 0.10

    net_score = tailwinds - headwinds
    boost = _step_boost_from_signed_score(net_score)
    return {
        "category": "Real Time Social Signals",
        "boost_percent": boost,
        "net_score": round(float(net_score), 4),
        "as_of_date": as_of_date,
        "inputs": {
            "Ingredient Trend Velocity": trend,
            "Brand Sentiment Score": sentiment,
            "Viral Hashtag Volume": hashtags,
            "Influencer Mention Count": influencer,
        },
    }


def calculate_marketing_spend_demand_boost(
    sku_id: str,
    customer_id: str = "BLINKIT",
    location_id: str = "BANGALORE",
    as_of_date: str = DEFAULT_AS_OF_DATE,
) -> Dict[str, Any]:
    """
    Uses: Performance Marketing Spend, CTR, Video Completion Rate, Retargeting Pool Size
    """
    values = _get_values(sku_id, customer_id, location_id, as_of_date)
    spend = _safe_float(values.get("Performance Marketing Spend"))  # INR/day
    ctr = _safe_float(values.get("Campaign Click-Through-Rate (CTR)"))  # 0..1
    vcr = _safe_float(values.get("Video Completion Rate"))  # 0..1
    retarget = _safe_float(values.get("Retargeting Pool Size"))

    tailwinds = 0.0
    headwinds = 0.0
    if spend is not None:
        if spend >= 200000:
            tailwinds += 0.35
        elif spend >= 120000:
            tailwinds += 0.25
        elif spend >= 60000:
            tailwinds += 0.15
        elif spend < 15000:
            headwinds += 0.35
        elif spend < 30000:
            headwinds += 0.20
    if ctr is not None:
        if ctr >= 0.025:
            tailwinds += 0.25
        elif ctr >= 0.018:
            tailwinds += 0.18
        elif ctr >= 0.012:
            tailwinds += 0.10
        elif ctr < 0.006:
            headwinds += 0.30
        elif ctr < 0.010:
            headwinds += 0.15
    if vcr is not None:
        if vcr >= 0.40:
            tailwinds += 0.20
        elif vcr >= 0.30:
            tailwinds += 0.15
        elif vcr >= 0.20:
            tailwinds += 0.08
        elif vcr < 0.10:
            headwinds += 0.20
    if retarget is not None:
        if retarget >= 20000:
            tailwinds += 0.20
        elif retarget >= 12000:
            tailwinds += 0.12
        elif retarget >= 6000:
            tailwinds += 0.06
        elif retarget < 1500:
            headwinds += 0.15

    net_score = tailwinds - headwinds
    boost = _step_boost_from_signed_score(net_score)
    return {
        "category": "Real Time Marketing Spend and Engagement Signals",
        "boost_percent": boost,
        "net_score": round(float(net_score), 4),
        "as_of_date": as_of_date,
        "inputs": {
            "Performance Marketing Spend": spend,
            "Campaign Click-Through-Rate (CTR)": ctr,
            "Video Completion Rate": vcr,
            "Retargeting Pool Size": retarget,
        },
    }


def calculate_trade_promo_demand_boost(
    sku_id: str,
    customer_id: str = "BLINKIT",
    location_id: str = "BANGALORE",
    as_of_date: str = DEFAULT_AS_OF_DATE,
) -> Dict[str, Any]:
    """
    Uses: Discount Depth, Bundle Status, Flash Sale Status, Cart-Level Offer Conversion
    """
    values = _get_values(sku_id, customer_id, location_id, as_of_date)
    discount = _safe_float(values.get("On-Platform Discount Depth"))  # 0..1
    bundle = _safe_bool(values.get("Bundle Offer Active Status"))
    flash = _safe_bool(values.get("Flash Sale Participation"))
    cart_conv = _safe_float(values.get("Cart-Level Offer Conversion"))  # 0..1

    tailwinds = 0.0
    headwinds = 0.0
    if discount is not None:
        if discount >= 0.30:
            tailwinds += 0.45
        elif discount >= 0.20:
            tailwinds += 0.35
        elif discount >= 0.10:
            tailwinds += 0.20
        elif discount >= 0.05:
            tailwinds += 0.10
        elif discount < 0.01:
            headwinds += 0.10
    if bundle is True:
        tailwinds += 0.15
    if flash is True:
        tailwinds += 0.25
    if cart_conv is not None:
        if cart_conv >= 0.10:
            tailwinds += 0.20
        elif cart_conv >= 0.06:
            tailwinds += 0.12
        elif cart_conv >= 0.03:
            tailwinds += 0.06
        elif cart_conv < 0.01:
            headwinds += 0.15
        elif cart_conv < 0.02:
            headwinds += 0.08

    # Small extra headwind if no promo levers are active at all (to enable - scenarios)
    if (bundle is False or bundle is None) and (flash is False or flash is None) and (discount is not None and discount < 0.02):
        headwinds += 0.10

    net_score = tailwinds - headwinds
    boost = _step_boost_from_signed_score(net_score)
    return {
        "category": "Real Time Trade Promo Signals",
        "boost_percent": boost,
        "net_score": round(float(net_score), 4),
        "as_of_date": as_of_date,
        "inputs": {
            "On-Platform Discount Depth": discount,
            "Bundle Offer Active Status": bundle,
            "Flash Sale Participation": flash,
            "Cart-Level Offer Conversion": cart_conv,
        },
    }


def calculate_digital_shelf_demand_boost(
    sku_id: str,
    customer_id: str = "BLINKIT",
    location_id: str = "BANGALORE",
    as_of_date: str = DEFAULT_AS_OF_DATE,
) -> Dict[str, Any]:
    """
    Uses: Keyword Rank, PDP Views, Buy Box Win Rate, Rating & Review Velocity
    """
    values = _get_values(sku_id, customer_id, location_id, as_of_date)
    rank = _safe_float(values.get("Share of Search (Keyword Rank)"))  # rank (lower is better)
    pdp = _safe_float(values.get("Product Detail Page (PDP) Views"))
    buybox = _safe_float(values.get("Buy Box Win Rate"))  # 0..1
    reviews = _safe_float(values.get("Rating & Review Velocity"))

    tailwinds = 0.0
    headwinds = 0.0
    if rank is not None:
        if rank <= 3:
            tailwinds += 0.30
        elif rank <= 6:
            tailwinds += 0.20
        elif rank <= 10:
            tailwinds += 0.10
        elif rank >= 25:
            headwinds += 0.35
        elif rank >= 15:
            headwinds += 0.20
    if pdp is not None:
        if pdp >= 60000:
            tailwinds += 0.25
        elif pdp >= 40000:
            tailwinds += 0.18
        elif pdp >= 20000:
            tailwinds += 0.10
        elif pdp < 8000:
            headwinds += 0.25
        elif pdp < 15000:
            headwinds += 0.15
    if buybox is not None:
        if buybox >= 0.95:
            tailwinds += 0.20
        elif buybox >= 0.90:
            tailwinds += 0.12
        elif buybox >= 0.80:
            tailwinds += 0.06
        elif buybox < 0.70:
            headwinds += 0.35
        elif buybox < 0.85:
            headwinds += 0.15
    if reviews is not None:
        if reviews >= 40:
            tailwinds += 0.20
        elif reviews >= 25:
            tailwinds += 0.12
        elif reviews >= 10:
            tailwinds += 0.06
        elif reviews < 3:
            headwinds += 0.20

    net_score = tailwinds - headwinds
    boost = _step_boost_from_signed_score(net_score)
    return {
        "category": "Real Time Digital Shelf Analytics Signals",
        "boost_percent": boost,
        "net_score": round(float(net_score), 4),
        "as_of_date": as_of_date,
        "inputs": {
            "Share of Search (Keyword Rank)": rank,
            "Product Detail Page (PDP) Views": pdp,
            "Buy Box Win Rate": buybox,
            "Rating & Review Velocity": reviews,
        },
    }


def calculate_weather_environment_demand_boost(
    sku_id: str,
    customer_id: str = "BLINKIT",
    location_id: str = "BANGALORE",
    as_of_date: str = DEFAULT_AS_OF_DATE,
) -> Dict[str, Any]:
    """
    Uses: Max Temperature Forecast, Humidity Index, UV Index, AQI
    """
    values = _get_values(sku_id, customer_id, location_id, as_of_date)
    temp = _safe_float(values.get("Max Temperature Forecast"))  # °C
    humidity = _safe_float(values.get("Humidity Index"))  # 0..1
    uv = _safe_float(values.get("UV Index"))
    aqi = _safe_float(values.get("Air Quality Index (AQI)"))

    tailwinds = 0.0
    headwinds = 0.0
    if temp is not None:
        if temp >= 35:
            tailwinds += 0.35
        elif temp >= 30:
            tailwinds += 0.25
        elif temp >= 26:
            tailwinds += 0.15
        elif temp <= 15:
            headwinds += 0.35
        elif temp <= 20:
            headwinds += 0.20
    if humidity is not None:
        if humidity >= 0.80:
            tailwinds += 0.20
        elif humidity >= 0.65:
            tailwinds += 0.12
        elif humidity >= 0.50:
            tailwinds += 0.06
        elif humidity <= 0.25:
            headwinds += 0.15
    if uv is not None:
        if uv >= 8:
            tailwinds += 0.25
        elif uv >= 6:
            tailwinds += 0.15
        elif uv >= 4:
            tailwinds += 0.08
        elif uv <= 1.5:
            headwinds += 0.15
    if aqi is not None:
        if aqi >= 200:
            tailwinds += 0.20
        elif aqi >= 150:
            tailwinds += 0.12
        elif aqi >= 100:
            tailwinds += 0.06
        elif aqi < 40:
            headwinds += 0.10

    net_score = tailwinds - headwinds
    boost = _step_boost_from_signed_score(net_score)
    return {
        "category": "Real Time Weather/Environment Signals",
        "boost_percent": boost,
        "net_score": round(float(net_score), 4),
        "as_of_date": as_of_date,
        "inputs": {
            "Max Temperature Forecast": temp,
            "Humidity Index": humidity,
            "UV Index": uv,
            "Air Quality Index (AQI)": aqi,
        },
    }


def _step_boost_from_competitor_net(net_score: float) -> float:
    """
    Competitor can be favorable or unfavorable; map net_score into step boosts.
    Positive => boost, Negative => reduction.
    """
    if net_score <= -0.80:
        return -0.30
    elif net_score <= -0.50:
        return -0.20
    elif net_score <= -0.20:
        return -0.10
    elif net_score < 0.20:
        return 0.0
    elif net_score < 0.50:
        return 0.10
    elif net_score < 0.80:
        return 0.20
    else:
        return 0.30


def calculate_competitor_data_demand_boost(
    sku_id: str,
    customer_id: str = "BLINKIT",
    location_id: str = "BANGALORE",
    as_of_date: str = DEFAULT_AS_OF_DATE,
) -> Dict[str, Any]:
    """
    Uses: Competitor Price Gap, Competitor OOS, Competitor Promo Intensity, Competitor New Launch Signal

    Note: This category can produce negative boost (i.e., headwinds).
    """
    values = _get_values(sku_id, customer_id, location_id, as_of_date)
    price_gap = _safe_float(values.get("Competitor Price Gap"))  # INR; negative => we cheaper (tailwind)
    oos = _safe_bool(values.get("Competitor Out-of-Stock Status"))
    promo = _safe_float(values.get("Competitor Promo Intensity"))  # 0..1; higher => headwind
    new_launch = _safe_bool(values.get("Competitor New Launch Signal"))

    # net_score: positive tailwinds, negative headwinds
    net_score = 0.0
    if price_gap is not None:
        # We are cheaper -> tailwind, we are more expensive -> headwind
        if price_gap <= -20:
            net_score += 0.40
        elif price_gap <= -5:
            net_score += 0.20
        elif price_gap >= 30:
            net_score -= 0.40
        elif price_gap >= 10:
            net_score -= 0.20
    if oos is True:
        net_score += 0.50
    if promo is not None:
        if promo >= 0.30:
            net_score -= 0.45
        elif promo >= 0.20:
            net_score -= 0.30
        elif promo >= 0.10:
            net_score -= 0.15
    if new_launch is True:
        net_score -= 0.25

    boost = _step_boost_from_competitor_net(net_score)
    return {
        "category": "Real Time Competitor Data",
        "boost_percent": boost,
        "net_score": round(float(net_score), 4),
        "as_of_date": as_of_date,
        "inputs": {
            "Competitor Price Gap": price_gap,
            "Competitor Out-of-Stock Status": oos,
            "Competitor Promo Intensity": promo,
            "Competitor New Launch Signal": new_launch,
        },
    }


def calculate_final_demand_boost(
    sku_id: str,
    customer_id: str = "BLINKIT",
    location_id: str = "BANGALORE",
    as_of_date: str = DEFAULT_AS_OF_DATE,
    cap_min: float = -0.30,
    cap_max: float = 0.60,  # 50%+
) -> Dict[str, Any]:
    """
    Aggregates per-category boosts (excluding POS drivers).
    Returns total_boost_percent plus a breakdown.
    """
    breakdown = {
        "social": calculate_social_signal_demand_boost(sku_id, customer_id, location_id, as_of_date),
        "marketing": calculate_marketing_spend_demand_boost(sku_id, customer_id, location_id, as_of_date),
        "trade_promo": calculate_trade_promo_demand_boost(sku_id, customer_id, location_id, as_of_date),
        "digital_shelf": calculate_digital_shelf_demand_boost(sku_id, customer_id, location_id, as_of_date),
        "weather": calculate_weather_environment_demand_boost(sku_id, customer_id, location_id, as_of_date),
        "competitor": calculate_competitor_data_demand_boost(sku_id, customer_id, location_id, as_of_date),
    }
    raw_total = float(sum(v["boost_percent"] for v in breakdown.values()))

    if raw_total < cap_min:
        total = cap_min
    elif raw_total > cap_max:
        total = cap_max
    else:
        total = raw_total

    return {
        "sku_id": _norm_upper(sku_id),
        "customer_id": _norm_upper(customer_id),
        "location_id": _norm_upper(location_id),
        "as_of_date": as_of_date,
        "raw_total_boost_percent": round(raw_total, 4),
        "total_boost_percent": round(total, 4),
        "caps": {"min": cap_min, "max": cap_max},
        "breakdown": breakdown,
    }


def calculate_final_demand_forecast(
    sku_id: str,
    customer_id: str = "BLINKIT",
    location_id: str = "BANGALORE",
    as_of_date: str = DEFAULT_AS_OF_DATE,
) -> Dict[str, Any]:
    """
    Converts baseline forecast + total boost into a final demand forecast number.
    """
    values = _get_values(sku_id, customer_id, location_id, as_of_date)
    baseline = values.get("Statistical Baseline Forecast")
    baseline_f = _safe_float(baseline) or 0.0

    boost = calculate_final_demand_boost(sku_id, customer_id, location_id, as_of_date)
    total_boost = float(boost["total_boost_percent"])

    final_forecast = baseline_f * (1.0 + total_boost)
    return {
        "sku_id": _norm_upper(sku_id),
        "customer_id": _norm_upper(customer_id),
        "location_id": _norm_upper(location_id),
        "as_of_date": as_of_date,
        "baseline_forecast": baseline_f,
        "total_boost_percent": total_boost,
        "final_demand_forecast": round(final_forecast, 2),
        "boost_breakdown": boost,
    }


def build_boost_reasoning_context(
    sku_id: str,
    customer_id: str = "BLINKIT",
    location_id: str = "BANGALORE",
    as_of_date: str = DEFAULT_AS_OF_DATE,
    final_boost: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Returns a compact context payload (values + notes + breakdown) that an LLM can turn into
    an explanation for the demand planner.
    """
    values = _get_values(sku_id, customer_id, location_id, as_of_date)
    notes = get_demand_driver_notes(sku_id, customer_id, location_id, as_of_date)
    scenario = get_demand_driver_scenario(sku_id, customer_id, location_id, as_of_date)
    if final_boost is None:
        final_boost = calculate_final_demand_boost(sku_id, customer_id, location_id, as_of_date)

    return {
        "sku_id": _norm_upper(sku_id),
        "customer_id": _norm_upper(customer_id),
        "location_id": _norm_upper(location_id),
        "as_of_date": as_of_date,
        "scenario": scenario,
        "driver_values": values,
        "driver_notes": notes,
        "boost": final_boost,
    }


# ======================================================================================
# Critic tool: validate boost thresholds + tool execution health
# ======================================================================================


def critic_review_consensus_demand_boost(
    sku_id: str,
    customer_id: str = "BLINKIT",
    location_id: str = "BANGALORE",
    as_of_date: str = DEFAULT_AS_OF_DATE,
    upper_threshold: float = 0.30,  # +30%
    lower_threshold: float = -0.20,  # -20%
) -> Dict[str, Any]:
    """
    Critic tool (basic version):
    - Computes total demand boost using `calculate_final_demand_boost`
    - Checks if total boost is outside thresholds
    - Checks "tool execution status" by validating presence of key driver values

    Output is structured so the future Critic agent can:
    - ask Actor to rerun specific tools if driver values are missing
    - otherwise route to human approval if boost is outside thresholds
    """

    # 1) Get computed boost
    final_boost = calculate_final_demand_boost(
        sku_id=sku_id,
        customer_id=customer_id,
        location_id=location_id,
        as_of_date=as_of_date,
    )
    total = float(final_boost["total_boost_percent"])

    outside_thresholds = total > upper_threshold or total < lower_threshold

    # 2) Tool execution "health" = do we have the expected driver values?
    required_by_tool: Dict[str, List[str]] = {
        "fetch_consensus_demand_driver": ["Statistical Baseline Forecast"],
        "fetch_social_signal_drivers": [
            "Ingredient Trend Velocity",
            "Brand Sentiment Score",
            "Viral Hashtag Volume",
            "Influencer Mention Count",
        ],
        "fetch_marketing_spend_drivers": [
            "Performance Marketing Spend",
            "Campaign Click-Through-Rate (CTR)",
            "Video Completion Rate",
            "Retargeting Pool Size",
        ],
        "fetch_trade_promo_drivers": [
            "On-Platform Discount Depth",
            "Bundle Offer Active Status",
            "Flash Sale Participation",
            "Cart-Level Offer Conversion",
        ],
        "fetch_digital_shelf_drivers": [
            "Share of Search (Keyword Rank)",
            "Product Detail Page (PDP) Views",
            "Buy Box Win Rate",
            "Rating & Review Velocity",
        ],
        "fetch_weather_environment_drivers": [
            "Max Temperature Forecast",
            "Humidity Index",
            "UV Index",
            "Air Quality Index (AQI)",
        ],
        "fetch_competitor_data_drivers": [
            "Competitor Price Gap",
            "Competitor Out-of-Stock Status",
            "Competitor Promo Intensity",
            "Competitor New Launch Signal",
        ],
        # POS intentionally excluded (not a causal demand factor per your design)
    }

    values = _get_values(sku_id, customer_id, location_id, as_of_date)

    tool_health: Dict[str, Any] = {}
    rerun_recommendations: List[str] = []
    issues: List[Dict[str, Any]] = []

    if not values:
        # No data for this (sku, customer, location, date) combination.
        issues.append(
            {
                "type": "missing_context_data",
                "message": "No demand driver values found for the given context/date.",
                "context": {
                    "sku_id": _norm_upper(sku_id),
                    "customer_id": _norm_upper(customer_id),
                    "location_id": _norm_upper(location_id),
                    "as_of_date": as_of_date,
                },
            }
        )
        # In this case, everything should be rerun (or data populated).
        rerun_recommendations = list(required_by_tool.keys())
        tool_health = {k: {"status": "missing_context_data", "missing": required_by_tool[k]} for k in required_by_tool}
    else:
        for tool_name, required_names in required_by_tool.items():
            missing = [n for n in required_names if n not in values]
            nulls = [n for n in required_names if n in values and values.get(n) is None]
            if missing or nulls:
                tool_health[tool_name] = {"status": "incomplete", "missing": missing, "nulls": nulls}
                rerun_recommendations.append(tool_name)
                issues.append(
                    {
                        "type": "missing_driver_values",
                        "tool": tool_name,
                        "missing": missing,
                        "nulls": nulls,
                    }
                )
            else:
                tool_health[tool_name] = {"status": "ok"}

    all_tools_ok = all(v.get("status") == "ok" for v in tool_health.values()) if tool_health else False

    # 3) Decision routing (basic)
    if outside_thresholds:
        if all_tools_ok:
            decision = "route_to_human_approval"
            next_action = "Request human approval to finalize consensus demand (boost outside thresholds)."
        else:
            decision = "ask_actor_rerun"
            next_action = "Ask Actor agent to rerun the flagged tool(s) and recompute boosts."
    else:
        if all_tools_ok:
            decision = "within_thresholds"
            next_action = "Boost within thresholds; proceed (or optionally send for lightweight review)."
        else:
            decision = "ask_actor_rerun"
            next_action = "Boost may be unreliable due to missing tool outputs; rerun flagged tool(s)."

    return {
        "sku_id": _norm_upper(sku_id),
        "customer_id": _norm_upper(customer_id),
        "location_id": _norm_upper(location_id),
        "as_of_date": as_of_date,
        "thresholds": {"upper": upper_threshold, "lower": lower_threshold},
        "total_boost_percent": total,
        "outside_thresholds": outside_thresholds,
        "decision": decision,
        "next_action": next_action,
        "tool_health": tool_health,
        "rerun_recommendations": rerun_recommendations,
        "issues": issues,
        "final_boost_breakdown": final_boost,
    }


# Optional registry to make it easy to plug into your agent layer later.
DEMAND_ACTOR_TOOLS: Dict[str, Any] = {
    "fetch_consensus_demand_driver": fetch_consensus_demand_driver,
    "fetch_social_signal_drivers": fetch_social_signal_drivers,
    "fetch_marketing_spend_drivers": fetch_marketing_spend_drivers,
    "fetch_trade_promo_drivers": fetch_trade_promo_drivers,
    "fetch_digital_shelf_drivers": fetch_digital_shelf_drivers,
    "fetch_weather_environment_drivers": fetch_weather_environment_drivers,
    "fetch_competitor_data_drivers": fetch_competitor_data_drivers,
    "fetch_pos_data_drivers": fetch_pos_data_drivers,
    "fetch_abc_xyz_classification": fetch_abc_xyz_classification,
    "fetch_relevant_products_by_abc_xyz": fetch_relevant_products_by_abc_xyz,
    # Boost calculators
    "calculate_social_signal_demand_boost": calculate_social_signal_demand_boost,
    "calculate_marketing_spend_demand_boost": calculate_marketing_spend_demand_boost,
    "calculate_trade_promo_demand_boost": calculate_trade_promo_demand_boost,
    "calculate_digital_shelf_demand_boost": calculate_digital_shelf_demand_boost,
    "calculate_weather_environment_demand_boost": calculate_weather_environment_demand_boost,
    "calculate_competitor_data_demand_boost": calculate_competitor_data_demand_boost,
    "calculate_final_demand_boost": calculate_final_demand_boost,
    "calculate_final_demand_forecast": calculate_final_demand_forecast,
    "build_boost_reasoning_context": build_boost_reasoning_context,
}


CRITIC_TOOLS: Dict[str, Any] = {
    "critic_review_consensus_demand_boost": critic_review_consensus_demand_boost,
}


def list_demand_actor_tools() -> List[str]:
    """
    Convenience for debugging / agent bootstrapping.
    """
    return sorted(DEMAND_ACTOR_TOOLS.keys())


