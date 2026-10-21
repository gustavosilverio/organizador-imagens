"""
Padrão Criacional: Abstract Factory
Finalidade: Criar famílias de objetos relacionados (leitores de imagens e geradores de miniaturas)
compatíveis com cada formato de imagem suportado (JPEG, PNG, BMP).
"""

from abc import ABC, abstractmethod
import os
from typing import Tuple, Dict, Any, List
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt, QSize
from PIL import Image as PILImage


class UnsupportedFormatException(Exception):
    """Exceção levantada quando o arquivo possui um formato não suportado pelo sistema."""
    pass


class InvalidImageFileException(Exception):
    """Exceção levantada quando o arquivo está corrompido ou malformado."""
    pass


# ---------------------------------------------------------------------------
# Produtos Abstratos (Abstract Products)
# ---------------------------------------------------------------------------

class ImageReader(ABC):
    """Produto Abstrato A: Leitor de arquivo de imagem."""

    @abstractmethod
    def read(self, file_path: str) -> Tuple[QImage, Dict[str, Any]]:
        """
        Lê o arquivo de imagem do disco, valida sua integridade e retorna o QImage
        carregado juntamente com metadados detalhados (largura, altura, formato, modo).
        """
        pass


class ThumbnailGenerator(ABC):
    """Produto Abstrato B: Gerador de miniatura compatível com o formato."""

    @abstractmethod
    def generate_thumbnail(self, qimage: QImage, target_size: QSize, smooth: bool = True) -> QPixmap:
        """
        Gera um QPixmap com a miniatura redimensionada, respeitando as características
        específicas do formato (como canal alfa no PNG ou otimização de cor no JPEG).
        """
        pass


# ---------------------------------------------------------------------------
# Produtos Concretos para JPEG (Concrete Products - JPEG)
# ---------------------------------------------------------------------------

class JPEGReader(ImageReader):
    """Leitor especializado para imagens JPEG/JPG."""

    def read(self, file_path: str) -> Tuple[QImage, Dict[str, Any]]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

        try:
            # Validação profunda com Pillow para detectar cabeçalhos corrompidos
            with PILImage.open(file_path) as pil_img:
                pil_img.verify()
        except Exception as e:
            raise InvalidImageFileException(f"Arquivo JPEG corrompido ou inválido: {e}")

        # Recarrega para obter dimensões e metadados reais
        try:
            with PILImage.open(file_path) as pil_img:
                width, height = pil_img.size
                mode = pil_img.mode
                format_detected = pil_img.format or "JPEG"
        except Exception as e:
            raise InvalidImageFileException(f"Falha ao extrair metadados JPEG: {e}")

        qimage = QImage(file_path)
        if qimage.isNull():
            raise InvalidImageFileException("O decodificador Qt não conseguiu renderizar a imagem JPEG.")

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
    """Gerador de miniaturas especializado em JPEG (otimizado para fotos, sem canal alfa)."""

    def generate_thumbnail(self, qimage: QImage, target_size: QSize, smooth: bool = True) -> QPixmap:
        # Imagens JPEG convertidas para formato RGB estável sem transparência
        if qimage.hasAlphaChannel():
            qimage = qimage.convertToFormat(QImage.Format.Format_RGB32)

        mode = Qt.TransformationMode.SmoothTransformation if smooth else Qt.TransformationMode.FastTransformation
        scaled_img = qimage.scaled(target_size, Qt.AspectRatioMode.KeepAspectRatio, mode)
        return QPixmap.fromImage(scaled_img)


# ---------------------------------------------------------------------------
# Produtos Concretos para PNG (Concrete Products - PNG)
# ---------------------------------------------------------------------------

class PNGReader(ImageReader):
    """Leitor especializado para imagens PNG (preserva canal alfa e transparência)."""

    def read(self, file_path: str) -> Tuple[QImage, Dict[str, Any]]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

        try:
            with PILImage.open(file_path) as pil_img:
                pil_img.verify()
        except Exception as e:
            raise InvalidImageFileException(f"Arquivo PNG corrompido ou inválido: {e}")

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
            raise InvalidImageFileException("O decodificador Qt não conseguiu renderizar a imagem PNG.")

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
    """Gerador de miniaturas especializado em PNG (garante preservação do canal de transparência ARGB)."""

    def generate_thumbnail(self, qimage: QImage, target_size: QSize, smooth: bool = True) -> QPixmap:
        # Garante suporte a transparência RGBA/ARGB32 Premultiplied
        if qimage.format() != QImage.Format.Format_ARGB32_Premultiplied:
            qimage = qimage.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)

        mode = Qt.TransformationMode.SmoothTransformation if smooth else Qt.TransformationMode.FastTransformation
        scaled_img = qimage.scaled(target_size, Qt.AspectRatioMode.KeepAspectRatio, mode)
        return QPixmap.fromImage(scaled_img)


# ---------------------------------------------------------------------------
# Produtos Concretos para BMP (Concrete Products - BMP)
# ---------------------------------------------------------------------------

