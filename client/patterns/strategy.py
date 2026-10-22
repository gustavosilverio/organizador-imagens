from abc import ABC, abstractmethod
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QSize


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
