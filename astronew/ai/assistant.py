"""Wrapper for an OpenAI-compatible astrophysics assistant.

This module communicates with any OpenAI-compatible cloud provider,
such as OpenRouter, NVIDIA NIM, or OpenAI directly. Configuration is loaded
from the local astronew/.env file using python-dotenv.
"""

from __future__ import annotations

import json
import os
import traceback
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from openai import (
    APIError,
    APIConnectionError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    OpenAI,
    RateLimitError,
    APITimeoutError,
)

from astronew.data.gaia_client import query_by_name, query_region

try:
    from astronew.analysis.calculations import (
        absolute_magnitude,
        luminosity_ratio,
        parallax_to_distance_pc,
        proper_motion_total as total_proper_motion,
        tangential_velocity,
    )
except ImportError:  # pragma: no cover - fallback for direct script execution
    from analysis.calculations import (
        absolute_magnitude,
        luminosity_ratio,
        parallax_to_distance_pc,
        proper_motion_total as total_proper_motion,
        tangential_velocity,
    )

ROOT_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT_DIR / ".env"

PLACEHOLDER_KEY = "INSERISCI_QUI_LA_TUA_CHIAVE_OPENROUTER"
# Nessun modello IA e' hardcodato: il nome del modello deve provenire SEMPRE da
# .env (variabile AI_MODEL), impostata dalla configurazione guidata
# (run_first_time_setup / configure_ai_provider). Qui il default resta vuoto
# apposta, cosi' nessun ID di modello di terze parti e' scritto nel sorgente.
DEFAULT_AI_MODEL = ""
# Modello di riserva: usato in automatico se il modello configurato in AI_MODEL
# restituisce una risposta in formato inatteso o non e' disponibile. Anche questo
# deve provenire da .env (AI_MODEL_FALLBACK); default vuoto (fallback disattivato
# finche' l'utente non ne configura uno).
DEFAULT_AI_MODEL_FALLBACK = ""
# API_BASE_URL non e' una credenziale: puo' restare come default nel codice.
DEFAULT_API_BASE_URL = "https://openrouter.ai/api/v1"

# Configurazione caricata da .env. I valori vengono (ri)popolati da
# reload_config() sia all'import sia dopo il setup guidato al primo avvio.
OPENROUTER_API_KEY = ""
AI_MODEL = ""
AI_MODEL_FALLBACK = DEFAULT_AI_MODEL_FALLBACK
API_BASE_URL = DEFAULT_API_BASE_URL


class ResponseFormatError(RuntimeError):
    """Sollevata quando la risposta dell'API non ha una struttura utilizzabile.

    Serve a distinguere gli errori di formato (che possono variare tra provider
    e modelli gratuiti diversi su OpenRouter) dagli errori di rete/autenticazione,
    così da poter attivare il fallback automatico su un modello di riserva.
    """


def reload_config() -> None:
    """(Ri)carica la configurazione dal file .env negli attributi del modulo.

    Va richiamata dopo che il setup guidato ha scritto/aggiornato .env, così che
    le costanti di modulo riflettano i nuovi valori nello stesso processo (le
    funzioni le leggono al momento della chiamata, non all'import).
    """
    global OPENROUTER_API_KEY, AI_MODEL, AI_MODEL_FALLBACK, API_BASE_URL
    load_dotenv(ENV_PATH, override=True)
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
    AI_MODEL = os.getenv("AI_MODEL", "").strip()
    AI_MODEL_FALLBACK = (
        os.getenv("AI_MODEL_FALLBACK", DEFAULT_AI_MODEL_FALLBACK).strip()
        or DEFAULT_AI_MODEL_FALLBACK
    )
    API_BASE_URL = (
        os.getenv("API_BASE_URL", DEFAULT_API_BASE_URL).strip() or DEFAULT_API_BASE_URL
    )


reload_config()

