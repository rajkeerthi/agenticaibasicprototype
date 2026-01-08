from __future__ import annotations

from typing import Any, Dict, List


def get_product_drivers(sku_id: str) -> List[Dict[str, Any]]:
    """
    Returns the master list of applicable demand drivers for a product.
    Drivers are organized into specific Real-Time categories.
    """

    sku_id = (sku_id or "").strip().upper()

    # 1. Consensus Demand Forecast Drivers
    consensus_demand_drivers = [
        {
            "category": "Statistical Demand Forecast",
            "driver_name": "Statistical Baseline Forecast",
            "description": (
                "The base volume predicted by internal time-series algorithms (ARIMA/Prophet) "
                "using 3-year historical sales data."
            ),
        },
    ]

    # 2. Real Time Social Signals
    social_signals_drivers = [
        {
            "category": "Real Time Social Signals",
            "driver_name": "Ingredient Trend Velocity",
            "description": (
                "Rate of change in search volume for key active ingredients "
                "(e.g., 'Hyaluronic', 'Sulphate-Free')."
            ),
        },
        {
            "category": "Real Time Social Signals",
            "driver_name": "Brand Sentiment Score",
            "description": (
                "Net Promoter Score (NPS) derived from real-time sentiment analysis of "
                "Twitter, Reddit, and Instagram comments."
            ),
        },
        {
            "category": "Real Time Social Signals",
            "driver_name": "Viral Hashtag Volume",
            "description": (
                "Frequency of brand-adjacent hashtags (e.g., #GlassSkin, #HairGoals) "
                "appearing in top 100 trending topics."
            ),
        },
        {
            "category": "Real Time Social Signals",
            "driver_name": "Influencer Mention Count",
            "description": (
                "Number of unique mentions by Tier-1 and Tier-2 beauty influencers in the last 24 hours."
            ),
        },
    ]

    # 3. Real Time Marketing Spend and Engagement Signals
    marketing_spend_drivers = [
        {
            "category": "Real Time Marketing Spend and Engagement Signals",
            "driver_name": "Performance Marketing Spend",
            "description": "Daily ad spend burn rate on Meta (Instagram/Facebook) and Google Ads for this SKU.",
        },
        {
            "category": "Real Time Marketing Spend and Engagement Signals",
            "driver_name": "Campaign Click-Through-Rate (CTR)",
            "description": (
                "Real-time efficiency metric of active digital ads; higher CTR indicates higher immediate "
                "purchase intent."
            ),
        },
        {
            "category": "Real Time Marketing Spend and Engagement Signals",
            "driver_name": "Video Completion Rate",
            "description": "Percentage of users watching full brand ads on YouTube/Reels; proxy for brand consideration.",
        },
        {
            "category": "Real Time Marketing Spend and Engagement Signals",
            "driver_name": "Retargeting Pool Size",
            "description": "Size of the audience who visited the product page but didn't buy, now being retargeted.",
        },
    ]

    # 4. Real Time Trade Promo Signals
    trade_promo_drivers = [
        {
            "category": "Real Time Trade Promo Signals",
            "driver_name": "On-Platform Discount Depth",
            "description": "Current percentage discount active on the retailer platform (e.g., Flat 20% Off).",
        },
        {
            "category": "Real Time Trade Promo Signals",
            "driver_name": "Bundle Offer Active Status",
            "description": "Flag indicating if the SKU is part of a 'Buy X Get Y' or 'Combo' pack promotion.",
        },
        {
            "category": "Real Time Trade Promo Signals",
            "driver_name": "Flash Sale Participation",
            "description": (
                "Whether the SKU is currently featured in a time-bound 'Lightning Deal' or 'Rush Hour' slot."
            ),
        },
        {
            "category": "Real Time Trade Promo Signals",
            "driver_name": "Cart-Level Offer Conversion",
            "description": "Conversion rate uplift attributed to coupons applied at the checkout stage.",
        },
    ]

    # 5. Real Time Digital Shelf Analytics Signals
    digital_shelf_drivers = [
        {
            "category": "Real Time Digital Shelf Analytics Signals",
            "driver_name": "Share of Search (Keyword Rank)",
            "description": (
                "The organic ranking of the SKU when a user searches generic terms like 'Face Wash' or 'Shampoo'."
            ),
        },
        {
            "category": "Real Time Digital Shelf Analytics Signals",
            "driver_name": "Product Detail Page (PDP) Views",
            "description": "Traffic volume landing specifically on the product page in the last 24 hours.",
        },
        {
            "category": "Real Time Digital Shelf Analytics Signals",
            "driver_name": "Buy Box Win Rate",
            "description": (
                "Percentage of time our seller account owns the 'Add to Cart' button vs. third-party sellers."
            ),
        },
        {
            "category": "Real Time Digital Shelf Analytics Signals",
            "driver_name": "Rating & Review Velocity",
            "description": "Number of new reviews added in the last 48 hours; high velocity often precedes a sales spike.",
        },
    ]

    # 6. Real Time Weather/Environment Signals
    weather_environment_drivers = [
        {
            "category": "Real Time Weather/Environment Signals",
            "driver_name": "Max Temperature Forecast",
            "description": (
                "Predicted maximum temperature for the next 3 days; critical for summer portfolio "
                "(Deos, Talc, Light Gels)."
            ),
        },
        {
            "category": "Real Time Weather/Environment Signals",
            "driver_name": "Humidity Index",
            "description": "Moisture levels in the air; triggers demand for Frizz-Control Hair products.",
        },
        {
            "category": "Real Time Weather/Environment Signals",
            "driver_name": "UV Index",
            "description": (
                "Intensity of ultraviolet radiation; direct correlation with Sunscreen and Light Gel sales."
            ),
        },
        {
            "category": "Real Time Weather/Environment Signals",
            "driver_name": "Air Quality Index (AQI)",
            "description": "Pollution levels; triggers demand for Deep Cleanse and Anti-Pollution skincare.",
        },
    ]

    # 7. Real Time Competitor Data
    competitor_data_drivers = [
        {
            "category": "Real Time Competitor Data",
            "driver_name": "Competitor Price Gap",
            "description": "The monetary difference between our SKU and the nearest equivalent competitor SKU.",
        },
        {
            "category": "Real Time Competitor Data",
            "driver_name": "Competitor Out-of-Stock Status",
            "description": (
                "Flag indicating if the main competitor SKU is currently unavailable, creating a switch opportunity."
            ),
        },
        {
            "category": "Real Time Competitor Data",
            "driver_name": "Competitor Promo Intensity",
            "description": (
                "Aggressiveness of competitor discounting (e.g., are they running a 50% off deep discount?)."
            ),
        },
        {
            "category": "Real Time Competitor Data",
            "driver_name": "Competitor New Launch Signal",
            "description": "Detection of a new competitive variant launching in the same category.",
        },
    ]

    # 8. Real Time POS Data & Open Orders
    pos_data_drivers = [
        {
            "category": "Real Time POS Data & Open Orders",
            "driver_name": "Real-Time Sales Velocity",
            "description": "Units sold per hour recorded at the Point of Sale (POS) in the last 6 hours.",
        },
        {
            "category": "Real Time POS Data & Open Orders",
            "driver_name": "Inventory Days on Hand (DOH)",
            "description": "Current stock level expressed in days of coverage based on current run-rate.",
        },
        {
            "category": "Real Time POS Data & Open Orders",
            "driver_name": "Distributor Open Orders",
            "description": "Volume of confirmed orders from distributors that are yet to be shipped.",
        },
        {
            "category": "Real Time POS Data & Open Orders",
            "driver_name": "Stock-Out Incidents",
            "description": "Count of instances where demand could not be fulfilled due to zero inventory.",
        },
    ]

    # Combine all lists into one master configuration
    all_bpc_drivers = (
        consensus_demand_drivers
        + social_signals_drivers
        + marketing_spend_drivers
        + trade_promo_drivers
        + digital_shelf_drivers
        + weather_environment_drivers
        + competitor_data_drivers
        + pos_data_drivers
    )

    # Map to Products
    mock_db = {
        "PONDS_SUPER_LIGHT_GEL_100G": all_bpc_drivers,
        "DOVE_HAIR_FALL_RESCUE_650ML": all_bpc_drivers,
    }

    return mock_db.get(sku_id, [])


