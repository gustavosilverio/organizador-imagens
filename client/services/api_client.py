"""
Camada de Integração de Rede: ImageApiClient
Responsável pela comunicação HTTP REST com o futuro servidor backend Flask.
Trata timeouts, desconexões e erros de rede de maneira resiliente.
"""

import os
from typing import List, Dict, Any, Optional
import requests


class ApiConnectionError(Exception):
    """Exceção levantada quando o servidor Flask não está acessível."""
    pass


class ImageApiClient:
    """
    Cliente REST HTTP para conexão com a API Flask do Organizador de Imagens.
    Endpoints previstos:
      - GET    /api/health            (Verificação de status)
      - GET    /api/images            (Listagem de imagens)
      - GET    /api/images/<id>       (Detalhes da imagem)
      - POST   /api/images            (Upload de imagem com metadados)
      - PUT    /api/images/<id>       (Atualização de metadados)
      - DELETE /api/images/<id>       (Exclusão)
      - GET    /api/images/<id>/file  (Download do arquivo binário)
    """

    def __init__(self, base_url: str = "http://127.0.0.1:5000/api", timeout_seconds: float = 2.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout_seconds
        self._is_online = False

    @property
    def is_online(self) -> bool:
        return self._is_online

    def check_health(self) -> bool:
        """Verifica se o backend Flask está ativo e respondendo."""
        try:
            resp = requests.get(f"{self.base_url}/health", timeout=self.timeout)
            self._is_online = (resp.status_code == 200)
            return self._is_online
        except Exception:
            self._is_online = False
            return False

    def list_images(self) -> List[Dict[str, Any]]:
        """Consulta listagem de imagens cadastradas no backend."""
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
        """Envia um arquivo de imagem e seus metadados ao servidor via multipart/form-data."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Arquivo local não encontrado: {file_path}")

        try:
            with open(file_path, "rb") as f:
                files = {"file": (os.path.basename(file_path), f)}
                data = {
                    "title": metadata.get("title", ""),
                    "description": metadata.get("description", ""),
                    "tags": ",".join(metadata.get("tags", [])),
                }
                resp = requests.post(f"{self.base_url}/images", files=files, data=data, timeout=self.timeout)

            if resp.status_code in (200, 201):
                self._is_online = True
                return resp.json()
            raise ApiConnectionError(f"Falha no upload: status {resp.status_code} - {resp.text}")
        except requests.exceptions.RequestException as e:
            self._is_online = False
            raise ApiConnectionError(f"Erro de conexão no upload: {e}")

    def update_metadata(self, image_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Atualiza os metadados de uma imagem no servidor (PUT)."""
        try:
            resp = requests.put(f"{self.base_url}/images/{image_id}", json=metadata, timeout=self.timeout)
            if resp.status_code == 200:
                self._is_online = True
                return resp.json()
            raise ApiConnectionError(f"Falha na atualização: status {resp.status_code}")
        except requests.exceptions.RequestException as e:
            self._is_online = False
            raise ApiConnectionError(f"Erro de conexão na atualização: {e}")

    def delete_image(self, image_id: str) -> bool:
        """Exclui uma imagem no servidor (DELETE)."""
        try:
            resp = requests.delete(f"{self.base_url}/images/{image_id}", timeout=self.timeout)
            if resp.status_code in (200, 204):
                self._is_online = True
                return True
            return False
        except requests.exceptions.RequestException as e:
            self._is_online = False
            raise ApiConnectionError(f"Erro de conexão na exclusão: {e}")

    def download_image(self, image_id: str, destination_path: str) -> bool:
        """Baixa o arquivo binário da imagem do servidor para o disco local."""
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
