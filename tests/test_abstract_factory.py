import os
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSize

_app = QApplication.instance() or QApplication([])

from client.patterns.abstract_factory import (
    ImageFormatFactorySelector,
    JPEGFormatFactory,
    PNGFormatFactory,
    BMPFormatFactory,
    JPEGReader,
    PNGReader,
    JPEGThumbnailGenerator,
    PNGThumbnailGenerator,
    UnsupportedFormatException,
    InvalidImageFileException,
)


def test_factory_selector_resolution():
    jpg_factory = ImageFormatFactorySelector.get_factory_for_extension(".jpg")
    jpeg_factory = ImageFormatFactorySelector.get_factory_for_extension(".jpeg")
    png_factory = ImageFormatFactorySelector.get_factory_for_extension(".png")
    bmp_factory = ImageFormatFactorySelector.get_factory_for_extension(".bmp")

    assert isinstance(jpg_factory, JPEGFormatFactory)
    assert isinstance(jpeg_factory, JPEGFormatFactory)
    assert isinstance(png_factory, PNGFormatFactory)
    assert isinstance(bmp_factory, BMPFormatFactory)


def test_factory_creates_family_of_products():
    factory = PNGFormatFactory()
    reader = factory.create_reader()
    thumb_gen = factory.create_thumbnail_generator()

    assert isinstance(reader, PNGReader)
    assert isinstance(thumb_gen, PNGThumbnailGenerator)

    jpg_factory = JPEGFormatFactory()
    assert isinstance(jpg_factory.create_reader(), JPEGReader)
    assert isinstance(jpg_factory.create_thumbnail_generator(), JPEGThumbnailGenerator)


def test_unsupported_format_raises_exception():
    with pytest.raises(UnsupportedFormatException):
        ImageFormatFactorySelector.get_factory_for_extension(".txt")

    with pytest.raises(UnsupportedFormatException):
        ImageFormatFactorySelector.get_factory_for_file("sample_images/document.txt")


def test_read_valid_png_and_generate_thumbnail():
    png_path = "sample_images/graphic_shapes.png"
    assert os.path.exists(png_path)

    factory = ImageFormatFactorySelector.get_factory_for_file(png_path)
    reader = factory.create_reader()
    thumb_gen = factory.create_thumbnail_generator()

    qimage, metadata = reader.read(png_path)
    assert not qimage.isNull()
    assert metadata["format"] == "PNG"
    assert metadata["width"] == 400
    assert metadata["height"] == 300

    thumb = thumb_gen.generate_thumbnail(qimage, QSize(100, 100))
    assert not thumb.isNull()
    assert thumb.width() <= 100
    assert thumb.height() <= 100


def test_read_valid_jpeg():
    jpg_path = "sample_images/sunset_landscape.jpg"
    assert os.path.exists(jpg_path)

    factory = ImageFormatFactorySelector.get_factory_for_file(jpg_path)
    reader = factory.create_reader()
    qimage, metadata = reader.read(jpg_path)

    assert not qimage.isNull()
    assert metadata["format"] == "JPEG"
    assert metadata["width"] == 600
    assert metadata["height"] == 400


def test_corrupted_image_raises_invalid_image_exception():
    corrupted_path = "sample_images/corrupted_image.jpg"
    assert os.path.exists(corrupted_path)

    factory = ImageFormatFactorySelector.get_factory_for_file(corrupted_path)
    reader = factory.create_reader()

    with pytest.raises(InvalidImageFileException):
        reader.read(corrupted_path)


def test_missing_file_raises_filenotfound():
    factory = JPEGFormatFactory()
    reader = factory.create_reader()

    with pytest.raises(FileNotFoundError):
        reader.read("sample_images/arquivo_fantasma.jpg")
