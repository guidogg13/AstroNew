"""Pannello "Assistente IA" della GUI di AstroNew (PyQt6).

Chat moderna a bolle, posizionata sulla destra della finestra principale.
Collega la GUI all'assistente reale definito in ``astronew/ai/assistant.py``:
il messaggio dell'utente viene inviato con ``ask_astro_assistant`` passando
come contesto l'ultima ricerca (il DataFrame condiviso dalla finestra
principale tramite ``get_df``). L'assistente può comunque interrogare Gaia in
autonomia tramite tool calling.

La chiamata all'API viene eseguita in un thread separato (QThread) per non
bloccare la finestra durante l'attesa della risposta.
"""

from __future__ import annotations

import html
from datetime import datetime

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import astronew.ai.assistant as assistant
from astronew.gui import theme


class AssistantWorker(QThread):
    """Interroga l'assistente IA in un thread separato.

    Emette ``success`` con la risposta testuale, oppure ``error`` con un
    messaggio chiaro se qualcosa va storto a un livello non gestito
    internamente da ``ask_astro_assistant``.
    """

    success = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, question, data_context, parent=None):
        super().__init__(parent)
        self._question = question
        self._data_context = data_context

    def run(self):
        try:
            answer = assistant.ask_astro_assistant(
                self._question, data_context=self._data_context
            )
            self.success.emit(answer if answer else "(Nessuna risposta dall'assistente.)")
        except Exception as exc:  # noqa: BLE001 — mostriamo l'errore reale
            self.error.emit(f"{type(exc).__name__}: {exc}")


class ChatInput(QTextEdit):
    """Campo di input multilinea che invia con Invio e va a capo con Shift+Invio.

    Si espande automaticamente in altezza fino a un massimo di poche righe,
    per lasciare più spazio possibile alla cronologia della chat.
    """

    submitted = pyqtSignal()

    _MIN_HEIGHT = 40
    _MAX_HEIGHT = 120

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("chatInput")
        self.setPlaceholderText("Scrivi un messaggio... (Invio per inviare)")
        self.setAcceptRichText(False)
        self.setFixedHeight(self._MIN_HEIGHT)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.textChanged.connect(self._adjust_height)

    def keyPressEvent(self, event):
        is_enter = event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
        if is_enter and not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
            self.submitted.emit()
            return
        super().keyPressEvent(event)

    def _adjust_height(self):
        doc_height = int(self.document().size().height()) + 12
        new_height = max(self._MIN_HEIGHT, min(doc_height, self._MAX_HEIGHT))
        self.setFixedHeight(new_height)


class ChatBubble(QFrame):
    """Una singola bolla di messaggio (utente, assistente o sistema)."""

    def __init__(self, text, kind, parent=None):
        super().__init__(parent)
        self.setObjectName(f"bubble{kind.capitalize()}")
        self.setMaximumWidth(340)

        safe = html.escape(text).replace("\n", "<br>")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 9, 12, 8)
        layout.setSpacing(2)

        label = QLabel(safe)
        label.setObjectName(f"bubbleText{kind.capitalize()}")
        label.setWordWrap(True)
        label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(label)

        timestamp = QLabel(datetime.now().strftime("%H:%M"))
        timestamp.setObjectName("bubbleTimestamp")
        timestamp.setAlignment(
            Qt.AlignmentFlag.AlignRight if kind == "user" else Qt.AlignmentFlag.AlignLeft
        )
        layout.addWidget(timestamp)


