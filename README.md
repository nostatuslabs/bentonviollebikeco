# Bentonville Bike Co – Editable Site + Portal

Static site driven by `data/content.json`, editable via the **portal**. Phases 1–7 implemented.

## Run the app

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the Flask server**
   ```bash
   python app.py
   ```
   Or: `flask --app app run` (with `FLASK_APP=app`).

3. **Open in browser**
   - **Public site:** http://127.0.0.1:5000/
   - **Portal (edit mode):** http://127.0.0.1:5000/portal
   - **Inventory:** http://127.0.0.1:5000/portal/inventory

## What’s included

- **Phase 1:** `data/content.json` and `data/inventory.json`; `content_store.py` and `inventory_store.py` (load/save).
- **Phase 2:** `templates/site.html` (Jinja) and `render_helpers.py` (rental cards from content or inventory).
- **Phase 3:** Flask app; `/` serves the public site; CSS/images in `static/`.
- **Phase 4:** `/portal` renders the same template with `edit_mode=True` (contenteditable, Save buttons, “Change image”).
- **Phase 5:** `POST /api/save-content` saves JSON and the next load of `/` shows updated content.
- **Phase 6:** `POST /api/upload-image` uploads to `static/uploads/`; portal “Change image” uses it.
- **Phase 7:** Inventory CRUD: `/portal/inventory`, add/edit/delete; rental section can “Use inventory” by category; resolver builds `rental_cards` from inventory when enabled.

## Portal usage

1. Go to **/portal**.
2. Edit text in place (contenteditable) and use **Change image** on hero, promo tiles, brands, map.
3. In **Rental** section: check “Use inventory” and set category (e.g. `rental`); open **Inventory** to add items with that category.
4. Click **Save** (top or bottom); content is written to `data/content.json` and the live site updates.

Auth (Phase 8) is not implemented; add protection before exposing the portal.
