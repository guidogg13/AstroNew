# AstroNew

AstroNew è un'app desktop Python per l'astrofisica che combina query ufficiali all'archivio Gaia DR3 dell'ESA, calcoli astrofisici e visualizzazioni scientifiche.

## Struttura del progetto

- `main.py` : entry point con menu interattivo
- `setup.py` : configurazione guidata al primo avvio (setup wizard)
- `data/gaia_client.py` : client per query TAP/ADQL ufficiali a Gaia DR3
- `analysis/calculations.py` : funzioni di calcolo astrofisico
- `viz/plots.py` : grafici scientifici con matplotlib
- `ai/assistant.py` : wrapper per l'assistente IA basato su un provider compatibile OpenAI (OpenRouter)

## Nota sulla liceità dei dati

I dati usati da AstroNew devono provenire esclusivamente da archivi pubblici ufficiali. Gaia DR3 è un archivio pubblico dell'ESA e il suo utilizzo è consentito con citazione della fonte e nel rispetto dei termini d'uso ufficiali.

## Installazione

```bash
pip install -r requirements.txt
```

## Configurazione IA

### Configurazione guidata al primo avvio (consigliata)

Al **primo avvio** dell'app, se il file `astronew/.env` non esiste ancora (oppure la chiave API è vuota o uguale al placeholder), parte automaticamente una **configurazione guidata** che chiede in sequenza:

- la **chiave API** di un provider compatibile OpenAI come OpenRouter (gratuito per molti modelli)
- il **nome del modello**: va inserito esplicitamente (non c'è un default hardcodato nel codice), copiandolo dalla pagina del modello su openrouter.ai; deve supportare il tool calling
- il **base URL** dell'API, con default `https://openrouter.ai/api/v1`: premi Invio per accettarlo

Le risposte vengono salvate automaticamente in `astronew/.env`: **non serve modificare il file a mano**.

Se lasci vuota la chiave (premi solo Invio), l'assistente IA resta disabilitato ma puoi comunque usare le altre funzioni (ricerca dati e grafici); la configurazione guidata ripartirà al prossimo avvio.

Ai **successivi avvii**, con una chiave valida già presente, il setup non viene rieseguito e l'app parte direttamente col menu principale.

### Configurazione manuale (alternativa)

In alternativa puoi creare tu stesso il file `astronew/.env` con queste variabili:

```text
OPENROUTER_API_KEY=INSERISCI_QUI_LA_TUA_CHIAVE_OPENROUTER
AI_MODEL=nvidia/nemotron-3-super-120b-a12b:free
API_BASE_URL=https://openrouter.ai/api/v1
```

Sostituisci `INSERISCI_QUI_LA_TUA_CHIAVE_OPENROUTER` con la tua chiave API reale. Se la chiave resta il placeholder, l'app mostrerà un messaggio chiaro al posto di fallire con un errore Python generico.

## Esecuzione

Lancia l'app come modulo dalla root del progetto (il nome del pacchetto è minuscolo, `astronew`):

```bash
python3 -m astronew.main
```

### Menu principale

```
1) Cerca stella/regione
2) Visualizza grafici
3) Assistente IA
4) Esci
5) Configura provider IA (chiave API e modello)
6) Togli tutte le chiavi API dal progetto
```

Le opzioni **5** e **6** gestiscono la configurazione dell'IA in qualsiasi momento, non solo al primo avvio:

- **`5) Configura provider IA`** — mostra la configurazione attuale (chiave API mascherata, es. `sk-or-v1-****...1234`, modello, modello di fallback e base URL) e permette di cambiare chiave API, modello (`AI_MODEL`), modello di fallback (`AI_MODEL_FALLBACK`) e base URL. Premi Invio su un campo per lasciarlo invariato. Le modifiche vengono scritte in `astronew/.env` (le righe esistenti vengono sostituite, mai duplicate) e ricaricate subito, senza riavviare l'app.
- **`6) Togli tutte le chiavi API dal progetto`** — pulsante di sicurezza: dopo una richiesta di conferma, scandisce ogni file di testo del progetto (saltando `.venv`, `.git` e i file binari) e sostituisce col placeholder ogni chiave in formato `sk-...`, senza toccare `.env.example`. La configurazione viene ricaricata, così la chiave rimossa non è più attiva nella sessione. Utile prima di condividere o committare il progetto; per rimettere una chiave usa l'opzione 5.