class TypingIndicator(QWidget):
    """Indicatore animato "sta scrivendo..." con puntini che pulsano."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 0, 4, 0)
        self._label = QLabel("AstroNew IA sta scrivendo")
        self._label.setObjectName("statusLabel")
        layout.addWidget(self._label)
        layout.addStretch()

        self._dots = 0
        self._timer = QTimer(self)
        self._timer.setInterval(450)
        self._timer.timeout.connect(self._tick)
        self.hide()

    def start(self):
        self._dots = 0
        self._timer.start()
        self.show()

    def stop(self):
        self._timer.stop()
        self.hide()

    def _tick(self):
        self._dots = (self._dots + 1) % 4
        self._label.setText("AstroNew IA sta scrivendo" + "." * self._dots)


class ChatPanel(QWidget):
    """Pannello di chat con l'assistente IA di AstroNew.

    ``get_df`` è una funzione che restituisce il DataFrame corrente della
    ricerca (condiviso con il pannello dei grafici), passato come contesto
    a ogni domanda. ``open_settings`` viene chiamata quando l'utente clicca
    sull'avviso di configurazione mancante.
    """

    def __init__(self, get_df, open_settings, parent=None):
        super().__init__(parent)
        self.setObjectName("rightPanel")
        self._get_df = get_df
        self._open_settings = open_settings
        self._worker = None
        self._build_ui()
        self.refresh_config_state()

    # ------------------------------------------------------------------ UI ---
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # --- Intestazione -------------------------------------------------
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(0)
        title = QLabel("🤖 Assistente IA")
        title.setObjectName("appTitle")
        title.setStyleSheet("font-size: 15px;")
        title_box.addWidget(title)

        status_row = QHBoxLayout()
        status_row.setSpacing(5)
        self.status_dot = QLabel("●")
        self.status_dot.setObjectName("statusDot")
        self.status_text = QLabel("Verifica configurazione...")
        self.status_text.setObjectName("statusLabel")
        status_row.addWidget(self.status_dot)
        status_row.addWidget(self.status_text)
        status_row.addStretch()
        title_box.addLayout(status_row)

        header.addLayout(title_box)
        header.addStretch()
        layout.addLayout(header)

        # --- Avviso configurazione (nascosto se valida) --------------------
        self.config_warning = QLabel()
        self.config_warning.setObjectName("warningBanner")
        self.config_warning.setWordWrap(True)
        self.config_warning.setVisible(False)
        self.config_warning.setCursor(Qt.CursorShape.PointingHandCursor)
        self.config_warning.mousePressEvent = lambda _e: self._open_settings()
        layout.addWidget(self.config_warning)

        # --- Cronologia della chat (scrollabile, a bolle) -------------------
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("chatScroll")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self.chat_canvas = QWidget()
        self.chat_canvas.setObjectName("chatCanvas")
        self.chat_layout = QVBoxLayout(self.chat_canvas)
        self.chat_layout.setContentsMargins(2, 2, 10, 2)
        self.chat_layout.setSpacing(10)
        self.chat_layout.addStretch(1)

        self.scroll_area.setWidget(self.chat_canvas)
        layout.addWidget(self.scroll_area, stretch=1)

        # --- Indicatore "sta scrivendo..." ----------------------------------
        self.typing_indicator = TypingIndicator()
        layout.addWidget(self.typing_indicator)

        # --- Riga di input ----------------------------------------------------
        input_row = QHBoxLayout()
        input_row.setSpacing(8)
        self.input_edit = ChatInput()
        self.input_edit.submitted.connect(self._on_send_clicked)
        input_row.addWidget(self.input_edit, stretch=1)

        self.send_button = QPushButton("➤")
        self.send_button.setObjectName("sendButton")
        self.send_button.setFixedSize(40, 40)
        self.send_button.clicked.connect(self._on_send_clicked)
        theme.apply_glow(self.send_button, color=theme.ACCENT_CYAN, blur=24, alpha=190)
        input_row.addWidget(self.send_button, alignment=Qt.AlignmentFlag.AlignBottom)
        layout.addLayout(input_row)

        self._append_message(
            "Ciao! Sono l'assistente IA di AstroNew. Posso rispondere a domande "
            "di astrofisica e interrogare Gaia DR3 in autonomia. Scrivi pure.",
            kind="system",
        )

    # ---------------------------------------------------------- config API ---
    def refresh_config_state(self):
        """Ricontrolla la configurazione API e abilita/disabilita l'invio."""
        assistant.reload_config()
        valid = assistant.is_config_valid()
        self.input_edit.setEnabled(valid)
        self.send_button.setEnabled(valid)
        if valid:
            self.config_warning.setVisible(False)
            self.status_dot.setStyleSheet(f"color: {theme.SUCCESS};")
            self.status_text.setText("Connesso")
        else:
            self.status_dot.setStyleSheet(f"color: {theme.DANGER};")
            self.status_text.setText("Non configurato")
            self.config_warning.setText(
                "⚠ " + assistant.get_assistant_status()
                + "  Clicca qui per aprire le Impostazioni."
            )
            self.config_warning.setVisible(True)

    # --------------------------------------------------------------- eventi ---
    def _on_send_clicked(self):
        """Invia il messaggio dell'utente all'assistente in un thread separato."""
        if self._worker is not None and self._worker.isRunning():
            return
        if not assistant.is_config_valid():
            self.refresh_config_state()
            return

        question = self.input_edit.toPlainText().strip()
        if not question:
            return

        self._append_message(question, kind="user")
        self.input_edit.clear()

        self._set_busy(True)
        self.typing_indicator.start()

        data_context = self._get_df()
        self._worker = AssistantWorker(question, data_context)
        self._worker.success.connect(self._on_answer)
        self._worker.error.connect(self._on_error)
        self._worker.finished.connect(lambda: self._set_busy(False))
        self._worker.finished.connect(self.typing_indicator.stop)
        self._worker.start()

    def _on_answer(self, answer):
        self._append_message(answer, kind="assistant")

    def _on_error(self, message):
        self._append_message(f"Errore durante la richiesta: {message}", kind="system")

    # ------------------------------------------------------------- supporto ---
    def _append_message(self, text, kind):
        """Aggiunge una bolla di messaggio in fondo alla cronologia."""
        bubble = ChatBubble(text, kind)
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        if kind == "user":
            row.addStretch(1)
            row.addWidget(bubble)
        elif kind == "system":
            row.addStretch(1)
            row.addWidget(bubble)
            row.addStretch(1)
        else:
            row.addWidget(bubble)
            row.addStretch(1)

        # Inserisce prima dello stretch finale (ultimo elemento del layout).
        insert_index = self.chat_layout.count() - 1
        container = QWidget()
        container.setLayout(row)
        self.chat_layout.insertWidget(insert_index, container)

        QTimer.singleShot(0, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        bar = self.scroll_area.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _set_busy(self, busy):
        self.input_edit.setEnabled(not busy)
        self.send_button.setEnabled(not busy)
        if not busy:
            self.input_edit.setFocus()
