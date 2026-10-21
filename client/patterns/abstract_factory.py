from abc import ABC, abstractmethod
import os
from typing import Tuple, Dict, Any, List
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt, QSize
from PIL import Image as PILImage


class UnsupportedFormatException(Exception):
    pass


class InvalidImageFileException(Exception):
    pass


class ImageReader(ABC):
    @abstractmethod
    def read(self, file_path: str) -> Tuple[QImage, Dict[str, Any]]:
        pass


class ThumbnailGenerator(ABC):
    @abstractmethod
    def generate_thumbnail(self, qimage: QImage, target_size: QSize, smooth: bool = True) -> QPixmap:
        pass


class JPEGReader(ImageReader):
    def read(self, file_path: str) -> Tuple[QImage, Dict[str, Any]]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Arquivo nao encontrado: {file_path}")

        try:
            with PILImage.open(file_path) as pil_img:
                pil_img.verify()
        except Exception as e:
            raise InvalidImageFileException(f"Arquivo JPEG corrompido ou invalido: {e}")

        try:
            with PILImage.open(file_path) as pil_img:
                width, height = pil_img.size
                mode = pil_img.mode
                format_detected = pil_img.format or "JPEG"
        except Exception as e:
            raise InvalidImageFileException(f"Falha ao extrair metadados JPEG: {e}")

        qimage = QImage(file_path)
        if qimage.isNull():
            raise InvalidImageFileException("Nao foi possivel carregar a imagem JPEG.")

        metadata = {
            "width": width,
            "height": height,
            "format": "JPEG",
            "detected_format": format_detected,
            "mode": mode,
            "has_alpha": False,
            "channels": 3,
        }
        return qimage, metadata


class JPEGThumbnailGenerator(ThumbnailGenerator):
    def generate_thumbnail(self, qimage: QImage, target_size: QSize, smooth: bool = True) -> QPixmap:
        if qimage.hasAlphaChannel():
            qimage = qimage.convertToFormat(QImage.Format.Format_RGB32)

        mode = Qt.TransformationMode.SmoothTransformation if smooth else Qt.TransformationMode.FastTransformation
        scaled_img = qimage.scaled(target_size, Qt.AspectRatioMode.KeepAspectRatio, mode)
        return QPixmap.fromImage(scaled_img)


class PNGReader(ImageReader):
    def read(self, file_path: str) -> Tuple[QImage, Dict[str, Any]]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Arquivo nao encontrado: {file_path}")

        try:
            with PILImage.open(file_path) as pil_img:
                pil_img.verify()
        except Exception as e:
            raise InvalidImageFileException(f"Arquivo PNG corrompido ou invalido: {e}")

        try:
            with PILImage.open(file_path) as pil_img:
                width, height = pil_img.size
                mode = pil_img.mode
                format_detected = pil_img.format or "PNG"
                has_alpha = "A" in mode or "transparency" in pil_img.info
        except Exception as e:
            raise InvalidImageFileException(f"Falha ao extrair metadados PNG: {e}")

        qimage = QImage(file_path)
        if qimage.isNull():
            raise InvalidImageFileException("Nao foi possivel carregar a imagem PNG.")

        metadata = {
            "width": width,
            "height": height,
            "format": "PNG",
            "detected_format": format_detected,
            "mode": mode,
            "has_alpha": has_alpha,
            "channels": 4 if has_alpha else 3,
        }
        return qimage, metadata


class PNGThumbnailGenerator(ThumbnailGenerator):
    def generate_thumbnail(self, qimage: QImage, target_size: QSize, smooth: bool = True) -> QPixmap:
        if qimage.format() != QImage.Format.Format_ARGB32_Premultiplied:
            qimage = qimage.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)

        mode = Qt.TransformationMode.SmoothTransformation if smooth else Qt.TransformationMode.FastTransformation
        scaled_img = qimage.scaled(target_size, Qt.AspectRatioMode.KeepAspectRatio, mode)
        return QPixmap.fromImage(scaled_img)