TOOL_DEFINITIONS = [
    {
        "name": "query_by_name",
        "description": "Search Gaia DR3 by star name and return astrometric data for matching sources.",
        "parameters": {
            "type": "object",
            "properties": {
                "star_name": {
                    "type": "string",
                    "description": "The name of the star to search for."
                },
                "radius_deg": {
                    "type": "number",
                    "description": "Search radius in degrees around the resolved star coordinates.",
                    "default": 0.1
                },
                "max_rows": {
                    "type": "integer",
                    "description": "Maximum number of Gaia rows to return.",
                    "default": 50
                },
            },
            "required": ["star_name"],
        },
    },
    {
        "name": "query_region",
        "description": "Search Gaia DR3 around RA and Dec coordinates within a radius.",
        "parameters": {
            "type": "object",
            "properties": {
                "ra": {
                    "type": "number",
                    "description": "Right ascension in degrees."
                },
                "dec": {
                    "type": "number",
                    "description": "Declination in degrees."
                },
                "radius_deg": {
                    "type": "number",
                    "description": "Search radius in degrees.",
                    "default": 0.5
                },
                "max_rows": {
                    "type": "integer",
                    "description": "Maximum number of Gaia rows to return.",
                    "default": 50
                },
            },
            "required": ["ra", "dec", "radius_deg"],
        },
    },
]
TOOLS = [{"type": "function", "function": tool_definition} for tool_definition in TOOL_DEFINITIONS]


def _is_api_key_placeholder() -> bool:
    return OPENROUTER_API_KEY == "" or OPENROUTER_API_KEY == PLACEHOLDER_KEY


def _validate_openai_config() -> None:
    if _is_api_key_placeholder():
        raise ValueError(
            "Devi inserire la tua chiave API reale nel file .env prima di usare l'assistente IA"
        )
    if not AI_MODEL:
        raise ValueError(
            "Devi impostare la variabile AI_MODEL nel file .env prima di usare l'assistente IA"
        )


def _get_openai_client() -> OpenAI:
    _validate_openai_config()
    return OpenAI(api_key=OPENROUTER_API_KEY, base_url=API_BASE_URL)


def _message_to_dict(message: object) -> dict[str, object]:
    if message is None:
        return {}
    if isinstance(message, dict):
        normalized = dict(message)
        content = normalized.get("content")
        if isinstance(content, list):
            normalized["content"] = "".join(
                item.get("text", item.get("value", ""))
                if isinstance(item, dict)
                else getattr(item, "text", getattr(item, "value", str(item)))
                for item in content
            )
        return normalized
    if hasattr(message, "to_dict"):
        return _message_to_dict(message.to_dict())
    if hasattr(message, "__dict__"):
        normalized = dict(message.__dict__)
        content = normalized.get("content")
        if isinstance(content, list):
            normalized["content"] = "".join(
                item.get("text", item.get("value", ""))
                if isinstance(item, dict)
                else getattr(item, "text", getattr(item, "value", str(item)))
                for item in content
            )
        return normalized
    return {"content": str(message)}


def _dump_raw_response(response: object) -> str:
    """Restituisce una rappresentazione testuale della risposta grezza dell'API.

    Utile per diagnosticare rapidamente differenze di formato tra provider/modelli
    diversi su OpenRouter, dove alcuni modelli gratuiti restituiscono strutture
    leggermente diverse (es. `delta` al posto di `message`, o `choices` vuota).
    """
    for attr in ("model_dump", "to_dict", "dict"):
        method = getattr(response, attr, None)
        if callable(method):
            try:
                return json.dumps(method(), indent=2, ensure_ascii=False, default=str)
            except Exception:  # pragma: no cover - solo diagnostica
                pass
    try:
        return json.dumps(response, indent=2, ensure_ascii=False, default=str)
    except Exception:  # pragma: no cover - solo diagnostica
        return repr(response)


