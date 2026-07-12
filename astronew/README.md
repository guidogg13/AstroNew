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
- il **nome del modello**, con un default già suggerito (`nvidia/nemotron-3-super-120b-a12b:free`): premi Invio per accettarlo
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
