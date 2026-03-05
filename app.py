"""
Flask app: public site, portal (edit mode), save-content API, upload, inventory API.
Phases 3–7.
"""
import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, session

from content_store import load_content, save_content
from inventory_store import load_inventory, add_inventory_item, update_inventory_item, delete_inventory_item, get_inventory_item
from render_helpers import get_site_context

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB for uploads
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Login: only this email can access the portal
PORTAL_EMAIL = "portal@bentonvillebicyclecompany.com"


def require_login(f):
    """Redirect to login if not logged in. Use for portal pages."""
    from functools import wraps
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login", next=request.full_path))
        return f(*args, **kwargs)
    return wrapped


def require_login_api(f):
    """Return 401 if not logged in. Use for API routes."""
    from functools import wraps
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"):
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return wrapped


@app.template_filter("static_asset")
def static_asset_filter(path):
    """Use path as-is if absolute URL, else static URL."""
    if not path:
        return ""
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return url_for("static", filename=path)


# ----- Phase 3: Public site -----
@app.route("/")
def index():
    ctx = get_site_context(url_for)
    return render_template("site.html", edit_mode=False, **ctx)


# ----- Login -----
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        if email == PORTAL_EMAIL.lower():
            session["logged_in"] = True
            session["email"] = email
            next_path = request.args.get("next", "").lstrip("/")
            if next_path and not next_path.startswith("http"):
                return redirect("/" + next_path)
            return redirect(url_for("portal"))
        return render_template("login.html", error="Invalid email.")
    return render_template("login.html")


@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    return redirect(url_for("index"))


# ----- Phase 4: Portal (edit mode) -----
@app.route("/portal")
@require_login
def portal():
    ctx = get_site_context(url_for)
    return render_template("site.html", edit_mode=True, **ctx)


@app.route("/portal/inventory")
@require_login
def portal_inventory():
    """Inventory list page (portal)."""
    inventory = load_inventory()
    return render_template("portal_inventory.html", inventory=inventory)


@app.route("/portal/inventory/add", methods=["GET", "POST"])
@require_login
def portal_inventory_add():
    """Add inventory item form and submit."""
    if request.method == "POST":
        images = request.form.getlist("images")
        data = {
            "name": request.form.get("name", ""),
            "description": request.form.get("description", ""),
            "images": images,
            "price": request.form.get("price", ""),
            "category": request.form.get("category", "rental"),
            "link": request.form.get("link", ""),
            "sort_order": int(request.form.get("sort_order") or 0),
        }
        add_inventory_item(data)
        return redirect(url_for("portal_inventory"))
    return render_template("portal_inventory_form.html", item=None)


@app.route("/portal/inventory/<item_id>/edit", methods=["GET", "POST"])
@require_login
def portal_inventory_edit(item_id):
    """Edit inventory item form and submit."""
    item = get_inventory_item(item_id)
    if not item:
        return "Not found", 404
    if request.method == "POST":
        images = request.form.getlist("images")
        updates = {
            "name": request.form.get("name", ""),
            "description": request.form.get("description", ""),
            "images": images,
            "price": request.form.get("price", ""),
            "category": request.form.get("category", "rental"),
            "link": request.form.get("link", ""),
            "sort_order": int(request.form.get("sort_order") or 0),
        }
        update_inventory_item(item_id, updates)
        return redirect(url_for("portal_inventory"))
    return render_template("portal_inventory_form.html", item=item)


@app.route("/portal/inventory/<item_id>/delete", methods=["POST"])
@require_login
def portal_inventory_delete(item_id):
    """Delete inventory item and redirect to list."""
    try:
        delete_inventory_item(item_id)
    except KeyError:
        pass
    return redirect(url_for("portal_inventory"))


# ----- Phase 5: Save content API -----
@app.route("/api/save-content", methods=["POST"])
@require_login_api
def api_save_content():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Invalid or missing JSON"}), 400
    try:
        save_content(data)
        return jsonify({"success": True, "message": "Saved"})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app.logger.exception("Save failed")
        return jsonify({"error": "Failed to save"}), 500


# ----- Phase 6: Image upload -----
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/api/upload-image", methods=["POST"])
@require_login_api
def api_upload_image():
    if "file" not in request.files and "image" not in request.files:
        return jsonify({"error": "No file"}), 400
    file = request.files.get("file") or request.files.get("image")
    if not file or file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400
    import uuid
    ext = file.filename.rsplit(".", 1)[1].lower()
    if ext == "jpeg":
        ext = "jpg"
    safe_name = f"{uuid.uuid4().hex}.{ext}"
    path_in_static = os.path.join("uploads", safe_name)
    full_path = os.path.join(app.static_folder, "uploads", safe_name)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    try:
        file.save(full_path)
        return jsonify({"path": path_in_static.replace("\\", "/"), "url": url_for("static", filename=path_in_static.replace("\\", "/"))})
    except Exception as e:
        app.logger.exception("Upload failed")
        return jsonify({"error": "Upload failed"}), 500


# ----- Phase 7: Inventory API -----
@app.route("/api/inventory", methods=["GET"])
@require_login_api
def api_inventory_list():
    items = load_inventory()
    return jsonify(items)


@app.route("/api/inventory", methods=["POST"])
@require_login_api
def api_inventory_add():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400
    try:
        item = add_inventory_item(data)
        return jsonify(item), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/inventory/<item_id>", methods=["GET"])
@require_login_api
def api_inventory_get(item_id):
    item = get_inventory_item(item_id)
    if not item:
        return jsonify({"error": "Not found"}), 404
    return jsonify(item)


@app.route("/api/inventory/<item_id>", methods=["PUT", "PATCH"])
@require_login_api
def api_inventory_update(item_id):
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400
    try:
        item = update_inventory_item(item_id, data)
        return jsonify(item)
    except KeyError as e:
        return jsonify({"error": str(e)}), 404


@app.route("/api/inventory/<item_id>", methods=["DELETE"])
@require_login_api
def api_inventory_delete(item_id):
    try:
        delete_inventory_item(item_id)
        return jsonify({"deleted": True})
    except KeyError:
        return jsonify({"error": "Not found"}), 404


if __name__ == "__main__":
    app.run(debug=True, port=5000)