def _extract_response_message(response: object) -> dict[str, object]:
    choices = None
    if isinstance(response, dict):
        choices = response.get("choices")
    else:
        choices = getattr(response, "choices", None)

    if not choices:
        raw = _dump_raw_response(response)
        print(
            "Risposta grezza dell'API IA (nessuna scelta valida trovata):\n" + raw
        )
        raise ResponseFormatError("Il provider IA non ha restituito scelte valide.")

    choice = choices[0]

    # Alcuni modelli/provider restituiscono `delta` (formato streaming parziale)
    # invece di `message`. Trattiamo `delta` come fallback di `message`.
    if isinstance(choice, dict):
        message = choice.get("message")
        if message is None:
            message = choice.get("delta")
    else:
        message = getattr(choice, "message", None)
        if message is None:
            message = getattr(choice, "delta", None)

    if message is None:
        raw = _dump_raw_response(response)
        print(
            "Risposta grezza dell'API IA (scelta senza 'message' né 'delta'):\n" + raw
        )
        raise ResponseFormatError(
            "Il provider IA ha restituito una scelta priva di 'message' o 'delta'."
        )

    message_dict = _message_to_dict(message)
    tool_calls = message_dict.get("tool_calls")
    if isinstance(tool_calls, list):
        normalized_tool_calls = []
        for tool_call in tool_calls:
            if isinstance(tool_call, dict):
                normalized_tool_calls.append(tool_call)
                continue
            function = getattr(tool_call, "function", None)
            normalized_tool_calls.append(
                {
                    "id": getattr(tool_call, "id", None),
                    "type": getattr(tool_call, "type", "function"),
                    "function": {
                        "name": getattr(function, "name", None),
                        "arguments": getattr(function, "arguments", None),
                    },
                }
            )
        # Scarta eventuali liste tool_calls vuote per non entrare nel loop dei tool
        # senza motivo: alcuni modelli restituiscono "tool_calls": [] o [None].
        normalized_tool_calls = [tc for tc in normalized_tool_calls if tc]
        if normalized_tool_calls:
            message_dict["tool_calls"] = normalized_tool_calls
        else:
            message_dict.pop("tool_calls", None)

    # Normalizza il contenuto: garantisce sempre una chiave 'content' testuale.
    # Casi limite gestiti in modo tollerante:
    #  - contenuto vuoto ma tool_calls presenti -> normale, il loop eseguirà i tool
    #  - tool_calls assenti e contenuto vuoto -> risposta finale vuota, non un errore
    content = message_dict.get("content")
    if content is None:
        message_dict["content"] = ""

    has_content = bool(str(message_dict.get("content", "")).strip())
    has_tool_calls = bool(message_dict.get("tool_calls")) or bool(
        message_dict.get("function_call")
    )
    if not has_content and not has_tool_calls:
        # Né testo né richieste di tool: struttura inutilizzabile. Logga il grezzo
        # e segnala un errore di formato così da poter attivare il fallback.
        raw = _dump_raw_response(response)
        print(
            "Risposta grezza dell'API IA (messaggio senza contenuto né tool_calls):\n"
            + raw
        )
        raise ResponseFormatError(
            "Il provider IA ha restituito un messaggio vuoto (né testo né tool_calls)."
        )

    return message_dict


def _call_openai_with_tools(
    messages: list[dict[str, object]], model: str | None = None
) -> dict[str, object]:
    client = _get_openai_client()
    model_to_use = model or AI_MODEL
    try:
        response = client.chat.completions.create(
            model=model_to_use,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            timeout=180,
        )
    except AuthenticationError:
        traceback.print_exc()
        raise
    except RateLimitError:
        traceback.print_exc()
        raise
    except APITimeoutError:
        traceback.print_exc()
        raise
    except APIConnectionError:
        traceback.print_exc()
        raise
    except APIError:
        traceback.print_exc()
        raise

    return _extract_response_message(response)


