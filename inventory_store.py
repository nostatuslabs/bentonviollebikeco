"""Phase 1: Load and save inventory (items) from JSON."""
import json
import os
import uuid

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
INVENTORY_PATH = os.path.join(DATA_DIR, "inventory.json")
MAX_IMAGES = 8


def _normalize_images(images):
    """Return list of image paths, max MAX_IMAGES."""
    if not images:
        return []
    if isinstance(images, str):
        images = [images] if images.strip() else []
    return [str(p).strip() for p in images if p and str(p).strip()][:MAX_IMAGES]


def load_inventory():
    """Load inventory list from inventory.json. Returns [] if missing or invalid."""
    if not os.path.isfile(INVENTORY_PATH):
        return []
    try:
        with open(INVENTORY_PATH, "r", encoding="utf-8") as f:
            items = json.load(f)
        for it in items:
            if "images" not in it and it.get("image"):
                it["images"] = [it["image"]]
        return items
    except (json.JSONDecodeError, IOError):
        return []


def _save_inventory(items):
    """Write inventory list to disk."""
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp_path = INVENTORY_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, INVENTORY_PATH)


def add_inventory_item(item):
    """Add a new item. Generates id. Supports 'image' or 'images' (max MAX_IMAGES)."""
    items = load_inventory()
    new_id = str(uuid.uuid4())
    images = _normalize_images(item.get("images") or item.get("image") or [])
    primary = images[0] if images else item.get("image", "")
    new_item = {
        "id": new_id,
        "name": item.get("name", ""),
        "image": primary,
        "images": images,
        "description": item.get("description", ""),
        "price": item.get("price", ""),
        "category": item.get("category", "rental"),
        "link": item.get("link", ""),
        "sort_order": item.get("sort_order", 0),
    }
    items.append(new_item)
    _save_inventory(items)
    return new_item


def update_inventory_item(item_id, updates):
    """Update item by id. Accepts 'images' (max MAX_IMAGES); sets 'image' to first."""
    items = load_inventory()
    for i, it in enumerate(items):
        if it.get("id") == item_id:
            if "images" in updates:
                images = _normalize_images(updates["images"])
                items[i]["images"] = images
                items[i]["image"] = images[0] if images else ""
            for key in ("name", "description", "price", "category", "link", "sort_order"):
                if key in updates:
                    items[i][key] = updates[key]
            if "image" in updates and "images" not in updates:
                items[i]["image"] = updates["image"]
                if not items[i].get("images"):
                    items[i]["images"] = [updates["image"]] if updates.get("image") else []
            _save_inventory(items)
            return items[i]
    raise KeyError(f"Inventory item not found: {item_id}")


def delete_inventory_item(item_id):
    """Remove item by id. Raises KeyError if not found."""
    items = load_inventory()
    for i, it in enumerate(items):
        if it.get("id") == item_id:
            items.pop(i)
            _save_inventory(items)
            return
    raise KeyError(f"Inventory item not found: {item_id}")


def get_inventory_item(item_id):
    """Get one item by id. Returns None if not found."""
    for it in load_inventory():
        if it.get("id") == item_id:
            return it
    return None
