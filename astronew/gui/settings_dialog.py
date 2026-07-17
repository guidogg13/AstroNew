"""Finestra "Impostazioni" della GUI di AstroNew (PyQt6).

Permette di configurare il provider IA (chiave API, modello, modello di
fallback, base URL) riusando ESATTAMENTE la stessa logica della versione da
terminale definita in ``astronew/setup.py``:
- ``_read_env_value``     legge i valori attuali dal file .env;
- ``_upsert_env_values``  aggiorna .env senza duplicare righe;
- ``_sanitize_base_url``  garantisce il suffisso ``/api/v1``;
- ``_mask_api_key``       maschera la chiave per la visualizzazione.

Dopo il salvataggio ricarica la configurazione in memoria con
``reload_config`` (load_dotenv override=True), così le nuove impostazioni sono
subito attive nel pannello della chat, senza riavviare l'app.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from PyQt6.QtCore import pyqtSignal

from astronew.ai.assistant import (
    DEFAULT_AI_MODEL,
    DEFAULT_AI_MODEL_FALLBACK,
    DEFAULT_API_BASE_URL,
    ENV_PATH,
    reload_config,
)
from astronew.gui import theme
from astronew.setup import (
    _mask_api_key,
    _read_env_value,
    _sanitize_base_url,
    _upsert_env_values,
)


class SettingsDialog(QDialog):
    """Finestra modale per configurare il provider IA.

    Emette ``config_saved`` dopo un salvataggio riuscito, così la finestra
    principale può aggiornare il pannello della chat.
    """

    config_saved = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Impostazioni — AstroNew")
        self.resize(480, 420)
        self._build_ui()
        self.refresh_display()

    # ------------------------------------------------------------------ UI ---
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # --- Messaggio di benvenuto (mostrato solo al primo avvio) -----------
        self.welcome_label = QLabel()
        self.welcome_label.setObjectName("infoBanner")
        self.welcome_label.setWordWrap(True)
        self.welcome_label.setVisible(False)
        layout.addWidget(self.welcome_label)

        # --- Configurazione attuale ------------------------------------------
        current_box = QGroupBox("Configurazione attuale")
        current_layout = QFormLayout(current_box)
        self.current_key_label = QLabel()
        self.current_model_label = QLabel()
        self.current_fallback_label = QLabel()
        self.current_base_url_label = QLabel()
        current_layout.addRow("Chiave API:", self.current_key_label)
        current_layout.addRow("Modello:", self.current_model_label)
        current_layout.addRow("Modello fallback:", self.current_fallback_label)
        current_layout.addRow("Base URL:", self.current_base_url_label)
        layout.addWidget(current_box)

        # --- Nuovi valori ------------------------------------------------------
        edit_box = QGroupBox("Modifica configurazione")
        edit_layout = QFormLayout(edit_box)

        self.key_edit = QLineEdit()
        self.key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_edit.setPlaceholderText("Lascia vuoto per non modificare")
        edit_layout.addRow("Nuova chiave API:", self.key_edit)

        self.model_edit = QLineEdit()
        edit_layout.addRow("Nuovo modello:", self.model_edit)

        self.fallback_edit = QLineEdit()
        edit_layout.addRow("Nuovo modello fallback:", self.fallback_edit)

        self.base_url_edit = QLineEdit()
        edit_layout.addRow("Base URL:", self.base_url_edit)

        layout.addWidget(edit_box)

        # --- Pulsante salva + stato --------------------------------------------
        button_layout = QHBoxLayout()
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        button_layout.addWidget(self.status_label, stretch=1)
        self.close_button = QPushButton("Chiudi")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        self.save_button = QPushButton("💾 Salva configurazione")
        self.save_button.setObjectName("primaryButton")
        self.save_button.clicked.connect(self._on_save_clicked)
        theme.apply_glow(self.save_button)
        button_layout.addWidget(self.save_button)
        layout.addLayout(button_layout)

    # ------------------------------------------------------------- display ---
    def _current_values(self):
        """Legge dal file .env i valori attuali, con fallback ai default."""
        key = _read_env_value(ENV_PATH, "OPENROUTER_API_KEY")
        model = _read_env_value(ENV_PATH, "AI_MODEL") or DEFAULT_AI_MODEL
        fallback = (
            _read_env_value(ENV_PATH, "AI_MODEL_FALLBACK") or DEFAULT_AI_MODEL_FALLBACK
        )
        base_url = _read_env_value(ENV_PATH, "API_BASE_URL") or DEFAULT_API_BASE_URL
        return key, model, fallback, base_url

    def refresh_display(self):
        """Aggiorna le etichette della config attuale e i campi di modifica."""
        key, model, fallback, base_url = self._current_values()

        self.current_key_label.setText(_mask_api_key(key))
        self.current_model_label.setText(model or "(non impostato)")
        self.current_fallback_label.setText(fallback or "(nessuno)")
        self.current_base_url_label.setText(base_url)

        self.model_edit.clear()
        self.model_edit.setPlaceholderText(model or "(non impostato)")
        self.fallback_edit.clear()
        self.fallback_edit.setPlaceholderText(fallback or "(nessuno)")
        self.base_url_edit.setText(base_url)
        self.key_edit.clear()

    def show_welcome(self):
        """Mostra il messaggio di benvenuto del primo avvio."""
        self.welcome_label.setText(
            "Benvenuto in AstroNew! Prima di usare l'assistente IA, configura qui "
            "la tua chiave API compatibile OpenAI (es. da openrouter.ai) e il nome "
            "del modello. Le funzioni di ricerca dati e grafici sono comunque già "
            "disponibili."
        )
        self.welcome_label.setVisible(True)

    # --------------------------------------------------------------- eventi ---
    def _on_save_clicked(self):
        """Salva le modifiche in .env con gli stessi criteri della versione CLI."""
        key, model, fallback, base_url = self._current_values()

        new_key = self.key_edit.text().strip()
        new_model = self.model_edit.text().strip()
        new_fallback = self.fallback_edit.text().strip()
        new_base_url = self.base_url_edit.text().strip()

        updates: dict[str, str] = {}
        if new_key:
            updates["OPENROUTER_API_KEY"] = new_key
        if new_model and new_model != model:
            updates["AI_MODEL"] = new_model
        if new_fallback and new_fallback != fallback:
            updates["AI_MODEL_FALLBACK"] = new_fallback
        if new_base_url:
            sanitized = _sanitize_base_url(new_base_url)
            if sanitized != base_url:
                updates["API_BASE_URL"] = sanitized

        if not updates:
            self.status_label.setStyleSheet("color: #ffb454;")
            self.status_label.setText("Nessuna modifica da salvare.")
            return

        try:
            _upsert_env_values(ENV_PATH, updates)
            reload_config()
        except Exception as exc:  # noqa: BLE001 — mostriamo l'errore reale
            self.status_label.setStyleSheet("color: #ff5470;")
            self.status_label.setText(
                f"Errore nel salvataggio: {type(exc).__name__}: {exc}"
            )
            return

        self.welcome_label.setVisible(False)
        self.refresh_display()
        self.status_label.setStyleSheet("color: #3ddc84;")
        self.status_label.setText(
            f"Configurazione salvata in {ENV_PATH} e attiva subito, "
            "senza riavviare l'app."
        )
        self.config_saved.emit()
