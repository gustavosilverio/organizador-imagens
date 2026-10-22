import os
import json
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
DATA_FILE = os.path.join(BASE_DIR, "data", "server_catalog.json")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

images_db = {}


def load_data():
    global images_db
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                images_db = json.load(f)
        except Exception:
            images_db = {}


def save_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(images_db, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


load_data()


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "online",
        "service": "Image Organizer Backend",
        "total_images": len(images_db),
        "timestamp": datetime.now().isoformat()
    }), 200


@app.route("/api/images", methods=["GET"])
def list_images():
    return jsonify(list(images_db.values())), 200


@app.route("/api/images/<image_id>", methods=["GET"])
def get_image(image_id):
    item = images_db.get(image_id)
    if not item:
        return jsonify({"error": "Imagem nao encontrada"}), 404
    return jsonify(item), 200


@app.route("/api/images", methods=["POST"])
def upload_image():
    if "file" not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Nome de arquivo vazio"}), 400

    filename = secure_filename(file.filename)
    image_id = str(uuid.uuid4())
    stored_filename = f"{image_id}_{filename}"
    save_path = os.path.join(UPLOAD_FOLDER, stored_filename)
    file.save(save_path)

    title = request.form.get("title") or os.path.splitext(filename)[0]
    file_size = os.path.getsize(save_path)
    ext = os.path.splitext(filename)[1].lower()
    fmt = "PNG" if ext == ".png" else ("BMP" if ext == ".bmp" else "JPEG")

    item = {
        "id": image_id,
        "file_path": save_path,
        "file_name": filename,
        "stored_name": stored_filename,
        "width": 0,
        "height": 0,
        "file_size_bytes": file_size,
        "format": fmt,
        "title": title,
    }

    images_db[image_id] = item
    save_data()

    return jsonify(item), 201


@app.route("/api/images/<image_id>", methods=["PUT"])
def update_image(image_id):
    item = images_db.get(image_id)
    if not item:
        return jsonify({"error": "Imagem nao encontrada"}), 404

    data = request.get_json(force=True, silent=True) or {}
    if "title" in data:
        item["title"] = data["title"].strip() or item["file_name"]

    save_data()
    return jsonify(item), 200


@app.route("/api/images/<image_id>", methods=["DELETE"])
def delete_image(image_id):
    item = images_db.pop(image_id, None)
    if not item:
        return jsonify({"error": "Imagem nao encontrada"}), 404

    stored_path = os.path.join(UPLOAD_FOLDER, item.get("stored_name", ""))
    if os.path.exists(stored_path):
        try:
            os.remove(stored_path)
        except Exception:
            pass

    save_data()
    return jsonify({"success": True}), 200


@app.route("/api/images/<image_id>/file", methods=["GET"])
def download_image_file(image_id):
    item = images_db.get(image_id)
    if not item:
        return jsonify({"error": "Imagem nao encontrada"}), 404

    stored_path = os.path.join(UPLOAD_FOLDER, item.get("stored_name", ""))
    if not os.path.exists(stored_path):
        return jsonify({"error": "Arquivo nao encontrado"}), 404

    return send_file(stored_path, as_attachment=True, download_name=item["file_name"])


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
