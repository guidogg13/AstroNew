"""Pannello "Grafici" della GUI di AstroNew (PyQt6).

Occupa il lato sinistro della finestra principale: in alto una barra di
ricerca compatta collegata alle funzioni reali di
``astronew/data/gaia_client.py`` (``query_by_name`` / ``query_region``), sotto
una selezione a "chip" del grafico scientifico da mostrare, costruito dalle
funzioni ``build_*`` reali di ``astronew/viz/plots.py`` e incorporato nella
finestra tramite il canvas matplotlib per Qt.

Le query Gaia vengono eseguite in un thread separato (QThread) per non
bloccare l'interfaccia durante l'attesa della risposta dell'archivio.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import (
    FigureCanvasQTAgg,
    NavigationToolbar2QT,
)

import pandas as pd

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from astronew.data.gaia_client import query_by_name, query_region
from astronew.viz.plots import (
    build_hr_diagram,
    build_sky_map,
    build_distance_histogram,
    build_proper_motion_vectors,
)
from astronew.gui import theme

RESULT_COLUMNS = [
    "source_id",
    "ra",
    "dec",
    "parallax",
    "phot_g_mean_mag",
    "bp_rp",
    "pmra",
    "pmdec",
]


class SearchWorker(QThread):
    """Esegue una query Gaia DR3 in un thread separato.

    Emette ``success`` con il DataFrame risultante, oppure ``error`` con un
    messaggio chiaro in caso di fallimento.
    """

    success = pyqtSignal(object)  # pandas.DataFrame
    error = pyqtSignal(str)

    def __init__(self, mode, params, parent=None):
        super().__init__(parent)
        self._mode = mode  # "name" oppure "coords"
        self._params = params

    def run(self):
        try:
            if self._mode == "name":
                df = query_by_name(
                    self._params["name"],
                    radius_deg=self._params["radius_deg"],
                    max_rows=self._params["max_rows"],
                )
            else:
                df = query_region(
                    ra=self._params["ra"],
                    dec=self._params["dec"],
                    radius_deg=self._params["radius_deg"],
                    max_rows=self._params["max_rows"],
                )
            self.success.emit(df)
        except Exception as exc:  # noqa: BLE001 — vogliamo il messaggio reale
            self.error.emit(f"{type(exc).__name__}: {exc}")


class DataTableDialog(QDialog):
    """Finestra secondaria con la tabella completa dell'ultima ricerca."""

    def __init__(self, df, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dati della ricerca")
        self.resize(760, 480)
        layout = QVBoxLayout(self)

        table = QTableWidget()
        table.setColumnCount(len(RESULT_COLUMNS))
        table.setHorizontalHeaderLabels(RESULT_COLUMNS)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setRowCount(len(df))
        for row_idx in range(len(df)):
            for col_idx, col_name in enumerate(RESULT_COLUMNS):
                value = df.iloc[row_idx][col_name] if col_name in df.columns else None
                text = self._format_value(col_name, value)
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row_idx, col_idx, item)
        layout.addWidget(table)

    def _format_value(self, col_name, value):
        if value is None or pd.isna(value):
            return ""
        if col_name == "source_id":
            return str(int(value))
        return str(value)


