from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QMenu
from PyQt6.QtGui import QPixmap, QPainter, QFont, QMouseEvent
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QRect

from client.models.image_item import ImageItem
from client.patterns.strategy import ThumbnailRenderStrategy


class ImageCard(QFrame):
    clicked = pyqtSignal(str)
    double_clicked = pyqtSignal(str)
    delete_requested = pyqtSignal(str)
    export_requested = pyqtSignal(str)

    CARD_WIDTH = 200
    CARD_HEIGHT = 240
    THUMB_WIDTH = 180
    THUMB_HEIGHT = 140

    def __init__(self, item: ImageItem, thumbnail_strategy: ThumbnailRenderStrategy, parent=None):
        super().__init__(parent)
        self.item = item
        self.thumbnail_strategy = thumbnail_strategy
        self._is_selected = False

        self.setFixedSize(self.CARD_WIDTH, self.CARD_HEIGHT)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(self.THUMB_WIDTH, self.THUMB_HEIGHT)
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_label.setStyleSheet("background-color: #0F172A; border-radius: 6px;")
        layout.addWidget(self.thumb_label)

        self.title_label = QLabel(self.item.title)
        self.title_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #F8FAFC;")
        self.title_label.setToolTip(self.item.title)
        self.title_label.setWordWrap(False)
        layout.addWidget(self.title_label)

        info_layout = QHBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(4)

        self.info_label = QLabel(f"{self.item.dimensions_text} - {self.item.size_formatted}")
        self.info_label.setFont(QFont("Segoe UI", 8))
        self.info_label.setStyleSheet("color: #94A3B8;")
        info_layout.addWidget(self.info_label)

        layout.addLayout(info_layout)
        self.update_thumbnail(self.thumbnail_strategy)

    def update_thumbnail(self, strategy: ThumbnailRenderStrategy) -> None:
        self.thumbnail_strategy = strategy
        target_size = QSize(self.THUMB_WIDTH, self.THUMB_HEIGHT)
        pixmap = self.item.get_thumbnail(strategy, target_size)

        if not pixmap.isNull():
            composite = QPixmap(pixmap)
            painter = QPainter(composite)
            badge_rect = QRect(6, 6, 42, 18)
            self.item.flyweight.draw_badge(painter, badge_rect)
            painter.end()
            self.thumb_label.setPixmap(composite)
        else:
            self.thumb_label.setText("Sem Previa")

    def set_selected(self, selected: bool) -> None:
        self._is_selected = selected
        self._apply_style()

    def _apply_style(self) -> None:
        if self._is_selected:
            self.setStyleSheet("""
                QFrame {
                    background-color: #1E293B;
                    border: 2px solid #3B82F6;
                    border-radius: 8px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #1E293B;
                    border: 1px solid #334155;
                    border-radius: 8px;
                }
                QFrame:hover {
                    border: 1px solid #64748B;
                    background-color: #273549;
                }
            """)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.item.id)
        elif event.button() == Qt.MouseButton.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.item.id)
        super().mouseDoubleClickEvent(event)

    def _show_context_menu(self, global_pos) -> None:
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1E293B;
                border: 1px solid #334155;
                color: #F8FAFC;
                padding: 4px;
            }
            QMenu::item:selected {
                background-color: #3B82F6;
            }
        """)
        action_view = menu.addAction("Visualizar e Editar")
        action_export = menu.addAction("Exportar Copia")
        menu.addSeparator()
        action_delete = menu.addAction("Excluir")

        chosen = menu.exec(global_pos)
        if chosen == action_view:
            self.double_clicked.emit(self.item.id)
        elif chosen == action_export:
            self.export_requested.emit(self.item.id)
        elif chosen == action_delete:
            self.delete_requested.emit(self.item.id)
