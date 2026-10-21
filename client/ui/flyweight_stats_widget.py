"""
Widget de Monitoramento do Padrão Flyweight: FlyweightStatsWidget
Demonstra de forma observável e mensurável o compartilhamento de recursos
e a economia de memória entre instâncias de miniaturas no organizador.
Atende ao critério de observabilidade de padrões da disciplina.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QDialog, QTextEdit, QFrame
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from client.services.image_service import ImageService


class FlyweightStatsWidget(QFrame):
    """Barra informativa e interativa que exibe métricas em tempo real do padrão Flyweight."""

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

        # Ícone e Título
        lbl_title = QLabel("🪶 <b>Padrão Flyweight Ativo:</b>")
        lbl_title.setStyleSheet("color: #38BDF8; font-size: 12px;")
        layout.addWidget(lbl_title)

        # Métrica: Formatos Compartilhados
        self.lbl_stats = QLabel("Formatos em Cache: 0 | Imagens: 0 | Economia: 0%")
        self.lbl_stats.setStyleSheet("color: #E2E8F0; font-size: 12px;")
        layout.addWidget(self.lbl_stats)

        layout.addStretch()

        # Botão para Inspecionar os Objetos Compartilhados
        btn_inspect = QPushButton("Inspecionar Ponteiros em Memória")
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
        """Atualiza os números na barra de métricas."""
        stats = self.service.get_flyweight_stats()
        pool = stats.get("flyweights_in_pool", 0)
        total = stats.get("total_images", 0)
        saved = stats.get("objects_saved", 0)
        ratio = stats.get("sharing_ratio_percent", 0.0)

        text = (
            f"<b>{pool}</b> formatos únicos em cache compartilhados por "
            f"<b>{total}</b> imagens ({saved} instâncias economizadas • {ratio:.1f}% reuso)"
        )
        self.lbl_stats.setText(text)

    def _inspect_flyweights(self) -> None:
        """Abre uma janela demonstrando que imagens de mesmo formato compartilham o mesmo ponteiro de memória."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Inspeção de Memória: Padrão Flyweight")
        dialog.resize(600, 400)

        dlg_layout = QVBoxLayout(dialog)

        info_header = QLabel(
            "<b>Demonstração de Comportamento Observável: Padrão Flyweight</b><br>"
            "Observe abaixo os endereços de memória (<code>hex(id(...))</code>) dos objetos Flyweight associados a cada imagem.<br>"
            "Imagens do mesmo formato compartilham <b>exatamente o mesmo objeto na memória RAM</b>:"
        )
        info_header.setWordWrap(True)
        dlg_layout.addWidget(info_header)

        text_area = QTextEdit()
        text_area.setReadOnly(True)

        images = self.service.get_all_images()
        lines = []
        lines.append("=== POOL DE FORMATOS ÚNICOS NO FLYWEIGHT FACTORY ===")
        factory = self.service.flyweight_factory
        for fmt, fw in factory._flyweights.items():
            lines.append(f"  • Formato [{fmt}] -> Endereço de Memória: {hex(id(fw))} ({fw.description})")

        lines.append("\n=== INSTÂNCIAS DE IMAGENS E SEUS PONTEIROS DE FLYWEIGHT ===")
        if not images:
            lines.append("  (Nenhuma imagem carregada na galeria no momento)")
        else:
            for img in images:
                fw_id = hex(id(img.flyweight))
                lines.append(f"  • Imagem: '{img.title}' | Formato: {img.format_name} | Ponteiro Flyweight: {fw_id}")

        text_area.setPlainText("\n".join(lines))
        dlg_layout.addWidget(text_area)

        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(dialog.accept)
        dlg_layout.addWidget(btn_ok)

        dialog.exec()