def _find_extreme_value(df: pd.DataFrame, question: str) -> tuple[str, str] | None:
    """Recognize common extreme-value questions and return a ready-to-use answer."""
    if df is None or df.empty:
        return None

    question_l = question.lower()
    df_prepared = _prepare_dataframe_context(df)

    if any(pattern in question_l for pattern in ["stella più vicina", "distanza minore", "più vicina"]):
        if "distance_pc" in df_prepared.columns:
            idx = df_prepared["distance_pc"].idxmin()
            row = df_prepared.loc[idx]
            return (
                "distance_pc",
                f"La stella più vicina è {row.get('source_id', idx)} con distanza {row['distance_pc']:.3f} pc.",
            )

    if any(pattern in question_l for pattern in ["stella più lontana", "distanza maggiore", "più lontana"]):
        if "distance_pc" in df_prepared.columns:
            idx = df_prepared["distance_pc"].idxmax()
            row = df_prepared.loc[idx]
            return (
                "distance_pc",
                f"La stella più lontana è {row.get('source_id', idx)} con distanza {row['distance_pc']:.3f} pc.",
            )

    if any(pattern in question_l for pattern in ["stella più luminosa", "più luminosa", "luminosa"]):
        if "phot_g_mean_mag" in df_prepared.columns:
            idx = df_prepared["phot_g_mean_mag"].idxmin()
            row = df_prepared.loc[idx]
            return (
                "phot_g_mean_mag",
                f"La stella più luminosa è {row.get('source_id', idx)} con magnitudine apparente {row['phot_g_mean_mag']:.3f}.",
            )

    if any(pattern in question_l for pattern in ["moto proprio più alto", "si muove più veloce", "moto proprio maggiore"]):
        if "proper_motion_total" in df_prepared.columns:
            idx = df_prepared["proper_motion_total"].idxmax()
            row = df_prepared.loc[idx]
            return (
                "proper_motion_total",
                f"La stella con moto proprio più alto è {row.get('source_id', idx)} con moto proprio totale {row['proper_motion_total']:.3f} mas/yr.",
            )

    if any(pattern in question_l for pattern in ["velocità tangenziale più alta", "tangenziale più alta"]):
        if "tangential_velocity_kms" in df_prepared.columns:
            idx = df_prepared["tangential_velocity_kms"].idxmax()
            row = df_prepared.loc[idx]
            return (
                "tangential_velocity_kms",
                f"La stella con velocità tangenziale più alta è {row.get('source_id', idx)} con {row['tangential_velocity_kms']:.3f} km/s.",
            )

    return None


def _prepare_dataframe_context(df: pd.DataFrame | None, max_rows: int = 8) -> pd.DataFrame:
    """Prepare a DataFrame for the assistant by computing derived columns row by row."""
    if df is None or not isinstance(df, pd.DataFrame):
        return pd.DataFrame()

    df_context = df.copy()
    if "parallax" in df_context.columns:
        df_context["parallax"] = pd.to_numeric(df_context["parallax"], errors="coerce")
        valid_parallax = df_context["parallax"] > 0
        if valid_parallax.any():
            df_context = df_context.loc[valid_parallax].copy()
            df_context["distance_pc"] = pd.Series([float("nan")] * len(df_context), index=df_context.index)

            for idx, row in df_context.iterrows():
                distance_pc = parallax_to_distance_pc(float(row["parallax"]))
                df_context.at[idx, "distance_pc"] = distance_pc

                if "phot_g_mean_mag" in df_context.columns:
                    df_context.at[idx, "absolute_mag"] = absolute_magnitude(
                        float(row["phot_g_mean_mag"]), distance_pc
                    )

                if "pmra" in df_context.columns and "pmdec" in df_context.columns:
                    df_context.at[idx, "proper_motion_total"] = total_proper_motion(
                        float(row["pmra"]), float(row["pmdec"])
                    )
                    df_context.at[idx, "tangential_velocity_kms"] = tangential_velocity(
                        float(row["pmra"]), float(row["pmdec"]), distance_pc
                    )

                if "absolute_mag" in df_context.columns:
                    df_context.at[idx, "luminosity_ratio"] = luminosity_ratio(
                        float(df_context.at[idx, "absolute_mag"])
                    )

    return df_context


def _format_dataframe_context(df: pd.DataFrame | None, max_rows: int = 8) -> str:
    """Convert a DataFrame to a compact textual context suitable for the model."""
    if df is None:
        return ""
    if not isinstance(df, pd.DataFrame):
        return str(df)

    df_context = _prepare_dataframe_context(df)

    columns_to_keep = [
        col for col in [
            "source_id",
            "ra",
            "dec",
            "parallax",
            "phot_g_mean_mag",
            "bp_rp",
            "pmra",
            "pmdec",
            "distance_pc",
            "absolute_mag",
            "proper_motion_total",
            "tangential_velocity_kms",
            "luminosity_ratio",
        ]
        if col in df_context.columns
    ]

    if not columns_to_keep:
        return df_context.head(max_rows).to_string(index=False)

    return df_context[columns_to_keep].head(max_rows).to_string(index=False)

def _resolve_tool_name(function):
    """Estrae il nome del tool dal dizionario 'function' passato dal modello."""
    if isinstance(function, dict):
        return function.get("name")
    return getattr(function, "name", None)

def _format_tool_response(df):
    """Converte il DataFrame risultato di una query Gaia in testo leggibile per il modello IA."""
    if df is None or df.empty:
        return "Nessun dato trovato per questa ricerca."
    
    # Limita a un numero ragionevole di righe per non sovraccaricare il contesto
    preview = df.head(20)
    return preview.to_string(index=False)



