from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

# Key = (SKU_ID, LOCATION_ID)
MOCK_PRODUCT_MASTER_DATA: Dict[Tuple[str, str], Dict[str, Any]] = {
    ("PONDS_SUPER_LIGHT_GEL_100G", "BANGALORE"): {
        "sku_name": "Ponds Super Light Gel 100g",
        "category": "Skin Care",
        "sub_category": "Face Moisturizers",
        "abc_class": "A",  # High Revenue Generator
        "xyz_class": "Y",  # Medium Volatility (Sensitive to Summer/Heat)
        "unit_price": 299,
        "currency": "INR",
        "description": "Oil-free moisturizer, high traction on Quick Commerce.",
    },
    ("DOVE_HAIR_FALL_RESCUE_650ML", "BANGALORE"): {
        "sku_name": "Dove Hair Fall Rescue Shampoo 650ml",
        "category": "Hair Care",
        "sub_category": "Shampoos",
        "abc_class": "A",  # High Revenue Generator
        "xyz_class": "Y",  # Medium Volatility (Sensitive to Weekend Shopping)
        "unit_price": 650,
        "currency": "INR",
        "description": "Large pack, typically planned purchase but high volume.",
    },
}


def get_product_master_data(sku_id: str, location_id: str) -> Optional[Dict[str, Any]]:
    """
    Returns ABC/XYZ classification and price for a specific Location.
    """
    sku_id = (sku_id or "").strip().upper()
    location_id = (location_id or "").strip().upper()
    return MOCK_PRODUCT_MASTER_DATA.get((sku_id, location_id))


def list_product_master_data(location_id: str) -> List[Dict[str, Any]]:
    """
    Returns all product master data entries for a location.
    Each entry includes sku_id and location_id.
    """
    location_id = (location_id or "").strip().upper()
    out: List[Dict[str, Any]] = []
    for (sku_id, loc), data in MOCK_PRODUCT_MASTER_DATA.items():
        if loc != location_id:
            continue
        row = {"sku_id": sku_id, "location_id": loc}
        row.update(data)
        out.append(row)
    return out


def find_skus_by_class(
    location_id: str,
    *,
    abc_class: Optional[str] = None,
    xyz_classes: Optional[Sequence[str]] = None,
) -> List[str]:
    """
    Convenience selector for SKUs by ABC/XYZ classes at a location.
    """
    abc_class_u = abc_class.strip().upper() if abc_class else None
    xyz_set = {c.strip().upper() for c in xyz_classes} if xyz_classes else None

    skus: List[str] = []
    for row in list_product_master_data(location_id):
        if abc_class_u and row.get("abc_class") != abc_class_u:
            continue
        if xyz_set and row.get("xyz_class") not in xyz_set:
            continue
        skus.append(str(row["sku_id"]))
    return skus


__all__ = [
    "MOCK_PRODUCT_MASTER_DATA",
    "get_product_master_data",
    "list_product_master_data",
    "find_skus_by_class",
]