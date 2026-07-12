# `astronew/viz/plots.py` — Grafici scientifici

Questo modulo genera le **visualizzazioni scientifiche** dei dati Gaia DR3 usando
matplotlib. Combina i dati grezzi con le grandezze derivate dal modulo
`analysis/calculations.py`.

## Ruolo nel progetto

È il livello di visualizzazione di AstroNew. Le sue funzioni vengono richiamate
dal sottomenu grafici in `main.py`. Il backend matplotlib è impostato su
`"Agg"` (non interattivo), quindi i grafici vengono salvati come file PNG senza
bisogno di un display grafico attivo.

## Helper condiviso

### `_filter_valid_parallax(df)`
Filtra le righe con parallasse non valida (≤ 0 o NaN), perché tali valori non
permettono di calcolare una distanza fisica. Emette un `UserWarning` indicando
quante righe sono state rimosse, così l'utente sa quanti dati sono stati esclusi.

## Funzioni di plotting

### `plot_hr_diagram(df, save_path=None)`
Crea un **diagramma di Hertzsprung-Russell**:
- Asse X: indice di colore `bp_rp`.
- Asse Y: magnitudine assoluta (calcolata da parallasse + magnitudine G),
  con l'asse invertito (le stelle più luminose in alto).
- I punti sono colorati per magnitudine apparente G.

### `plot_sky_map(df, save_path=None)`
Crea una **mappa celeste**:
- Asse X: ascensione retta (RA); asse Y: declinazione (Dec).
- La dimensione dei punti è proporzionale alla luminosità (radice della
  `luminosity_ratio`), il colore alla magnitudine apparente.

### `plot_distance_histogram(df, save_path=None)`
Crea un **istogramma della distribuzione delle distanze** (in parsec), calcolate
dalla parallasse. Aggiunge due linee verticali tratteggiate per **media** e
**mediana** con relativa legenda.

### `plot_proper_motion_vectors(df, save_path=None)`
Crea una mappa celeste con i **vettori di moto proprio**: usa `ax.quiver` per
disegnare frecce dalle posizioni (RA, Dec) nella direzione (`pmra`, `pmdec`).
Filtra le righe con `pmra`/`pmdec` mancanti. Un `scale_factor` regola la
lunghezza visiva delle frecce.

## Comportamento comune

Ogni funzione:
- Filtra i dati non validi e stampa un messaggio se non resta nulla da
  disegnare (evitando grafici vuoti o crash).
- Se `save_path` è indicato, salva il PNG a 150 DPI; altrimenti mostra a schermo.
- Chiude sempre la figura con `plt.close(fig)` per liberare memoria.

## Blocco di test

Il blocco `if __name__ == "__main__":` scarica dati reali attorno a Sirio e
genera tutti e quattro i grafici, salvandoli come PNG nella root del progetto.
