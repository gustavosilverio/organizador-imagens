import os
from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QLineEdit,
    QFileDialog, QMessageBox, QGroupBox, QComboBox, QSplitter
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap

from client.models.image_item import ImageItem
from client.services.image_service import ImageService
from client.patterns.abstract_factory import (
    UnsupportedFormatException,
    InvalidImageFileException,
    ImageFormatFactorySelector
)
from client.patterns.strategy import (
    SmoothThumbnailStrategy,
    FastThumbnailStrategy
)


class MainWindow(QMainWindow):
    def __init__(self, service: Optional[ImageService] = None):
        super().__init__()
        self.service = service or ImageService()
        self.selected_item: Optional[ImageItem] = None

        self.setWindowTitle("Organizador de Imagens")
        self.resize(750, 500)

        self._setup_ui()
        self.refresh_list()

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        top_buttons_layout = QHBoxLayout()
        self.btn_add = QPushButton("Adicionar Imagem")
        self.btn_add.clicked.connect(self._on_add_image)
        top_buttons_layout.addWidget(self.btn_add)

        self.btn_samples = QPushButton("Carregar Exemplos")
        self.btn_samples.clicked.connect(self._on_load_samples)
        top_buttons_layout.addWidget(self.btn_samples)

        self.btn_test_invalid = QPushButton("Testar Arquivo Invalido")
        self.btn_test_invalid.clicked.connect(self._on_test_invalid)
        top_buttons_layout.addWidget(self.btn_test_invalid)

        top_buttons_layout.addStretch()
        main_layout.addLayout(top_buttons_layout)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(QLabel("Lista de Imagens:"))
        self.list_widget = QListWidget()
        self.list_widget.currentRowChanged.connect(self._on_row_changed)
        left_layout.addWidget(self.list_widget)

        self.btn_delete = QPushButton("Excluir Imagem")
        self.btn_delete.setEnabled(False)
        self.btn_delete.clicked.connect(self._on_delete)
        left_layout.addWidget(self.btn_delete)

        self.btn_export = QPushButton("Exportar Copia")
        self.btn_export.setEnabled(False)
        self.btn_export.clicked.connect(self._on_export)
        left_layout.addWidget(self.btn_export)

        splitter.addWidget(left_widget)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        group_view = QGroupBox("Visualizacao")
        group_view_layout = QVBoxLayout(group_view)
        self.lbl_preview = QLabel("Nenhuma imagem selecionada")
        self.lbl_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_preview.setMinimumSize(220, 200)
        group_view_layout.addWidget(self.lbl_preview)
        right_layout.addWidget(group_view)

        group_data = QGroupBox("Dados e Edicao (CRUD)")
        group_data_layout = QVBoxLayout(group_data)

        self.lbl_format = QLabel("Formato: -")
        self.lbl_dims = QLabel("Dimensoes: -")
        self.lbl_size = QLabel("Tamanho: -")
        group_data_layout.addWidget(self.lbl_format)
        group_data_layout.addWidget(self.lbl_dims)
        group_data_layout.addWidget(self.lbl_size)

        edit_layout = QHBoxLayout()
        edit_layout.addWidget(QLabel("Nome:"))
        self.edit_title = QLineEdit()
        edit_layout.addWidget(self.edit_title)
        self.btn_save_title = QPushButton("Salvar Nome")
        self.btn_save_title.setEnabled(False)
        self.btn_save_title.clicked.connect(self._on_save_title)
        edit_layout.addWidget(self.btn_save_title)
        group_data_layout.addLayout(edit_layout)

        right_layout.addWidget(group_data)

        group_strat = QGroupBox("Miniatura (Strategy)")
        group_strat_layout = QHBoxLayout(group_strat)
        group_strat_layout.addWidget(QLabel("Algoritmo:"))
        self.combo_strategy = QComboBox()
        self.strategies = [
            SmoothThumbnailStrategy(),
            FastThumbnailStrategy()
        ]
        for s in self.strategies:
            self.combo_strategy.addItem(s.name, s)
        self.combo_strategy.currentIndexChanged.connect(self._on_strategy_changed)
        group_strat_layout.addWidget(self.combo_strategy)
        right_layout.addWidget(group_strat)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        main_layout.addWidget(splitter)

        self.lbl_flyweight_status = QLabel("Flyweight: 0 formatos compartilhados")
        main_layout.addWidget(self.lbl_flyweight_status)

    def refresh_list(self) -> None:
        self.list_widget.clear()
        images = self.service.get_all_images()
        for img in images:
            item = QListWidgetItem(f"{img.title} ({img.format_name})")
            item.setData(Qt.ItemDataRole.UserRole, img.id)
            self.list_widget.addItem(item)

        stats = self.service.get_flyweight_stats()
        self.lbl_flyweight_status.setText(
            f"Flyweight: {stats.get('flyweights_in_pool', 0)} formatos no pool, "
            f"{stats.get('objects_saved', 0)} instancias salvas na memoria."
        )

        if not images:
            self.selected_item = None
            self.lbl_preview.setText("Nenhuma imagem selecionada")
            self.lbl_preview.setPixmap(QPixmap())
            self.lbl_format.setText("Formato: -")
            self.lbl_dims.setText("Dimensoes: -")
            self.lbl_size.setText("Tamanho: -")
            self.edit_title.clear()
            self.btn_delete.setEnabled(False)
            self.btn_export.setEnabled(False)
            self.btn_save_title.setEnabled(False)

    def _on_row_changed(self, row: int) -> None:
        if row < 0:
            return
        item_widget = self.list_widget.item(row)
        if not item_widget:
            return
        image_id = item_widget.data(Qt.ItemDataRole.UserRole)
        self.selected_item = self.service.get_image_by_id(image_id)

        if self.selected_item:
            self.lbl_format.setText(f"Formato: {self.selected_item.format_name} ({self.selected_item.flyweight.mime_type})")
            self.lbl_dims.setText(f"Dimensoes: {self.selected_item.dimensions_text}")
            self.lbl_size.setText(f"Tamanho: {self.selected_item.size_formatted}")
            self.edit_title.setText(self.selected_item.title)

            self.btn_delete.setEnabled(True)
            self.btn_export.setEnabled(True)
            self.btn_save_title.setEnabled(True)

            self._update_preview()

    def _update_preview(self) -> None:
        if not self.selected_item:
            return
        strategy = self.combo_strategy.currentData()
        target_size = QSize(220, 200)
        thumb = self.selected_item.get_thumbnail(strategy, target_size)
        if not thumb.isNull():
            self.lbl_preview.setPixmap(thumb)
        else:
            self.lbl_preview.setText("Sem previa disponivel")

    def _on_strategy_changed(self) -> None:
        self._update_preview()

    def _on_save_title(self) -> None:
        if not self.selected_item:
            return
        new_title = self.edit_title.text().strip()
        if new_title:
            self.service.update_image_title(self.selected_item.id, new_title)
            self.refresh_list()
            QMessageBox.information(self, "Sucesso", "Nome atualizado.")

    def _on_delete(self) -> None:
        if not self.selected_item:
            return
        confirm = QMessageBox.question(
            self,
            "Excluir",
            f"Deseja excluir '{self.selected_item.title}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.service.delete_image(self.selected_item.id)
            self.selected_item = None
            self.refresh_list()

    def _on_export(self) -> None:
        if not self.selected_item:
            return
        ext = os.path.splitext(self.selected_item.file_name)[1]
        dest, _ = QFileDialog.getSaveFileName(self, "Exportar Copia", f"{self.selected_item.title}{ext}")
        if dest:
            try:
                self.service.export_image(self.selected_item.id, dest)
                QMessageBox.information(self, "Sucesso", f"Imagem salva em:\n{dest}")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao exportar: {e}")

    def _on_add_image(self) -> None:
        supported_exts = " ".join(f"*{ext}" for ext in ImageFormatFactorySelector.get_all_supported_extensions())
        fpath, _ = QFileDialog.getOpenFileName(self, "Selecionar Imagem", "", f"Imagens ({supported_exts})")
        if not fpath:
            return
        try:
            self.service.import_image(fpath)
            self.refresh_list()
        except (UnsupportedFormatException, InvalidImageFileException, FileNotFoundError) as e:
            QMessageBox.warning(self, "Erro", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Erro Inesperado", str(e))

    def _on_load_samples(self) -> None:
        sample_dir = os.path.abspath("sample_images")
        if not os.path.exists(sample_dir):
            return
        for fname in sorted(os.listdir(sample_dir)):
            fpath = os.path.join(sample_dir, fname)
            if os.path.isfile(fpath) and not fname.startswith("invalid") and not fname.startswith("corrupted") and not fname.endswith(".txt"):
                try:
                    self.service.import_image(fpath)
                except Exception:
                    pass
        self.refresh_list()

    def _on_test_invalid(self) -> None:
        txt_path = os.path.abspath("sample_images/document.txt")
        corrupted_path = os.path.abspath("sample_images/corrupted_image.jpg")
        missing_path = os.path.abspath("sample_images/nao_existe.jpg")

        msg = []
        try:
            self.service.import_image(txt_path)
            msg.append("Falha no teste txt.")
        except UnsupportedFormatException as e:
            msg.append(f"OK: formato invalido rejeitado ({e})")

        try:
            self.service.import_image(corrupted_path)
            msg.append("Falha no teste arquivo corrompido.")
        except InvalidImageFileException as e:
            msg.append(f"OK: arquivo corrompido rejeitado ({e})")

        try:
            self.service.import_image(missing_path)
            msg.append("Falha no teste caminho ausente.")
        except FileNotFoundError as e:
            msg.append(f"OK: caminho ausente rejeitado ({e})")

        QMessageBox.information(self, "Teste T10.2", "\n\n".join(msg))
