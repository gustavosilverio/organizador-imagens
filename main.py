import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from PyQt6.QtWidgets import QApplication
from client.ui.main_window import MainWindow
from client.services.image_service import ImageService


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Organizador de Imagens")

    service = ImageService()
    window = MainWindow(service=service)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
