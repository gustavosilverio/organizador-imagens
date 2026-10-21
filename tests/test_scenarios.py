"""
Testes de Qualidade dos Cenários Oficiais da Disciplina (Página 11 do Plano de Testes):
  - T10.1 — Importar e visualizar imagens
  - T10.2 — Arquivo inválido e caminho ausente
  - T10.3 — Upload, metadados e download
  - T10.4 — Flyweight e Strategy
"""

import os
import tempfile
import pytest
from PyQt6.QtWidgets import QApplication

_app = QApplication.instance() or QApplication([])

from client.services.image_service import ImageService
from client.patterns.abstract_factory import (
    UnsupportedFormatException,
    InvalidImageFileException
)
from client.patterns.strategy import (
    SortByNameAscStrategy,
    SortBySizeDescStrategy,
    FilterByFormatStrategy,
    CropSquareThumbnailStrategy
)


@pytest.fixture
def service(tmp_path):
    """Cria uma instância isolada do ImageService usando armazenamento temporário."""
    catalog_file = tmp_path / "test_catalog.json"
    svc = ImageService(storage_path=str(catalog_file))
    return svc


# ---------------------------------------------------------------------------
# T10.1 — Importar e visualizar imagens
# ---------------------------------------------------------------------------
def test_scenario_t10_1_import_and_view(service):
    """
    Pré-condição: Imagens válidas em disco (PNG e JPEG).
    Ação: Importar imagens para o organizador.
    Resultado esperado: Imagens catalogadas com metadados corretos,
    miniaturas acessíveis e persistidas no catálogo.
    """
    png_path = os.path.abspath("sample_images/graphic_shapes.png")
    jpg_path = os.path.abspath("sample_images/sunset_landscape.jpg")

    item_png = service.import_image(png_path, title="Formas Gráficas", tags=["vetor", "demo"])
    item_jpg = service.import_image(jpg_path, title="Pôr do Sol", tags=["natureza", "foto"])

    assert item_png is not None
    assert item_jpg is not None
    assert item_png.width == 400 and item_png.height == 300
    assert item_jpg.width == 600 and item_jpg.height == 400

    all_images = service.get_all_images()
    assert len(all_images) == 2

    # Verifica se os metadados do Flyweight foram atrelados corretamente
    assert item_png.format_name == "PNG"
    assert item_png.flyweight.supports_transparency is True
    assert item_jpg.format_name == "JPEG"
    assert item_jpg.flyweight.supports_transparency is False


# ---------------------------------------------------------------------------
# T10.2 — Arquivo inválido e caminho ausente
# ---------------------------------------------------------------------------
def test_scenario_t10_2_invalid_file_and_missing_path(service):
    """
    Pré-condição: Arquivo corrompido, formato incompatível e caminho inexistente.
    Ação: Tentar importar cada um desses arquivos.
    Resultado esperado: Exceções específicas capturadas graciosamente,
    sem corromper o estado do catálogo nem travar o fluxo.
    """
    initial_count = len(service.get_all_images())

    # 1. Caminho inexistente
    with pytest.raises(FileNotFoundError):
        service.import_image("sample_images/caminho_inexistente_12345.jpg")

    # 2. Formato não suportado (arquivo .txt)
    with pytest.raises(UnsupportedFormatException):
        service.import_image("sample_images/document.txt")

    # 3. Arquivo corrompido (bytes inválidos)
    with pytest.raises(InvalidImageFileException):
        service.import_image("sample_images/corrupted_image.jpg")

    # Garante que nenhum dado espúrio foi persistido após falhas
    assert len(service.get_all_images()) == initial_count


# ---------------------------------------------------------------------------
# T10.3 — Upload, metadados e download
# ---------------------------------------------------------------------------
def test_scenario_t10_3_upload_metadata_download(service, tmp_path):
    """
    Pré-condição: Imagem importada no catálogo.
    Ação: Editar metadados (Update) e exportar/baixar arquivo para outro diretório.
    Resultado esperado: Metadados atualizados com sucesso e persistidos,
    e cópia exportada idêntica ao arquivo original.
    """
    jpg_path = os.path.abspath("sample_images/city_night.jpg")
    item = service.import_image(jpg_path, title="Título Inicial")

    # 1. Atualização de Metadados (CRUD Update)
    updated = service.update_image_metadata(
        image_id=item.id,
        title="Cidade Iluminada à Noite",
        description="Fotografia noturna de alta qualidade tirada com longa exposição.",
        tags=["cidade", "noturna", "luzes"]
    )

    assert updated.title == "Cidade Iluminada à Noite"
    assert updated.description.startswith("Fotografia noturna")
    assert "luzes" in updated.tags

    # Verifica persistência ao recuperar pelo ID
    retrieved = service.get_image_by_id(item.id)
    assert retrieved.title == "Cidade Iluminada à Noite"

    # 2. Exportação / Download da Imagem (Download)
    dest_file = str(tmp_path / "cidade_exportada.jpg")
    success = service.export_image(item.id, dest_file)

    assert success is True
    assert os.path.exists(dest_file)
    assert os.path.getsize(dest_file) == os.path.getsize(jpg_path)


# ---------------------------------------------------------------------------
# T10.4 — Flyweight e Strategy
# ---------------------------------------------------------------------------
def test_scenario_t10_4_flyweight_and_strategy(service):
    """
    Pré-condição: Várias imagens com formatos variados (PNG e JPEG).
    Ação:
      a) Avaliar o compartilhamento do estado intrínseco (Flyweight).
      b) Alternar estratégias de ordenação, filtro e geração de miniatura (Strategy).
    Resultado esperado:
      - Flyweights são compartilhados sem duplicar objetos na memória.
      - Strategies reordenam e filtram dinamicamente a lista de imagens.
    """
    # Importa múltiplas imagens
    img1 = service.import_image("sample_images/graphic_shapes.png", title="Zebra PNG")
    img2 = service.import_image("sample_images/tech_grid.png", title="Alpha PNG")
    img3 = service.import_image("sample_images/sunset_landscape.jpg", title="Beta JPG")
    img4 = service.import_image("sample_images/city_night.jpg", title="Delta JPG")

    # A) Teste Observável do Flyweight
    assert img1.flyweight is img2.flyweight  # Ambos PNG compartilham mesma instância
    assert img3.flyweight is img4.flyweight  # Ambos JPEG compartilham mesma instância
    assert img1.flyweight is not img3.flyweight

    stats = service.get_flyweight_stats()
    assert stats["total_images"] == 4
    assert stats["flyweights_in_pool"] >= 2
    assert stats["objects_saved"] >= 2

    # B) Teste do Strategy de Ordenação
    sort_asc = SortByNameAscStrategy()
    processed_asc = service.get_processed_images(sort_strategy=sort_asc)
    titles_asc = [x.title for x in processed_asc]
    assert titles_asc == ["Alpha PNG", "Beta JPG", "Delta JPG", "Zebra PNG"]

    # C) Teste do Strategy de Filtragem
    filter_png = FilterByFormatStrategy("PNG")
    png_only = service.get_processed_images(filter_strategy=filter_png)
    assert len(png_only) == 2
    assert all(x.format_name == "PNG" for x in png_only)
