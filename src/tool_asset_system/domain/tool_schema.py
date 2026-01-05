from __future__ import annotations

# =========================
# Layer dictionary (ORDER FIXED)
# =========================

LAYERS = {
    "HOLDER": {
        "label": "ホルダー",
        "sort_order": 10,
        "allow_free_category": False,
    },
    "TOOL_BODY": {
        "label": "カッターボディ",
        "sort_order": 20,
        "allow_free_category": False,
    },
    "INSERT": {
        "label": "インサート",
        "sort_order": 30,
        "allow_free_category": False,
    },
    "SOLID_TOOL": {
        "label": "ソリッド工具",
        "sort_order": 40,
        "allow_free_category": False,
    },
    "SUB_HOLDER": {
        "label": "サブホルダー",
        "sort_order": 50,
        "allow_free_category": False,
    },
    "SCREW": {
        "label": "ねじ・クランプ",
        "sort_order": 60,
        "allow_free_category": True,
    },
    "ACCESSORY": {
        "label": "付属品",
        "sort_order": 70,
        "allow_free_category": True,
    },
}

# =========================
# Category dictionary
# =========================

CATEGORIES = {
    "INSERT": {
        "MILLING_INSERT": "ミーリング用",
        "TURNING_INSERT": "旋削用",
        "DRILL_INSERT": "穴あけ用",
    },
    "TOOL_BODY": {
        "MODULAR_HEAD": "モジュラーヘッド",
        "FACE_MILL_BODY": "フェイスミル",
    },
    "SOLID_TOOL": {
        "END_MILL": "エンドミル",
        "DRILL": "ドリル",
        "REAMER": "リーマ",
    },
    "HOLDER": {
        "HSK_HOLDER": "HSKホルダー",
        "BT_HOLDER": "BTホルダー",
    },
}

# =========================
# Helpers
# =========================

def is_valid_layer(code: str) -> bool:
    return code in LAYERS

def allows_free_category(layer_code: str) -> bool:
    return LAYERS[layer_code]["allow_free_category"]

def is_valid_category(layer_code: str, category_code: str) -> bool:
    return category_code in CATEGORIES.get(layer_code, {})
