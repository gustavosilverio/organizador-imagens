"""
Camada de Serviço: ImageService
Orquestra as operações de CRUD, persistência local em JSON, integração com a Abstract Factory
para validação/leitura de arquivos, uso do Flyweight e aplicação das Strategies.
"""

import os
import json
import shutil
from typing import List, Dict, Any, Optional
from PyQt6.QtCore import QSize

from client.models.image_item import ImageItem
from client.patterns.abstract_factory import (
    ImageFormatFactorySelector,
    UnsupportedFormatException,
    InvalidImageFileException,
)
from client.patterns.flyweight import FormatFlyweightFactory
from client.patterns.strategy import (
    SortStrategy,
    FilterStrategy,
    ThumbnailRenderStrategy,
    SortByNameAscStrategy,
    FilterAllStrategy,
    SmoothThumbnailStrategy,
)
from client.services.api_client import ImageApiClient, ApiConnectionError


class ImageService:
    """
    Controlador central de regras de negócio para gerenciamento das imagens.
    Garante que os testes T10.1 a T10.4 sejam atendidos integralmente.
    """

    def __init__(self, storage_path: str = "data/catalog.json", api_client: Optional[ImageApiClient] = None):
        self.storage_path = os.path.abspath(storage_path)
        self.api_client = api_client or ImageApiClient()
        self._items: Dict[str, ImageItem] = {}
        self.flyweight_factory = FormatFlyweightFactory()

        # Estratégias padrão ativas
        self.active_sort_strategy: SortStrategy = SortByNameAscStrategy()
        self.active_filter_strategy: FilterStrategy = FilterAllStrategy()
        self.active_thumbnail_strategy: ThumbnailRenderStrategy = SmoothThumbnailStrategy()

        # Carrega dados persistidos localmente
        self._load_from_storage()

    # -----------------------------------------------------------------------
    # CRUD - Create (Importar / Cadastrar Imagem)
    # -----------------------------------------------------------------------

    def import_image(
        self,
        file_path: str,
        title: Optional[str] = None,
        description: str = "",
        tags: Optional[List[str]] = None,
    ) -> ImageItem:
        """
        Importa uma imagem para o sistema.
        Utiliza o Abstract Factory para identificar o formato, validar a integridade
        e extrair os metadados técnicos reais do arquivo.
        Lança FileNotFoundError, UnsupportedFormatException ou InvalidImageFileException
        em casos de erro (Cenário T10.2).
        """
        if not file_path or not os.path.exists(file_path):
            raise FileNotFoundError(f"O caminho do arquivo informado não existe: '{file_path}'")

        if os.path.isdir(file_path):
            raise InvalidImageFileException(f"O caminho '{file_path}' é uma pasta, selecione um arquivo de imagem.")

        # 1. Abstract Factory: Obter a fábrica compatível com o formato do arquivo
        factory = ImageFormatFactorySelector.get_factory_for_file(file_path)

        # 2. Abstract Factory: Criar leitor especializado e ler/validar imagem
        reader = factory.create_reader()
        qimage, metadata = reader.read(file_path)

        file_size = os.path.getsize(file_path)

        # 3. Criar ImageItem (associa com Flyweight do formato)
        item = ImageItem(
            file_path=file_path,
            width=metadata.get("width", qimage.width()),
            height=metadata.get("height", qimage.height()),
            file_size_bytes=file_size,
            format_name=factory.format_name,
            title=title or os.path.splitext(os.path.basename(file_path))[0],
            description=description,
            tags=tags or [],
        )

        # 4. Registrar no catálogo e persistir
        self._items[item.id] = item
        self._save_to_storage()

        # 5. Se o backend estiver online, tenta sincronizar (Upload assíncrono/opcional)
        if self.api_client.check_health():
            try:
                self.api_client.upload_image(file_path, item.to_dict())
            except ApiConnectionError:
                pass  # Permanece no modo local de forma resiliente

        return item

    # -----------------------------------------------------------------------
    # CRUD - Read (Consultar Imagens)
    # -----------------------------------------------------------------------

    def get_all_images(self) -> List[ImageItem]:
        """Retorna todas as imagens cadastradas."""
        return list(self._items.values())

    def get_image_by_id(self, image_id: str) -> Optional[ImageItem]:
        """Localiza uma imagem específica pelo identificador único."""
        return self._items.get(image_id)

    def get_processed_images(
        self,
        sort_strategy: Optional[SortStrategy] = None,
        filter_strategy: Optional[FilterStrategy] = None,
    ) -> List[ImageItem]:
        """
        Aplica a Strategy de Filtragem e a Strategy de Ordenação sobre as imagens.
        Permite trocar dinamicamente o comportamento (Cenário T10.4).
        """
        active_sort = sort_strategy or self.active_sort_strategy
        active_filter = filter_strategy or self.active_filter_strategy

        items = list(self._items.values())
        filtered = active_filter.filter(items)
        sorted_items = active_sort.sort(filtered)
        return sorted_items

    # -----------------------------------------------------------------------
    # CRUD - Update (Editar Metadados)
    # -----------------------------------------------------------------------

    def update_image_metadata(
        self,
        image_id: str,
        title: str,
        description: str = "",
        tags: Optional[List[str]] = None,
    ) -> ImageItem:
        """
        Atualiza metadados editáveis da imagem (título, descrição, tags).
        Persiste as alterações e sincroniza com o backend se disponível (Cenário T10.3).
        """
        item = self.get_image_by_id(image_id)
        if not item:
            raise KeyError(f"Imagem com ID '{image_id}' não encontrada no catálogo.")

        item.title = title.strip() or item.file_name
        item.description = description.strip()
        if tags is not None:
            item.tags = [t.strip() for t in tags if t.strip()]

        self._save_to_storage()

        if self.api_client.is_online:
            try:
                self.api_client.update_metadata(image_id, item.to_dict())
            except ApiConnectionError:
                pass

        return item

    # -----------------------------------------------------------------------
    # CRUD - Delete (Excluir Imagem)
    # -----------------------------------------------------------------------

    def delete_image(self, image_id: str) -> bool:
        """Remove a imagem do catálogo e da persistência."""
        if image_id in self._items:
            del self._items[image_id]
            self._save_to_storage()

            if self.api_client.is_online:
                try:
                    self.api_client.delete_image(image_id)
                except ApiConnectionError:
                    pass

            return True
        return False

    # -----------------------------------------------------------------------
    # Export / Download (Cenário T10.3)
    # -----------------------------------------------------------------------

    def export_image(self, image_id: str, destination_path: str) -> bool:
        """
        Exporta/copia o arquivo de imagem para o caminho de destino especificado.
        Se estiver no modo servidor e o arquivo local não estiver disponível, faz o download via API.
        """
        item = self.get_image_by_id(image_id)
        if not item:
            raise KeyError(f"Imagem com ID '{image_id}' não encontrada.")

        dest_dir = os.path.dirname(destination_path)
        if dest_dir:
            os.makedirs(dest_dir, exist_ok=True)

        if os.path.exists(item.file_path):
            shutil.copy2(item.file_path, destination_path)
            return True
        elif self.api_client.is_online:
            return self.api_client.download_image(image_id, destination_path)
        else:
            raise FileNotFoundError(f"Arquivo de origem não encontrado em '{item.file_path}'.")

    # -----------------------------------------------------------------------
    # Métricas e Estatísticas do Flyweight (Cenário T10.4)
    # -----------------------------------------------------------------------

    def get_flyweight_stats(self) -> dict:
        """Retorna estatísticas detalhadas do uso do padrão Flyweight."""
        unique_formats = len(set(item.format_name for item in self._items.values()))
        return self.flyweight_factory.get_stats(
            total_images=len(self._items),
            unique_formats_count=unique_formats if unique_formats > 0 else None
        )

    # -----------------------------------------------------------------------
    # Persistência Local em JSON (Sem dependência de SGBD externo)
    # -----------------------------------------------------------------------

    def _save_to_storage(self) -> None:
        """Persiste os metadados das imagens no arquivo JSON."""
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            data = [item.to_dict() for item in self._items.values()]
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Aviso] Falha ao salvar catálogo local: {e}")

    def _load_from_storage(self) -> None:
        """Carrega os metadados do arquivo JSON, caso exista."""
        if not os.path.exists(self.storage_path):
            return

        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for entry in data:
                        # Valida se o arquivo de imagem ainda existe no caminho apontado
                        if os.path.exists(entry.get("file_path", "")):
                            item = ImageItem.from_dict(entry)
                            self._items[item.id] = item
        except Exception as e:
            print(f"[Aviso] Falha ao carregar catálogo local: {e}")
