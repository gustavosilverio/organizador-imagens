"""
Testes Unitários para o Padrão Flyweight.
Verifica se objetos de formato e recursos visuais são devidamente compartilhados
e se a fábrica Flyweight preserva o pool único de instâncias.
"""

from PyQt6.QtWidgets import QApplication
from client.patterns.flyweight import FormatFlyweightFactory, ImageFormatFlyweight
from client.models.image_item import ImageItem

_app = QApplication.instance() or QApplication([])


def test_flyweight_factory_singleton_and_caching():
    """Valida se o pool Flyweight retorna a mesma instância para o mesmo formato."""
    factory1 = FormatFlyweightFactory()
    factory2 = FormatFlyweightFactory()

    assert factory1 is factory2

    fw_png1 = factory1.get_flyweight("PNG")
    fw_png2 = factory2.get_flyweight("PNG")

    # Devem apontar exatamente para o mesmo objeto na memória RAM
    assert fw_png1 is fw_png2
    assert id(fw_png1) == id(fw_png2)

    fw_jpg1 = factory1.get_flyweight("JPEG")
    fw_jpg2 = factory1.get_flyweight("JPG")
    assert fw_jpg1 is fw_jpg2


def test_flyweight_pool_size_remains_stable():
    """Valida que múltiplas requisições não aumentam o tamanho do pool."""
    factory = FormatFlyweightFactory()
    initial_pool_size = factory.get_pool_size()

    # Faz 100 requisições aos formatos
    for _ in range(100):
        factory.get_flyweight("JPEG")
        factory.get_flyweight("PNG")
        factory.get_flyweight("BMP")

    assert factory.get_pool_size() == initial_pool_size
    assert factory.get_served_requests_count() >= 300


def test_image_items_share_flyweight_instance():
    """Valida que múltiplos ImageItems do mesmo formato compartilham a mesma instância intrínseca."""
    item1 = ImageItem(
        file_path="sample_images/sunset_landscape.jpg",
        width=600,
        height=400,
        file_size_bytes=45000,
        format_name="JPEG",
        title="Pôr do Sol"
    )

    item2 = ImageItem(
        file_path="sample_images/city_night.jpg",
        width=800,
        height=600,
        file_size_bytes=75000,
        format_name="JPEG",
        title="Cidade à Noite"
    )

    # Estado extrínseco diferente
    assert item1.title != item2.title
    assert item1.file_size_bytes != item2.file_size_bytes
    assert item1.width != item2.width

    # Estado intrínseco compartilhado (mesmo objeto)
    assert item1.flyweight is item2.flyweight
    assert id(item1.flyweight) == id(item2.flyweight)
    assert item1.format_name == "JPEG"
    assert item2.format_name == "JPEG"


def test_flyweight_stats_computation():
    """Valida o cálculo de economia de memória e reuso de objetos."""
    factory = FormatFlyweightFactory()
    stats = factory.get_stats(total_images=10)

    assert stats["flyweights_in_pool"] >= 3
    assert stats["total_images"] == 10
    assert stats["objects_saved"] == (10 - stats["flyweights_in_pool"])
    assert stats["sharing_ratio_percent"] > 0
