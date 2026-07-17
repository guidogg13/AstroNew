"""
Punto di ingresso dell'interfaccia grafica desktop di AstroNew (PyQt6).

Questo entry point è separato da `astronew/main.py`, che resta l'app da
terminale e continua a funzionare invariato. Avvia l'applicazione Qt e mostra
la finestra principale.

Avvio:
    python3 -m astronew.gui_main
"""

import sys

from PyQt6.QtWidgets import QApplication

from astronew.gui.main_window import MainWindow
from astronew.gui.theme import stylesheet


def main():
    """Avvia l'applicazione grafica Qt con il tema scuro di AstroNew."""
    app = QApplication(sys.argv)
    app.setStyleSheet(stylesheet())

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
