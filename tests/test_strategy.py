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
    SmoothThumbnailStrategy,
    FastThumbnailStrategy,
)


def create_sample_items():
    i1 = ImageItem("sample_images/sunset_landscape.jpg", 600, 400, 100000, "JPEG", title="Beta", tags=["nature"])
    i2 = ImageItem("sample_images/graphic_shapes.png", 400, 300, 50000, "PNG", title="Alpha", tags=["art"])
    i3 = ImageItem("sample_images/city_night.jpg", 800, 600, 3000000, "JPEG", title="Gama", tags=["urban"])
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
    assert [x.title for x in sorted_asc] == ["Alpha", "Beta", "Gama"]

    desc_strat = SortBySizeDescStrategy()
    sorted_desc = desc_strat.sort(items)
    assert [x.title for x in sorted_desc] == ["Gama", "Beta", "Alpha"]


def test_thumbnail_rendering_strategies():
    pixmap = QPixmap(200, 100)
    pixmap.fill()
    target_size = QSize(80, 80)

    smooth_strat = SmoothThumbnailStrategy()
    fast_strat = FastThumbnailStrategy()

    p_smooth = smooth_strat.render(pixmap, target_size)
    assert not p_smooth.isNull()

    p_fast = fast_strat.render(pixmap, target_size)
    assert not p_fast.isNull()
