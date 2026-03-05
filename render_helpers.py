"""Phase 2: Build template context (content + resolved section cards)."""
from content_store import load_content
from inventory_store import load_inventory


def _image_url(path, url_for_static=None):
    """Return path if absolute URL, else static URL. url_for_static('static', filename=x) if provided."""
    if not path:
        return ""
    if path.startswith("http://") or path.startswith("https://"):
        return path
    if url_for_static:
        return url_for_static("static", filename=path)
    return "/static/" + path.lstrip("/")


def get_rental_cards(content, inventory_list, url_for_static=None):
    """Build list of rental card dicts from content (manual cards or inventory)."""
    section = content.get("rental_section") or {}
    use_inventory = section.get("use_inventory") is True
    inventory_ids = section.get("inventory_ids") or []
    category = section.get("inventory_category") or "rental"
    max_items = section.get("max_items") or 6
    manual_cards = section.get("cards") or []

    if use_inventory and inventory_ids:
        # Ordered list of ids
        cards = []
        for iid in inventory_ids:
            for it in inventory_list:
                if it.get("id") == iid:
                    cards.append({
                        "image": _image_url(it.get("image", ""), url_for_static),
                        "title": it.get("name", ""),
                        "description": it.get("description", ""),
                        "href": it.get("link") or "#",
                    })
                    break
        return cards

    if use_inventory and inventory_list:
        # By category, take first max_items
        filtered = [it for it in inventory_list if it.get("category") == category]
        filtered.sort(key=lambda x: (x.get("sort_order", 0), x.get("name", "")))
        return [
            {
                "image": _image_url(it.get("image", ""), url_for_static),
                "title": it.get("name", ""),
                "description": it.get("description", ""),
                "href": it.get("link") or "#",
            }
            for it in filtered[:max_items]
        ]

    # Manual cards
    return [
        {
            "image": _image_url(c.get("image", ""), url_for_static),
            "title": c.get("title", ""),
            "description": c.get("description", ""),
            "href": c.get("href", "#"),
        }
        for c in manual_cards
    ]


def get_site_context(url_for_static=None):
    """Load content and inventory, resolve rental cards, return dict for template.
    url_for_static: callable like Flask's url_for('static', filename=path) for building image URLs.
    """
    content = load_content()
    inventory_list = load_inventory()
    rental_cards = get_rental_cards(content, inventory_list, url_for_static)
    return {
        "content": content,
        "rental_cards": rental_cards,
    }
