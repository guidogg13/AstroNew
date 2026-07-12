# AstroNew — Panoramica del progetto

Questo file introduce l'intero progetto **AstroNew** e serve da indice per le
altre note presenti in questa cartella. Ogni script del pacchetto ha una nota
dedicata che spiega, riga per riga a livello concettuale, cosa fa e come si
inserisce nel resto dell'applicazione.

## Cos'è AstroNew

AstroNew è un'applicazione desktop scritta in Python che:

1. **Interroga** l'archivio pubblico ufficiale **Gaia DR3** dell'ESA tramite le
   API ufficiali (`astroquery.gaia`, protocollo TAP/ADQL, accesso anonimo).
2. **Elabora** i dati astrometrici con calcoli astrofisici reali (distanza da
   parallasse, magnitudine assoluta, moto proprio, velocità tangenziale,
   rapporto di luminosità).
3. **Visualizza** i risultati con grafici scientifici realizzati in matplotlib
   (diagramma H-R, mappa celeste, istogramma delle distanze, vettori di moto
   proprio).
4. Offre un **assistente IA** con tool calling autonomo, basato su un'API
   compatibile OpenAI (attualmente OpenRouter con modello NVIDIA Nemotron),
   capace di interrogare Gaia da solo quando serve.

## Regola non negoziabile sui dati

Tutti i dati provengono **esclusivamente** da archivi pubblici ufficiali,
tramite le loro API ufficiali. È vietato ogni scraping non autorizzato o bypass
dei rate limit. In ADQL si usa solo `TOP` per limitare le righe, mai `LIMIT`.

## Struttura del pacchetto `astronew`

| Cartella / file          | Ruolo                                            |
|--------------------------|--------------------------------------------------|
| `data/gaia_client.py`    | Accesso a Gaia DR3 (query per nome o coordinate) |
| `analysis/calculations.py` | Formule astrofisiche                           |
| `viz/plots.py`           | Grafici scientifici                              |
| `ai/assistant.py`        | Assistente IA con tool calling                   |
| `setup.py`               | Configurazione guidata al primo avvio            |
| `main.py`                | Entry point con menu principale                  |

## Indice delle note

- `01_main.md` — menu principale ed entry point
- `02_gaia_client.md` — client di accesso a Gaia DR3
- `03_calculations.md` — funzioni di calcolo astrofisico
- `04_plots.md` — funzioni di plotting scientifico
- `05_assistant.md` — assistente IA con tool calling
- `06_setup.md` — configurazione guidata al primo avvio

## Come avviare l'app

Dalla root del progetto, eseguire come modulo (il nome del pacchetto è
case-sensitive e sempre minuscolo):

```
python3 -m astronew.main
```

## Licenza

Progetto no-profit/educativo, licenza PolyForm Noncommercial License 1.0.0.
Attribuzione obbligatoria a ESA Gaia DR3.
