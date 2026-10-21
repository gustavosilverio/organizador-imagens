"""
Padrão Estrutural: Flyweight
Finalidade: Compartilhar metadados e recursos comuns em miniaturas e formatos de imagens,
economizando memória e centralizando atributos intrínsecos de cada formato.
"""

from dataclasses import dataclass
from typing import Dict, Optional
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen, QFont
from PyQt6.QtCore import Qt, QRect


@dataclass(frozen=True)
class ImageFormatFlyweight:
    """
    Estado Intrínseco compartilhado entre todas as imagens do mesmo formato.
    É imutável e reutilizado por qualquer imagem daquele tipo.
    """
    format_name: str           # Ex: "JPEG", "PNG", "BMP"
    mime_type: str             # Ex: "image/jpeg", "image/png", "image/bmp"
    supports_transparency: bool
    default_extension: str     # Ex: ".jpg", ".png", ".bmp"
    badge_bg_color: str        # Cor hexadecimal para renderização visual do formato
    badge_text_color: str      # Cor do texto do badge
    badge_label: str           # Rótulo curto, ex: "JPG", "PNG", "BMP"
    description: str           # Descrição técnica do formato

    def get_summary_text(self, extrinsic_size_bytes: int, width: int, height: int) -> str:
        """
        Combina o estado intrínseco (formato, suporte a transparência) com o
        estado extrínseco (tamanho em bytes, dimensões específicas da imagem).
        """
        size_kb = extrinsic_size_bytes / 1024.0
        alpha_info = "Com transparência (Alpha)" if self.supports_transparency else "Sem transparência"
        return f"{self.format_name} ({self.mime_type}) | {width}x{height} px | {size_kb:.1f} KB | {alpha_info}"

    def draw_badge(self, painter: QPainter, rect: QRect) -> None:
        """
        Desenha o badge visual de formato na miniatura usando os recursos
        compartilhados intrínsecos.
        """
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Fundo do badge
        bg_color = QColor(self.badge_bg_color)
        bg_color.setAlpha(220)
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, 4, 4)
        
        # Texto do badge
        painter.setPen(QPen(QColor(self.badge_text_color)))
        font = QFont("Segoe UI", 8, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.badge_label)
        
        painter.restore()


class FormatFlyweightFactory:
    """
    Fábrica Flyweight que gerencia o pool de instâncias únicas de ImageFormatFlyweight.
    Garante que nunca haja mais de uma instância na memória para o mesmo formato.
    """
    _instance: Optional["FormatFlyweightFactory"] = None
    _flyweights: Dict[str, ImageFormatFlyweight] = {}
    _served_requests: int = 0

    def __new__(cls) -> "FormatFlyweightFactory":
        if cls._instance is None:
            cls._instance = super(FormatFlyweightFactory, cls).__new__(cls)
            cls._instance._flyweights = {}
            cls._instance._served_requests = 0
            cls._instance._initialize_default_flyweights()
        return cls._instance

    def _initialize_default_flyweights(self) -> None:
        """Registra os formatos padrão do sistema."""
        self._flyweights["JPEG"] = ImageFormatFlyweight(
            format_name="JPEG",
            mime_type="image/jpeg",
            supports_transparency=False,
            default_extension=".jpg",
            badge_bg_color="#D35400",  # Laranja
            badge_text_color="#FFFFFF",
            badge_label="JPG",
            description="Formato de imagem com perdas, otimizado para fotografias."
        )
        self._flyweights["PNG"] = ImageFormatFlyweight(
            format_name="PNG",
            mime_type="image/png",
            supports_transparency=True,
            default_extension=".png",
            badge_bg_color="#2980B9",  # Azul
            badge_text_color="#FFFFFF",
            badge_label="PNG",
            description="Formato de imagem sem perdas com suporte total a transparência alfa."
        )
        self._flyweights["BMP"] = ImageFormatFlyweight(
            format_name="BMP",
            mime_type="image/bmp",
            supports_transparency=False,
            default_extension=".bmp",
            badge_bg_color="#27AE60",  # Verde
            badge_text_color="#FFFFFF",
            badge_label="BMP",
            description="Formato de imagem bitmap de mapa de bits descompactado."
        )

    def get_flyweight(self, format_name: str) -> ImageFormatFlyweight:
        """
        Retorna o objeto Flyweight existente para o formato especificado.
        Se ainda não existir no pool, cria e armazena.
        """
        key = format_name.upper().strip()
        if key in ("JPG", "JPEG"):
            key = "JPEG"
        elif key == "PNG":
            key = "PNG"
        elif key == "BMP":
            key = "BMP"

        self._served_requests += 1

        if key not in self._flyweights:
            # Fallback dinâmico para formatos adicionais
            self._flyweights[key] = ImageFormatFlyweight(
                format_name=key,
                mime_type=f"image/{key.lower()}",
                supports_transparency=False,
                default_extension=f".{key.lower()}",
                badge_bg_color="#7F8C8D",
                badge_text_color="#FFFFFF",
                badge_label=key[:3],
                description=f"Formato {key} genérico suportado."
            )

        return self._flyweights[key]

    def get_pool_size(self) -> int:
        """Retorna o número de instâncias Flyweight únicas ativas na memória."""
        return len(self._flyweights)

    def get_served_requests_count(self) -> int:
        """Retorna quantas vezes instâncias Flyweight foram consultadas pelas imagens."""
        return self._served_requests

    def get_stats(self, total_images: int, unique_formats_count: Optional[int] = None) -> dict:
        """
        Estatísticas observáveis da aplicação para verificação de qualidade:
        Demonstra o compartilhamento real de objetos e economia de memória.
        """
        pool_size = self.get_pool_size()
        active_formats = unique_formats_count if unique_formats_count is not None and unique_formats_count > 0 else pool_size
        objects_saved = max(0, total_images - active_formats) if total_images > 0 else 0
        ratio = (objects_saved / total_images * 100.0) if total_images > 0 else 0.0
        return {
            "flyweights_in_pool": pool_size,
            "active_formats_used": active_formats,
            "total_images": total_images,
            "references_served": self._served_requests,
            "objects_saved": objects_saved,
            "sharing_ratio_percent": ratio,
            "formats_cached": list(self._flyweights.keys()),
        }
