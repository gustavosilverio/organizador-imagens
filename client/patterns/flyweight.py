from dataclasses import dataclass
from typing import Dict, Optional
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen, QFont
from PyQt6.QtCore import Qt, QRect


@dataclass(frozen=True)
class ImageFormatFlyweight:
    format_name: str
    mime_type: str
    supports_transparency: bool
    default_extension: str
    badge_bg_color: str
    badge_text_color: str
    badge_label: str
    description: str

    def get_summary_text(self, extrinsic_size_bytes: int, width: int, height: int) -> str:
        size_kb = extrinsic_size_bytes / 1024.0
        alpha_info = "Com transparencia" if self.supports_transparency else "Sem transparencia"
        return f"{self.format_name} ({self.mime_type}) | {width}x{height} px | {size_kb:.1f} KB | {alpha_info}"

    def draw_badge(self, painter: QPainter, rect: QRect) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        bg_color = QColor(self.badge_bg_color)
        bg_color.setAlpha(220)
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, 4, 4)

        painter.setPen(QPen(QColor(self.badge_text_color)))
        font = QFont("Segoe UI", 8, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.badge_label)

        painter.restore()


class FormatFlyweightFactory:
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
        self._flyweights["JPEG"] = ImageFormatFlyweight(
            format_name="JPEG",
            mime_type="image/jpeg",
            supports_transparency=False,
            default_extension=".jpg",
            badge_bg_color="#D35400",
            badge_text_color="#FFFFFF",
            badge_label="JPG",
            description="Formato JPEG."
        )
        self._flyweights["PNG"] = ImageFormatFlyweight(
            format_name="PNG",
            mime_type="image/png",
            supports_transparency=True,
            default_extension=".png",
            badge_bg_color="#2980B9",
            badge_text_color="#FFFFFF",
            badge_label="PNG",
            description="Formato PNG."
        )
        self._flyweights["BMP"] = ImageFormatFlyweight(
            format_name="BMP",
            mime_type="image/bmp",
            supports_transparency=False,
            default_extension=".bmp",
            badge_bg_color="#27AE60",
            badge_text_color="#FFFFFF",
            badge_label="BMP",
            description="Formato BMP."
        )

    def get_flyweight(self, format_name: str) -> ImageFormatFlyweight:
        key = format_name.upper().strip()
        if key in ("JPG", "JPEG"):
            key = "JPEG"
        elif key == "PNG":
            key = "PNG"
        elif key == "BMP":
            key = "BMP"

        self._served_requests += 1

        if key not in self._flyweights:
            self._flyweights[key] = ImageFormatFlyweight(
                format_name=key,
                mime_type=f"image/{key.lower()}",
                supports_transparency=False,
                default_extension=f".{key.lower()}",
                badge_bg_color="#7F8C8D",
                badge_text_color="#FFFFFF",
                badge_label=key[:3],
                description=f"Formato {key}."
            )

        return self._flyweights[key]

    def get_pool_size(self) -> int:
        return len(self._flyweights)

    def get_served_requests_count(self) -> int:
        return self._served_requests

    def get_stats(self, total_images: int, unique_formats_count: Optional[int] = None) -> dict:
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
