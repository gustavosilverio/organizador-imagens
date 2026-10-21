"""
Padrão Comportamental: Strategy
Finalidade: Permitir a troca dinâmica e intercambiável de algoritmos de:
  1. Ordenação (Sort Strategy)
  2. Filtragem (Filter Strategy)
  3. Geração / Renderização de Miniaturas (Thumbnail Strategy)
"""

from abc import ABC, abstractmethod
from typing import List, Any, Optional
from PyQt6.QtGui import QPixmap, QPainter, QColor, QBrush
from PyQt6.QtCore import Qt, QSize, QRect


# ===========================================================================
# 1. Estratégias de Ordenação (Sorting Strategies)
# ===========================================================================

class SortStrategy(ABC):
    """Interface abstrata para algoritmos de ordenação de imagens."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Nome legível para exibição na interface gráfica."""
        pass

    @abstractmethod
    def sort(self, items: List[Any]) -> List[Any]:
        """Aplica o critério de ordenação e retorna a nova lista ordenada."""
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


class SortByDateDescStrategy(SortStrategy):
    @property
    def name(self) -> str:
        return "Data de Modificação (Mais recentes)"

    def sort(self, items: List[Any]) -> List[Any]:
        return sorted(items, key=lambda x: x.date_modified, reverse=True)


class SortByDateAscStrategy(SortStrategy):
    @property
    def name(self) -> str:
        return "Data de Modificação (Mais antigas)"

    def sort(self, items: List[Any]) -> List[Any]:
        return sorted(items, key=lambda x: x.date_modified)


class SortByFormatStrategy(SortStrategy):
    @property
    def name(self) -> str:
        return "Formato (JPEG, PNG, BMP)"

    def sort(self, items: List[Any]) -> List[Any]:
        return sorted(items, key=lambda x: (x.format_name, (x.title or x.file_name).lower()))


# ===========================================================================
# 2. Estratégias de Filtragem (Filter Strategies)
# ===========================================================================

class FilterStrategy(ABC):
    """Interface abstrata para algoritmos de filtragem de imagens."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Nome amigável da estratégia para o usuário."""
        pass

    @abstractmethod
    def filter(self, items: List[Any]) -> List[Any]:
        """Aplica a regra de filtro e retorna apenas os itens correspondentes."""
        pass


class FilterAllStrategy(FilterStrategy):
    @property
    def name(self) -> str:
        return "Todos os Formatos e Tamanhos"

    def filter(self, items: List[Any]) -> List[Any]:
        return list(items)


class FilterByFormatStrategy(FilterStrategy):
    def __init__(self, target_format: str):
        self.target_format = target_format.upper().strip()

    @property
    def name(self) -> str:
        return f"Somente {self.target_format}"

    def filter(self, items: List[Any]) -> List[Any]:
        return [item for item in items if item.format_name.upper() == self.target_format]


class FilterBySizeStrategy(FilterStrategy):
    """
    Filtra por faixas de tamanho:
    - 'small': < 500 KB
    - 'medium': 500 KB a 2 MB
    - 'large': > 2 MB
    """
    def __init__(self, category: str):
        self.category = category.lower().strip()

    @property
    def name(self) -> str:
        if self.category == "small":
            return "Pequenas (< 500 KB)"
        elif self.category == "medium":
            return "Médias (500 KB - 2 MB)"
        elif self.category == "large":
            return "Grandes (> 2 MB)"
        return "Tamanho Desconhecido"

    def filter(self, items: List[Any]) -> List[Any]:
        kb = 1024
        mb = 1024 * 1024
        if self.category == "small":
            return [it for it in items if it.file_size_bytes < (500 * kb)]
        elif self.category == "medium":
            return [it for it in items if (500 * kb) <= it.file_size_bytes <= (2 * mb)]
        elif self.category == "large":
            return [it for it in items if it.file_size_bytes > (2 * mb)]
        return items


class FilterBySearchStrategy(FilterStrategy):
    """Filtra imagens com base em texto (título, nome do arquivo ou tags)."""
    def __init__(self, query: str):
        self.query = query.lower().strip()

    @property
    def name(self) -> str:
        return f"Busca: '{self.query}'"

    def filter(self, items: List[Any]) -> List[Any]:
        if not self.query:
            return list(items)
        results = []
        for it in items:
            title = (it.title or "").lower()
            fname = (it.file_name or "").lower()
            desc = (it.description or "").lower()
            tags = " ".join(t.lower() for t in (it.tags or []))
            if (self.query in title or
                self.query in fname or
                self.query in desc or
                self.query in tags):
                results.append(it)
        return results


# ===========================================================================
# 3. Estratégias de Geração de Miniaturas (Thumbnail Render Strategies)
# ===========================================================================

class ThumbnailRenderStrategy(ABC):
    """Interface abstrata para algoritmos de renderização de miniaturas."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def render(self, original_pixmap: QPixmap, target_size: QSize) -> QPixmap:
        """Processa e renderiza a miniatura conforme o algoritmo selecionado."""
        pass


class SmoothThumbnailStrategy(ThumbnailRenderStrategy):
    """Gera miniatura com alta qualidade (SmoothTransformation) mantendo proporção."""
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
    """Gera miniatura com rapidez (FastTransformation) com menor custo computacional."""
    @property
    def name(self) -> str:
        return "Rápida (Fast / Baixo Custo)"

    def render(self, original_pixmap: QPixmap, target_size: QSize) -> QPixmap:
        if original_pixmap.isNull():
            return QPixmap(target_size)
        return original_pixmap.scaled(
            target_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation
        )


class CropSquareThumbnailStrategy(ThumbnailRenderStrategy):
    """Gera miniatura com recorte quadrado centralizado (1:1 Aspect Ratio)."""
    @property
    def name(self) -> str:
        return "Recorte Quadrado Central (1:1)"

    def render(self, original_pixmap: QPixmap, target_size: QSize) -> QPixmap:
        if original_pixmap.isNull():
            return QPixmap(target_size)

        # Escala primeiro para cobrir todo o target_size mantendo aspecto
        scaled = original_pixmap.scaled(
            target_size,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )

        # Recorta a porção central
        w, h = scaled.width(), scaled.height()
        tw, th = target_size.width(), target_size.height()
        x = max(0, (w - tw) // 2)
        y = max(0, (h - th) // 2)
        return scaled.copy(x, y, tw, th)


class LetterboxThumbnailStrategy(ThumbnailRenderStrategy):
    """Gera miniatura padronizada com moldura e fundo escuro (Letterbox)."""
    @property
    def name(self) -> str:
        return "Ajustada com Moldura (Letterbox)"

    def render(self, original_pixmap: QPixmap, target_size: QSize) -> QPixmap:
        canvas = QPixmap(target_size)
        canvas.fill(QColor("#1A1D24"))

        if original_pixmap.isNull():
            return canvas

        scaled = original_pixmap.scaled(
            target_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        painter = QPainter(canvas)
        x = (target_size.width() - scaled.width()) // 2
        y = (target_size.height() - scaled.height()) // 2
        painter.drawPixmap(x, y, scaled)
        painter.end()

        return canvas
