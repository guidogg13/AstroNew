# `astronew/data/gaia_client.py` — Client di accesso a Gaia DR3

Questo modulo è l'unico punto di contatto con l'archivio **Gaia DR3 dell'ESA**.
Usa la libreria `astroquery.gaia` e query TAP/ADQL anonime verso l'archivio
ufficiale (`https://gea.esac.esa.int`). Nessuna autenticazione è richiesta e
nessuno scraping non autorizzato viene eseguito.

## Ruolo nel progetto

Tutti gli altri moduli che hanno bisogno di dati reali (grafici, assistente IA,
calcoli) passano da qui. Centralizzare l'accesso in un solo file garantisce che
la regola non negoziabile sui dati sia rispettata in un unico posto.

## Funzioni e helper

### `_adql_cone_query(ra, dec, radius_deg, max_rows)`
Costruisce la stringa ADQL di una **cone search** (ricerca a cono) attorno a una
coordinata. Seleziona le colonne astrometriche fondamentali: `source_id`, `ra`,
`dec`, `parallax`, `parallax_error`, `phot_g_mean_mag`, `bp_rp`, `pmra`,
`pmdec`. Usa `SELECT TOP {max_rows}` (mai `LIMIT`, che causerebbe errore 400 dal
server Gaia) e ordina per magnitudine G crescente (le stelle più luminose per
prime).

### `_to_dataframe(table)`
Converte il risultato della query (una tabella astropy) in un `pandas.DataFrame`.
Se la tabella è `None`, ritorna un DataFrame vuoto con le colonne attese, così
il resto del codice può contare sempre sullo stesso schema.

### `query_region(ra, dec, radius_deg, max_rows=100)`
Funzione principale: interroga Gaia per gli oggetti in una regione di cielo.
- **Valida gli input**: solleva `ValueError` se il raggio o `max_rows` non sono
  positivi.
- Rispetta `Gaia.ROW_LIMIT` se impostato, riducendo `max_rows` con un avviso.
- Lancia il job con `Gaia.launch_job` e ne raccoglie i risultati.
- **Gestisce esplicitamente gli errori di rete**: `ConnectionError` (rete),
  `TimeoutError` (query troppo lunga) e qualunque altra eccezione, che viene
  rilanciata come `RuntimeError` con messaggio chiaro in italiano.

### `query_by_name(star_name, radius_deg=0.1, max_rows=100)`
Risolve un nome di stella in coordinate tramite `SkyCoord.from_name` (che
interroga i name resolver ufficiali come SIMBAD/NED) e poi delega a
`query_region`. Solleva errori chiari se il nome è vuoto o non risolvibile.

## Blocco di test

Il blocco `if __name__ == "__main__":` esegue una query di esempio su Sirio e ne
stampa le prime righe, utile per verificare rapidamente la connettività.

## Note sulla conformità

- Solo API ufficiali, accesso anonimo, nessun bypass dei rate limit.
- Solo `TOP` in ADQL, mai `LIMIT`.