def _execute_tool_call(tool_call: dict[str, object]) -> tuple[str, str]:
    """Execute a tool call and return a tuple of (tool_name, tool_output)."""
    function = tool_call.get("function", {})
    tool_name = _resolve_tool_name(function)
    arguments = function.get("arguments") or {}
    if tool_name == "query_by_name":
        star_name = arguments.get("star_name") or arguments.get("name")
        if not star_name:
            return tool_name, "Errore: manca il parametro star_name."
        try:
            df = query_by_name(
                star_name,
                radius_deg=float(arguments.get("radius_deg", 0.1)),
                max_rows=int(arguments.get("max_rows", 50)),
            )
        except Exception as exc:
            return tool_name, f"Errore durante query_by_name: {type(exc).__name__}: {exc}"
        if df is None or df.empty:
            return tool_name, f"Nessun dato Gaia trovato per '{star_name}'."
        return tool_name, _format_tool_response(df)

    if tool_name == "query_region":
        try:
            ra = float(arguments.get("ra"))
            dec = float(arguments.get("dec"))
            radius_deg = float(arguments.get("radius_deg", 0.5))
            max_rows = int(arguments.get("max_rows", 50))
        except (TypeError, ValueError):
            return tool_name, "Errore: parametri ra, dec e radius_deg devono essere numerici."
        try:
            df = query_region(ra=ra, dec=dec, radius_deg=radius_deg, max_rows=max_rows)
        except Exception as exc:
            return tool_name, f"Errore durante query_region: {type(exc).__name__}: {exc}"
        if df is None or df.empty:
            return tool_name, f"Nessun dato Gaia trovato nella regione RA={ra}, Dec={dec}, raggio={radius_deg}°."
        return tool_name, _format_tool_response(df)

    return tool_name, f"Errore: tool sconosciuto '{tool_name}'."


def is_config_valid() -> bool:
    """Restituisce True se la configurazione API IA è utilizzabile.

    Effettua la stessa verifica di ``_validate_openai_config`` (chiave reale
    presente e ``AI_MODEL`` impostato) ma senza sollevare eccezioni, così la
    GUI può decidere se abilitare l'invio dei messaggi.
    """
    try:
        _validate_openai_config()
        return True
    except ValueError:
        return False


def get_assistant_status() -> str:
    """Check whether the assistant can run with the current configuration."""
    if _is_api_key_placeholder():
        return "Assistente IA: Devi inserire la tua chiave API reale nel file .env prima di usare l'assistente IA."
    if not AI_MODEL:
        return "Assistente IA: Devi impostare AI_MODEL nel file .env prima di usare l'assistente IA."
    return "Assistente IA: configurazione API valida."


def _api_error_to_user_message(exc: Exception) -> str:
    """Traduce un'eccezione API in un messaggio chiaro per l'utente.

    Stampa sempre il traceback completo (regola di progetto: mai nascondere
    l'errore reale durante lo sviluppo) e ritorna un testo comprensibile.
    """
    traceback.print_exc()
    if isinstance(exc, AuthenticationError):
        return "Chiave API non valida o mancante. Controlla OPENROUTER_API_KEY nel file .env."
    if isinstance(exc, RateLimitError):
        return "Hai superato il limite di richieste dell'API. Riprova più tardi."
    if isinstance(exc, APITimeoutError):
        return "Timeout di rete durante la richiesta all'API IA. Riprova più tardi."
    if isinstance(exc, APIConnectionError):
        return "Errore di connessione alla API IA. Controlla la rete e l'URL di API_BASE_URL."
    if isinstance(exc, NotFoundError):
        return "Modello IA non trovato o non disponibile. Controlla AI_MODEL e il provider API."
    if isinstance(exc, BadRequestError):
        return (
            "Il modello IA non è valido o non supporta il tool calling. "
            f"Controlla AI_MODEL (e AI_MODEL_FALLBACK) sul provider. Dettaglio: {exc}"
        )
    if isinstance(exc, ResponseFormatError):
        return f"Il provider IA ha restituito una risposta in un formato inatteso: {exc}"
    if isinstance(exc, APIError):
        return f"Errore API IA: {exc}"
    return f"Errore inatteso: {exc}"


