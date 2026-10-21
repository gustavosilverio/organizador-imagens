"""
Janela Principal da Aplicação: MainWindow
Interface gráfica desktop moderna desenvolvida em PyQt6.
Integra e torna observáveis os três Design Patterns exigidos:
  - Abstract Factory (importação, validação e leitores por formato)
  - Flyweight (compartilhamento de recursos comuns e economia de memória)
  - Strategy (algoritmos intercambiáveis de ordenação, filtro e geração de miniaturas)
"""

import os
from typing import List, Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QScrollArea, QGridLayout,
    QFileDialog, QMessageBox, QStatusBar, QToolBar, QFrame, QSizePolicy
)
from PyQt6.QtGui import QAction, QIcon, QFont
from PyQt6.QtCore import Qt, QSize

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
    SortByDateDescStrategy,
    SortByDateAscStrategy,
    SortByFormatStrategy,
    FilterStrategy,
    FilterAllStrategy,
    FilterByFormatStrategy,
    FilterBySizeStrategy,
    FilterBySearchStrategy,
    ThumbnailRenderStrategy,
    SmoothThumbnailStrategy,
    FastThumbnailStrategy,
    CropSquareThumbnailStrategy,
    LetterboxThumbnailStrategy
)


class MainWindow(QMainWindow):
    """Janela principal do cliente QT para o Organizador de Imagens."""

    def __init__(self, service: Optional[ImageService] = None):
        super().__init__()
        self.service = service or ImageService()
        self.selected_image_id: Optional[str] = None
        self.card_widgets: List[ImageCard] = []

        self.setWindowTitle("Organizador de Imagens • Cliente Desktop (Design Patterns)")
        self.resize(1150, 780)
        self.setMinimumSize(900, 600)

        # Aplica a folha de estilos personalizada
        self.setStyleSheet(APP_STYLESHEET)

        self._setup_toolbar()
        self._setup_ui()
        self._setup_statusbar()

        # Carrega dados iniciais na interface
        self.refresh_gallery()

    # -----------------------------------------------------------------------
    # Barra de Ferramentas Superior (Toolbar)
    # -----------------------------------------------------------------------

    def _setup_toolbar(self) -> None:
        toolbar = QToolBar("Ações Rápidas")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Botão Importar Imagens (Cenários T10.1 e T10.2)
        btn_import = QPushButton("📁 Importar Imagem(ns)")
        btn_import.setToolTip("Selecionar arquivos de imagem (PNG, JPEG, BMP) para o organizador")
        btn_import.clicked.connect(self._on_import_files)
        toolbar.addWidget(btn_import)

        toolbar.addSeparator()

        # Botão Carregar Imagens de Exemplo
        btn_samples = QPushButton("🧪 Carregar Imagens de Exemplo")
        btn_samples.setObjectName("btnSecondary")
        btn_samples.setToolTip("Carrega lote com imagens de teste PNG, JPEG e arquivos para validação de erros")
        btn_samples.clicked.connect(self._on_load_samples)
        toolbar.addWidget(btn_samples)

        # Botão Testar Arquivo Inválido (Cenário T10.2)
        btn_test_error = QPushButton("⚠️ Testar Arquivo Inválido")
        btn_test_error.setObjectName("btnSecondary")
        btn_test_error.setToolTip("Tenta importar arquivo inválido/corrompido para testar resiliência (T10.2)")
        btn_test_error.clicked.connect(self._on_test_invalid_file)
        toolbar.addWidget(btn_test_error)

        toolbar.addSeparator()

        # Botão Excluir Selecionada
        self.btn_delete_selected = QPushButton("🗑️ Excluir Selecionada")
        self.btn_delete_selected.setObjectName("btnDanger")
        self.btn_delete_selected.setEnabled(False)
        self.btn_delete_selected.clicked.connect(self._on_delete_selected)
        toolbar.addWidget(self.btn_delete_selected)

        # Espaçador flexível
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        # Indicador de Modo Backend
        self.lbl_backend = QLabel("Modo: Local (JSON)")
        self.lbl_backend.setStyleSheet("color: #38BDF8; font-weight: bold; padding: 0 10px;")
        toolbar.addWidget(self.lbl_backend)

    # -----------------------------------------------------------------------
    # Configuração da Interface Principal
    # -----------------------------------------------------------------------

    def _setup_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # 1. Painel de Controle de Strategies (Ordenação, Filtro e Miniaturas)
        strategy_panel = QFrame()
        strategy_panel.setObjectName("strategyPanel")
        strategy_layout = QHBoxLayout(strategy_panel)
        strategy_layout.setContentsMargins(10, 8, 10, 8)
        strategy_layout.setSpacing(12)

        # Campo de Busca Textual
        strategy_layout.addWidget(QLabel("🔍 Buscar:"))
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Filtrar por nome, tag ou descrição...")
        self.txt_search.textChanged.connect(self._on_search_changed)
        strategy_layout.addWidget(self.txt_search, stretch=2)

        # Strategy: Filtro
        strategy_layout.addWidget(QLabel("🎯 Filtro:"))
        self.combo_filter = QComboBox()
        self.filter_strategies = [
            FilterAllStrategy(),
            FilterByFormatStrategy("JPEG"),
            FilterByFormatStrategy("PNG"),
            FilterByFormatStrategy("BMP"),
            FilterBySizeStrategy("small"),
            FilterBySizeStrategy("medium"),
            FilterBySizeStrategy("large"),
        ]
        for strat in self.filter_strategies:
            self.combo_filter.addItem(strat.name, strat)
        self.combo_filter.currentIndexChanged.connect(self._on_filter_changed)
        strategy_layout.addWidget(self.combo_filter)

        # Strategy: Ordenação
        strategy_layout.addWidget(QLabel("↕️ Ordenação:"))
        self.combo_sort = QComboBox()
        self.sort_strategies = [
            SortByNameAscStrategy(),
            SortByNameDescStrategy(),
            SortBySizeAscStrategy(),
            SortBySizeDescStrategy(),
            SortByDateDescStrategy(),
            SortByDateAscStrategy(),
            SortByFormatStrategy(),
        ]
        for strat in self.sort_strategies:
            self.combo_sort.addItem(strat.name, strat)
        self.combo_sort.currentIndexChanged.connect(self._on_sort_changed)
        strategy_layout.addWidget(self.combo_sort)

        # Strategy: Geração de Miniaturas
        strategy_layout.addWidget(QLabel("🖼️ Miniatura:"))
        self.combo_thumb = QComboBox()
        self.thumb_strategies = [
            SmoothThumbnailStrategy(),
            FastThumbnailStrategy(),
            CropSquareThumbnailStrategy(),
            LetterboxThumbnailStrategy(),
        ]
        for strat in self.thumb_strategies:
            self.combo_thumb.addItem(strat.name, strat)
        self.combo_thumb.currentIndexChanged.connect(self._on_thumb_strategy_changed)
        strategy_layout.addWidget(self.combo_thumb)

        main_layout.addWidget(strategy_panel)

        # 2. Área de Rolagem para a Grade da Galeria de Imagens
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

        # 3. Widget de Demonstração e Estatísticas do Padrão Flyweight
        self.flyweight_widget = FlyweightStatsWidget(self.service)
        main_layout.addWidget(self.flyweight_widget)

    # -----------------------------------------------------------------------
    # Barra de Status
    # -----------------------------------------------------------------------

    def _setup_statusbar(self) -> None:
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Pronto. Importe imagens para começar.")

    # -----------------------------------------------------------------------
    # Atualização e Renderização da Galeria
    # -----------------------------------------------------------------------

    def refresh_gallery(self) -> None:
        """Limpa e recria a grade de imagens aplicando as Strategies ativas."""
        # 1. Limpa widgets anteriores da grade
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.card_widgets.clear()

        # 2. Obtém a lista processada pelas Strategies de Ordenação e Filtragem
        active_sort = self.combo_sort.currentData()
        active_filter = self._get_combined_filter()
        active_thumb = self.combo_thumb.currentData()

        images = self.service.get_processed_images(
            sort_strategy=active_sort,
            filter_strategy=active_filter
        )

        total_in_db = len(self.service.get_all_images())

        if not images:
            empty_label = QLabel(
                "Nenhuma imagem encontrada para os critérios atuais.<br>"
                "Clique em <b>'📁 Importar Imagem(ns)'</b> ou <b>'🧪 Carregar Imagens de Exemplo'</b>."
            )
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("color: #64748B; font-size: 14px; padding: 60px;")
            self.grid_layout.addWidget(empty_label, 0, 0)
        else:
            # Distribui em grade de até 4 colunas dinâmicas
            columns = max(1, (self.scroll_area.width() - 40) // (ImageCard.CARD_WIDTH + 16))
            columns = max(2, min(columns, 5))

            for index, img_item in enumerate(images):
                row = index // columns
                col = index % columns

                card = ImageCard(img_item, thumbnail_strategy=active_thumb)
                card.clicked.connect(self._on_card_clicked)
                card.double_clicked.connect(self._on_card_double_clicked)
                card.delete_requested.connect(self._on_card_delete_requested)
                card.export_requested.connect(self._on_card_export_requested)

                if img_item.id == self.selected_image_id:
                    card.set_selected(True)

                self.grid_layout.addWidget(card, row, col)
                self.card_widgets.append(card)

        # Atualiza métricas do Flyweight e barra de status
        self.flyweight_widget.refresh()
        self.status_bar.showMessage(
            f"Exibindo {len(images)} de {total_in_db} imagens • "
            f"Estratégia de Ordenação: '{active_sort.name}' • "
            f"Estratégia de Miniatura: '{active_thumb.name}'"
        )
        self.btn_delete_selected.setEnabled(self.selected_image_id is not None)

    def _get_combined_filter(self) -> FilterStrategy:
        """Combina o filtro do ComboBox com o termo digitado na caixa de busca."""
        base_filter = self.combo_filter.currentData()
        search_query = self.txt_search.text().strip()

        if search_query:
            return FilterBySearchStrategy(search_query)
        return base_filter

    # -----------------------------------------------------------------------
    # Handlers dos Controles de Strategy
    # -----------------------------------------------------------------------

    def _on_sort_changed(self) -> None:
        self.refresh_gallery()

    def _on_filter_changed(self) -> None:
        self.refresh_gallery()

    def _on_search_changed(self) -> None:
        self.refresh_gallery()

    def _on_thumb_strategy_changed(self) -> None:
        """Quando a Thumbnail Strategy muda, atualiza as miniaturas sem recriar toda a grade."""
        new_strategy = self.combo_thumb.currentData()
        for card in self.card_widgets:
            card.update_thumbnail(new_strategy)
        self.status_bar.showMessage(f"Estratégia de Miniatura atualizada para: '{new_strategy.name}'")

    # -----------------------------------------------------------------------
    # Handlers de Seleção e Ações de Imagem (CRUD)
    # -----------------------------------------------------------------------

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
                QMessageBox.information(self, "Exportação Concluída", f"Imagem salva com sucesso em:\n{dest_path}")
            except Exception as e:
                QMessageBox.critical(self, "Falha na Exportação", f"Erro: {e}")

    def _on_card_delete_requested(self, image_id: str) -> None:
        item = self.service.get_image_by_id(image_id)
        if not item:
            return
        confirm = QMessageBox.question(
            self,
            "Excluir Imagem",
            f"Deseja remover '{item.title}' do catálogo?",
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

    # -----------------------------------------------------------------------
    # Importação e Cenários de Teste (T10.1 e T10.2)
    # -----------------------------------------------------------------------

    def _on_import_files(self) -> None:
        """Abre caixa de diálogo para seleção de múltiplos arquivos de imagem."""
        supported_exts = " ".join(f"*{ext}" for ext in ImageFormatFactorySelector.get_all_supported_extensions())
        filter_str = f"Imagens Suportadas ({supported_exts});;Todos os Arquivos (*.*)"

        files, _ = QFileDialog.getOpenFileNames(self, "Selecionar Imagens para Importar", "", filter_str)
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
                errors.append(f"{os.path.basename(fpath)}: Erro inesperado ({e})")

        self.refresh_gallery()

        if errors:
            error_msg = "\n".join(errors[:5])
            if len(errors) > 5:
                error_msg += f"\n...e mais {len(errors) - 5} erros."
            QMessageBox.warning(
                self,
                "Avisos de Importação",
                f"Foram importadas {imported_count} imagens com sucesso.\n\n"
                f"Arquivos com problemas (rejeitados com segurança):\n{error_msg}"
            )
        elif imported_count > 0:
            self.status_bar.showMessage(f"Sucesso: {imported_count} imagem(ns) importada(s).", 4000)

    def _on_load_samples(self) -> None:
        """Carrega automaticamente as imagens da pasta sample_images para demonstração rápida."""
        sample_dir = os.path.abspath("sample_images")
        if not os.path.exists(sample_dir):
            QMessageBox.warning(self, "Aviso", f"Diretório de exemplos '{sample_dir}' não encontrado.")
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
        QMessageBox.information(
            self,
            "Exemplos Carregados",
            f"{imported} imagens de exemplo (PNG e JPEG) foram importadas e catalogadas com sucesso!"
        )

    def _on_test_invalid_file(self) -> None:
        """
        Demonstração explícita do Cenário T10.2:
        Tenta importar propositalmente um arquivo inválido e um caminho ausente,
        provando que a aplicação trata graciosamente sem travamentos ou quebras.
        """
        # Teste 1: Arquivo com extensão incompatível (.txt)
        txt_path = os.path.abspath("sample_images/document.txt")
        # Teste 2: Arquivo JPG com bytes corrompidos
        corrupted_path = os.path.abspath("sample_images/corrupted_image.jpg")
        # Teste 3: Caminho inexistente
        missing_path = os.path.abspath("sample_images/arquivo_fantasma_inexistente.jpg")

        results = []

        # Executa teste 1
        try:
            self.service.import_image(txt_path)
            results.append("❌ Falha: arquivo .txt deveria ter sido rejeitado!")
        except UnsupportedFormatException as e:
            results.append(f"✓ Formato não suportado detectado: {e}")
        except Exception as e:
            results.append(f"✓ Erro capturado: {e}")

        # Executa teste 2
        try:
            self.service.import_image(corrupted_path)
            results.append("❌ Falha: arquivo corrompido deveria ter sido rejeitado!")
        except InvalidImageFileException as e:
            results.append(f"✓ Arquivo corrompido detectado com segurança: {e}")
        except Exception as e:
            results.append(f"✓ Erro capturado: {e}")

        # Executa teste 3
        try:
            self.service.import_image(missing_path)
            results.append("❌ Falha: caminho ausente deveria ter lançado erro!")
        except FileNotFoundError as e:
            results.append(f"✓ Caminho ausente detectado com segurança: {e}")
        except Exception as e:
            results.append(f"✓ Erro capturado: {e}")

        dialog_text = (
            "<b>Demonstração do Cenário T10.2 (Arquivo inválido e caminho ausente):</b><br><br>"
            + "<br><br>".join(results)
            + "<br><br><b>Resultado:</b> Todas as exceções foram tratadas de forma graciosa "
            "pela Abstract Factory e pelo Service, sem travamento da interface Qt!"
        )
        QMessageBox.information(self, "Teste de Resiliência T10.2", dialog_text)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        # Reorganiza o layout da grade conforme a largura da janela muda
        columns = max(1, (self.scroll_area.width() - 40) // (ImageCard.CARD_WIDTH + 16))
        columns = max(2, min(columns, 5))
        for index, card in enumerate(self.card_widgets):
            row = index // columns
            col = index % columns
            self.grid_layout.addWidget(card, row, col)
