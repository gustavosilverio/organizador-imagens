from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QDialog, QVBoxLayout, QTextEdit, QFrame
)
from client.services.image_service import ImageService


class FlyweightStatsWidget(QFrame):
    def __init__(self, service: ImageService, parent=None):
        super().__init__(parent)
        self.service = service
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setStyleSheet("""
            FlyweightStatsWidget {
                background-color: #1E293B;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 4px 12px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(12)

        lbl_title = QLabel("<b>Flyweight:</b>")
        lbl_title.setStyleSheet("color: #38BDF8; font-size: 12px;")
        layout.addWidget(lbl_title)

        self.lbl_stats = QLabel("Formatos: 0 | Imagens: 0")
        self.lbl_stats.setStyleSheet("color: #E2E8F0; font-size: 12px;")
        layout.addWidget(self.lbl_stats)

        layout.addStretch()

        btn_inspect = QPushButton("Inspecionar Memoria")
        btn_inspect.setStyleSheet("""
            QPushButton {
                background-color: #0F172A;
                color: #38BDF8;
                border: 1px solid #38BDF8;
                border-radius: 4px;
                padding: 3px 8px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1E3A8A;
            }
        """)
        btn_inspect.clicked.connect(self._inspect_flyweights)
        layout.addWidget(btn_inspect)

        self.refresh()

    def refresh(self) -> None:
        stats = self.service.get_flyweight_stats()
        pool = stats.get("flyweights_in_pool", 0)
        total = stats.get("total_images", 0)
        saved = stats.get("objects_saved", 0)

        text = f"{pool} formatos em cache compartilhados por {total} imagens ({saved} instancias economizadas)"
        self.lbl_stats.setText(text)

    def _inspect_flyweights(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Inspecao de Memoria - Flyweight")
        dialog.resize(600, 380)

        dlg_layout = QVBoxLayout(dialog)
        dlg_layout.addWidget(QLabel("Enderecos de memoria das instancias compartilhadas:"))

        text_area = QTextEdit()
        text_area.setReadOnly(True)

        images = self.service.get_all_images()
        lines = []
        lines.append("Formatos no Factory:")
        for fmt, fw in self.service.flyweight_factory._flyweights.items():
            lines.append(f"  [{fmt}] -> {hex(id(fw))}")

        lines.append("\nImagens e referencias:")
        if not images:
            lines.append("  Nenhuma imagem carregada.")
        else:
            for img in images:
                lines.append(f"  '{img.title}' ({img.format_name}) -> {hex(id(img.flyweight))}")

        text_area.setPlainText("\n".join(lines))
        dlg_layout.addWidget(text_area)

        btn_ok = QPushButton("Fechar")
        btn_ok.clicked.connect(dialog.accept)
        dlg_layout.addWidget(btn_ok)

        dialog.exec()
