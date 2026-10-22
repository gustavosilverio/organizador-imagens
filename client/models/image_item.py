import os
import uuid
from typing import Dict, Any, Optional
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QSize

from client.patterns.flyweight import ImageFormatFlyweight, FormatFlyweightFactory
from client.patterns.strategy import ThumbnailRenderStrategy


class ImageItem:
    def __init__(
        self,
        file_path: str,
        width: int,
        height: int,
        file_size_bytes: int,
        format_name: str,
        title: Optional[str] = None,
        image_id: Optional[str] = None,
    ):
        self.id: str = image_id or str(uuid.uuid4())
        self.file_path: str = os.path.abspath(file_path)
        self.file_name: str = os.path.basename(file_path)
        self.width: int = width
        self.height: int = height
        self.file_size_bytes: int = file_size_bytes
        self.title: str = title or os.path.splitext(self.file_name)[0]

        self.flyweight: ImageFormatFlyweight = FormatFlyweightFactory().get_flyweight(format_name)
        self._cached_thumbnail: Optional[QPixmap] = None
        self._cached_strategy_name: Optional[str] = None

    @property
    def format_name(self) -> str:
        return self.flyweight.format_name

    @property
    def dimensions_text(self) -> str:
        return f"{self.width}x{self.height}"

    @property
    def size_formatted(self) -> str:
        kb = self.file_size_bytes / 1024.0
        return f"{kb:.1f} KB"

    def load_full_pixmap(self) -> QPixmap:
        if not os.path.exists(self.file_path):
            return QPixmap()
        return QPixmap(self.file_path)

    def get_thumbnail(self, strategy: ThumbnailRenderStrategy, target_size: QSize) -> QPixmap:
        if (
            self._cached_thumbnail is not None
            and self._cached_strategy_name == strategy.name
            and not self._cached_thumbnail.isNull()
        ):
            return self._cached_thumbnail

        original = self.load_full_pixmap()
        rendered = strategy.render(original, target_size)
        self._cached_thumbnail = rendered
        self._cached_strategy_name = strategy.name
        return rendered

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "file_path": self.file_path,
            "file_name": self.file_name,
            "width": self.width,
            "height": self.height,
            "file_size_bytes": self.file_size_bytes,
            "format": self.format_name,
            "title": self.title,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ImageItem":
        return cls(
            file_path=data.get("file_path", ""),
            width=data.get("width", 0),
            height=data.get("height", 0),
            file_size_bytes=data.get("file_size_bytes", 0),
            format_name=data.get("format", "JPEG"),
            title=data.get("title"),
            image_id=data.get("id"),
        )
