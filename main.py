"""
Ponto de Entrada da Aplicação: Organizador de Imagens (Cliente QT)
Disciplina: Paradigmas de Programação
Padrões Demonstrados:
  - Abstract Factory (Criacional)
  - Flyweight (Estrutural)
  - Strategy (Comportamental)
"""

import sys
import os

# Adiciona o diretório raiz ao sys.path para garantir importações corretas
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from client.ui.main_window import MainWindow
from client.services.image_service import ImageService


def main():
    # Criação da aplicação Qt
    app = QApplication(sys.argv)
    app.setApplicationName("Organizador de Imagens - Cliente QT")
    app.setOrganizationName("CC5AN - Paradigmas de Programação")

    # Inicialização do serviço de imagens e da janela principal
    service = ImageService()
    window = MainWindow(service=service)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