def _run_conversation(model: str, base_messages: list[dict[str, object]]) -> str:
    """Esegue una conversazione completa (con eventuali tool call) usando `model`.

    Riceve i messaggi iniziali e ne lavora su una copia, così che un eventuale
    retry con un modello di riserva riparta sempre da uno stato pulito. Le
    eccezioni (di rete, autenticazione, formato risposta) vengono propagate al
    chiamante, che decide se attivare il fallback o mostrare un errore.
    """
    messages = [dict(message) for message in base_messages]

    response_message = _call_openai_with_tools(messages, model=model)

    while response_message.get("tool_calls") or response_message.get("function_call"):
        tool_calls = response_message.get("tool_calls") or []
        if not tool_calls:
            tool_call = response_message.get("function_call") or {}
            tool_calls = [
                {
                    "id": "call_legacy",
                    "type": "function",
                    "function": {
                        "name": tool_call.get("name", ""),
                        "arguments": tool_call.get("arguments") or {},
                    },
                }
            ]

        assistant_message = {"role": "assistant", "content": response_message.get("content", "")}
        if tool_calls:
            assistant_message["tool_calls"] = tool_calls
        messages.append(assistant_message)

        for tool_call in tool_calls:
            function = tool_call.get("function", {}) if isinstance(tool_call, dict) else getattr(tool_call, "function", {})
            tool_name = function.get("name", "") if isinstance(function, dict) else getattr(function, "name", "")
            raw_arguments = function.get("arguments") or {} if isinstance(function, dict) else getattr(function, "arguments", None)
            if isinstance(raw_arguments, str):
                try:
                    arguments = json.loads(raw_arguments)
                except json.JSONDecodeError:
                    arguments = {}
            else:
                arguments = raw_arguments

            tool_name, tool_output = _execute_tool_call({"function": {"name": tool_name, "arguments": arguments}})
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.get("id") if isinstance(tool_call, dict) else getattr(tool_call, "id", None),
                    "content": tool_output,
                }
            )

        response_message = _call_openai_with_tools(messages, model=model)

    return response_message.get("content", "") or ""


