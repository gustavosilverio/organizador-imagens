import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
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
        description: str = "",
        tags: Optional[List[str]] = None,
        date_modified: Optional[str] = None,
        image_id: Optional[str] = None,
    ):
        self.id: str = image_id or str(uuid.uuid4())
        self.file_path: str = os.path.abspath(file_path)
        self.file_name: str = os.path.basename(file_path)
        self.width: int = width
        self.height: int = height
        self.file_size_bytes: int = file_size_bytes
        self.title: str = title or os.path.splitext(self.file_name)[0]
        self.description: str = description
        self.tags: List[str] = tags or []

        if date_modified:
            self.date_modified = date_modified
        elif os.path.exists(self.file_path):
            mtime = os.path.getmtime(self.file_path)
            self.date_modified = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        else:
            self.date_modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.flyweight: ImageFormatFlyweight = FormatFlyweightFactory().get_flyweight(format_name)
        self._cached_thumbnail: Optional[QPixmap] = None
        self._cached_strategy_name: Optional[str] = None
        self._cached_size: Optional[QSize] = None

    @property
    def format_name(self) -> str:
        return self.flyweight.format_name

    @property
    def mime_type(self) -> str:
        return self.flyweight.mime_type

    @property
    def dimensions_text(self) -> str:
        return f"{self.width}x{self.height} px"

    @property
    def size_formatted(self) -> str:
        bytes_val = self.file_size_bytes
        if bytes_val < 1024:
            return f"{bytes_val} B"
        elif bytes_val < 1024 * 1024:
            return f"{bytes_val / 1024.0:.1f} KB"
        else:
            return f"{bytes_val / (1024.0 * 1024.0):.2f} MB"

    def get_summary_text(self) -> str:
        return self.flyweight.get_summary_text(self.file_size_bytes, self.width, self.height)

    def load_full_pixmap(self) -> QPixmap:
        if not os.path.exists(self.file_path):
            return QPixmap()
        return QPixmap(self.file_path)

    def get_thumbnail(self, strategy: ThumbnailRenderStrategy, target_size: QSize) -> QPixmap:
        if (
            self._cached_thumbnail is not None
            and self._cached_strategy_name == strategy.name
            and self._cached_size == target_size
            and not self._cached_thumbnail.isNull()
        ):
            return self._cached_thumbnail

        original = self.load_full_pixmap()
        rendered = strategy.render(original, target_size)
        self._cached_thumbnail = rendered
        self._cached_strategy_name = strategy.name
        self._cached_size = target_size
        return rendered

    def invalidate_thumbnail_cache(self) -> None:
        self._cached_thumbnail = None
        self._cached_strategy_name = None
        self._cached_size = None

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
            "description": self.description,
            "tags": self.tags,
            "date_modified": self.date_modified,
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
            description=data.get("description", ""),
            tags=data.get("tags", []),
            date_modified=data.get("date_modified"),
            image_id=data.get("id"),
        )
