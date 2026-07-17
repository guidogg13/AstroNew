"""Finestra principale dell'interfaccia grafica desktop di AstroNew (PyQt6).

Layout moderno a due colonne divise da uno splitter ridimensionabile:
- sinistra: ricerca Gaia DR3 + grafici scientifici (``GraphsPanel``);
- destra: chat con l'assistente IA (``ChatPanel``).

Le Impostazioni non sono più una scheda separata: si apre una finestra
modale (``SettingsDialog``) dall'icona a forma di ingranaggio nell'intestazione.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSplitter,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from astronew.gui.graphs_panel import GraphsPanel
from astronew.gui.chat_panel import ChatPanel
from astronew.gui.settings_dialog import SettingsDialog
from astronew.gui.starfield import StarfieldBackground
from astronew.setup import is_setup_needed


class MainWindow(QMainWindow):
    """Finestra principale dell'applicazione AstroNew."""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("AstroNew — Esplorazione astronomica con dati Gaia DR3")
        self.resize(1360, 840)
        self.setMinimumSize(980, 620)

        # DataFrame dell'ultima ricerca, condiviso tra i pannelli Grafici e
        # Assistente IA.
        self.current_df = None
        self._settings_dialog = None

        # Sfondo "campo stellato" generato via codice: la finestra centrale è
        # il widget che lo disegna, con l'header e lo splitter sovrapposti
        # sopra (trasparenti nei margini, così le stelle restano visibili).
        central = StarfieldBackground()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)

        central_layout.addWidget(self._build_header())

        self.graphs_panel = GraphsPanel()
        self.graphs_panel.data_loaded.connect(self._on_data_loaded)

        self.chat_panel = ChatPanel(
            get_df=lambda: self.current_df,
            open_settings=self._open_settings,
        )

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.graphs_panel)
        splitter.addWidget(self.chat_panel)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([880, 440])
        central_layout.addWidget(splitter, stretch=1)

        self.setCentralWidget(central)

        # Al primissimo avvio (nessun .env valido o chiave ancora placeholder)
        # apri direttamente le Impostazioni con un messaggio di benvenuto.
        if is_setup_needed():
            self._settings_dialog = SettingsDialog(parent=self)
            self._settings_dialog.config_saved.connect(self._on_config_saved)
            self._settings_dialog.show_welcome()
            self._settings_dialog.exec()

        self._center_on_screen()

    # ------------------------------------------------------------------ UI ---
    def _build_header(self):
        header = QWidget()
        header.setObjectName("header")
        header.setFixedHeight(64)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 8, 16, 8)

        title_box = QVBoxLayout()
        title_box.setSpacing(0)
        title = QLabel("🌌 AstroNew")
        title.setObjectName("appTitle")
        subtitle = QLabel("Esplorazione astronomica con dati Gaia DR3 (ESA)")
        subtitle.setObjectName("appSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        layout.addLayout(title_box)

        layout.addStretch()

        settings_button = QToolButton()
        settings_button.setObjectName("iconButton")
        settings_button.setText("⚙️")
        settings_button.setToolTip("Impostazioni")
        settings_button.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_button.clicked.connect(self._open_settings)
        layout.addWidget(settings_button)

        return header

    # --------------------------------------------------------------- eventi ---
    def _on_data_loaded(self, df):
        """Conserva l'ultimo DataFrame ottenuto dalla ricerca per la chat."""
        self.current_df = df

    def _open_settings(self):
        """Apre (o porta in primo piano) la finestra modale delle Impostazioni."""
        if self._settings_dialog is None:
            self._settings_dialog = SettingsDialog(parent=self)
            self._settings_dialog.config_saved.connect(self._on_config_saved)
        else:
            self._settings_dialog.refresh_display()
        self._settings_dialog.exec()
        return self._settings_dialog

    def _on_config_saved(self):
        """Dopo il salvataggio in Impostazioni, riabilita l'assistente IA."""
        self.chat_panel.refresh_config_state()

    def _center_on_screen(self):
        """Centra la finestra rispetto allo schermo disponibile."""
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        screen_geometry = screen.availableGeometry()
        frame_geometry = self.frameGeometry()
        frame_geometry.moveCenter(screen_geometry.center())
        self.move(frame_geometry.topLeft())
