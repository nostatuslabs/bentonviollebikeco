"""Phase 1: Load and save site content from JSON."""
import json
import os

# Path relative to project root
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CONTENT_PATH = os.path.join(DATA_DIR, "content.json")

REQUIRED_KEYS = [
    "topbar", "header", "hero", "intro", "promo_strip", "quick_links",
    "brands", "rental_section", "ride_to_buy", "visit", "footer"
]


def get_default_content():
    """Return minimal default content when file is missing."""
    return {
        "meta": {"title": "Bentonville Bike Co | Bike Shop | Rentals | Sales"},
        "topbar": {"visible": True, "promo": "", "phone": "", "address": "", "email": ""},
        "header": {"logo_line1": "", "logo_line2": "", "logo_href": "#", "nav_items": []},
        "hero": {
            "background_image": "", "tagline": "", "title": "",
            "button1_text": "", "button1_href": "#", "button2_text": "", "button2_href": "#"
        },
        "intro": {"heading": "", "lead": "", "paragraphs": [], "hours": ""},
        "promo_strip": {"title": "", "tiles": []},
        "quick_links": [],
        "brands": {"title": "", "logos": []},
        "rental_section": {
            "title": "", "use_inventory": False, "inventory_ids": [],
            "inventory_category": "rental", "max_items": 6, "cards": []
        },
        "ride_to_buy": {"heading": "", "tagline": "", "button_text": "", "button_href": "#"},
        "visit": {
            "title": "", "hours": "", "address_block": "", "links": [],
            "phone": "", "cta_text": "", "cta_href": "#", "map_image": ""
        },
        "footer": {"columns": [], "address_block": "", "newsletter_heading": "", "copyright": ""},
    }


def load_content():
    """Load content from content.json. Returns default if file missing or invalid."""
    if not os.path.isfile(CONTENT_PATH):
        return get_default_content()
    try:
        with open(CONTENT_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Ensure required keys exist
        default = get_default_content()
        for key in REQUIRED_KEYS:
            if key not in data:
                data[key] = default.get(key, {} if key != "quick_links" else [])
        if "meta" not in data:
            data["meta"] = default["meta"]
        return data
    except (json.JSONDecodeError, IOError):
        return get_default_content()


def save_content(content):
    """Validate and save content to content.json. Raises ValueError on invalid data."""
    if not isinstance(content, dict):
        raise ValueError("Content must be a dict")
    for key in REQUIRED_KEYS:
        if key not in content:
            raise ValueError(f"Missing required key: {key}")
    os.makedirs(DATA_DIR, exist_ok=True)
    # Atomic write: temp then rename
    tmp_path = CONTENT_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(content, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, CONTENT_PATH)
