from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QPixmap

_app = QApplication.instance() or QApplication([])

from client.patterns.strategy import (
    SmoothThumbnailStrategy,
    FastThumbnailStrategy,
)


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
