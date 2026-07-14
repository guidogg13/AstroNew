# Istruzioni per Claude Code — Progetto AstroNew

## Descrizione del progetto
AstroNew è un'app desktop in Python che interroga l'archivio pubblico ufficiale Gaia DR3 
(ESA), elabora i dati con calcoli astrofisici reali, li visualizza con grafici scientifici 
(matplotlib) e offre un assistente IA con tool calling autonomo (basato su un'API compatibile 
OpenAI via OpenRouter, modello nvidia/nemotron-3-super-120b-a12b:free) che risponde a domande 
e interroga Gaia in autonomia quando necessario, senza richiedere che l'utente carichi prima 
i dati manualmente.

Repository: https://github.com/guidogg13/AstroNew

## Regola non negoziabile sui dati
Tutti i dati devono provenire ESCLUSIVAMENTE da archivi pubblici ufficiali, tramite le loro 
API ufficiali:
- Gaia DR3 (ESA) via `astroquery.gaia` / TAP-ADQL — nessuna autenticazione richiesta, 
  accesso pubblico e legale
- In futuro: MAST (TESS, Hubble), SDSS — solo tramite le rispettive API ufficiali

È VIETATO qualsiasi scraping non autorizzato, bypass di autenticazione, o superamento dei 
rate limit degli archivi. ADQL supporta SOLO "TOP" per limitare le righe, MAI "LIMIT" 
insieme a TOP nella stessa query (causa errore 400 dal server Gaia — bug già riscontrato 
e risolto in questo progetto).

## Stack tecnico
- Python 3.11+, ambiente virtuale in `.venv` (va ricreato da zero se il progetto viene 
  spostato su un computer diverso o via chiavetta/SSD, mai copiato direttamente)
- Librerie: astroquery, astropy, matplotlib, pandas, openai (>=1.0), python-dotenv
- Struttura cartelle (nome pacchetto: `astronew`, SEMPRE minuscolo — su macOS il 
  filesystem è case-insensitive ma Python è case-sensitive, quindi una cartella 
  rinominata "AstroNew" con maiuscole rompe gli import):
  - `astronew/data/` → client di accesso a Gaia (query)
  - `astronew/analysis/` → funzioni di calcolo astrofisico
  - `astronew/viz/` → funzioni di plotting scientifico
  - `astronew/ai/` → assistente IA con tool calling
  - `astronew/main.py` → entry point con menu principale
  - `astronew/setup.py` → setup guidato configurazione (in sviluppo)
  - `NOTE/` → documentazione tecnica per modulo (numerata: 00_panoramica.md, 01_main.md, ecc.)

## Configurazione IA (importante)
- Il progetto usa un'API compatibile OpenAI (OpenRouter), NON Ollama locale (migrazione 
  già avvenuta e completata da Ollama a causa di tool calling inaffidabile su modelli 
  piccoli locali come qwen2.5-coder:1.5b)
- Variabili in `astronew/.env` (MAI in `.env` nella root esterna, va dentro `astronew/`):
OPENROUTER_API_KEY=...
AI_MODEL=nvidia/nemotron-3-super-120b-a12b:free
API_BASE_URL=https://openrouter.ai/api/v1
- ATTENZIONE: l'URL deve finire con `/api/v1` per intero — un errore comune già capitato 
  è avere solo `https://openrouter.ai/` (manca `/api/v1`), che causa "Modello IA non 
  trovato o non disponibile" anche se la chiave e il modello sono corretti
- MAI hardcodare la chiave nel codice, MAI committare `.env` con valori reali (deve 
  restare nel .gitignore — verificato più volte che funziona correttamente)
- La libreria `openai` usata è versione >=1.0: gli errori si importano direttamente da 
  `openai` (es. `from openai import APITimeoutError, RateLimitError`), NON da 
  `openai.error` (modulo rimosso — bug già riscontrato e risolto)