class BMPReader(ImageReader):
    def read(self, file_path: str) -> Tuple[QImage, Dict[str, Any]]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Arquivo nao encontrado: {file_path}")

        try:
            with PILImage.open(file_path) as pil_img:
                pil_img.verify()
        except Exception as e:
            raise InvalidImageFileException(f"Arquivo BMP corrompido ou invalido: {e}")

        try:
            with PILImage.open(file_path) as pil_img:
                width, height = pil_img.size
                mode = pil_img.mode
                format_detected = pil_img.format or "BMP"
        except Exception as e:
            raise InvalidImageFileException(f"Falha ao extrair metadados BMP: {e}")

        qimage = QImage(file_path)
        if qimage.isNull():
            raise InvalidImageFileException("Nao foi possivel carregar a imagem BMP.")

        metadata = {
            "width": width,
            "height": height,
            "format": "BMP",
            "detected_format": format_detected,
            "mode": mode,
            "has_alpha": False,
            "channels": 3,
        }
        return qimage, metadata


class BMPThumbnailGenerator(ThumbnailGenerator):
    def generate_thumbnail(self, qimage: QImage, target_size: QSize, smooth: bool = True) -> QPixmap:
        mode = Qt.TransformationMode.SmoothTransformation if smooth else Qt.TransformationMode.FastTransformation
        scaled_img = qimage.scaled(target_size, Qt.AspectRatioMode.KeepAspectRatio, mode)
        return QPixmap.fromImage(scaled_img)


class ImageFormatFactory(ABC):
    @abstractmethod
    def create_reader(self) -> ImageReader:
        pass

    @abstractmethod
    def create_thumbnail_generator(self) -> ThumbnailGenerator:
        pass

    @property
    @abstractmethod
    def format_name(self) -> str:
        pass

    @property
    @abstractmethod
    def supported_extensions(self) -> Tuple[str, ...]:
        pass


class JPEGFormatFactory(ImageFormatFactory):
    def create_reader(self) -> ImageReader:
        return JPEGReader()

    def create_thumbnail_generator(self) -> ThumbnailGenerator:
        return JPEGThumbnailGenerator()

    @property
    def format_name(self) -> str:
        return "JPEG"

    @property
    def supported_extensions(self) -> Tuple[str, ...]:
        return (".jpg", ".jpeg", ".jpe", ".jfif")


class PNGFormatFactory(ImageFormatFactory):
    def create_reader(self) -> ImageReader:
        return PNGReader()

    def create_thumbnail_generator(self) -> ThumbnailGenerator:
        return PNGThumbnailGenerator()

    @property
    def format_name(self) -> str:
        return "PNG"

    @property
    def supported_extensions(self) -> Tuple[str, ...]:
        return (".png",)


class BMPFormatFactory(ImageFormatFactory):
    def create_reader(self) -> ImageReader:
        return BMPReader()

    def create_thumbnail_generator(self) -> ThumbnailGenerator:
        return BMPThumbnailGenerator()

    @property
    def format_name(self) -> str:
        return "BMP"

    @property
    def supported_extensions(self) -> Tuple[str, ...]:
        return (".bmp", ".dib")


class ImageFormatFactorySelector:
    _factories: List[ImageFormatFactory] = [
        JPEGFormatFactory(),
        PNGFormatFactory(),
        BMPFormatFactory(),
    ]

    @classmethod
    def get_factory_for_extension(cls, extension: str) -> ImageFormatFactory:
        ext = extension.lower().strip()
        if not ext.startswith("."):
            ext = "." + ext

        for factory in cls._factories:
            if ext in factory.supported_extensions:
                return factory

        supported_list = cls.get_all_supported_extensions()
        raise UnsupportedFormatException(
            f"Extensao '{ext}' nao suportada. Formatos aceitos: {', '.join(supported_list)}"
        )

    @classmethod
    def get_factory_for_file(cls, file_path: str) -> ImageFormatFactory:
        _, ext = os.path.splitext(file_path)
        if not ext:
            raise UnsupportedFormatException(f"O arquivo '{file_path}' nao possui extensao.")
        return cls.get_factory_for_extension(ext)

    @classmethod
    def get_factory_for_format(cls, format_name: str) -> ImageFormatFactory:
        norm = format_name.upper().strip()
        if norm in ("JPG", "JPEG"):
            norm = "JPEG"
        for factory in cls._factories:
            if factory.format_name == norm:
                return factory
        raise UnsupportedFormatException(f"Formato desconhecido: '{format_name}'")

    @classmethod
    def get_all_supported_extensions(cls) -> List[str]:
        exts = []
        for factory in cls._factories:
            exts.extend(factory.supported_extensions)
        return exts
