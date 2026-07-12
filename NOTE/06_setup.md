# `astronew/setup.py` — Configurazione guidata al primo avvio

Questo modulo implementa il **setup wizard** di AstroNew: al primo avvio guida
l'utente nella creazione del file `.env` con la configurazione dell'assistente
IA, senza doverlo modificare a mano.

## Ruolo nel progetto

Viene richiamato da `main.py` all'avvio, prima del menu principale. Il suo scopo
è rendere l'app usabile "out of the box": se manca la configurazione IA, la
chiede in modo interattivo; se è già presente e valida, non fa nulla e l'app
parte direttamente.

## Funzioni

### `_read_env_value(env_path, key)`
Legge il valore di una chiave **direttamente dal file `.env`**, senza dipendere
da `os.environ` (che potrebbe contenere valori ereditati dalla shell). Ignora
righe vuote e commenti, e gestisce virgolette attorno ai valori. Ritorna `None`
se la chiave non è presente o il file non è leggibile.

### `is_setup_needed(env_path=ENV_PATH)`
Ritorna `True` se serve il setup guidato, cioè quando:
- il file `.env` non esiste, **oppure**
- `OPENROUTER_API_KEY` manca, è vuota, o è ancora il placeholder di default.

### `_write_env(env_path, api_key, model, base_url)`
Scrive (o sovrascrive) le tre righe di configurazione nel file `.env`:
`OPENROUTER_API_KEY`, `AI_MODEL`, `API_BASE_URL`. Crea la cartella genitore se
necessario.

### `run_first_time_setup(env_path=ENV_PATH)`
Funzione principale, eseguita all'avvio dell'app:
- Se il setup non serve (chiave valida già presente), ritorna subito.
- Altrimenti mostra un messaggio di benvenuto e chiede in sequenza: chiave API,
  nome modello (con default `DEFAULT_AI_MODEL`) e base URL (con default
  `DEFAULT_API_BASE_URL`).
- Gestisce `KeyboardInterrupt`/`EOFError`: se l'utente annulla, il setup
  ripartirà al prossimo avvio.
- **Se la chiave è inserita**: scrive `.env`, ricarica la configurazione con
  `reload_config()` e conferma che tutto è pronto.
- **Se la chiave è vuota**: salva comunque modello e base URL con il placeholder,
  così le altre funzioni (ricerca dati, grafici) restano disponibili e il setup
  ripartirà al prossimo avvio. L'assistente IA resta disattivato finché non si
  configura una chiave.

## Relazione con `assistant.py`

Il modulo importa da `astronew.ai.assistant` le costanti condivise
(`DEFAULT_AI_MODEL`, `DEFAULT_API_BASE_URL`, `ENV_PATH`, `PLACEHOLDER_KEY`) e la
funzione `reload_config`, così che scrittura del `.env` e ricarica in memoria
restino coerenti.

## Blocco di test

Il blocco `if __name__ == "__main__":` stampa il percorso del `.env`, indica se
il setup è necessario e, in caso, lo esegue — utile per testare il wizard in
isolamento.