class GraphsPanel(QWidget):
    """Pannello di ricerca + visualizzazione grafici Gaia DR3.

    Emette ``data_loaded`` con il DataFrame risultante ogni volta che una
    ricerca ha successo, così la finestra principale può condividerlo con
    il pannello della chat.
    """

    data_loaded = pyqtSignal(object)  # pandas.DataFrame

    PLOT_BUILDERS = [
        ("Diagramma H-R", build_hr_diagram),
        ("Mappa celeste", build_sky_map),
        ("Istogramma distanze", build_distance_histogram),
        ("Vettori moto proprio", build_proper_motion_vectors),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("leftPanel")
        self._search_worker = None
        self._current_df = None
        self._current_fig = None
        self._current_canvas = None
        self._current_toolbar = None
        self._build_ui()

    # ------------------------------------------------------------------ UI ---
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 12, 16)
        layout.setSpacing(10)

        title = QLabel("🔭 Esplora i dati Gaia DR3")
        title.setObjectName("appTitle")
        title.setStyleSheet("font-size: 15px;")
        layout.addWidget(title)

        search_heading = QLabel("🔭  RICERCA")
        search_heading.setObjectName("sectionTitle")
        layout.addWidget(search_heading)
        layout.addWidget(self._build_search_card())

        plots_heading = QLabel("📊  GRAFICI")
        plots_heading.setObjectName("sectionTitle")
        layout.addWidget(plots_heading)
        layout.addWidget(self._build_plot_chips())
        layout.addWidget(self._build_canvas_area(), stretch=1)
        layout.addLayout(self._build_footer())

    def _build_search_card(self):
        card = QWidget()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(8)

        # --- Toggle metodo di ricerca (chip esclusivi) -----------------------
        toggle_row = QHBoxLayout()
        self.method_group = QButtonGroup(self)
        self.chip_name = QPushButton("Per nome")
        self.chip_coords = QPushButton("Per coordinate")
        for chip in (self.chip_name, self.chip_coords):
            chip.setObjectName("chip")
            chip.setCheckable(True)
            chip.setCursor(Qt.CursorShape.PointingHandCursor)
            self.method_group.addButton(chip)
            toggle_row.addWidget(chip)
        self.chip_name.setChecked(True)
        self.chip_name.toggled.connect(self._on_method_changed)
        toggle_row.addStretch()
        toggle_row.addWidget(QLabel("Righe max:"))
        self.max_rows_spin = QSpinBox()
        self.max_rows_spin.setRange(1, 10000)
        self.max_rows_spin.setValue(100)
        self.max_rows_spin.setFixedWidth(72)
        toggle_row.addWidget(self.max_rows_spin)
        card_layout.addLayout(toggle_row)

        # --- Campi di input (impilati: nome oppure coordinate) --------------
        self.input_stack = QStackedWidget()

        name_page = QWidget()
        name_row = QHBoxLayout(name_page)
        name_row.setContentsMargins(0, 0, 0, 0)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Nome stella (es. Sirius)")
        self.name_edit.returnPressed.connect(self._on_search_clicked)
        self.name_radius = self._make_radius_spinbox(default=0.1)
        name_row.addWidget(self.name_edit, stretch=1)
        name_row.addWidget(QLabel("Raggio:"))
        name_row.addWidget(self.name_radius)
        self.input_stack.addWidget(name_page)

        coords_page = QWidget()
        coords_row = QHBoxLayout(coords_page)
        coords_row.setContentsMargins(0, 0, 0, 0)
        self.ra_spin = QDoubleSpinBox()
        self.ra_spin.setRange(0.0, 360.0)
        self.ra_spin.setDecimals(4)
        self.ra_spin.setSuffix(" °")
        self.dec_spin = QDoubleSpinBox()
        self.dec_spin.setRange(-90.0, 90.0)
        self.dec_spin.setDecimals(4)
        self.dec_spin.setSuffix(" °")
        self.coords_radius = self._make_radius_spinbox(default=0.1)
        coords_row.addWidget(QLabel("RA:"))
        coords_row.addWidget(self.ra_spin)
        coords_row.addWidget(QLabel("Dec:"))
        coords_row.addWidget(self.dec_spin)
        coords_row.addWidget(QLabel("Raggio:"))
        coords_row.addWidget(self.coords_radius)
        self.input_stack.addWidget(coords_page)

        card_layout.addWidget(self.input_stack)

        # --- Pulsante di ricerca + stato --------------------------------------
        action_row = QHBoxLayout()
        self.status_label = QLabel("Pronto.")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setWordWrap(True)
        action_row.addWidget(self.status_label, stretch=1)

        self.table_button = QPushButton("Vedi tabella")
        self.table_button.setEnabled(False)
        self.table_button.clicked.connect(self._on_show_table)
        action_row.addWidget(self.table_button)

        self.search_button = QPushButton("🔍 Cerca")
        self.search_button.setObjectName("primaryButton")
        self.search_button.clicked.connect(self._on_search_clicked)
        theme.apply_glow(self.search_button)
        action_row.addWidget(self.search_button)
        card_layout.addLayout(action_row)

        return card

    def _build_plot_chips(self):
        row_widget = QWidget()
        row = QHBoxLayout(row_widget)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        self.plot_group = QButtonGroup(self)
        self.plot_group.setExclusive(True)
        for label, builder in self.PLOT_BUILDERS:
            chip = QPushButton(label)
            chip.setObjectName("chip")
            chip.setCheckable(True)
            chip.setCursor(Qt.CursorShape.PointingHandCursor)
            chip.clicked.connect(lambda _c=False, b=builder, ttl=label: self._show_plot(b, ttl))
            self.plot_group.addButton(chip)
            row.addWidget(chip)
        row.addStretch()
        return row_widget

    def _build_canvas_area(self):
        card = QWidget()
        card.setObjectName("card")
        self._canvas_layout = QVBoxLayout(card)
        self._canvas_layout.setContentsMargins(4, 4, 4, 4)
        self._placeholder = QLabel(
            "Seleziona un grafico dopo aver cercato una stella o una regione."
        )
        self._placeholder.setObjectName("statusLabel")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._canvas_layout.addWidget(self._placeholder)
        return card

    def _build_footer(self):
        row = QHBoxLayout()
        self.plot_status_label = QLabel("")
        self.plot_status_label.setObjectName("statusLabel")
        row.addWidget(self.plot_status_label, stretch=1)
        self.save_button = QPushButton("Esporta PNG")
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self._on_save_clicked)
        row.addWidget(self.save_button)
        return row

    def _make_radius_spinbox(self, default):
        spin = QDoubleSpinBox()
        spin.setRange(0.0, 90.0)
        spin.setDecimals(3)
        spin.setSingleStep(0.05)
        spin.setValue(default)
        spin.setSuffix(" °")
        spin.setFixedWidth(90)
        return spin

    # --------------------------------------------------------------- eventi ---
    def _on_method_changed(self):
        self.input_stack.setCurrentIndex(0 if self.chip_name.isChecked() else 1)

    def _on_search_clicked(self):
        if self._search_worker is not None and self._search_worker.isRunning():
            return

        max_rows = self.max_rows_spin.value()

        if self.chip_name.isChecked():
            name = self.name_edit.text().strip()
            if not name:
                self._show_search_error("Inserisci il nome di una stella prima di cercare.")
                return
            radius_deg = self.name_radius.value()
            if radius_deg <= 0:
                self._show_search_error("Il raggio di ricerca deve essere maggiore di 0.")
                return
            mode = "name"
            params = {"name": name, "radius_deg": radius_deg, "max_rows": max_rows}
        else:
            radius_deg = self.coords_radius.value()
            if radius_deg <= 0:
                self._show_search_error("Il raggio di ricerca deve essere maggiore di 0.")
                return
            mode = "coords"
            params = {
                "ra": self.ra_spin.value(),
                "dec": self.dec_spin.value(),
                "radius_deg": radius_deg,
                "max_rows": max_rows,
            }

        self._set_search_busy(True)
        self.status_label.setText("Ricerca in corso...")

        self._search_worker = SearchWorker(mode, params)
        self._search_worker.success.connect(self._on_query_success)
        self._search_worker.error.connect(self._on_query_error)
        self._search_worker.finished.connect(lambda: self._set_search_busy(False))
        self._search_worker.start()

    def _on_query_success(self, df):
        self._current_df = df
        n = len(df)
        if n == 0:
            self.status_label.setText("Nessun oggetto trovato per i parametri indicati.")
        else:
            self.status_label.setText(f"Trovati {n} oggetti.")
        self.table_button.setEnabled(n > 0)
        self.data_loaded.emit(df)

    def _on_query_error(self, message):
        self._show_search_error(f"Errore durante la ricerca: {message}")

    def _on_show_table(self):
        if self._current_df is None:
            return
        dialog = DataTableDialog(self._current_df, parent=self)
        dialog.exec()

    def _show_plot(self, builder, title):
        if self._current_df is None or getattr(self._current_df, "empty", True):
            self.plot_status_label.setText(
                "Cerca prima una stella o regione prima di generare un grafico."
            )
            return

        self.plot_status_label.setText(f"Generazione grafico: {title}...")
        try:
            fig = builder(self._current_df)
        except ValueError as exc:
            self.plot_status_label.setText(f"Impossibile generare il grafico: {exc}")
            return
        except Exception as exc:  # noqa: BLE001 — mostriamo l'errore reale
            self.plot_status_label.setText(f"Errore nel grafico: {type(exc).__name__}: {exc}")
            return

        theme.apply_dark_style(fig)
        self._embed_figure(fig)
        self.plot_status_label.setText(f"Grafico mostrato: {title}.")

    def _embed_figure(self, fig):
        self._clear_canvas()

        self._current_fig = fig
        self._current_canvas = FigureCanvasQTAgg(fig)
        self._current_toolbar = NavigationToolbar2QT(self._current_canvas, self)
        self._canvas_layout.addWidget(self._current_toolbar)
        self._canvas_layout.addWidget(self._current_canvas)
        self._current_canvas.draw()

        self.save_button.setEnabled(True)

    def _clear_canvas(self):
        if self._placeholder is not None:
            self._placeholder.setParent(None)
            self._placeholder = None

        if self._current_toolbar is not None:
            self._canvas_layout.removeWidget(self._current_toolbar)
            self._current_toolbar.setParent(None)
            self._current_toolbar.deleteLater()
            self._current_toolbar = None

        if self._current_canvas is not None:
            self._canvas_layout.removeWidget(self._current_canvas)
            self._current_canvas.setParent(None)
            self._current_canvas.deleteLater()
            self._current_canvas = None

        if self._current_fig is not None:
            plt.close(self._current_fig)
            self._current_fig = None

    def _on_save_clicked(self):
        if self._current_fig is None:
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salva grafico come immagine",
            "grafico.png",
            "Immagini PNG (*.png);;Tutti i file (*)",
        )
        if not file_path:
            return
        if not file_path.lower().endswith(".png"):
            file_path += ".png"
        try:
            self._current_fig.savefig(file_path, dpi=150, facecolor=self._current_fig.get_facecolor())
        except Exception as exc:  # noqa: BLE001 — mostriamo l'errore reale
            QMessageBox.critical(
                self,
                "Errore di salvataggio",
                f"Impossibile salvare l'immagine:\n{type(exc).__name__}: {exc}",
            )
            return
        self.plot_status_label.setText(f"Grafico salvato: {file_path}")

    # ------------------------------------------------------------- supporto ---
    def _show_search_error(self, message):
        self.status_label.setText(message)

    def _set_search_busy(self, busy):
        self.search_button.setEnabled(not busy)
        self.input_stack.setEnabled(not busy)