class BMPReader(ImageReader):
    """Leitor especializado para imagens Bitmap (BMP)."""

    def read(self, file_path: str) -> Tuple[QImage, Dict[str, Any]]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

        try:
            with PILImage.open(file_path) as pil_img:
                pil_img.verify()
        except Exception as e:
            raise InvalidImageFileException(f"Arquivo BMP corrompido ou inválido: {e}")

        try:
            with PILImage.open(file_path) as pil_img:
                width, height = pil_img.size
                mode = pil_img.mode
                format_detected = pil_img.format or "BMP"
        except Exception as e:
            raise InvalidImageFileException(f"Falha ao extrair metadados BMP: {e}")

        qimage = QImage(file_path)
        if qimage.isNull():
            raise InvalidImageFileException("O decodificador Qt não conseguiu renderizar a imagem BMP.")

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
    """Gerador de miniaturas para formato BMP."""

    def generate_thumbnail(self, qimage: QImage, target_size: QSize, smooth: bool = True) -> QPixmap:
        mode = Qt.TransformationMode.SmoothTransformation if smooth else Qt.TransformationMode.FastTransformation
        scaled_img = qimage.scaled(target_size, Qt.AspectRatioMode.KeepAspectRatio, mode)
        return QPixmap.fromImage(scaled_img)


# ---------------------------------------------------------------------------
# Fábrica Abstrata (Abstract Factory Interface)
# ---------------------------------------------------------------------------

class ImageFormatFactory(ABC):
    """
    Interface da Abstract Factory.
    Declara métodos para criar cada produto da família de um formato de imagem.
    """

    @abstractmethod
    def create_reader(self) -> ImageReader:
        """Cria o leitor de arquivo compatível com o formato."""
        pass

    @abstractmethod
    def create_thumbnail_generator(self) -> ThumbnailGenerator:
        """Cria o gerador de miniaturas compatível com o formato."""
        pass

    @property
    @abstractmethod
    def format_name(self) -> str:
        """Nome identificador do formato (ex: 'JPEG', 'PNG', 'BMP')."""
        pass

    @property
    @abstractmethod
    def supported_extensions(self) -> Tuple[str, ...]:
        """Extensões suportadas pela fábrica."""
        pass


# ---------------------------------------------------------------------------
# Fábricas Concretas (Concrete Factories)
# ---------------------------------------------------------------------------

class JPEGFormatFactory(ImageFormatFactory):
    """Fábrica concreta para arquivos no formato JPEG/JPG."""

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
    """Fábrica concreta para arquivos no formato PNG."""

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
    """Fábrica concreta para arquivos no formato BMP."""

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


# ---------------------------------------------------------------------------
# Seletor de Fábrica (Abstract Factory Selector / Registry)
# ---------------------------------------------------------------------------

class ImageFormatFactorySelector:
    """
    Localizador e seletor da Abstract Factory apropriada com base na
    extensão do arquivo ou nome do formato.
    """
    _factories: List[ImageFormatFactory] = [
        JPEGFormatFactory(),
        PNGFormatFactory(),
        BMPFormatFactory(),
    ]

    @classmethod
    def get_factory_for_extension(cls, extension: str) -> ImageFormatFactory:
        """
        Retorna a fábrica concreta correspondente à extensão de arquivo.
        Lança UnsupportedFormatException se a extensão não for suportada.
        """
        ext = extension.lower().strip()
        if not ext.startswith("."):
            ext = "." + ext

        for factory in cls._factories:
            if ext in factory.supported_extensions:
                return factory

        supported_list = cls.get_all_supported_extensions()
        raise UnsupportedFormatException(
            f"O formato com extensão '{ext}' não é suportado pelo organizador. "
            f"Formatos aceitos: {', '.join(supported_list)}"
        )

    @classmethod
    def get_factory_for_file(cls, file_path: str) -> ImageFormatFactory:
        """Identifica a fábrica adequada com base no caminho do arquivo."""
        _, ext = os.path.splitext(file_path)
        if not ext:
            raise UnsupportedFormatException(f"O arquivo '{file_path}' não possui extensão de formato de imagem.")
        return cls.get_factory_for_extension(ext)

    @classmethod
    def get_factory_for_format(cls, format_name: str) -> ImageFormatFactory:
        """Retorna a fábrica pelo nome do formato (ex: 'JPEG', 'PNG', 'BMP')."""
        norm = format_name.upper().strip()
        if norm in ("JPG", "JPEG"):
            norm = "JPEG"
        for factory in cls._factories:
            if factory.format_name == norm:
                return factory
        raise UnsupportedFormatException(f"Formato desconhecido: '{format_name}'")

    @classmethod
    def get_all_supported_extensions(cls) -> List[str]:
        """Retorna lista consolidada de todas as extensões suportadas."""
        exts = []
        for factory in cls._factories:
            exts.extend(factory.supported_extensions)
        return exts