- Il parametro per il timeout nelle chiamate si chiama `timeout`, non `request_timeout` 
  (bug già riscontrato e risolto)
- Non istanziare mai manualmente eccezioni come `APIError(...)` da zero: nei blocchi 
  except, catturare l'eccezione originale e usare `str(e)` per il messaggio (bug già 
  riscontrato e risolto)
- Quando si mostra un errore generico all'utente, usare SEMPRE `except Exception as e: 
  print(f"Errore: {type(e).__name__}: {e}")` durante lo sviluppo — mai un messaggio 
  generico che nasconde l'errore reale, ha causato perdite di tempo significative in 
  passato nel debug

## Convenzioni di codice
- Ogni funzione di calcolo deve avere una docstring che cita la formula fisica usata 
  (es. modulo di distanza, legge di Pogson, ecc.)
- Validare sempre gli input (es. parallasse <= 0 deve sollevare un errore chiaro, non un crash)
- Gestire esplicitamente gli errori di rete e i rate limit (mai fallire in silenzio)
- Prima di chiamare una funzione di supporto/helper, verificare che sia effettivamente 
  definita nel file — sono già capitati bug per funzioni richiamate ma mai implementate 
  (es. `_resolve_tool_name`, `_format_tool_response`)
- Ogni funzione che accede a un archivio deve citare nel commento la fonte ufficiale 
  e l'URL dell'archivio

## System prompt dell'assistente IA (regole comportamentali)
- Deve rispondere in modo conversazionale naturale a saluti/messaggi generici, SENZA 
  scaricare dump di dati grezzi quando non richiesto (bug già riscontrato e risolto)
- Deve attenersi rigorosamente ai dati reali quando la domanda li richiede, senza inventare 
  numeri, algoritmi, teorie o nomi di metodi scientifici inesistenti (bug già riscontrato: 
  il modello aveva inventato un "algoritmo di Gregory-Chapman" inesistente)
- Deve usare la terminologia astronomica corretta (ra = ascensione retta, dec = declinazione, 
  parallax in mas, phot_g_mean_mag = magnitudine banda G, bp_rp = indice di colore, pmra/pmdec 
  = moto proprio) e non tradurla con termini inventati
- Se una domanda richiede conoscenze che vanno oltre i dati caricati, deve dirlo chiaramente 
  invece di rispondere con falsa sicurezza
- Il tool calling autonomo (query_by_name, query_region) funziona correttamente con il 
  modello attuale (nvidia/nemotron-3-super-120b-a12b:free) — non funzionava affidabilmente 
  con modelli piccoli locali

## Gestione input utente
- Il loop principale (menu e sessione IA) deve gestire KeyboardInterrupt e EOFError in 
  modo pulito, mostrando un messaggio e tornando al menu invece di mostrare un traceback

## Git e distribuzione
- `.env` è protetto da `.gitignore` sia dentro `astronew/` che verificato più volte 
  con `git log -p --all -- astronew/.env` (nessuna esposizione mai avvenuta)
- Se emergono divergenze tra branch locale e remoto: `git config pull.rebase false`, 
  poi `git pull origin main`, poi `git push`
- Se si è spostato il progetto su un nuovo computer (es. via SSD): ricreare SEMPRE 
  `.venv` da zero (`rm -rf .venv && python3 -m venv .venv`), mai riusare quello copiato, 
  perché contiene percorsi assoluti legati alla macchina precedente

## Validazione delle modifiche
Ogni modulo ha un blocco `if __name__ == "__main__":` con un test rapido. Testare sempre 
lanciando come modulo dalla root del progetto:
python3 -m astronew.main
## Licenza e distribuzione
Progetto no-profit/educativo, licenza PolyForm Noncommercial License 1.0.0 (file 
LICENZE.md nella root). Attribuzione obbligatoria a ESA Gaia DR3 deve comparire 
nell'app e nella documentazione.