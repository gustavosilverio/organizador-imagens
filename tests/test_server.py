"""
Testes Unitários para o Módulo Servidor (Flask API).
Verifica os endpoints REST:
  - GET    /api/health
  - GET    /api/images
  - POST   /api/images
  - PUT    /api/images/<id>
  - DELETE /api/images/<id>
  - GET    /api/images/<id>/file
"""

import io
import pytest
from server.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_server_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "online"


def test_server_crud_lifecycle(client):
    # 1. Upload
    image_content = b"\x89PNG\r\n\x1a\nFakePngContentForServerTest"
    data = {
        "file": (io.BytesIO(image_content), "test_art.png"),
        "title": "Arte Abstrata",
        "description": "Uma imagem gerada para testes",
        "tags": "teste, servidor, flask"
    }
    post_resp = client.post("/api/images", data=data, content_type="multipart/form-data")
    assert post_resp.status_code == 201
    created_item = post_resp.get_json()
    image_id = created_item["id"]
    assert created_item["title"] == "Arte Abstrata"

    # 2. Get list
    list_resp = client.get("/api/images")
    assert list_resp.status_code == 200
    images = list_resp.get_json()
    assert any(x["id"] == image_id for x in images)

    # 3. Get single
    get_resp = client.get(f"/api/images/{image_id}")
    assert get_resp.status_code == 200
    assert get_resp.get_json()["title"] == "Arte Abstrata"

    # 4. Update
    put_data = {"title": "Arte Abstrata Editada", "tags": ["novo", "update"]}
    put_resp = client.put(f"/api/images/{image_id}", json=put_data)
    assert put_resp.status_code == 200
    assert put_resp.get_json()["title"] == "Arte Abstrata Editada"

    # 5. Download file
    file_resp = client.get(f"/api/images/{image_id}/file")
    assert file_resp.status_code == 200
    assert file_resp.data == image_content

    # 6. Delete
    del_resp = client.delete(f"/api/images/{image_id}")
    assert del_resp.status_code == 200

    # 7. Verify deletion
    verify_resp = client.get(f"/api/images/{image_id}")
    assert verify_resp.status_code == 404
