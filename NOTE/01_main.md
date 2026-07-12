# `astronew/main.py` — Entry point e menu principale

Questo è il **punto di ingresso** dell'applicazione AstroNew. Contiene il menu
principale a riga di comando e coordina tutti gli altri moduli: ricerca dati,
grafici e assistente IA.

## Ruolo nel progetto

`main.py` è il "direttore d'orchestra": non contiene logica astrofisica né di
rete, ma richiama le funzioni definite negli altri moduli in base alle scelte
dell'utente. Mantiene lo stato di sessione tramite un unico DataFrame,
`current_df`, caricato dall'opzione 1 e riutilizzato dalle opzioni 2 e 3.

## Funzioni principali

### `_search_region_session()`
Gestisce l'opzione "Cerca stella/regione". Propone due metodi:
- **Ricerca per nome** (es. "Sirius"): chiama `query_by_name` del client Gaia.
- **Ricerca per coordinate** (RA, Dec, raggio in gradi): chiama `query_region`.

Valida gli input numerici (gestendo `ValueError` sugli input non numerici) e
cattura le eccezioni di rete/query, stampando un messaggio d'errore chiaro
invece di far crashare l'app. Ritorna il DataFrame risultante oppure `None`.

### `_plots_menu(session_df)`
Sottomenu per generare i grafici sul DataFrame caricato. Le opzioni sono:
1. Diagramma H-R → `plot_hr_diagram`
2. Mappa celeste → `plot_sky_map`
3. Istogramma distanze → `plot_distance_histogram`
4. Vettori di moto proprio → `plot_proper_motion_vectors`
5. Ritorno al menu principale

Ogni grafico viene salvato come file PNG nella root del progetto.

### `main()`
Contiene il ciclo `while True` del menu principale con quattro opzioni:
1. Cerca stella/regione — aggiorna `current_df` solo se la ricerca ha esito.
2. Visualizza grafici — richiede che `current_df` sia già caricato.
3. Assistente IA — controlla prima lo stato della configurazione con
   `get_assistant_status()`, e avvia la sessione interattiva solo se la
   configurazione API è valida.
4. Esci.

All'avvio, prima del menu, viene chiamato `run_first_time_setup()`: la
configurazione guidata parte solo se `.env` manca o la chiave è ancora un
placeholder.

## Gestione degli errori

Il ciclo cattura `KeyboardInterrupt` ed `EOFError` per non far crashare l'app se
l'utente preme Ctrl+C: torna semplicemente al menu principale.

## Come si esegue

```
python3 -m astronew.main
```
