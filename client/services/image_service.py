import os
import json
import shutil
from typing import List, Dict, Optional

from client.models.image_item import ImageItem
from client.patterns.abstract_factory import (
    ImageFormatFactorySelector,
    UnsupportedFormatException,
    InvalidImageFileException,
)
from client.patterns.flyweight import FormatFlyweightFactory
from client.patterns.strategy import (
    SortStrategy,
    ThumbnailRenderStrategy,
    SortByNameAscStrategy,
    SmoothThumbnailStrategy,
)
from client.services.api_client import ImageApiClient, ApiConnectionError


class ImageService:
    def __init__(self, storage_path: str = "data/catalog.json", api_client: Optional[ImageApiClient] = None):
        self.storage_path = os.path.abspath(storage_path)
        self.api_client = api_client or ImageApiClient()
        self._items: Dict[str, ImageItem] = {}
        self.flyweight_factory = FormatFlyweightFactory()
        self.active_sort_strategy: SortStrategy = SortByNameAscStrategy()
        self.active_thumbnail_strategy: ThumbnailRenderStrategy = SmoothThumbnailStrategy()
        self._load_from_storage()

    def import_image(
        self,
        file_path: str,
        title: Optional[str] = None,
        description: str = "",
        tags: Optional[List[str]] = None,
    ) -> ImageItem:
        if not file_path or not os.path.exists(file_path):
            raise FileNotFoundError(f"Arquivo nao encontrado: '{file_path}'")

        if os.path.isdir(file_path):
            raise InvalidImageFileException(f"O caminho '{file_path}' e uma pasta.")

        factory = ImageFormatFactorySelector.get_factory_for_file(file_path)
        reader = factory.create_reader()
        qimage, metadata = reader.read(file_path)

        file_size = os.path.getsize(file_path)
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

        self._items[item.id] = item
        self._save_to_storage()

        if self.api_client.check_health():
            try:
                self.api_client.upload_image(file_path, item.to_dict())
            except ApiConnectionError:
                pass

        return item

    def get_all_images(self) -> List[ImageItem]:
        return list(self._items.values())

    def get_image_by_id(self, image_id: str) -> Optional[ImageItem]:
        return self._items.get(image_id)

    def get_sorted_images(self, sort_strategy: Optional[SortStrategy] = None) -> List[ImageItem]:
        active_sort = sort_strategy or self.active_sort_strategy
        return active_sort.sort(list(self._items.values()))

    def update_image_metadata(
        self,
        image_id: str,
        title: str,
        description: str = "",
        tags: Optional[List[str]] = None,
    ) -> ImageItem:
        item = self.get_image_by_id(image_id)
        if not item:
            raise KeyError(f"Imagem '{image_id}' nao encontrada.")

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

    def delete_image(self, image_id: str) -> bool:
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

    def export_image(self, image_id: str, destination_path: str) -> bool:
        item = self.get_image_by_id(image_id)
        if not item:
            raise KeyError(f"Imagem '{image_id}' nao encontrada.")

        dest_dir = os.path.dirname(destination_path)
        if dest_dir:
            os.makedirs(dest_dir, exist_ok=True)

        if os.path.exists(item.file_path):
            shutil.copy2(item.file_path, destination_path)
            return True
        elif self.api_client.is_online:
            return self.api_client.download_image(image_id, destination_path)
        else:
            raise FileNotFoundError(f"Arquivo de origem nao encontrado: '{item.file_path}'.")

    def get_flyweight_stats(self) -> dict:
        unique_formats = len(set(item.format_name for item in self._items.values()))
        return self.flyweight_factory.get_stats(
            total_images=len(self._items),
            unique_formats_count=unique_formats if unique_formats > 0 else None
        )

    def _save_to_storage(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            data = [item.to_dict() for item in self._items.values()]
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _load_from_storage(self) -> None:
        if not os.path.exists(self.storage_path):
            return

        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for entry in data:
                        if os.path.exists(entry.get("file_path", "")):
                            item = ImageItem.from_dict(entry)
                            self._items[item.id] = item
        except Exception:
            pass
