# `astronew/analysis/calculations.py` — Calcoli astrofisici

Questo modulo raccoglie le **formule astrofisiche reali** usate in tutta
l'applicazione. Ogni funzione ha una docstring che cita esplicitamente la
formula fisica implementata, come richiesto dalle convenzioni del progetto.

## Ruolo nel progetto

È la "libreria di fisica" di AstroNew. I grafici (`viz/plots.py`) e l'assistente
IA (`ai/assistant.py`) importano queste funzioni per derivare grandezze fisiche
dai dati grezzi di Gaia (parallasse, magnitudini, moto proprio).

## Funzioni implementate

### `parallax_to_distance_pc(parallax_mas)`
Converte una parallasse in milliarcosecondi (mas) in una distanza in parsec.
- **Formula:** `d[pc] = 1 / p[arcsec]`
- La parallasse in mas viene prima convertita in arcosecondi dividendo per 1000.
- **Validazione:** solleva `ValueError` se la parallasse è ≤ 0 (una parallasse
  non positiva non ha significato fisico e produrrebbe distanze assurde).

### `absolute_magnitude(apparent_mag, distance_pc)`
Calcola la magnitudine assoluta dalla magnitudine apparente e dalla distanza.
- **Formula (modulo di distanza):** `M = m − 5·log₁₀(d/10 pc)`
- Solleva `ValueError` se la distanza è ≤ 0.

### `proper_motion_total(mua_mas_yr, mud_mas_yr)`
Calcola l'ampiezza totale del moto proprio dalle due componenti (in RA e Dec).
- **Formula:** `μ = √(μ_α² + μ_δ²)` — implementata con `math.hypot`.

### `tangential_velocity(pmra_mas_yr, pmdec_mas_yr, distance_pc)`
Calcola la velocità tangenziale dal moto proprio e dalla distanza.
- **Formula:** `v_t[km/s] = 4.74 · μ[arcsec/yr] · d[pc]`; con μ in mas/yr si
  divide per 1000.
- Riusa `proper_motion_total` per ottenere il moto proprio totale.
- Solleva `ValueError` se la distanza è ≤ 0.

### `luminosity_ratio(abs_mag)`
Calcola il rapporto di luminosità rispetto al Sole dalla scala delle magnitudini.
- **Formula (legge di Pogson):** `L/L☉ = 10^(−(M − M☉)/2.5)`, con `M☉ = 4.83`
  (magnitudine visuale assoluta del Sole).

## Blocco di test

Il blocco `if __name__ == "__main__":` esegue un test con i valori noti di
**Sirio** (parallasse ~379 mas, magnitudine apparente −1.46, moto proprio, ecc.)
e stampa distanza, magnitudine assoluta, moto proprio totale, velocità
tangenziale e luminosità relativa, così da confrontare i risultati con valori
di riferimento reali.
