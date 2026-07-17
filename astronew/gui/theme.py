"""Tema visivo condiviso della GUI di AstroNew (PyQt6).

Definisce la palette colori "dark / space" e il foglio di stile QSS applicato
a tutta l'applicazione da ``gui_main.py``. Nessuna logica applicativa qui:
solo costanti e stringhe di stile, così ogni widget resta coerente senza
duplicare colori sparsi nei vari file.
"""

from __future__ import annotations

from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QGraphicsDropShadowEffect

# --------------------------------------------------------------------------- #
# Palette — tema "notte profonda" spaziale                                    #
# --------------------------------------------------------------------------- #
BG_APP = "#0a0e1a"
BG_APP_TOP = "#111a30"  # cima del gradiente di sfondo (leggermente più blu)
BG_PANEL = "#111522"
BG_ELEVATED = "#171c2c"
BG_ELEVATED_2 = "#1e2438"
BORDER = "#262d42"
BORDER_SOFT = "#1c2236"

TEXT_PRIMARY = "#eef0f8"
TEXT_SECONDARY = "#8b93ac"
TEXT_MUTED = "#5b6280"

# Accento primario: viola/blu elettrico. Accento secondario: ciano, usato per
# bagliori e piccoli tocchi "futuristici" (stelle colorate, glow del pulsante
# di invio in chat).
ACCENT = "#6c5ce7"
ACCENT_HOVER = "#8172f0"
ACCENT_PRESSED = "#5b4bd1"
ACCENT_SOFT = "#241f45"
ACCENT_CYAN = "#00d4ff"

SUCCESS = "#3ddc84"
WARNING = "#ffb454"
DANGER = "#ff5470"

# Bolle della chat: utente in un tono di blu elettrico, assistente in un tono
# di viola profondo — ben distinguibili a colpo d'occhio.
BUBBLE_USER_BG = "#1f4fd1"
BUBBLE_USER_BORDER = "#3f74ff"
BUBBLE_ASSISTANT_BG = "#332a63"
BUBBLE_ASSISTANT_BORDER = "#6c5ce7"


def apply_glow(widget, color=ACCENT, blur=26, alpha=170) -> None:
    """Applica un bagliore colorato (drop shadow) a un widget "importante".

    Usato sui pulsanti primari (Cerca, Salva, invio chat) per dare un tocco
    futuristico coerente col tema, senza intaccare la leggibilità: il colore
    resta quello d'accento e il bagliore è morbido (blur ampio, offset nullo).
    """
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, 0)
    glow_color = QColor(color)
    glow_color.setAlpha(alpha)
    effect.setColor(glow_color)
    widget.setGraphicsEffect(effect)


def apply_dark_style(fig, axes=None) -> None:
    """Ricolora una ``Figure`` matplotlib già costruita per il tema scuro.

    Non tocca i calcoli dei grafici (definiti in ``astronew/viz/plots.py``):
    agisce solo su colori di sfondo, assi, testo, griglia e serie che non
    codificano un dato scientifico (istogrammi, vettori), DOPO che la figura
    è già stata costruita da una funzione ``build_*``. Le mappe di colore che
    rappresentano una grandezza reale (es. magnitudine, viridis/cool) restano
    invariate: cambiarle ridurrebbe la leggibilità scientifica del grafico.
    """
    if axes is None:
        axes = fig.get_axes()

    fig.patch.set_facecolor(BG_PANEL)
    for ax in axes:
        ax.set_facecolor(BG_ELEVATED)
        ax.tick_params(colors=TEXT_SECONDARY, labelsize=9)
        for spine in ax.spines.values():
            spine.set_color(BORDER)
        ax.xaxis.label.set_color(TEXT_PRIMARY)
        ax.yaxis.label.set_color(TEXT_PRIMARY)
        ax.title.set_color(TEXT_PRIMARY)
        ax.grid(True, color=BORDER, alpha=0.35)

        # Barre di un istogramma (nessuna colormap: colore unico) -> accento.
        for patch in ax.patches:
            patch.set_facecolor(ACCENT)
            patch.set_edgecolor(BORDER)

        # Vettori di moto proprio (quiver): rosso originale -> ciano d'accento.
        for collection in ax.collections:
            if type(collection).__name__ == "Quiver":
                collection.set_color(ACCENT_CYAN)

        legend = ax.get_legend()
        if legend is not None:
            legend.get_frame().set_facecolor(BG_ELEVATED_2)
            legend.get_frame().set_edgecolor(BORDER)
            for text in legend.get_texts():
                text.set_color(TEXT_PRIMARY)
    # Colorbar (se presente) è un asse extra già incluso in get_axes().


