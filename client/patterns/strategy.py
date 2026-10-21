from abc import ABC, abstractmethod
from typing import List, Any
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QSize


class SortStrategy(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def sort(self, items: List[Any]) -> List[Any]:
        pass


class SortByNameAscStrategy(SortStrategy):
    @property
    def name(self) -> str:
        return "Nome (A-Z)"

    def sort(self, items: List[Any]) -> List[Any]:
        return sorted(items, key=lambda x: (x.title or x.file_name).lower())


class SortByNameDescStrategy(SortStrategy):
    @property
    def name(self) -> str:
        return "Nome (Z-A)"

    def sort(self, items: List[Any]) -> List[Any]:
        return sorted(items, key=lambda x: (x.title or x.file_name).lower(), reverse=True)


class SortBySizeAscStrategy(SortStrategy):
    @property
    def name(self) -> str:
        return "Tamanho (Menor primeiro)"

    def sort(self, items: List[Any]) -> List[Any]:
        return sorted(items, key=lambda x: x.file_size_bytes)


class SortBySizeDescStrategy(SortStrategy):
    @property
    def name(self) -> str:
        return "Tamanho (Maior primeiro)"

    def sort(self, items: List[Any]) -> List[Any]:
        return sorted(items, key=lambda x: x.file_size_bytes, reverse=True)


class ThumbnailRenderStrategy(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def render(self, original_pixmap: QPixmap, target_size: QSize) -> QPixmap:
        pass


class SmoothThumbnailStrategy(ThumbnailRenderStrategy):
    @property
    def name(self) -> str:
        return "Alta Qualidade (Smooth)"

    def render(self, original_pixmap: QPixmap, target_size: QSize) -> QPixmap:
        if original_pixmap.isNull():
            return QPixmap(target_size)
        return original_pixmap.scaled(
            target_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )


class FastThumbnailStrategy(ThumbnailRenderStrategy):
    @property
    def name(self) -> str:
        return "Rapida (Fast)"

    def render(self, original_pixmap: QPixmap, target_size: QSize) -> QPixmap:
        if original_pixmap.isNull():
            return QPixmap(target_size)
        return original_pixmap.scaled(
            target_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation
        )
