import os
from typing import List, Dict, Any
import requests


class ApiConnectionError(Exception):
    pass


class ImageApiClient:
    def __init__(self, base_url: str = "http://127.0.0.1:5000/api", timeout_seconds: float = 2.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout_seconds
        self._is_online = False

    @property
    def is_online(self) -> bool:
        return self._is_online

    def check_health(self) -> bool:
        try:
            resp = requests.get(f"{self.base_url}/health", timeout=self.timeout)
            self._is_online = (resp.status_code == 200)
            return self._is_online
        except Exception:
            self._is_online = False
            return False

    def list_images(self) -> List[Dict[str, Any]]:
        try:
            resp = requests.get(f"{self.base_url}/images", timeout=self.timeout)
            if resp.status_code == 200:
                self._is_online = True
                return resp.json()
            return []
        except Exception as e:
            self._is_online = False
            raise ApiConnectionError(f"Erro ao listar imagens no backend: {e}")

    def upload_image(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Arquivo local nao encontrado: {file_path}")

        try:
            with open(file_path, "rb") as f:
                files = {"file": (os.path.basename(file_path), f)}
                data = {
                    "title": metadata.get("title", ""),
                }
                resp = requests.post(f"{self.base_url}/images", files=files, data=data, timeout=self.timeout)

            if resp.status_code in (200, 201):
                self._is_online = True
                return resp.json()
            raise ApiConnectionError(f"Falha no upload: status {resp.status_code}")
        except requests.exceptions.RequestException as e:
            self._is_online = False
            raise ApiConnectionError(f"Erro de conexao no upload: {e}")

    def update_metadata(self, image_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        try:
            resp = requests.put(f"{self.base_url}/images/{image_id}", json=metadata, timeout=self.timeout)
            if resp.status_code == 200:
                self._is_online = True
                return resp.json()
            raise ApiConnectionError(f"Falha na atualizacao: status {resp.status_code}")
        except requests.exceptions.RequestException as e:
            self._is_online = False
            raise ApiConnectionError(f"Erro de conexao na atualizacao: {e}")

    def delete_image(self, image_id: str) -> bool:
        try:
            resp = requests.delete(f"{self.base_url}/images/{image_id}", timeout=self.timeout)
            if resp.status_code in (200, 204):
                self._is_online = True
                return True
            return False
        except requests.exceptions.RequestException as e:
            self._is_online = False
            raise ApiConnectionError(f"Erro de conexao na exclusao: {e}")

    def download_image(self, image_id: str, destination_path: str) -> bool:
        try:
            resp = requests.get(f"{self.base_url}/images/{image_id}/file", stream=True, timeout=self.timeout)
            if resp.status_code == 200:
                with open(destination_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                self._is_online = True
                return True
            return False
        except requests.exceptions.RequestException as e:
            self._is_online = False
            raise ApiConnectionError(f"Erro ao baixar arquivo do servidor: {e}")
