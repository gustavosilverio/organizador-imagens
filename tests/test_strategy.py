"""
Testes Unitários para o Padrão Strategy.
Verifica a intercambialidade e o funcionamento correto de:
  - Algoritmos de Ordenação (SortStrategy)
  - Algoritmos de Filtragem (FilterStrategy)
  - Algoritmos de Renderização de Miniaturas (ThumbnailRenderStrategy)
"""

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QPixmap

_app = QApplication.instance() or QApplication([])

from client.models.image_item import ImageItem
from client.patterns.strategy import (
    SortByNameAscStrategy,
    SortByNameDescStrategy,
    SortBySizeAscStrategy,
    SortBySizeDescStrategy,
    SortByDateDescStrategy,
    SortByFormatStrategy,
    FilterAllStrategy,
    FilterByFormatStrategy,
    FilterBySizeStrategy,
    FilterBySearchStrategy,
    SmoothThumbnailStrategy,
    FastThumbnailStrategy,
    CropSquareThumbnailStrategy,
    LetterboxThumbnailStrategy,
)


def create_sample_items():
    i1 = ImageItem("sample_images/sunset_landscape.jpg", 600, 400, 100000, "JPEG", title="Beta", tags=["nature"])
    i1.date_modified = "2026-01-01 10:00:00"

    i2 = ImageItem("sample_images/graphic_shapes.png", 400, 300, 50000, "PNG", title="Alpha", tags=["art"])
    i2.date_modified = "2026-01-02 12:00:00"

    i3 = ImageItem("sample_images/city_night.jpg", 800, 600, 3000000, "JPEG", title="Gama", tags=["urban"])
    i3.date_modified = "2026-01-03 14:00:00"

    return [i1, i2, i3]


def test_sort_by_name_strategy():
    items = create_sample_items()

    asc_strat = SortByNameAscStrategy()
    sorted_asc = asc_strat.sort(items)
    assert [x.title for x in sorted_asc] == ["Alpha", "Beta", "Gama"]

    desc_strat = SortByNameDescStrategy()
    sorted_desc = desc_strat.sort(items)
    assert [x.title for x in sorted_desc] == ["Gama", "Beta", "Alpha"]


def test_sort_by_size_strategy():
    items = create_sample_items()

    asc_strat = SortBySizeAscStrategy()
    sorted_asc = asc_strat.sort(items)
    assert [x.title for x in sorted_asc] == ["Alpha", "Beta", "Gama"]  # 50KB, 100KB, 3MB

    desc_strat = SortBySizeDescStrategy()
    sorted_desc = desc_strat.sort(items)
    assert [x.title for x in sorted_desc] == ["Gama", "Beta", "Alpha"]


def test_filter_by_format_strategy():
    items = create_sample_items()

    png_filter = FilterByFormatStrategy("PNG")
    png_items = png_filter.filter(items)
    assert len(png_items) == 1
    assert png_items[0].title == "Alpha"

    jpeg_filter = FilterByFormatStrategy("JPEG")
    jpeg_items = jpeg_filter.filter(items)
    assert len(jpeg_items) == 2


def test_filter_by_size_strategy():
    items = create_sample_items()

    small_filter = FilterBySizeStrategy("small")  # < 500KB
    small_items = small_filter.filter(items)
    assert len(small_items) == 2  # 50KB and 100KB

    large_filter = FilterBySizeStrategy("large")  # > 2MB
    large_items = large_filter.filter(items)
    assert len(large_items) == 1
    assert large_items[0].title == "Gama"


def test_filter_by_search_strategy():
    items = create_sample_items()

    search_art = FilterBySearchStrategy("art")
    assert len(search_art.filter(items)) == 1

    search_beta = FilterBySearchStrategy("beta")
    assert len(search_beta.filter(items)) == 1

    search_nonexistent = FilterBySearchStrategy("inexistente")
    assert len(search_nonexistent.filter(items)) == 0


def test_thumbnail_rendering_strategies():
    pixmap = QPixmap(200, 100)
    pixmap.fill()
    target_size = QSize(80, 80)

    smooth_strat = SmoothThumbnailStrategy()
    fast_strat = FastThumbnailStrategy()
    crop_strat = CropSquareThumbnailStrategy()
    letterbox_strat = LetterboxThumbnailStrategy()

    p_smooth = smooth_strat.render(pixmap, target_size)
    assert not p_smooth.isNull()

    p_fast = fast_strat.render(pixmap, target_size)
    assert not p_fast.isNull()

    p_crop = crop_strat.render(pixmap, target_size)
    assert not p_crop.isNull()
    assert p_crop.width() == 80 and p_crop.height() == 80

    p_letter = letterbox_strat.render(pixmap, target_size)
    assert not p_letter.isNull()
    assert p_letter.width() == 80 and p_letter.height() == 80
