import os
from typing import List, Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QScrollArea, QGridLayout,
    QFileDialog, QMessageBox, QStatusBar, QToolBar, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt

from client.models.image_item import ImageItem
from client.services.image_service import ImageService
from client.ui.image_card import ImageCard
from client.ui.image_detail_dialog import ImageDetailDialog
from client.ui.flyweight_stats_widget import FlyweightStatsWidget
from client.ui.style import APP_STYLESHEET

from client.patterns.abstract_factory import (
    UnsupportedFormatException,
    InvalidImageFileException,
    ImageFormatFactorySelector
)
from client.patterns.strategy import (
    SortStrategy,
    SortByNameAscStrategy,
    SortByNameDescStrategy,
    SortBySizeAscStrategy,
    SortBySizeDescStrategy,
    ThumbnailRenderStrategy,
    SmoothThumbnailStrategy,
)


class MainWindow(QMainWindow):
    def __init__(self, service: Optional[ImageService] = None):
        super().__init__()
        self.service = service or ImageService()
        self.selected_image_id: Optional[str] = None
        self.card_widgets: List[ImageCard] = []

        self.setWindowTitle("Organizador de Imagens - Cliente QT")
        self.resize(1000, 700)
        self.setMinimumSize(800, 550)
        self.setStyleSheet(APP_STYLESHEET)

        self._setup_toolbar()
        self._setup_ui()
        self._setup_statusbar()
        self.refresh_gallery()

    def _setup_toolbar(self) -> None:
        toolbar = QToolBar("Acoes")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        btn_import = QPushButton("Importar Imagem")
        btn_import.clicked.connect(self._on_import_files)
        toolbar.addWidget(btn_import)

        toolbar.addSeparator()

        btn_samples = QPushButton("Carregar Exemplos")
        btn_samples.setObjectName("btnSecondary")
        btn_samples.clicked.connect(self._on_load_samples)
        toolbar.addWidget(btn_samples)

        btn_test_error = QPushButton("Testar Arquivo Invalido")
        btn_test_error.setObjectName("btnSecondary")
        btn_test_error.clicked.connect(self._on_test_invalid_file)
        toolbar.addWidget(btn_test_error)

        toolbar.addSeparator()

        self.btn_delete_selected = QPushButton("Excluir Selecionada")
        self.btn_delete_selected.setObjectName("btnDanger")
        self.btn_delete_selected.setEnabled(False)
        self.btn_delete_selected.clicked.connect(self._on_delete_selected)
        toolbar.addWidget(self.btn_delete_selected)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        self.lbl_backend = QLabel("Modo: Local")
        self.lbl_backend.setStyleSheet("color: #38BDF8; font-weight: bold; padding: 0 10px;")
        toolbar.addWidget(self.lbl_backend)

    def _setup_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        control_panel = QFrame()
        control_panel.setObjectName("controlPanel")
        control_layout = QHBoxLayout(control_panel)
        control_layout.setContentsMargins(10, 8, 10, 8)
        control_layout.setSpacing(12)

        control_layout.addWidget(QLabel("Ordenar por:"))
        self.combo_sort = QComboBox()
        self.sort_strategies = [
            SortByNameAscStrategy(),
            SortByNameDescStrategy(),
            SortBySizeAscStrategy(),
            SortBySizeDescStrategy(),
        ]
        for strat in self.sort_strategies:
            self.combo_sort.addItem(strat.name, strat)
        self.combo_sort.currentIndexChanged.connect(self._on_sort_changed)
        control_layout.addWidget(self.combo_sort)

        control_layout.addStretch()
        main_layout.addWidget(control_panel)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.gallery_container = QWidget()
        self.gallery_container.setStyleSheet("background-color: transparent;")
        self.grid_layout = QGridLayout(self.gallery_container)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        self.grid_layout.setSpacing(16)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.scroll_area.setWidget(self.gallery_container)
        main_layout.addWidget(self.scroll_area, stretch=1)

        self.flyweight_widget = FlyweightStatsWidget(self.service)
        main_layout.addWidget(self.flyweight_widget)

    def _setup_statusbar(self) -> None:
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Pronto.")

    def refresh_gallery(self) -> None:
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.card_widgets.clear()

        active_sort = self.combo_sort.currentData()
        images = self.service.get_sorted_images(sort_strategy=active_sort)
        total_in_db = len(images)

        if not images:
            empty_label = QLabel("Nenhuma imagem cadastrada. Clique em 'Importar Imagem' para comecar.")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("color: #64748B; font-size: 14px; padding: 60px;")
            self.grid_layout.addWidget(empty_label, 0, 0)
        else:
            columns = max(1, (self.scroll_area.width() - 40) // (ImageCard.CARD_WIDTH + 16))
            columns = max(2, min(columns, 5))
            thumb_strategy = SmoothThumbnailStrategy()

            for index, img_item in enumerate(images):
                row = index // columns
                col = index % columns

                card = ImageCard(img_item, thumbnail_strategy=thumb_strategy)
                card.clicked.connect(self._on_card_clicked)
                card.double_clicked.connect(self._on_card_double_clicked)
                card.delete_requested.connect(self._on_card_delete_requested)
                card.export_requested.connect(self._on_card_export_requested)

                if img_item.id == self.selected_image_id:
                    card.set_selected(True)

                self.grid_layout.addWidget(card, row, col)
                self.card_widgets.append(card)

        self.flyweight_widget.refresh()
        self.status_bar.showMessage(f"Total: {total_in_db} imagens | Ordenacao: {active_sort.name}")
        self.btn_delete_selected.setEnabled(self.selected_image_id is not None)

    def _on_sort_changed(self) -> None:
        self.refresh_gallery()

    def _on_card_clicked(self, image_id: str) -> None:
        self.selected_image_id = image_id
        for card in self.card_widgets:
            card.set_selected(card.item.id == image_id)
        self.btn_delete_selected.setEnabled(True)

    def _on_card_double_clicked(self, image_id: str) -> None:
        item = self.service.get_image_by_id(image_id)
        if not item:
            return
        dialog = ImageDetailDialog(item, self.service, self)
        dialog.image_updated.connect(lambda _: self.refresh_gallery())
        dialog.image_deleted.connect(lambda _: self.refresh_gallery())
        dialog.exec()

    def _on_card_export_requested(self, image_id: str) -> None:
        item = self.service.get_image_by_id(image_id)
        if not item:
            return
        dest_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Imagem",
            item.file_name,
            f"Arquivo (*{os.path.splitext(item.file_name)[1]})"
        )
        if dest_path:
            try:
                self.service.export_image(image_id, dest_path)
                QMessageBox.information(self, "Sucesso", f"Imagem salva em: {dest_path}")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha na exportacao: {e}")

    def _on_card_delete_requested(self, image_id: str) -> None:
        item = self.service.get_image_by_id(image_id)
        if not item:
            return
        confirm = QMessageBox.question(
            self,
            "Confirmar Exclusao",
            f"Deseja remover '{item.title}' do catalogo?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.service.delete_image(image_id)
            if self.selected_image_id == image_id:
                self.selected_image_id = None
            self.refresh_gallery()

    def _on_delete_selected(self) -> None:
        if self.selected_image_id:
            self._on_card_delete_requested(self.selected_image_id)

    def _on_import_files(self) -> None:
        supported_exts = " ".join(f"*{ext}" for ext in ImageFormatFactorySelector.get_all_supported_extensions())
        filter_str = f"Imagens Suportadas ({supported_exts});;Todos os Arquivos (*.*)"

        files, _ = QFileDialog.getOpenFileNames(self, "Selecionar Imagens", "", filter_str)
        if not files:
            return

        imported_count = 0
        errors = []

        for fpath in files:
            try:
                self.service.import_image(fpath)
                imported_count += 1
            except (UnsupportedFormatException, InvalidImageFileException, FileNotFoundError) as e:
                errors.append(f"{os.path.basename(fpath)}: {str(e)}")
            except Exception as e:
                errors.append(f"{os.path.basename(fpath)}: {e}")

        self.refresh_gallery()

        if errors:
            QMessageBox.warning(
                self,
                "Aviso de Importacao",
                f"{imported_count} imagens importadas.\n\nErros:\n" + "\n".join(errors[:5])
            )
        elif imported_count > 0:
            self.status_bar.showMessage(f"{imported_count} imagem(ns) importada(s).", 4000)

    def _on_load_samples(self) -> None:
        sample_dir = os.path.abspath("sample_images")
        if not os.path.exists(sample_dir):
            QMessageBox.warning(self, "Aviso", f"Pasta '{sample_dir}' nao encontrada.")
            return

        imported = 0
        for fname in sorted(os.listdir(sample_dir)):
            fpath = os.path.join(sample_dir, fname)
            if os.path.isfile(fpath) and not fname.startswith("invalid") and not fname.startswith("corrupted") and not fname.endswith(".txt"):
                try:
                    self.service.import_image(fpath)
                    imported += 1
                except Exception:
                    pass

        self.refresh_gallery()
        QMessageBox.information(self, "Sucesso", f"{imported} imagens de exemplo carregadas.")

    def _on_test_invalid_file(self) -> None:
        txt_path = os.path.abspath("sample_images/document.txt")
        corrupted_path = os.path.abspath("sample_images/corrupted_image.jpg")
        missing_path = os.path.abspath("sample_images/arquivo_fantasma.jpg")

        results = []

        try:
            self.service.import_image(txt_path)
            results.append("Falha: arquivo .txt aceito indevidamente.")
        except UnsupportedFormatException as e:
            results.append(f"Sucesso: formato nao suportado rejeitado ({e})")
        except Exception as e:
            results.append(f"Sucesso: erro capturado ({e})")

        try:
            self.service.import_image(corrupted_path)
            results.append("Falha: arquivo corrompido aceito indevidamente.")
        except InvalidImageFileException as e:
            results.append(f"Sucesso: arquivo corrompido rejeitado ({e})")
        except Exception as e:
            results.append(f"Sucesso: erro capturado ({e})")

        try:
            self.service.import_image(missing_path)
            results.append("Falha: caminho inexistente aceito indevidamente.")
        except FileNotFoundError as e:
            results.append(f"Sucesso: caminho inexistente rejeitado ({e})")
        except Exception as e:
            results.append(f"Sucesso: erro capturado ({e})")

        dialog_text = "Resultado do Teste T10.2 (Arquivo invalido e caminho ausente):\n\n" + "\n".join(results)
        QMessageBox.information(self, "Teste T10.2", dialog_text)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        columns = max(1, (self.scroll_area.width() - 40) // (ImageCard.CARD_WIDTH + 16))
        columns = max(2, min(columns, 5))
        for index, card in enumerate(self.card_widgets):
            row = index // columns
            col = index % columns
            self.grid_layout.addWidget(card, row, col)
