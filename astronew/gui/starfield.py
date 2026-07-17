"""Sfondo "campo stellato" della finestra principale di AstroNew (PyQt6).

Nessuna immagine esterna: le stelle sono punti generati via codice (posizione,
raggio e opacità casuali) e disegnati con ``QPainter`` su un gradiente blu/nero
molto scuro. Il widget si ridisegna solo quando viene ridimensionato o quando
Qt lo richiede esplicitamente: le stelle sono generate una sola volta e le
loro coordinate sono espresse in percentuale, così restano proporzionate se
la finestra viene ridimensionata.
"""

from __future__ import annotations

import random

from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QColor, QLinearGradient, QPainter
from PyQt6.QtWidgets import QWidget

from astronew.gui import theme

_STAR_COUNT = 240
# Frazione di stelle con una tinta di accento (ciano/violetto) invece del
# consueto bianco/grigio-azzurro, per un tocco "elettrico" senza saturare.
_TINTED_FRACTION = 0.12


class StarfieldBackground(QWidget):
    """Sfondo della finestra principale con stelle generate proceduralmente."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        rng = random.Random(20260717)  # seed fissa: aspetto stabile tra gli avvii
        self._stars = []
        for _ in range(_STAR_COUNT):
            tinted = rng.random() < _TINTED_FRACTION
            self._stars.append(
                {
                    "x": rng.random(),
                    "y": rng.random(),
                    "radius": rng.uniform(0.5, 1.9),
                    "alpha": rng.randint(60, 235),
                    "tinted": tinted,
                }
            )

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, QColor(theme.BG_APP_TOP))
        gradient.setColorAt(1.0, QColor(theme.BG_APP))
        painter.fillRect(self.rect(), gradient)

        painter.setPen(Qt.PenStyle.NoPen)
        w, h = self.width(), self.height()
        for star in self._stars:
            color = QColor(theme.ACCENT_CYAN if star["tinted"] else "#dbe6ff")
            color.setAlpha(star["alpha"])
            painter.setBrush(color)
            x = star["x"] * w
            y = star["y"] * h
            r = star["radius"]
            painter.drawEllipse(QPointF(x, y), r, r)

        painter.end()