def stylesheet() -> str:
    """Restituisce il foglio di stile QSS globale dell'applicazione."""
    return f"""
    QMainWindow, QDialog {{
        background-color: {BG_APP};
    }}

    QWidget {{
        color: {TEXT_PRIMARY};
        background-color: transparent;
    }}

    QWidget#header {{
        background-color: {BG_PANEL};
        border-bottom: 1px solid {BORDER};
    }}

    QLabel#appTitle {{
        font-size: 17px;
        font-weight: 700;
        color: {TEXT_PRIMARY};
    }}

    QLabel#appSubtitle {{
        font-size: 11px;
        color: {TEXT_SECONDARY};
    }}

    QWidget#leftPanel, QWidget#rightPanel {{
        background-color: transparent;
    }}

    QWidget#card {{
        background-color: {BG_PANEL};
        border: 1px solid {BORDER};
        border-radius: 12px;
    }}

    QLabel#sectionTitle {{
        font-size: 12px;
        font-weight: 600;
        color: {TEXT_SECONDARY};
        letter-spacing: 1px;
    }}

    QLabel#statusLabel {{
        color: {TEXT_SECONDARY};
        font-size: 12px;
    }}

    QLabel {{
        color: {TEXT_PRIMARY};
    }}

    /* --- Pulsanti standard ------------------------------------------------ */
    QPushButton {{
        background-color: {BG_ELEVATED_2};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 7px 14px;
        font-size: 12.5px;
    }}
    QPushButton:hover {{
        background-color: #232a42;
        border-color: {ACCENT};
    }}
    QPushButton:pressed {{
        background-color: #1a2035;
    }}
    QPushButton:disabled {{
        color: {TEXT_MUTED};
        background-color: {BG_ELEVATED};
        border-color: {BORDER_SOFT};
    }}

    /* --- Pulsante primario / invio ---------------------------------------- */
    QPushButton#primaryButton {{
        background-color: {ACCENT};
        border: none;
        color: white;
        font-weight: 600;
    }}
    QPushButton#primaryButton:hover {{
        background-color: {ACCENT_HOVER};
    }}
    QPushButton#primaryButton:pressed {{
        background-color: {ACCENT_PRESSED};
    }}
    QPushButton#primaryButton:disabled {{
        background-color: {BG_ELEVATED_2};
        color: {TEXT_MUTED};
    }}

    /* --- Chip / pillola per selezione grafico e toggle metodo ricerca ----- */
    QPushButton#chip {{
        background-color: {BG_ELEVATED};
        border: 1px solid {BORDER};
        border-radius: 15px;
        padding: 6px 14px;
        font-size: 12px;
        color: {TEXT_SECONDARY};
    }}
    QPushButton#chip:hover {{
        border-color: {ACCENT};
        color: {TEXT_PRIMARY};
    }}
    QPushButton#chip:checked {{
        background-color: {ACCENT_SOFT};
        border-color: {ACCENT};
        color: {ACCENT_HOVER};
        font-weight: 600;
    }}

    /* --- Bottone icona (gear, ecc.) ---------------------------------------- */
    QToolButton#iconButton {{
        background-color: transparent;
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 6px 10px;
        color: {TEXT_SECONDARY};
        font-size: 15px;
    }}
    QToolButton#iconButton:hover {{
        border-color: {ACCENT};
        color: {TEXT_PRIMARY};
        background-color: {BG_ELEVATED_2};
    }}

    /* --- Campi di input ----------------------------------------------------- */
    QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox {{
        background-color: {BG_ELEVATED};
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 6px 10px;
        color: {TEXT_PRIMARY};
        selection-background-color: {ACCENT};
        font-size: 12.5px;
    }}
    QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
        border-color: {ACCENT};
    }}
    QLineEdit::placeholder {{
        color: {TEXT_MUTED};
    }}
    QSpinBox::up-button, QSpinBox::down-button,
    QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
        width: 14px;
        border: none;
        background-color: transparent;
    }}

    /* --- Chat -------------------------------------------------------------- */
    QScrollArea#chatScroll {{
        background-color: {BG_APP};
        border: none;
    }}
    QWidget#chatCanvas {{
        background-color: {BG_APP};
    }}
    QFrame#bubbleUser {{
        background-color: {BUBBLE_USER_BG};
        border: 1px solid {BUBBLE_USER_BORDER};
        border-radius: 14px;
    }}
    QFrame#bubbleAssistant {{
        background-color: {BUBBLE_ASSISTANT_BG};
        border: 1px solid {BUBBLE_ASSISTANT_BORDER};
        border-radius: 14px;
    }}
    QFrame#bubbleSystem {{
        background-color: transparent;
        border: 1px dashed {BORDER};
        border-radius: 10px;
    }}
    QLabel#bubbleTextUser {{
        color: white;
        font-size: 13px;
    }}
    QLabel#bubbleTextAssistant {{
        color: {TEXT_PRIMARY};
        font-size: 13px;
    }}
    QLabel#bubbleTextSystem {{
        color: {TEXT_SECONDARY};
        font-size: 11.5px;
        font-style: italic;
    }}
    QLabel#bubbleTimestamp {{
        color: {TEXT_MUTED};
        font-size: 10px;
    }}

    QTextEdit#chatInput {{
        background-color: {BG_ELEVATED};
        border: 1px solid {BORDER};
        border-radius: 16px;
        padding: 9px 14px;
        font-size: 13px;
    }}
    QTextEdit#chatInput:focus {{
        border-color: {ACCENT};
    }}

    QPushButton#sendButton {{
        background-color: {ACCENT};
        border: none;
        border-radius: 18px;
        color: white;
        font-size: 15px;
        font-weight: 600;
    }}
    QPushButton#sendButton:hover {{
        background-color: {ACCENT_HOVER};
    }}
    QPushButton#sendButton:disabled {{
        background-color: {BG_ELEVATED_2};
        color: {TEXT_MUTED};
    }}

    QLabel#statusDot {{
        font-size: 10px;
    }}

    /* --- Banner di avviso ---------------------------------------------------- */
    QLabel#warningBanner {{
        background-color: #33270f;
        color: {WARNING};
        border: 1px solid #5a3f16;
        border-radius: 8px;
        padding: 9px 12px;
        font-size: 12px;
    }}
    QLabel#infoBanner {{
        background-color: #16233a;
        color: #7fb2ff;
        border: 1px solid #234066;
        border-radius: 8px;
        padding: 9px 12px;
        font-size: 12px;
    }}

    /* --- Splitter ------------------------------------------------------------ */
    QSplitter::handle {{
        background-color: transparent;
        width: 7px;
    }}
    QSplitter::handle:hover {{
        background-color: {ACCENT_SOFT};
    }}

    /* --- GroupBox (dialogo impostazioni) -------------------------------------- */
    QGroupBox {{
        border: 1px solid {BORDER};
        border-radius: 10px;
        margin-top: 10px;
        padding-top: 14px;
        font-size: 12px;
        color: {TEXT_SECONDARY};
        font-weight: 600;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 4px;
    }}

    /* --- Barra strumenti matplotlib ------------------------------------------- */
    QToolBar {{
        background-color: {BG_PANEL};
        border: none;
        spacing: 4px;
    }}

    /* --- Scrollbar ------------------------------------------------------------ */
    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 2px;
    }}
    QScrollBar::handle:vertical {{
        background: {BG_ELEVATED_2};
        border-radius: 5px;
        min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {ACCENT};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 10px;
        margin: 2px;
    }}
    QScrollBar::handle:horizontal {{
        background: {BG_ELEVATED_2};
        border-radius: 5px;
        min-width: 24px;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}

    QTableWidget {{
        background-color: {BG_PANEL};
        gridline-color: {BORDER};
        border: 1px solid {BORDER};
        border-radius: 8px;
        color: {TEXT_PRIMARY};
    }}
    QHeaderView::section {{
        background-color: {BG_ELEVATED};
        color: {TEXT_SECONDARY};
        border: none;
        border-bottom: 1px solid {BORDER};
        padding: 6px;
        font-size: 11px;
    }}
    """
