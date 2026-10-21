import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QPushButton, QFileDialog, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from client.models.image_item import ImageItem
from client.services.image_service import ImageService


class ImageDetailDialog(QDialog):
    image_updated = pyqtSignal(str)
    image_deleted = pyqtSignal(str)

    def __init__(self, item: ImageItem, service: ImageService, parent=None):
        super().__init__(parent)
        self.item = item
        self.service = service

        self.setWindowTitle(f"Detalhes: {self.item.title}")
        self.resize(800, 600)
        self._setup_ui()

    def _setup_ui(self) -> None:
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(16)

        left_layout = QVBoxLayout()
        preview_box = QGroupBox("Visualizacao")
        preview_box_layout = QVBoxLayout(preview_box)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("background-color: #0F172A; border-radius: 6px; padding: 10px;")

        full_pixmap = self.item.load_full_pixmap()
        if not full_pixmap.isNull():
            scaled = full_pixmap.scaled(
                380, 380,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.preview_label.setPixmap(scaled)
        else:
            self.preview_label.setText("Nao foi possivel carregar a imagem.")

        preview_box_layout.addWidget(self.preview_label)

        action_layout = QHBoxLayout()
        self.btn_export = QPushButton("Exportar Copia")
        self.btn_export.setObjectName("btnSecondary")
        self.btn_export.clicked.connect(self._on_export)
        action_layout.addWidget(self.btn_export)

        self.btn_delete = QPushButton("Excluir")
        self.btn_delete.setObjectName("btnDanger")
        self.btn_delete.clicked.connect(self._on_delete)
        action_layout.addWidget(self.btn_delete)

        preview_box_layout.addLayout(action_layout)
        left_layout.addWidget(preview_box)
        main_layout.addLayout(left_layout, stretch=1)

        right_layout = QVBoxLayout()

        flyweight_group = QGroupBox("Metadados Compartilhados (Flyweight)")
        flyweight_layout = QVBoxLayout(flyweight_group)
        lbl_format = QLabel(f"<b>Formato:</b> {self.item.flyweight.format_name} ({self.item.flyweight.mime_type})")
        lbl_alpha = QLabel(f"<b>Suporte a Canal Alfa:</b> {'Sim' if self.item.flyweight.supports_transparency else 'Nao'}")
        lbl_desc = QLabel(f"<b>Descricao do Formato:</b> {self.item.flyweight.description}")
        for lbl in (lbl_format, lbl_alpha, lbl_desc):
            flyweight_layout.addWidget(lbl)
        right_layout.addWidget(flyweight_group)

        tech_group = QGroupBox("Dados do Arquivo")
        tech_layout = QVBoxLayout(tech_group)
        lbl_dim = QLabel(f"<b>Dimensoes:</b> {self.item.dimensions_text}")
        lbl_size = QLabel(f"<b>Tamanho:</b> {self.item.size_formatted} ({self.item.file_size_bytes} bytes)")
        lbl_date = QLabel(f"<b>Modificado em:</b> {self.item.date_modified}")
        lbl_path = QLabel(f"<b>Caminho:</b> {self.item.file_path}")
        lbl_path.setWordWrap(True)
        lbl_path.setStyleSheet("font-size: 11px; color: #94A3B8;")
        for lbl in (lbl_dim, lbl_size, lbl_date, lbl_path):
            tech_layout.addWidget(lbl)
        right_layout.addWidget(tech_group)

        edit_group = QGroupBox("Editar Metadados (CRUD)")
        edit_layout = QVBoxLayout(edit_group)

        edit_layout.addWidget(QLabel("Titulo:"))
        self.edit_title = QLineEdit(self.item.title)
        edit_layout.addWidget(self.edit_title)

        edit_layout.addWidget(QLabel("Tags (separadas por virgula):"))
        self.edit_tags = QLineEdit(", ".join(self.item.tags))
        edit_layout.addWidget(self.edit_tags)

        edit_layout.addWidget(QLabel("Descricao:"))
        self.edit_desc = QTextEdit(self.item.description)
        self.edit_desc.setMaximumHeight(80)
        edit_layout.addWidget(self.edit_desc)

        btn_save = QPushButton("Salvar Alteracoes")
        btn_save.clicked.connect(self._on_save_metadata)
        edit_layout.addWidget(btn_save)
        right_layout.addWidget(edit_group)

        btn_close = QPushButton("Fechar")
        btn_close.setObjectName("btnSecondary")
        btn_close.clicked.connect(self.accept)
        right_layout.addWidget(btn_close)

        main_layout.addLayout(right_layout, stretch=1)

    def _on_save_metadata(self) -> None:
        new_title = self.edit_title.text().strip()
        new_desc = self.edit_desc.toPlainText().strip()
        tags_raw = self.edit_tags.text().split(",")
        new_tags = [t.strip() for t in tags_raw if t.strip()]

        try:
            self.service.update_image_metadata(
                image_id=self.item.id,
                title=new_title,
                description=new_desc,
                tags=new_tags
            )
            self.image_updated.emit(self.item.id)
            QMessageBox.information(self, "Sucesso", "Metadados atualizados com sucesso.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao salvar metadados: {e}")

    def _on_export(self) -> None:
        suggested_name = f"{self.item.title}{os.path.splitext(self.item.file_name)[1]}"
        dest_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Imagem",
            suggested_name,
            f"Arquivo (*{os.path.splitext(self.item.file_name)[1]})"
        )
        if not dest_path:
            return

        try:
            self.service.export_image(self.item.id, dest_path)
            QMessageBox.information(self, "Sucesso", f"Imagem exportada para: {dest_path}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao exportar imagem: {e}")

    def _on_delete(self) -> None:
        confirm = QMessageBox.question(
            self,
            "Confirmar Exclusao",
            f"Deseja remover a imagem '{self.item.title}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                self.service.delete_image(self.item.id)
                self.image_deleted.emit(self.item.id)
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao excluir imagem: {e}")
