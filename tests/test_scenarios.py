import os
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
    SortBySizeDescStrategy
)


@pytest.fixture
def service(tmp_path):
    catalog_file = tmp_path / "test_catalog.json"
    return ImageService(storage_path=str(catalog_file))


def test_scenario_t10_1_import_and_view(service):
    png_path = os.path.abspath("sample_images/graphic_shapes.png")
    jpg_path = os.path.abspath("sample_images/sunset_landscape.jpg")

    item_png = service.import_image(png_path, title="Formas Graficas", tags=["vetor", "demo"])
    item_jpg = service.import_image(jpg_path, title="Por do Sol", tags=["natureza", "foto"])

    assert item_png is not None
    assert item_jpg is not None
    assert item_png.width == 400 and item_png.height == 300
    assert item_jpg.width == 600 and item_jpg.height == 400

    all_images = service.get_all_images()
    assert len(all_images) == 2
    assert item_png.format_name == "PNG"
    assert item_png.flyweight.supports_transparency is True
    assert item_jpg.format_name == "JPEG"
    assert item_jpg.flyweight.supports_transparency is False


def test_scenario_t10_2_invalid_file_and_missing_path(service):
    initial_count = len(service.get_all_images())

    with pytest.raises(FileNotFoundError):
        service.import_image("sample_images/caminho_inexistente.jpg")

    with pytest.raises(UnsupportedFormatException):
        service.import_image("sample_images/document.txt")

    with pytest.raises(InvalidImageFileException):
        service.import_image("sample_images/corrupted_image.jpg")

    assert len(service.get_all_images()) == initial_count


def test_scenario_t10_3_upload_metadata_download(service, tmp_path):
    jpg_path = os.path.abspath("sample_images/city_night.jpg")
    item = service.import_image(jpg_path, title="Titulo Inicial")

    updated = service.update_image_metadata(
        image_id=item.id,
        title="Cidade Iluminada a Noite",
        description="Fotografia noturna.",
        tags=["cidade", "noturna"]
    )

    assert updated.title == "Cidade Iluminada a Noite"
    retrieved = service.get_image_by_id(item.id)
    assert retrieved.title == "Cidade Iluminada a Noite"

    dest_file = str(tmp_path / "cidade_exportada.jpg")
    success = service.export_image(item.id, dest_file)

    assert success is True
    assert os.path.exists(dest_file)
    assert os.path.getsize(dest_file) == os.path.getsize(jpg_path)


def test_scenario_t10_4_flyweight_and_strategy(service):
    img1 = service.import_image("sample_images/graphic_shapes.png", title="Zebra PNG")
    img2 = service.import_image("sample_images/tech_grid.png", title="Alpha PNG")
    img3 = service.import_image("sample_images/sunset_landscape.jpg", title="Beta JPG")
    img4 = service.import_image("sample_images/city_night.jpg", title="Delta JPG")

    assert img1.flyweight is img2.flyweight
    assert img3.flyweight is img4.flyweight
    assert img1.flyweight is not img3.flyweight

    stats = service.get_flyweight_stats()
    assert stats["total_images"] == 4
    assert stats["objects_saved"] >= 2

    sort_asc = SortByNameAscStrategy()
    processed_asc = service.get_sorted_images(sort_strategy=sort_asc)
    titles_asc = [x.title for x in processed_asc]
    assert titles_asc == ["Alpha PNG", "Beta JPG", "Delta JPG", "Zebra PNG"]

    sort_size_desc = SortBySizeDescStrategy()
    processed_size = service.get_sorted_images(sort_strategy=sort_size_desc)
    assert processed_size[0].file_size_bytes >= processed_size[-1].file_size_bytes
