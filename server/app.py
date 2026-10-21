"""
Módulo do Servidor: Backend Flask
Organizador de Imagens (Projeto 10)
Não utiliza banco de dados externo nem serviços de terceiros (atende estritamente às orientações acadêmicas).
Armazena metadados em arquivo JSON local e arquivos enviados na pasta de uploads.
"""

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

# Armazenamento em memória com sincronização em JSON (sem banco de dados externo)
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
    except Exception as e:
        print(f"Erro ao salvar dados do servidor: {e}")


load_data()


@app.route("/api/health", methods=["GET"])
def health_check():
    """Verificação de integridade do servidor."""
    return jsonify({
        "status": "online",
        "service": "Image Organizer Backend",
        "total_images": len(images_db),
        "timestamp": datetime.now().isoformat()
    }), 200


@app.route("/api/images", methods=["GET"])
def list_images():
    """Listagem de todas as imagens cadastradas."""
    return jsonify(list(images_db.values())), 200


@app.route("/api/images/<image_id>", methods=["GET"])
def get_image(image_id):
    """Consulta de uma imagem específica."""
    item = images_db.get(image_id)
    if not item:
        return jsonify({"error": "Imagem não encontrada"}), 404
    return jsonify(item), 200


@app.route("/api/images", methods=["POST"])
def upload_image():
    """Upload de arquivo de imagem com metadados."""
    if "file" not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado no campo 'file'"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Nome de arquivo vazio"}), 400

    filename = secure_filename(file.filename)
    image_id = str(uuid.uuid4())
    stored_filename = f"{image_id}_{filename}"
    save_path = os.path.join(UPLOAD_FOLDER, stored_filename)
    file.save(save_path)

    title = request.form.get("title") or os.path.splitext(filename)[0]
    description = request.form.get("description", "")
    tags_raw = request.form.get("tags", "")
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else []

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
        "description": description,
        "tags": tags,
        "date_modified": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    images_db[image_id] = item
    save_data()

    return jsonify(item), 201


@app.route("/api/images/<image_id>", methods=["PUT"])
def update_image(image_id):
    """Atualização dos metadados de uma imagem."""
    item = images_db.get(image_id)
    if not item:
        return jsonify({"error": "Imagem não encontrada"}), 404

    data = request.get_json(force=True, silent=True) or {}
    if "title" in data:
        item["title"] = data["title"].strip() or item["file_name"]
    if "description" in data:
        item["description"] = data["description"].strip()
    if "tags" in data and isinstance(data["tags"], list):
        item["tags"] = [str(t).strip() for t in data["tags"] if str(t).strip()]

    save_data()
    return jsonify(item), 200


@app.route("/api/images/<image_id>", methods=["DELETE"])
def delete_image(image_id):
    """Exclusão de imagem e arquivo do servidor."""
    item = images_db.pop(image_id, None)
    if not item:
        return jsonify({"error": "Imagem não encontrada"}), 404

    stored_path = os.path.join(UPLOAD_FOLDER, item.get("stored_name", ""))
    if os.path.exists(stored_path):
        try:
            os.remove(stored_path)
        except Exception:
            pass

    save_data()
    return jsonify({"success": True, "message": f"Imagem {image_id} removida"}), 200


@app.route("/api/images/<image_id>/file", methods=["GET"])
def download_image_file(image_id):
    """Download do arquivo binário da imagem."""
    item = images_db.get(image_id)
    if not item:
        return jsonify({"error": "Imagem não encontrada"}), 404

    stored_path = os.path.join(UPLOAD_FOLDER, item.get("stored_name", ""))
    if not os.path.exists(stored_path):
        return jsonify({"error": "Arquivo físico não encontrado no servidor"}), 404

    return send_file(stored_path, as_attachment=True, download_name=item["file_name"])


if __name__ == "__main__":
    print("Iniciando Servidor Flask do Organizador de Imagens...")
    print("Endpoints em http://127.0.0.1:5000/api")
    app.run(host="127.0.0.1", port=5000, debug=True)
