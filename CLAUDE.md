# Istruzioni per Claude Code — Progetto AstroNew

## Descrizione del progetto
AstroNew è un'app desktop in Python che interroga l'archivio pubblico ufficiale Gaia DR3 
(ESA), elabora i dati con calcoli astrofisici reali, li visualizza con grafici scientifici 
(matplotlib) e offre un assistente IA con tool calling autonomo (basato su un'API compatibile 
OpenAI, attualmente OpenRouter con modello NVIDIA Nemotron) che risponde a domande e 
interroga Gaia in autonomia quando necessario.

## Regola non negoziabile sui dati
Tutti i dati devono provenire ESCLUSIVAMENTE da archivi pubblici ufficiali, tramite le loro 
API ufficiali:
- Gaia DR3 (ESA) via `astroquery.gaia` / TAP-ADQL — nessuna autenticazione richiesta, 
  accesso pubblico e legale
- In futuro: MAST (TESS, Hubble), SDSS — solo tramite le rispettive API ufficiali

È VIETATO qualsiasi scraping non autorizzato, bypass di autenticazione, o superamento dei 
rate limit degli archivi. ADQL supporta SOLO "TOP" per limitare le righe, MAI "LIMIT" 
insieme a TOP nella stessa query (causa errore 400 dal server Gaia).

## Stack tecnico
- Python 3.11+, ambiente virtuale in `.venv`
- Librerie: astroquery, astropy, matplotlib, pandas, openai (>=1.0), python-dotenv
- Struttura cartelle (nome pacchetto: `astronew`, tutto minuscolo):
  - `astronew/data/` → client di accesso a Gaia (query)
  - `astronew/analysis/` → funzioni di calcolo astrofisico
  - `astronew/viz/` → funzioni di plotting scientifico
  - `astronew/ai/` → assistente IA con tool calling
  - `astronew/main.py` → entry point con menu principale

## Configurazione IA (importante)
- Il progetto usa un'API compatibile OpenAI (OpenRouter), NON Ollama locale (migrazione 
  già avvenuta da Ollama a causa di tool calling inaffidabile su modelli piccoli locali)
- Variabili in `.env`: OPENROUTER_API_KEY, AI_MODEL, API_BASE_URL — MAI hardcodare la 
  chiave nel codice, MAI committare `.env` con valori reali (deve restare nel .gitignore)
- La libreria `openai` usata è versione >=1.0: gli errori si importano direttamente da 
  `openai` (es. `from openai import APITimeoutError, RateLimitError`), NON da `openai.error` 
  (modulo rimosso nelle versioni recenti — errore noto già riscontrato in questo progetto)
- Il parametro per il timeout nelle chiamate si chiama `timeout`, non `request_timeout` 
  (altro errore noto già riscontrato)
- Non istanziare mai manualmente eccezioni come `APIError(...)` da zero: nei blocchi 
  except, catturare l'eccezione originale e usare `str(e)` per il messaggio, mai ricreare 
  l'oggetto eccezione a mano

## Convenzioni di codice
- Ogni funzione di calcolo deve avere una docstring che cita la formula fisica usata 
  (es. modulo di distanza, legge di Pogson, ecc.)
- Validare sempre gli input (es. parallasse <= 0 deve sollevare un errore chiaro, non un crash)
- Gestire esplicitamente gli errori di rete e i rate limit (mai fallire in silenzio con 
  messaggi generici che nascondono l'errore reale — sempre mostrare il tipo di eccezione 
  e il messaggio specifico durante lo sviluppo/debug)
- Non hardcodare mai chiavi API: sempre da `.env` via `python-dotenv`
- Prima di chiamare una funzione di supporto/helper, verificare che sia effettivamente 
  definita nel file — sono già capitati bug per funzioni richiamate ma mai implementate 
  (es. `_resolve_tool_name`, `_format_tool_response`)

## System prompt dell'assistente IA (regole comportamentali)
- Deve rispondere in modo conversazionale naturale a saluti/messaggi generici, SENZA 
  scaricare dump di dati grezzi quando non richiesto
- Deve attenersi rigorosamente ai dati reali quando la domanda li richiede, senza inventare 
  numeri, algoritmi, teorie o nomi di metodi scientifici inesistenti
- Deve usare la terminologia astronomica corretta (ra = ascensione retta, dec = declinazione, 
  parallax in mas, phot_g_mean_mag = magnitudine banda G, bp_rp = indice di colore, pmra/pmdec 
  = moto proprio) e non tradurla o reinterpretarla con termini inventati
- Se una domanda richiede conoscenze che vanno oltre i dati caricati, deve dirlo chiaramente 
  invece di rispondere con falsa sicurezza

## Validazione delle modifiche
Ogni modulo ha un blocco `if __name__ == "__main__":` con un test rapido. Testare sempre 
lanciando come modulo dalla root del progetto:
python3 -m astronew.main

(nota: il nome del pacchetto è case-sensitive, deve essere sempre minuscolo `astronew`, 
anche se la cartella esterna del progetto può avere maiuscole)

## Licenza e distribuzione
Progetto no-profit/educativo, licenza PolyForm Noncommercial License 1.0.0. Attribuzione 
obbligatoria a ESA Gaia DR3 deve comparire nell'app e nella documentazione.