def ask_astro_assistant(user_question: str, data_context: object | None = None) -> str:
    """Ask the local OpenAI-compatible assistant an astrophysics question."""
    if _is_api_key_placeholder():
        return "Devi inserire la tua chiave API reale nel file .env prima di usare l'assistente IA"
    if not AI_MODEL:
        return "Devi impostare AI_MODEL nel file .env prima di usare l'assistente IA"

    system_prompt = (
        "Sei un assistente conversazionale specializzato in astrofisica. "
        "Rispondi in modo naturale, cortese e di supporto a saluti, ringraziamenti e richieste generiche "
        "come 'ciao', 'come stai', 'cosa puoi fare' o 'grazie'. In questi casi non è necessario usare "
        "i dati del dataset, quindi non includere numeri o colonne se la domanda non chiede informazioni "
        "scientifiche specifiche.\n\n"
        "Quando la domanda richiede dati astronomici specifici dal dataset caricato (ad es. distanze, "
        "magnitudini, moto proprio, confronti tra stelle, o quante stelle sono caricate), usa SOLO i dati "
        "presenti in `data_context` e rispondi basandoti su di essi. Se l'informazione richiesta non è presente "
        "nel dataset, rispondi esplicitamente che non hai abbastanza dati per rispondere, invece di inventare.\n\n"
        "Se il dataset caricato non contiene già le informazioni richieste, chiama gli strumenti "
        "disponibili per interrogare direttamente Gaia DR3. Non rispondere con informazioni generiche se "
        "l'utente chiede dati specifici su una stella o una regione. Usa gli strumenti con le seguenti regole: "
        "1) Se la richiesta riguarda una stella identificabile per nome, chiama `query_by_name`. "
        "2) Se la richiesta riguarda coordinate celesti specifiche, chiama `query_region`. "
        "3) Restituisci sempre la risposta finale in linguaggio naturale, basata sui dati reali ottenuti.\n\n"
        "Non inventare nomi di algoritmi, teorie o metodi scientifici. Se non sei sicuro di un'informazione, "
        "ammettilo chiaramente invece di rispondere con sicurezza. Quando riporti valori numerici, indica "
        "sempre la colonna di origine e l'unità di misura. Usa Python/astropy/pandas per i calcoli se necessario "
        "e evita qualsiasi congettura."
    )

    messages: list[dict[str, object]] = [{"role": "system", "content": system_prompt}]

    if data_context is not None and isinstance(data_context, pd.DataFrame):
        extreme_match = _find_extreme_value(data_context, user_question)
        if extreme_match is not None:
            _, computed_answer = extreme_match
            messages.append({"role": "user", "content": f"Dati contestuali calcolati in Python:\n{computed_answer}"})
            messages.append({"role": "user", "content": "Rispondi in linguaggio naturale usando solo questo dato specifico e non altre colonne."})
        else:
            context_text = _format_dataframe_context(data_context)
            if context_text:
                messages.append({"role": "user", "content": f"Dati contestuali:\n{context_text}"})

    messages.append({"role": "user", "content": user_question})

    # Errori che indicano un problema di formato della risposta o di modello non
    # disponibile/incompatibile: in questi casi ha senso ritentare con un modello
    # di riserva, perché i modelli gratuiti su OpenRouter differiscono nel
    # supporto ai tool e nel formato restituito. NotFoundError (404) e
    # BadRequestError (400) coprono i casi tipici di OpenRouter, che segnala sia
    # "is not a valid model ID" sia "no endpoints support tool use" con un 400.
    # Errori di rete/autenticazione/rate limit NON attivano il fallback (riprovare
    # con un altro modello non li risolverebbe). Se anche il modello di riserva
    # fallisce, l'errore reale viene comunque mostrato all'utente.
    fallback_triggers = (ResponseFormatError, NotFoundError, BadRequestError)

    try:
        return _run_conversation(AI_MODEL, messages)
    except ValueError as exc:
        return str(exc)
    except fallback_triggers as exc:
        fallback_model = (AI_MODEL_FALLBACK or DEFAULT_AI_MODEL_FALLBACK).strip()
        if not fallback_model or fallback_model == AI_MODEL:
            # Nessun modello di riserva utile disponibile: mostra l'errore.
            return _api_error_to_user_message(exc)

        traceback.print_exc()
        print(
            "Il modello configurato non ha risposto correttamente, "
            f"sto riprovando con un modello di riserva ({fallback_model})."
        )
        try:
            return _run_conversation(fallback_model, messages)
        except Exception as fallback_exc:
            return _api_error_to_user_message(fallback_exc)
    except Exception as exc:
        return _api_error_to_user_message(exc)


def interactive_session(df: pd.DataFrame | None = None) -> None:
    """Run an interactive command-line session with the OpenAI-compatible assistant."""
    print("\nAvvio sessione interattiva con l'assistente IA.")
    print("Digita 'esci', 'exit' o 'quit' per interrompere la sessione.\n")

    if _is_api_key_placeholder():
        print("Devi inserire la tua chiave API reale nel file .env prima di usare l'assistente IA")
        return
    if not AI_MODEL:
        print("Devi impostare AI_MODEL nel file .env prima di usare l'assistente IA")
        return

    if df is not None and isinstance(df, pd.DataFrame) and not df.empty:
        print(f"Sessione IA avviata con {len(df)} oggetti già caricati.")
    else:
        print("Sessione IA avviata senza dati caricati. L'assistente può interrogare Gaia automaticamente se necessario.")

    try:
        while True:
            try:
                user_question = input(">>> ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nSessione interrotta, torno al menu principale")
                return

            if user_question.lower() in {"esci", "exit", "quit"}:
                print("Chiusura sessione assistente IA.")
                break

            answer = ask_astro_assistant(user_question, data_context=df)
            print(f"\nRisposta:\n{answer}\n")
    except (KeyboardInterrupt, EOFError):
        print("\nSessione interrotta, torno al menu principale")
        return


if __name__ == "__main__":
    print(get_assistant_status())
    try:
        from astronew.data.gaia_client import query_region

        example_df = query_region(ra=101.28, dec=-16.72, radius_deg=0.5, max_rows=8)
    except Exception as exc:  # pragma: no cover - network-dependent fallback
        example_df = None
        print(f"Impossibile recuperare dati Gaia di esempio: {exc}")

    interactive_session(df=example_df)
