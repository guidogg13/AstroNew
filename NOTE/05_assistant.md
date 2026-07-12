# `astronew/ai/assistant.py` — Assistente IA con tool calling

Questo modulo implementa l'**assistente IA** di AstroNew. Comunica con un
provider cloud **compatibile OpenAI** (attualmente OpenRouter con modello NVIDIA
Nemotron) e può interrogare Gaia DR3 in autonomia tramite *tool calling*.

## Ruolo nel progetto

È il modulo più complesso dell'app. Riceve le domande dell'utente, allega come
contesto i dati già caricati, decide (tramite il modello) se servono altre query
a Gaia, esegue gli strumenti richiesti e restituisce una risposta in linguaggio
naturale basata su dati reali.

## Configurazione

- La chiave API, il modello e la base URL sono letti da `astronew/.env` con
  `python-dotenv`. **Mai** hardcodare la chiave nel codice.
- `reload_config()` (ri)popola le costanti di modulo dal `.env`, da richiamare
  dopo il setup guidato così che i nuovi valori valgano nello stesso processo.
- Gli errori si importano direttamente da `openai` (>=1.0), non da `openai.error`.
- Il timeout nelle chiamate usa il parametro `timeout` (non `request_timeout`).

## Definizione degli strumenti

`TOOL_DEFINITIONS` descrive due strumenti esposti al modello:
- **`query_by_name`**: cerca su Gaia per nome di stella.
- **`query_region`**: cerca su Gaia per coordinate (RA/Dec) e raggio.

Questi vengono impacchettati in `TOOLS` nel formato richiesto dall'API OpenAI.

## Funzioni principali

### Validazione e client
- `_is_api_key_placeholder()` / `_validate_openai_config()`: verificano che la
  chiave non sia vuota o placeholder e che il modello sia impostato.
- `_get_openai_client()`: costruisce il client `OpenAI` con chiave e base URL.

### Normalizzazione delle risposte
- `_message_to_dict()` e `_extract_response_message()`: normalizzano la risposta
  del provider (che può essere dict o oggetto) in un dizionario uniforme,
  includendo eventuali `tool_calls`.
- `_call_openai_with_tools()`: esegue la chiamata `chat.completions.create` con
  `tools` e `tool_choice="auto"`, gestendo separatamente ogni tipo di errore
  (autenticazione, rate limit, timeout, connessione, API).

### Contesto dati
- `_prepare_dataframe_context()`: calcola colonne derivate (distanza, magnitudine
  assoluta, moto proprio totale, velocità tangenziale, luminosità) riga per riga.
- `_format_dataframe_context()`: converte il DataFrame in testo compatto per il
  modello, mantenendo solo le colonne utili.
- `_find_extreme_value()`: riconosce domande su valori estremi (stella più
  vicina/lontana/luminosa, moto proprio o velocità massima) e calcola la
  risposta direttamente in Python, evitando che il modello inventi numeri.

### Esecuzione degli strumenti
- `_resolve_tool_name()`: estrae il nome del tool dal dizionario `function`.
- `_format_tool_response()`: converte il DataFrame risultato in testo leggibile.
- `_execute_tool_call()`: esegue realmente la query Gaia richiesta dal modello e
  ne restituisce l'output (o un messaggio d'errore esplicito).

### Interfaccia pubblica
- `get_assistant_status()`: restituisce un messaggio sullo stato della
  configurazione (usato da `main.py` prima di avviare la sessione).
- `ask_astro_assistant()`: orchestrazione completa — costruisce il system
  prompt, allega il contesto, chiama il modello, esegue in loop gli eventuali
  tool call finché non arriva la risposta finale.
- `interactive_session()`: ciclo interattivo a riga di comando (`>>>`) per
  dialogare con l'assistente; si esce con `esci`/`exit`/`quit`.

## Regole comportamentali del system prompt

Rispondere in modo naturale ai saluti senza scaricare dati grezzi; attenersi ai
dati reali senza inventare numeri, algoritmi o metodi; usare la terminologia
astronomica corretta; ammettere chiaramente quando non ci sono dati sufficienti.
