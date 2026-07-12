"""Configurazione guidata al primo avvio di AstroNew (setup wizard).

Al primo avvio, se il file .env non esiste oppure la chiave API è ancora il
placeholder (o è vuota/mancante), questo modulo guida l'utente nella creazione
del file .env, senza doverlo modificare a mano. Ai successivi avvii, con una
chiave valida già presente, non fa nulla e l'app parte direttamente col menu.
"""

from __future__ import annotations

from pathlib import Path

from astronew.ai.assistant import (
    DEFAULT_AI_MODEL,
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

    Serve setup se: il file .env non esiste, oppure OPENROUTER_API_KEY manca,
    è vuota o è ancora il placeholder di default.
    """
    if not env_path.exists():
        return True
    api_key = _read_env_value(env_path, "OPENROUTER_API_KEY")
    return not api_key or api_key == PLACEHOLDER_KEY


def _write_env(env_path: Path, api_key: str, model: str, base_url: str) -> None:
    """Scrive (o sovrascrive) le tre righe di configurazione in .env."""
    content = (
        f"OPENROUTER_API_KEY={api_key}\n"
        f"AI_MODEL={model}\n"
        f"API_BASE_URL={base_url}\n"
    )
    env_path.parent.mkdir(parents=True, exist_ok=True)
    env_path.write_text(content, encoding="utf-8")


def run_first_time_setup(env_path: Path = ENV_PATH) -> None:
    """Esegue la configurazione guidata al primo avvio, se necessaria.

    Se .env esiste già con una chiave valida (diversa dal placeholder), non fa
    nulla e l'app prosegue direttamente. Altrimenti mostra un messaggio di
    benvenuto, chiede in sequenza chiave API, modello e base_url (con default
    suggeriti), scrive .env e ricarica la configurazione dell'assistente.
    """
    if not is_setup_needed(env_path):
        return

    print("\n=== Configurazione guidata di AstroNew ===")
    print(
        "Benvenuto in AstroNew! Per usare l'assistente IA devi configurare una "
        "chiave API compatibile OpenAI (es. da openrouter.ai, gratuito per molti "
        "modelli)."
    )
    print(
        "Suggerimento: puoi lasciare vuota la chiave e premere Invio per saltare. "
        "Le altre funzioni (ricerca dati e grafici) resteranno comunque disponibili.\n"
    )

    try:
        api_key = input("Incolla qui la tua chiave API: ").strip()
        model = (
            input(f"Nome modello [default: {DEFAULT_AI_MODEL}]: ").strip()
            or DEFAULT_AI_MODEL
        )
        base_url = (
            input(f"Base URL API [default: {DEFAULT_API_BASE_URL}]: ").strip()
            or DEFAULT_API_BASE_URL
        )
    except (KeyboardInterrupt, EOFError):
        print("\nConfigurazione annullata. Potrai rieseguirla al prossimo avvio.")
        return

    if api_key:
        _write_env(env_path, api_key, model, base_url)
        reload_config()
        print(f"\nConfigurazione salvata in {env_path}.")
        print("Tutto pronto: puoi procedere e usare tutte le funzioni, IA inclusa!\n")
    else:
        # Nessuna chiave: salviamo comunque modello e base_url con il placeholder,
        # così le altre funzioni partono e il setup ripartirà al prossimo avvio.
        _write_env(env_path, PLACEHOLDER_KEY, model, base_url)
        reload_config()
        print(
            "\nNessuna chiave API inserita: l'assistente IA NON sarà disponibile "
            "finché non configurerai una chiave. Le altre funzionalità dell'app "
            "(ricerca dati, grafici) restano pienamente utilizzabili."
        )
        print("La configurazione guidata ripartirà al prossimo avvio.\n")


if __name__ == "__main__":
    # Test rapido: mostra se il setup è necessario e, in caso, lo esegue.
    print(f"File .env: {ENV_PATH}")
    print(f"Setup necessario? {is_setup_needed()}")
    run_first_time_setup()