__all__ = ["get_product_drivers"]

def get_product_drivers(sku_id: str):
    """
    Returns the master list of applicable demand drivers for a product.
    Drivers are organized into specific Real-Time categories.
    """

    # 1. Consensus Demand Forecast Drivers
    consensus_demand_drivers = [
        {
            "category": "Statistical Demand Forecast",
            "driver_name": "Statistical Baseline Forecast",
            "description": "The base volume predicted by internal time-series algorithms (ARIMA/Prophet) using 3-year historical sales data."
        },
        
    ]

    # 2. Real Time Social Signals
    social_signals_drivers = [
        {
            "category": "Real Time Social Signals",
            "driver_name": "Ingredient Trend Velocity",
            "description": "Rate of change in search volume for key active ingredients (e.g., 'Hyaluronic', 'Sulphate-Free')."
        },
        {
            "category": "Real Time Social Signals",
            "driver_name": "Brand Sentiment Score",
            "description": "Net Promoter Score (NPS) derived from real-time sentiment analysis of Twitter, Reddit, and Instagram comments."
        },
        {
            "category": "Real Time Social Signals",
            "driver_name": "Viral Hashtag Volume",
            "description": "Frequency of brand-adjacent hashtags (e.g., #GlassSkin, #HairGoals) appearing in top 100 trending topics."
        },
        {
            "category": "Real Time Social Signals",
            "driver_name": "Influencer Mention Count",
            "description": "Number of unique mentions by Tier-1 and Tier-2 beauty influencers in the last 24 hours."
        }
    ]

    # 3. Real Time Marketing Spend and Engagement Signals
    marketing_spend_drivers = [
        {
            "category": "Real Time Marketing Spend and Engagement Signals",
            "driver_name": "Performance Marketing Spend",
            "description": "Daily ad spend burn rate on Meta (Instagram/Facebook) and Google Ads for this SKU."
        },
        {
            "category": "Real Time Marketing Spend and Engagement Signals",
            "driver_name": "Campaign Click-Through-Rate (CTR)",
            "description": "Real-time efficiency metric of active digital ads; higher CTR indicates higher immediate purchase intent."
        },
        {
            "category": "Real Time Marketing Spend and Engagement Signals",
            "driver_name": "Video Completion Rate",
            "description": "Percentage of users watching full brand ads on YouTube/Reels; proxy for brand consideration."
        },
        {
            "category": "Real Time Marketing Spend and Engagement Signals",
            "driver_name": "Retargeting Pool Size",
            "description": "Size of the audience who visited the product page but didn't buy, now being retargeted."
        }
    ]

    # 4. Real Time Trade Promo Signals
    trade_promo_drivers = [
        {
            "category": "Real Time Trade Promo Signals",
            "driver_name": "On-Platform Discount Depth",
            "description": "Current percentage discount active on the retailer platform (e.g., Flat 20% Off)."
        },
        {
            "category": "Real Time Trade Promo Signals",
            "driver_name": "Bundle Offer Active Status",
            "description": "Flag indicating if the SKU is part of a 'Buy X Get Y' or 'Combo' pack promotion."
        },
        {
            "category": "Real Time Trade Promo Signals",
            "driver_name": "Flash Sale Participation",
            "description": "Whether the SKU is currently featured in a time-bound 'Lightning Deal' or 'Rush Hour' slot."
        },
        {
            "category": "Real Time Trade Promo Signals",
            "driver_name": "Cart-Level Offer Conversion",
            "description": "Conversion rate uplift attributed to coupons applied at the checkout stage."
        }
    ]

    # 5. Real Time Digital Shelf Analytics Signals
    digital_shelf_drivers = [
        {
            "category": "Real Time Digital Shelf Analytics Signals",
            "driver_name": "Share of Search (Keyword Rank)",
            "description": "The organic ranking of the SKU when a user searches generic terms like 'Face Wash' or 'Shampoo'."
        },
        {
            "category": "Real Time Digital Shelf Analytics Signals",
            "driver_name": "Product Detail Page (PDP) Views",
            "description": "Traffic volume landing specifically on the product page in the last 24 hours."
        },
        {
            "category": "Real Time Digital Shelf Analytics Signals",
            "driver_name": "Buy Box Win Rate",
            "description": "Percentage of time our seller account owns the 'Add to Cart' button vs. third-party sellers."
        },
        {
            "category": "Real Time Digital Shelf Analytics Signals",
            "driver_name": "Rating & Review Velocity",
            "description": "Number of new reviews added in the last 48 hours; high velocity often precedes a sales spike."
        }
    ]

    # 6. Real Time Weather/Environment Signals
    weather_environment_drivers = [
        {
            "category": "Real Time Weather/Environment Signals",
            "driver_name": "Max Temperature Forecast",
            "description": "Predicted maximum temperature for the next 3 days; critical for summer portfolio (Deos, Talc, Light Gels)."
        },
        {
            "category": "Real Time Weather/Environment Signals",
            "driver_name": "Humidity Index",
            "description": "Moisture levels in the air; triggers demand for Frizz-Control Hair products."
        },
        {
            "category": "Real Time Weather/Environment Signals",
            "driver_name": "UV Index",
            "description": "Intensity of ultraviolet radiation; direct correlation with Sunscreen and Light Gel sales."
        },
        {
            "category": "Real Time Weather/Environment Signals",
            "driver_name": "Air Quality Index (AQI)",
            "description": "Pollution levels; triggers demand for Deep Cleanse and Anti-Pollution skincare."
        }
    ]

    # 7. Real Time Competitor Data
    competitor_data_drivers = [
        {
            "category": "Real Time Competitor Data",
            "driver_name": "Competitor Price Gap",
            "description": "The monetary difference between our SKU and the nearest equivalent competitor SKU."
        },
        {
            "category": "Real Time Competitor Data",
            "driver_name": "Competitor Out-of-Stock Status",
            "description": "Flag indicating if the main competitor SKU is currently unavailable, creating a switch opportunity."
        },
        {
            "category": "Real Time Competitor Data",
            "driver_name": "Competitor Promo Intensity",
            "description": "Aggressiveness of competitor discounting (e.g., are they running a 50% off deep discount?)."
        },
        {
            "category": "Real Time Competitor Data",
            "driver_name": "Competitor New Launch Signal",
            "description": "Detection of a new competitive variant launching in the same category."
        }
    ]

    # 8. Real Time POS Data & Open Orders
    pos_data_drivers = [
        {
            "category": "Real Time POS Data & Open Orders",
            "driver_name": "Real-Time Sales Velocity",
            "description": "Units sold per hour recorded at the Point of Sale (POS) in the last 6 hours."
        },
        {
            "category": "Real Time POS Data & Open Orders",
            "driver_name": "Inventory Days on Hand (DOH)",
            "description": "Current stock level expressed in days of coverage based on current run-rate."
        },
        {
            "category": "Real Time POS Data & Open Orders",
            "driver_name": "Distributor Open Orders",
            "description": "Volume of confirmed orders from distributors that are yet to be shipped."
        },
        {
            "category": "Real Time POS Data & Open Orders",
            "driver_name": "Stock-Out Incidents",
            "description": "Count of instances where demand could not be fulfilled due to zero inventory."
        }
    ]

    # Combine all lists into one master configuration
    all_bpc_drivers = (
        consensus_demand_drivers +
        social_signals_drivers +
        marketing_spend_drivers +
        trade_promo_drivers +
        digital_shelf_drivers +
        weather_environment_drivers +
        competitor_data_drivers +
        pos_data_drivers
    )

    # Map to Products
    mock_db = {
        "PONDS_SUPER_LIGHT_GEL_100G": all_bpc_drivers,
        "DOVE_HAIR_FALL_RESCUE_650ML": all_bpc_drivers
    }
    
    return mock_db.get(sku_id, [])