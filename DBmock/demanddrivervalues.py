"""
Mock "real-time" demand driver values.

Key requirement:
- Provide data at the (sku_id, customer_id, location_id, date) grain
- Keep the default mocked date as Jan 1, 2026
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

DEFAULT_AS_OF_DATE = "2026-01-01"
CASE_2_AS_OF_DATE = "2026-01-02"
CASE_3_AS_OF_DATE = "2026-01-03"

# Key = (SKU_ID, CUSTOMER_ID, LOCATION_ID, AS_OF_DATE)
# Value = { driver_name: driver_value }
MOCK_DEMAND_DRIVER_VALUES: Dict[Tuple[str, str, str, str], Dict[str, Any]] = {
    # ==================================================================================
    # PONDS_SUPER_LIGHT_GEL_100G — BLINKIT — BANGALORE — 2026-01-01
    # ==================================================================================
    ("PONDS_SUPER_LIGHT_GEL_100G", "BLINKIT", "BANGALORE", DEFAULT_AS_OF_DATE): {
        # 1) Consensus demand
        "Statistical Baseline Forecast": 92,
        # 2) Social
        "Ingredient Trend Velocity": 0.18,  # +18% WoW search velocity
        "Brand Sentiment Score": 73,  # 0-100
        "Viral Hashtag Volume": 1450,  # mentions/day
        "Influencer Mention Count": 26,  # mentions/day
        # 3) Marketing spend & engagement
        "Performance Marketing Spend": 220000,  # INR/day
        "Campaign Click-Through-Rate (CTR)": 0.021,  # 2.1%
        "Video Completion Rate": 0.34,  # 34%
        "Retargeting Pool Size": 18500,
        # 4) Trade promo
        "On-Platform Discount Depth": 0.10,  # 10%
        "Bundle Offer Active Status": False,
        "Flash Sale Participation": False,
        "Cart-Level Offer Conversion": 0.06,  # 6%
        # 5) Digital shelf analytics
        "Share of Search (Keyword Rank)": 4,  # rank (lower is better)
        "Product Detail Page (PDP) Views": 52000,
        "Buy Box Win Rate": 0.96,  # 96%
        "Rating & Review Velocity": 38,  # new reviews / 48h
        # 6) Weather/environment
        "Max Temperature Forecast": 26.5,  # °C
        "Humidity Index": 0.62,  # 62%
        "UV Index": 5.8,
        "Air Quality Index (AQI)": 138,
        # 7) Competitor data
        "Competitor Price Gap": -15,  # INR vs closest competitor (negative means we are cheaper)
        "Competitor Out-of-Stock Status": False,
        "Competitor Promo Intensity": 0.10,  # 10%
        "Competitor New Launch Signal": False,
        # 8) POS & open orders
        "Real-Time Sales Velocity": 12.4,  # units/hour
        "Inventory Days on Hand (DOH)": 7.2,
        "Distributor Open Orders": 320,  # units
        "Stock-Out Incidents": 0,
    },
    # ==================================================================================
    # PONDS_SUPER_LIGHT_GEL_100G — ZEPTO — BANGALORE — 2026-01-01
    # ==================================================================================
    ("PONDS_SUPER_LIGHT_GEL_100G", "ZEPTO", "BANGALORE", DEFAULT_AS_OF_DATE): {
        "Statistical Baseline Forecast": 88,
        "Ingredient Trend Velocity": 0.14,
        "Brand Sentiment Score": 71,
        "Viral Hashtag Volume": 1320,
        "Influencer Mention Count": 22,
        "Performance Marketing Spend": 150000,
        "Campaign Click-Through-Rate (CTR)": 0.019,
        "Video Completion Rate": 0.31,
        "Retargeting Pool Size": 14200,
        "On-Platform Discount Depth": 0.12,
        "Bundle Offer Active Status": True,
        "Flash Sale Participation": False,
        "Cart-Level Offer Conversion": 0.07,
        "Share of Search (Keyword Rank)": 6,
        "Product Detail Page (PDP) Views": 41000,
        "Buy Box Win Rate": 0.93,
        "Rating & Review Velocity": 29,
        "Max Temperature Forecast": 26.5,
        "Humidity Index": 0.62,
        "UV Index": 5.8,
        "Air Quality Index (AQI)": 138,
        "Competitor Price Gap": 10,
        "Competitor Out-of-Stock Status": False,
        "Competitor Promo Intensity": 0.12,
        "Competitor New Launch Signal": False,
        "Real-Time Sales Velocity": 9.8,
        "Inventory Days on Hand (DOH)": 5.9,
        "Distributor Open Orders": 260,
        "Stock-Out Incidents": 1,
    },
    # ==================================================================================
    # DOVE_HAIR_FALL_RESCUE_650ML — BLINKIT — BANGALORE — 2026-01-01
    # ==================================================================================
    ("DOVE_HAIR_FALL_RESCUE_650ML", "BLINKIT", "BANGALORE", DEFAULT_AS_OF_DATE): {
        "Statistical Baseline Forecast": 78,
        "Ingredient Trend Velocity": 0.06,
        "Brand Sentiment Score": 69,
        "Viral Hashtag Volume": 820,
        "Influencer Mention Count": 9,
        "Performance Marketing Spend": 90000,
        "Campaign Click-Through-Rate (CTR)": 0.014,
        "Video Completion Rate": 0.29,
        "Retargeting Pool Size": 9100,
        "On-Platform Discount Depth": 0.08,
        "Bundle Offer Active Status": False,
        "Flash Sale Participation": False,
        "Cart-Level Offer Conversion": 0.04,
        "Share of Search (Keyword Rank)": 8,
        "Product Detail Page (PDP) Views": 29000,
        "Buy Box Win Rate": 0.91,
        "Rating & Review Velocity": 21,
        "Max Temperature Forecast": 26.5,
        "Humidity Index": 0.62,
        "UV Index": 5.8,
        "Air Quality Index (AQI)": 138,
        "Competitor Price Gap": 35,
        "Competitor Out-of-Stock Status": True,
        "Competitor Promo Intensity": 0.18,
        "Competitor New Launch Signal": True,
        "Real-Time Sales Velocity": 6.1,
        "Inventory Days on Hand (DOH)": 9.4,
        "Distributor Open Orders": 180,
        "Stock-Out Incidents": 0,
    },
    # ==================================================================================
    # DOVE_HAIR_FALL_RESCUE_650ML — ZEPTO — BANGALORE — 2026-01-01
    # ==================================================================================
    ("DOVE_HAIR_FALL_RESCUE_650ML", "ZEPTO", "BANGALORE", DEFAULT_AS_OF_DATE): {
        "Statistical Baseline Forecast": 74,
        "Ingredient Trend Velocity": 0.05,
        "Brand Sentiment Score": 68,
        "Viral Hashtag Volume": 760,
        "Influencer Mention Count": 8,
        "Performance Marketing Spend": 70000,
        "Campaign Click-Through-Rate (CTR)": 0.013,
        "Video Completion Rate": 0.27,
        "Retargeting Pool Size": 8300,
        "On-Platform Discount Depth": 0.10,
        "Bundle Offer Active Status": True,
        "Flash Sale Participation": True,
        "Cart-Level Offer Conversion": 0.06,
        "Share of Search (Keyword Rank)": 10,
        "Product Detail Page (PDP) Views": 24500,
        "Buy Box Win Rate": 0.88,
        "Rating & Review Velocity": 18,
        "Max Temperature Forecast": 26.5,
        "Humidity Index": 0.62,
        "UV Index": 5.8,
        "Air Quality Index (AQI)": 138,
        "Competitor Price Gap": 20,
        "Competitor Out-of-Stock Status": False,
        "Competitor Promo Intensity": 0.22,
        "Competitor New Launch Signal": False,
        "Real-Time Sales Velocity": 5.4,
        "Inventory Days on Hand (DOH)": 6.8,
        "Distributor Open Orders": 160,
        "Stock-Out Incidents": 1,
    },

    # ==================================================================================
    # CASE 2: 2026-01-02 (Bullish day: strong social + promos + shelf)
    # ==================================================================================
    ("PONDS_SUPER_LIGHT_GEL_100G", "BLINKIT", "BANGALORE", CASE_2_AS_OF_DATE): {
        "Statistical Baseline Forecast": 95,
        "Ingredient Trend Velocity": 0.32,
        "Brand Sentiment Score": 82,
        "Viral Hashtag Volume": 2600,
        "Influencer Mention Count": 38,
        "Performance Marketing Spend": 260000,
        "Campaign Click-Through-Rate (CTR)": 0.028,
        "Video Completion Rate": 0.41,
        "Retargeting Pool Size": 24000,
        "On-Platform Discount Depth": 0.20,
        "Bundle Offer Active Status": True,
        "Flash Sale Participation": True,
        "Cart-Level Offer Conversion": 0.11,
        "Share of Search (Keyword Rank)": 2,
        "Product Detail Page (PDP) Views": 72000,
        "Buy Box Win Rate": 0.98,
        "Rating & Review Velocity": 52,
        "Max Temperature Forecast": 31.0,
        "Humidity Index": 0.68,
        "UV Index": 7.2,
        "Air Quality Index (AQI)": 165,
        "Competitor Price Gap": -25,
        "Competitor Out-of-Stock Status": True,
        "Competitor Promo Intensity": 0.05,
        "Competitor New Launch Signal": False,
        "Real-Time Sales Velocity": 19.8,
        "Inventory Days on Hand (DOH)": 4.8,
        "Distributor Open Orders": 520,
        "Stock-Out Incidents": 0,
    },
    ("PONDS_SUPER_LIGHT_GEL_100G", "ZEPTO", "BANGALORE", CASE_2_AS_OF_DATE): {
        "Statistical Baseline Forecast": 90,
        "Ingredient Trend Velocity": 0.26,
        "Brand Sentiment Score": 79,
        "Viral Hashtag Volume": 2100,
        "Influencer Mention Count": 28,
        "Performance Marketing Spend": 180000,
        "Campaign Click-Through-Rate (CTR)": 0.023,
        "Video Completion Rate": 0.36,
        "Retargeting Pool Size": 17500,
        "On-Platform Discount Depth": 0.18,
        "Bundle Offer Active Status": True,
        "Flash Sale Participation": False,
        "Cart-Level Offer Conversion": 0.10,
        "Share of Search (Keyword Rank)": 4,
        "Product Detail Page (PDP) Views": 56000,
        "Buy Box Win Rate": 0.95,
        "Rating & Review Velocity": 41,
        "Max Temperature Forecast": 31.0,
        "Humidity Index": 0.68,
        "UV Index": 7.2,
        "Air Quality Index (AQI)": 165,
        "Competitor Price Gap": -10,
        "Competitor Out-of-Stock Status": True,
        "Competitor Promo Intensity": 0.08,
        "Competitor New Launch Signal": False,
        "Real-Time Sales Velocity": 15.2,
        "Inventory Days on Hand (DOH)": 5.1,
        "Distributor Open Orders": 420,
        "Stock-Out Incidents": 0,
    },
    ("DOVE_HAIR_FALL_RESCUE_650ML", "BLINKIT", "BANGALORE", CASE_2_AS_OF_DATE): {
        "Statistical Baseline Forecast": 82,
        "Ingredient Trend Velocity": 0.14,
        "Brand Sentiment Score": 75,
        "Viral Hashtag Volume": 1350,
        "Influencer Mention Count": 16,
        "Performance Marketing Spend": 120000,
        "Campaign Click-Through-Rate (CTR)": 0.019,
        "Video Completion Rate": 0.33,
        "Retargeting Pool Size": 13000,
        "On-Platform Discount Depth": 0.12,
        "Bundle Offer Active Status": True,
        "Flash Sale Participation": False,
        "Cart-Level Offer Conversion": 0.08,
        "Share of Search (Keyword Rank)": 6,
        "Product Detail Page (PDP) Views": 38000,
        "Buy Box Win Rate": 0.93,
        "Rating & Review Velocity": 33,
        "Max Temperature Forecast": 28.0,
        "Humidity Index": 0.72,
        "UV Index": 6.1,
        "Air Quality Index (AQI)": 150,
        "Competitor Price Gap": -5,
        "Competitor Out-of-Stock Status": False,
        "Competitor Promo Intensity": 0.10,
        "Competitor New Launch Signal": False,
        "Real-Time Sales Velocity": 8.4,
        "Inventory Days on Hand (DOH)": 8.2,
        "Distributor Open Orders": 260,
        "Stock-Out Incidents": 0,
    },
    ("DOVE_HAIR_FALL_RESCUE_650ML", "ZEPTO", "BANGALORE", CASE_2_AS_OF_DATE): {
        "Statistical Baseline Forecast": 78,
        "Ingredient Trend Velocity": 0.10,
        "Brand Sentiment Score": 73,
        "Viral Hashtag Volume": 1100,
        "Influencer Mention Count": 14,
        "Performance Marketing Spend": 95000,
        "Campaign Click-Through-Rate (CTR)": 0.017,
        "Video Completion Rate": 0.31,
        "Retargeting Pool Size": 11500,
        "On-Platform Discount Depth": 0.15,
        "Bundle Offer Active Status": True,
        "Flash Sale Participation": True,
        "Cart-Level Offer Conversion": 0.09,
        "Share of Search (Keyword Rank)": 7,
        "Product Detail Page (PDP) Views": 34000,
        "Buy Box Win Rate": 0.91,
        "Rating & Review Velocity": 28,
        "Max Temperature Forecast": 28.0,
        "Humidity Index": 0.72,
        "UV Index": 6.1,
        "Air Quality Index (AQI)": 150,
        "Competitor Price Gap": 5,
        "Competitor Out-of-Stock Status": False,
        "Competitor Promo Intensity": 0.12,
        "Competitor New Launch Signal": False,
        "Real-Time Sales Velocity": 7.6,
        "Inventory Days on Hand (DOH)": 7.4,
        "Distributor Open Orders": 230,
        "Stock-Out Incidents": 0,
    },

    # ==================================================================================
    # CASE 3: 2026-01-03 (Bearish day: weak social + low marketing + poor shelf + competitor headwinds)
    # ==================================================================================
    ("PONDS_SUPER_LIGHT_GEL_100G", "BLINKIT", "BANGALORE", CASE_3_AS_OF_DATE): {
        "Statistical Baseline Forecast": 85,
        "Ingredient Trend Velocity": -0.12,
        "Brand Sentiment Score": 47,
        "Viral Hashtag Volume": 180,
        "Influencer Mention Count": 1,
        "Performance Marketing Spend": 18000,
        "Campaign Click-Through-Rate (CTR)": 0.007,
        "Video Completion Rate": 0.09,
        "Retargeting Pool Size": 1200,
        "On-Platform Discount Depth": 0.00,
        "Bundle Offer Active Status": False,
        "Flash Sale Participation": False,
        "Cart-Level Offer Conversion": 0.01,
        "Share of Search (Keyword Rank)": 22,
        "Product Detail Page (PDP) Views": 9000,
        "Buy Box Win Rate": 0.68,
        "Rating & Review Velocity": 2,
        "Max Temperature Forecast": 19.5,
        "Humidity Index": 0.28,
        "UV Index": 1.2,
        "Air Quality Index (AQI)": 35,
        "Competitor Price Gap": 35,
        "Competitor Out-of-Stock Status": False,
        "Competitor Promo Intensity": 0.35,
        "Competitor New Launch Signal": True,
        "Real-Time Sales Velocity": 4.2,
        "Inventory Days on Hand (DOH)": 14.5,
        "Distributor Open Orders": 80,
        "Stock-Out Incidents": 0,
    },
    ("PONDS_SUPER_LIGHT_GEL_100G", "ZEPTO", "BANGALORE", CASE_3_AS_OF_DATE): {
        "Statistical Baseline Forecast": 82,
        "Ingredient Trend Velocity": -0.08,
        "Brand Sentiment Score": 50,
        "Viral Hashtag Volume": 240,
        "Influencer Mention Count": 2,
        "Performance Marketing Spend": 25000,
        "Campaign Click-Through-Rate (CTR)": 0.009,
        "Video Completion Rate": 0.11,
        "Retargeting Pool Size": 1700,
        "On-Platform Discount Depth": 0.01,
        "Bundle Offer Active Status": False,
        "Flash Sale Participation": False,
        "Cart-Level Offer Conversion": 0.015,
        "Share of Search (Keyword Rank)": 18,
        "Product Detail Page (PDP) Views": 12000,
        "Buy Box Win Rate": 0.74,
        "Rating & Review Velocity": 3,
        "Max Temperature Forecast": 19.5,
        "Humidity Index": 0.28,
        "UV Index": 1.2,
        "Air Quality Index (AQI)": 35,
        "Competitor Price Gap": 20,
        "Competitor Out-of-Stock Status": False,
        "Competitor Promo Intensity": 0.30,
        "Competitor New Launch Signal": True,
        "Real-Time Sales Velocity": 4.9,
        "Inventory Days on Hand (DOH)": 13.0,
        "Distributor Open Orders": 110,
        "Stock-Out Incidents": 0,
    },
    ("DOVE_HAIR_FALL_RESCUE_650ML", "BLINKIT", "BANGALORE", CASE_3_AS_OF_DATE): {
        "Statistical Baseline Forecast": 72,
        "Ingredient Trend Velocity": -0.04,
        "Brand Sentiment Score": 52,
        "Viral Hashtag Volume": 260,
        "Influencer Mention Count": 2,
        "Performance Marketing Spend": 22000,
        "Campaign Click-Through-Rate (CTR)": 0.009,
        "Video Completion Rate": 0.12,
        "Retargeting Pool Size": 1400,
        "On-Platform Discount Depth": 0.02,
        "Bundle Offer Active Status": False,
        "Flash Sale Participation": False,
        "Cart-Level Offer Conversion": 0.02,
        "Share of Search (Keyword Rank)": 16,
        "Product Detail Page (PDP) Views": 14000,
        "Buy Box Win Rate": 0.79,
        "Rating & Review Velocity": 4,
        "Max Temperature Forecast": 20.0,
        "Humidity Index": 0.30,
        "UV Index": 1.3,
        "Air Quality Index (AQI)": 38,
        "Competitor Price Gap": 30,
        "Competitor Out-of-Stock Status": False,
        "Competitor Promo Intensity": 0.28,
        "Competitor New Launch Signal": True,
        "Real-Time Sales Velocity": 3.8,
        "Inventory Days on Hand (DOH)": 12.2,
        "Distributor Open Orders": 90,
        "Stock-Out Incidents": 0,
    },
    ("DOVE_HAIR_FALL_RESCUE_650ML", "ZEPTO", "BANGALORE", CASE_3_AS_OF_DATE): {
        "Statistical Baseline Forecast": 70,
        "Ingredient Trend Velocity": -0.06,
        "Brand Sentiment Score": 49,
        "Viral Hashtag Volume": 210,
        "Influencer Mention Count": 1,
        "Performance Marketing Spend": 15000,
        "Campaign Click-Through-Rate (CTR)": 0.006,
        "Video Completion Rate": 0.08,
        "Retargeting Pool Size": 900,
        "On-Platform Discount Depth": 0.00,
        "Bundle Offer Active Status": False,
        "Flash Sale Participation": False,
        "Cart-Level Offer Conversion": 0.01,
        "Share of Search (Keyword Rank)": 20,
        "Product Detail Page (PDP) Views": 9500,
        "Buy Box Win Rate": 0.66,
        "Rating & Review Velocity": 2,
        "Max Temperature Forecast": 20.0,
        "Humidity Index": 0.30,
        "UV Index": 1.3,
        "Air Quality Index (AQI)": 38,
        "Competitor Price Gap": 25,
        "Competitor Out-of-Stock Status": False,
        "Competitor Promo Intensity": 0.32,
        "Competitor New Launch Signal": True,
        "Real-Time Sales Velocity": 3.1,
        "Inventory Days on Hand (DOH)": 11.8,
        "Distributor Open Orders": 70,
        "Stock-Out Incidents": 0,
    },
}


# Short, human-readable notes per driver for LLM reasoning/explanations.
# Key = (SKU_ID, CUSTOMER_ID, LOCATION_ID, AS_OF_DATE)
# Value = { driver_name: short_note }
MOCK_DEMAND_DRIVER_NOTES: Dict[Tuple[str, str, str, str], Dict[str, str]] = {
    # --- 2026-01-01 (Base) ---
    ("PONDS_SUPER_LIGHT_GEL_100G", "BLINKIT", "BANGALORE", DEFAULT_AS_OF_DATE): {
        "Statistical Baseline Forecast": "Baseline from 3-year history; seasonality adjusted for early January.",
        "Ingredient Trend Velocity": "Search trend mildly positive (steady hydration/gel moisturizers).",
        "On-Platform Discount Depth": "Only a light discount; not a major promo day.",
        "Buy Box Win Rate": "Strong availability and seller control.",
        "Competitor Promo Intensity": "Competitors running moderate promo pressure.",
    },
    ("PONDS_SUPER_LIGHT_GEL_100G", "ZEPTO", "BANGALORE", DEFAULT_AS_OF_DATE): {
        "Statistical Baseline Forecast": "Baseline demand slightly lower vs Blinkit due to lower usual traffic.",
        "Bundle Offer Active Status": "Bundle enabled to improve conversion without deep discount.",
        "Buy Box Win Rate": "Healthy but slightly lower vs Blinkit (more third-party competition).",
    },
    ("DOVE_HAIR_FALL_RESCUE_650ML", "BLINKIT", "BANGALORE", DEFAULT_AS_OF_DATE): {
        "Statistical Baseline Forecast": "Baseline reflects steady replenishment behavior for large pack shampoo.",
        "Competitor Out-of-Stock Status": "Key competitor intermittently OOS, creating a tailwind.",
        "Competitor New Launch Signal": "New launch creating some attention split in category.",
    },
    ("DOVE_HAIR_FALL_RESCUE_650ML", "ZEPTO", "BANGALORE", DEFAULT_AS_OF_DATE): {
        "Statistical Baseline Forecast": "Base demand steady; Zepto slightly more promo-driven.",
        "Flash Sale Participation": "Flash sale planned; expect short-lived demand spike.",
        "Competitor Promo Intensity": "Competitors are relatively aggressive on price.",
    },

    # --- 2026-01-02 (Bullish) ---
    ("PONDS_SUPER_LIGHT_GEL_100G", "BLINKIT", "BANGALORE", CASE_2_AS_OF_DATE): {
        "Ingredient Trend Velocity": "Hydration/gel keywords trending strongly (viral skincare content).",
        "Brand Sentiment Score": "Sentiment uplift driven by recent positive influencer reviews.",
        "Flash Sale Participation": "Flash sale slot secured; high short-term traffic expected.",
        "Share of Search (Keyword Rank)": "Top-of-search placement improves discoverability materially.",
        "Competitor Out-of-Stock Status": "Main competitor OOS -> switching opportunity.",
    },
    ("PONDS_SUPER_LIGHT_GEL_100G", "ZEPTO", "BANGALORE", CASE_2_AS_OF_DATE): {
        "Ingredient Trend Velocity": "Strong upward velocity across search/social for hydration products.",
        "Cart-Level Offer Conversion": "Coupons converting unusually well today.",
        "Competitor Out-of-Stock Status": "Competitor OOS supports incremental demand capture.",
    },
    ("DOVE_HAIR_FALL_RESCUE_650ML", "BLINKIT", "BANGALORE", CASE_2_AS_OF_DATE): {
        "Humidity Index": "Higher humidity increases hair-fall/frizz concern demand.",
        "Bundle Offer Active Status": "Bundle improves perceived value without deep discounting.",
    },
    ("DOVE_HAIR_FALL_RESCUE_650ML", "ZEPTO", "BANGALORE", CASE_2_AS_OF_DATE): {
        "Flash Sale Participation": "Flash sale increases visibility and conversion.",
        "On-Platform Discount Depth": "Meaningful discount; expect demand lift.",
    },

    # --- 2026-01-03 (Bearish) ---
    ("PONDS_SUPER_LIGHT_GEL_100G", "BLINKIT", "BANGALORE", CASE_3_AS_OF_DATE): {
        "Ingredient Trend Velocity": "Search momentum turned negative after trend cooled.",
        "Brand Sentiment Score": "Sentiment weakened due to recent negative comments/complaints.",
        "Performance Marketing Spend": "Spend cut sharply; fewer conversions expected.",
        "Buy Box Win Rate": "Buy box loss due to availability/seller competition.",
        "Competitor Promo Intensity": "Competitors running steep promos + new launch distracting demand.",
    },
    ("PONDS_SUPER_LIGHT_GEL_100G", "ZEPTO", "BANGALORE", CASE_3_AS_OF_DATE): {
        "On-Platform Discount Depth": "No meaningful promo levers active; demand likely soft.",
        "Share of Search (Keyword Rank)": "Lower visibility; fewer PDP visits.",
        "Competitor New Launch Signal": "New competitor variant pulling attention and traffic.",
    },
    ("DOVE_HAIR_FALL_RESCUE_650ML", "BLINKIT", "BANGALORE", CASE_3_AS_OF_DATE): {
        "Performance Marketing Spend": "Low spend reduces demand capture in planned purchases.",
        "Competitor Promo Intensity": "Competitor discounting is heavy; headwind for volume.",
    },
    ("DOVE_HAIR_FALL_RESCUE_650ML", "ZEPTO", "BANGALORE", CASE_3_AS_OF_DATE): {
        "Campaign Click-Through-Rate (CTR)": "Low CTR indicates weak creative/targeting today.",
        "Buy Box Win Rate": "Availability/competition issues reduce conversion.",
        "Competitor Promo Intensity": "Strong competitor promo pressure.",
    },
}


MOCK_DEMAND_DRIVER_SCENARIO: Dict[Tuple[str, str, str, str], str] = {
    # Base
    ("PONDS_SUPER_LIGHT_GEL_100G", "BLINKIT", "BANGALORE", DEFAULT_AS_OF_DATE): "BASE",
    ("PONDS_SUPER_LIGHT_GEL_100G", "ZEPTO", "BANGALORE", DEFAULT_AS_OF_DATE): "BASE",
    ("DOVE_HAIR_FALL_RESCUE_650ML", "BLINKIT", "BANGALORE", DEFAULT_AS_OF_DATE): "BASE",
    ("DOVE_HAIR_FALL_RESCUE_650ML", "ZEPTO", "BANGALORE", DEFAULT_AS_OF_DATE): "BASE",
    # Bullish
    ("PONDS_SUPER_LIGHT_GEL_100G", "BLINKIT", "BANGALORE", CASE_2_AS_OF_DATE): "BULLISH",
    ("PONDS_SUPER_LIGHT_GEL_100G", "ZEPTO", "BANGALORE", CASE_2_AS_OF_DATE): "BULLISH",
    ("DOVE_HAIR_FALL_RESCUE_650ML", "BLINKIT", "BANGALORE", CASE_2_AS_OF_DATE): "BULLISH",
    ("DOVE_HAIR_FALL_RESCUE_650ML", "ZEPTO", "BANGALORE", CASE_2_AS_OF_DATE): "BULLISH",
    # Bearish
    ("PONDS_SUPER_LIGHT_GEL_100G", "BLINKIT", "BANGALORE", CASE_3_AS_OF_DATE): "BEARISH",
    ("PONDS_SUPER_LIGHT_GEL_100G", "ZEPTO", "BANGALORE", CASE_3_AS_OF_DATE): "BEARISH",
    ("DOVE_HAIR_FALL_RESCUE_650ML", "BLINKIT", "BANGALORE", CASE_3_AS_OF_DATE): "BEARISH",
    ("DOVE_HAIR_FALL_RESCUE_650ML", "ZEPTO", "BANGALORE", CASE_3_AS_OF_DATE): "BEARISH",
}


def get_demand_driver_values(
    sku_id: str,
    customer_id: str,
    location_id: str,
    as_of_date: str = DEFAULT_AS_OF_DATE,
) -> Dict[str, Any]:
    """
    Returns a {driver_name: value} mapping for the given context.
    """
    key = (sku_id.upper(), customer_id.upper(), location_id.upper(), as_of_date)
    return dict(MOCK_DEMAND_DRIVER_VALUES.get(key, {}))


def get_demand_driver_notes(
    sku_id: str,
    customer_id: str,
    location_id: str,
    as_of_date: str = DEFAULT_AS_OF_DATE,
) -> Dict[str, str]:
    """
    Returns {driver_name: short_note} for the given context/date.
    Notes are optional; missing drivers simply won't have a note.
    """
    key = (sku_id.upper(), customer_id.upper(), location_id.upper(), as_of_date)
    return dict(MOCK_DEMAND_DRIVER_NOTES.get(key, {}))


def get_demand_driver_scenario(
    sku_id: str,
    customer_id: str,
    location_id: str,
    as_of_date: str = DEFAULT_AS_OF_DATE,
) -> Optional[str]:
    """
    Returns scenario label like BASE/BULLISH/BEARISH (if available).
    """
    key = (sku_id.upper(), customer_id.upper(), location_id.upper(), as_of_date)
    return MOCK_DEMAND_DRIVER_SCENARIO.get(key)


def get_demand_driver_value(
    sku_id: str,
    customer_id: str,
    location_id: str,
    driver_name: str,
    as_of_date: str = DEFAULT_AS_OF_DATE,
) -> Optional[Any]:
    """
    Convenience accessor for one driver value.
    """
    values = get_demand_driver_values(
        sku_id=sku_id,
        customer_id=customer_id,
        location_id=location_id,
        as_of_date=as_of_date,
    )
    return values.get(driver_name)


