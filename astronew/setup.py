"""Configurazione guidata al primo avvio di AstroNew (setup wizard).

Al primo avvio, se il file .env non esiste oppure la chiave API è ancora il
placeholder (o è vuota/mancante), questo modulo guida l'utente nella creazione
del file .env, senza doverlo modificare a mano. Ai successivi avvii, con una
chiave valida già presente, non fa nulla e l'app parte direttamente col menu.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from astronew.ai.assistant import (
    DEFAULT_AI_MODEL,
    DEFAULT_AI_MODEL_FALLBACK,
    DEFAULT_API_BASE_URL,
    ENV_PATH,
    PLACEHOLDER_KEY,
    reload_config,
)


def _read_env_value(env_path: Path, key: str) -> str | None:
    """Legge il valore di `key` direttamente dal file .env.

    Non dipende da os.environ (che potrebbe contenere valori già caricati o
    ereditati dall'ambiente della shell). Ignora righe vuote e commenti.
    Ritorna None se la chiave non è presente o il file non è leggibile.
    """
    try:
        lines = env_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        name, _, value = stripped.partition("=")
        if name.strip() == key:
            return value.strip().strip('"').strip("'")
    return None


def is_setup_needed(env_path: Path = ENV_PATH) -> bool:
    """True se la configurazione IA manca e serve il setup guidato.

    Serve setup se il file .env non esiste, oppure se OPENROUTER_API_KEY manca /
    è vuota / è ancora il placeholder, oppure se AI_MODEL manca / è vuoto. In
    questo modo all'avvio vengono sempre chiesti esplicitamente ENTRAMBI i valori
    (chiave API e nome del modello), che non sono mai hardcodati nel sorgente.
    """
    if not env_path.exists():
        return True
    api_key = _read_env_value(env_path, "OPENROUTER_API_KEY")
    if not api_key or api_key == PLACEHOLDER_KEY:
        return True
    model = _read_env_value(env_path, "AI_MODEL")
    return not model


def _sanitize_base_url(raw: str) -> str:
    """Ripulisce il base_url e garantisce il suffisso `/api/v1`.

    Bug già riscontrato: caratteri residui incollati dal terminale (spazi
    interni, tab, newline, caratteri di controllo o zero-width) e URL senza il
    suffisso `/api/v1` causano "Modello IA non trovato". Qui rimuoviamo ogni
    spazio/carattere di controllo e, se manca, aggiungiamo `/api/v1` alla fine.
    """
    if not raw:
        return DEFAULT_API_BASE_URL
    # Rimuove qualsiasi spazio (anche interno) e caratteri di controllo/zero-width.
    cleaned = "".join(ch for ch in raw if ch.isprintable() and not ch.isspace())
    if not cleaned:
        return DEFAULT_API_BASE_URL
    # Toglie eventuali slash finali di troppo prima di controllare il suffisso.
    cleaned = cleaned.rstrip("/")
    if not cleaned.endswith("/api/v1"):
        cleaned = f"{cleaned}/api/v1"
    return cleaned


def _write_env(env_path: Path, api_key: str, model: str, base_url: str) -> None:
    """Scrive (o sovrascrive) le righe di configurazione in .env.

    Usa _upsert_env_values così da NON duplicare righe e da preservare eventuali
    altre righe già presenti (bug già riscontrato: righe duplicate della stessa
    variabile, es. due AI_MODEL, che rendevano imprevedibile il valore letto).
    """
    _upsert_env_values(
        env_path,
        {
            "OPENROUTER_API_KEY": api_key,
            "AI_MODEL": model,
            "API_BASE_URL": _sanitize_base_url(base_url),
        },
    )


def _upsert_env_values(env_path: Path, updates: dict[str, str]) -> None:
    """Aggiorna in .env solo le variabili in `updates`, senza duplicare righe.

    Regole (per evitare il bug delle righe duplicate già riscontrato):
    - per ogni variabile in `updates`, sostituisce la PRIMA riga esistente con
      quel nome e rimuove ogni eventuale riga duplicata successiva con lo stesso
      nome;
    - se la variabile non esiste ancora, la aggiunge in fondo;
    - qualsiasi altra riga (commenti, righe vuote, altre variabili) resta intatta.
    """
    try:
        existing_lines = env_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        existing_lines = []

    remaining = dict(updates)
    result_lines: list[str] = []
    written_names: set[str] = set()

    for line in existing_lines:
        stripped = line.strip()
        # Righe vuote/commenti/senza '=' vengono preservate così come sono.
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            result_lines.append(line)
            continue
        name = stripped.partition("=")[0].strip()
        if name in updates:
            if name in written_names:
                # Riga duplicata dello stesso nome: la scartiamo del tutto.
                continue
            result_lines.append(f"{name}={updates[name]}")
            written_names.add(name)
            remaining.pop(name, None)
        else:
            result_lines.append(line)

    # Variabili non ancora presenti nel file: le aggiungiamo in fondo.
    for name, value in remaining.items():
        result_lines.append(f"{name}={value}")

    env_path.parent.mkdir(parents=True, exist_ok=True)
    env_path.write_text("\n".join(result_lines) + "\n", encoding="utf-8")


def _mask_api_key(api_key: str | None) -> str:
    """Restituisce una versione mascherata della chiave API per la visualizzazione.

    Mostra solo il prefisso (i primi 9 caratteri) e le ultime 4 cifre, mai la
    parte centrale della chiave: es. 'abcdefghi****...1234'. Ritorna
    '(non impostata)' se la chiave manca o è ancora il placeholder.
    """
    if not api_key or api_key == PLACEHOLDER_KEY:
        return "(non impostata)"
    if len(api_key) <= 12:
        return "****"
    prefix = api_key[:9]
    suffix = api_key[-4:]
    return f"{prefix}****...{suffix}"


def configure_ai_provider(env_path: Path = ENV_PATH) -> None:
    """Riconfigura provider IA (chiave, modello, fallback, base_url) in qualsiasi momento.

    Mostra la configurazione attuale (chiave mascherata) e chiede i nuovi valori:
    premendo solo Invio si mantiene il valore corrente. Scrive SOLO le righe
    relative in astronew/.env senza duplicarle, poi ricarica la configurazione in
    memoria con reload_config() (load_dotenv override=True) così la nuova
    impostazione è usata subito, senza riavviare l'app.
    """
    print("\n=== Configura provider IA (chiave API e modello) ===")

    current_key = _read_env_value(env_path, "OPENROUTER_API_KEY")
    current_model = _read_env_value(env_path, "AI_MODEL") or DEFAULT_AI_MODEL
    current_fallback = (
        _read_env_value(env_path, "AI_MODEL_FALLBACK") or DEFAULT_AI_MODEL_FALLBACK
    )
    current_base_url = (
        _read_env_value(env_path, "API_BASE_URL") or DEFAULT_API_BASE_URL
    )

    print("\nConfigurazione attuale:")
    print(f"  Chiave API      : {_mask_api_key(current_key)}")
    print(f"  Modello         : {current_model}")
    print(f"  Modello fallback: {current_fallback}")
    print(f"  Base URL        : {current_base_url}")
    print(
        "\nPremi Invio per mantenere il valore attuale, oppure digita un nuovo valore.\n"
    )

    try:
        new_key = input("Nuova chiave API [Invio = invariata]: ").strip()
        new_model = input(f"Modello [{current_model}]: ").strip()
        new_fallback = input(f"Modello fallback [{current_fallback}]: ").strip()
        new_base_url = input(f"Base URL [{current_base_url}]: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nConfigurazione annullata. Nessuna modifica effettuata.")
        return

    updates: dict[str, str] = {}
    if new_key:
        updates["OPENROUTER_API_KEY"] = new_key
    if new_model and new_model != current_model:
        updates["AI_MODEL"] = new_model
    if new_fallback and new_fallback != current_fallback:
        updates["AI_MODEL_FALLBACK"] = new_fallback
    if new_base_url:
        sanitized = _sanitize_base_url(new_base_url)
        if sanitized != current_base_url:
            updates["API_BASE_URL"] = sanitized

    if not updates:
        print("\nNessuna modifica effettuata.")
        return

    _upsert_env_values(env_path, updates)
    reload_config()

    print(f"\nConfigurazione salvata in {env_path}.")
    print("Le nuove impostazioni sono già attive in questa sessione:")
    print(f"  Chiave API      : {_mask_api_key(_read_env_value(env_path, 'OPENROUTER_API_KEY'))}")
    print(f"  Modello         : {_read_env_value(env_path, 'AI_MODEL') or DEFAULT_AI_MODEL}")
    print(f"  Modello fallback: {_read_env_value(env_path, 'AI_MODEL_FALLBACK') or DEFAULT_AI_MODEL_FALLBACK}")
    print(f"  Base URL        : {_read_env_value(env_path, 'API_BASE_URL') or DEFAULT_API_BASE_URL}\n")


def run_first_time_setup(env_path: Path = ENV_PATH) -> None:
    """Esegue la configurazione guidata al primo avvio, se necessaria.

    Se .env esiste già con chiave valida e modello impostato, non fa nulla e
    l'app prosegue. Altrimenti chiede ESPLICITAMENTE all'utente sia la chiave API
    sia il nome del modello (nessuno dei due è hardcodato nel sorgente né
    precompilato con un valore che sembri reale) e il base_url (che non è una
    credenziale e ha un default noto). Scrive .env senza duplicare righe e
    ricarica la configurazione dell'assistente.
    """
    if not is_setup_needed(env_path):
        return

    current_key = _read_env_value(env_path, "OPENROUTER_API_KEY")
    current_model = _read_env_value(env_path, "AI_MODEL")
    current_base_url = _read_env_value(env_path, "API_BASE_URL") or DEFAULT_API_BASE_URL
    key_is_set = bool(current_key) and current_key != PLACEHOLDER_KEY

    print("\n=== Configurazione guidata di AstroNew ===")
    print(
        "Benvenuto in AstroNew! Per usare l'assistente IA devi configurare una "
        "chiave API compatibile OpenAI (es. da openrouter.ai, gratuito per molti "
        "modelli) e il nome del modello da usare."
    )
    print(
        "Suggerimento: puoi lasciare vuota la chiave e premere Invio per saltare. "
        "Le altre funzioni (ricerca dati e grafici) resteranno comunque disponibili.\n"
    )

    try:
        if key_is_set:
            api_key = (
                input("Chiave API [Invio = mantieni quella attuale]: ").strip()
                or current_key
            )
        else:
            api_key = input("Incolla qui la tua chiave API (Invio per saltare): ").strip()

        # Il nome del modello va SEMPRE chiesto all'utente: nessun ID di modello
        # è suggerito dal codice. Se ne esiste già uno in .env, Invio lo mantiene.
        if current_model:
            model = (
                input(f"Nome del modello IA [Invio = mantieni '{current_model}']: ").strip()
                or current_model
            )
        else:
            model = input(
                "Nome del modello IA (copialo dalla pagina del modello su "
                "openrouter.ai, deve supportare il tool calling): "
            ).strip()

        base_url = (
            input(f"Base URL API [default: {current_base_url}]: ").strip()
            or current_base_url
        )
    except (KeyboardInterrupt, EOFError):
        print("\nConfigurazione annullata. Potrai rieseguirla al prossimo avvio.")
        return

    if api_key and api_key != PLACEHOLDER_KEY:
        _upsert_env_values(
            env_path,
            {
                "OPENROUTER_API_KEY": api_key,
                "AI_MODEL": model,
                "API_BASE_URL": _sanitize_base_url(base_url),
            },
        )
        reload_config()
        print(f"\nConfigurazione salvata in {env_path}.")
        if model:
            print("Tutto pronto: puoi procedere e usare tutte le funzioni, IA inclusa!\n")
        else:
            print(
                "Chiave salvata, ma nessun modello IA impostato: l'assistente IA "
                "NON partirà finché non configuri un modello (menu: opzione 5).\n"
            )
    else:
        # Nessuna chiave: salviamo comunque modello e base_url con il placeholder,
        # così le altre funzioni partono e il setup ripartirà al prossimo avvio.
        _upsert_env_values(
            env_path,
            {
                "OPENROUTER_API_KEY": PLACEHOLDER_KEY,
                "AI_MODEL": model,
                "API_BASE_URL": _sanitize_base_url(base_url),
            },
        )
        reload_config()
        print(
            "\nNessuna chiave API inserita: l'assistente IA NON sarà disponibile "
            "finché non configurerai una chiave. Le altre funzionalità dell'app "
            "(ricerca dati, grafici) restano pienamente utilizzabili."
        )
        print("La configurazione guidata ripartirà al prossimo avvio.\n")


# Cartelle da NON scandire durante la rimozione delle chiavi (ambiente virtuale,
# repository git, cache, dipendenze): non contengono sorgenti del progetto e
# scandirle sarebbe lento e rischioso.
_SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".mypy_cache"}

# Pattern di una chiave API in stile OpenAI/OpenRouter: prefisso "sk-" seguito da
# almeno 12 caratteri fra lettere, cifre, trattino e underscore. Copre le chiavi
# OpenRouter ("sk-or-v1-..."), OpenAI ("sk-...", "sk-proj-...") ecc. Non tocca il
# placeholder (che non contiene "sk-").
_API_KEY_PATTERN = re.compile(r"sk-[A-Za-z0-9_-]{12,}")

# Nome della cartella radice del progetto (una sopra il pacchetto `astronew`).
PROJECT_ROOT = ENV_PATH.parent.parent


def _iter_project_files(project_root: Path):
    """Itera sui file del progetto saltando ambienti virtuali, .git e cache."""
    for dirpath, dirnames, filenames in os.walk(project_root):
        # Pota le cartelle da ignorare (modifica in-place per non discenderci).
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        for filename in filenames:
            yield Path(dirpath) / filename


def _scan_and_purge_keys(project_root: Path, placeholder: str) -> list[Path]:
    """Sostituisce ogni chiave API 'sk-...' col placeholder in tutti i file di testo.

    Salta `.env.example` (contiene solo placeholder) e i file binari/illeggibili.
    Ritorna la lista dei file effettivamente modificati.
    """
    changed: list[Path] = []
    for path in _iter_project_files(project_root):
        if path.name == ".env.example":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            # File binario o non leggibile: non può contenere una chiave in chiaro
            # da neutralizzare in modo sicuro, quindi lo saltiamo.
            continue
        if not _API_KEY_PATTERN.search(text):
            continue
        new_text = _API_KEY_PATTERN.sub(placeholder, text)
        if new_text != text:
            try:
                path.write_text(new_text, encoding="utf-8")
            except OSError:
                continue
            changed.append(path)
    return changed


def remove_all_api_keys(
    project_root: Path = PROJECT_ROOT, assume_yes: bool = False
) -> list[Path]:
    """Rimuove TUTTE le chiavi API (formato 'sk-...') da tutto il progetto.

    Cerca in ogni file di testo sotto `project_root` (esclusi ambienti virtuali,
    .git e cache) qualsiasi chiave in stile OpenAI/OpenRouter e la sostituisce col
    placeholder. Non tocca `.env.example`. Al termine ricarica la configurazione
    in memoria, così la sessione corrente non usa più la chiave rimossa. Ritorna
    la lista dei file modificati.
    """
    print("\n=== Togli tutte le chiavi API dal progetto ===")
    print(
        "Verrà cercata e neutralizzata ogni chiave API in formato 'sk-...' in tutti "
        f"i file di testo sotto:\n  {project_root}"
    )
    print(
        "Ogni chiave trovata sarà sostituita col placeholder. Il file .env.example "
        "e le cartelle .venv/.git non vengono toccati.\n"
    )

    if not assume_yes:
        try:
            conferma = input(
                "Confermi la rimozione di TUTTE le chiavi? Digita 'si' per procedere: "
            ).strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\nOperazione annullata. Nessuna modifica effettuata.")
            return []
        if conferma not in {"si", "sì", "s", "yes", "y"}:
            print("Operazione annullata. Nessuna modifica effettuata.")
            return []

    changed = _scan_and_purge_keys(project_root, PLACEHOLDER_KEY)
    reload_config()

    if changed:
        print(f"\nChiavi API rimosse da {len(changed)} file:")
        for path in changed:
            try:
                rel = path.relative_to(project_root)
            except ValueError:
                rel = path
            print(f"  - {rel}")
        print(
            "\nLa configurazione IA è stata ricaricata: la chiave rimossa non è più "
            "attiva in questa sessione. Reimposta una chiave dal menu (opzione 5) "
            "quando vuoi riusare l'assistente IA."
        )
    else:
        print("\nNessuna chiave API trovata nel progetto: niente da rimuovere.")

    return changed


if __name__ == "__main__":
    # Test rapido: mostra se il setup è necessario e, in caso, lo esegue.
    print(f"File .env: {ENV_PATH}")
    print(f"Setup necessario? {is_setup_needed()}")
    run_first_time_setup()
