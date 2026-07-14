"""AstroNew command-line interface.

Menu:
1. Cerca stella/regione
2. Visualizza grafici
3. Assistente IA
4. Esci

The session holds a `current_df` DataFrame loaded by option 1 and reused by
options 2 and 3.
"""

from __future__ import annotations

from typing import Optional
import pandas as pd

from astronew.data.gaia_client import query_region, query_by_name
from astronew.viz.plots import (
    plot_hr_diagram,
    plot_sky_map,
    plot_distance_histogram,
    plot_proper_motion_vectors,
)
from astronew.ai.assistant import interactive_session, get_assistant_status
from astronew.setup import (
    run_first_time_setup,
    configure_ai_provider,
    remove_all_api_keys,
)


def _search_region_session() -> Optional[pd.DataFrame]:
    """Prompt user to search Gaia and return the resulting DataFrame.

    Offers search by star name or by coordinates.
    """
    print("\n[Cerca stella/regione]")
    print("1) Cerca per nome (es. Sirius)")
    print("2) Cerca per coordinate (RA, Dec, raggio in gradi)")
    choice = input("Metodo (1/2): ").strip()
    if choice == "1":
        name = input("Nome della stella: ").strip()
        if not name:
            print("Nome non valido.")
            return None
        try:
            df = query_by_name(name, radius_deg=0.1, max_rows=200)
            print(f"Trovati {len(df)} oggetti intorno a {name}.")
            return df
        except Exception as e:
            print(f"Errore durante la ricerca per nome: {e}")
            return None
    elif choice == "2":
        try:
            ra = float(input("RA (gradi): ").strip())
            dec = float(input("Dec (gradi): ").strip())
            radius = float(input("Raggio (gradi): ").strip())
            max_rows_in = input("Max righe (predefinito 100): ").strip()
            max_rows = int(max_rows_in) if max_rows_in else 100
        except ValueError:
            print("Input numerico non valido.")
            return None
        try:
            df = query_region(ra=ra, dec=dec, radius_deg=radius, max_rows=max_rows)
            print(f"Trovati {len(df)} oggetti nella regione.")
            return df
        except Exception as e:
            print(f"Errore durante la query: {e}")
            return None
    else:
        print("Metodo non valido.")
        return None


def _plots_menu(session_df: pd.DataFrame) -> None:
    """Submenu to choose which plot to generate for the loaded DataFrame."""
    while True:
        print("\n[Visualizza grafici]")
        print("1) Diagramma H-R")
        print("2) Mappa celeste (RA/Dec)")
        print("3) Istogramma distanze")
        print("4) Vettori di moto proprio")
        print("5) Torna al menu principale")
        choice = input("Scegli un'opzione: ").strip()
        if choice == "1":
            plot_hr_diagram(session_df, save_path="hr_diagram.png")
        elif choice == "2":
            plot_sky_map(session_df, save_path="sky_map.png")
        elif choice == "3":
            plot_distance_histogram(session_df, save_path="distance_histogram.png")
        elif choice == "4":
            plot_proper_motion_vectors(session_df, save_path="proper_motion_vectors.png")
        elif choice == "5":
            return
        else:
            print("Scelta non valida. Inserisci 1-5.")


def main() -> None:
    """Main menu loop for AstroNew."""
    current_df: Optional[pd.DataFrame] = None

    print("\n=== AstroNew ===")
    print("Piccola app di esplorazione astronomica con dati Gaia DR3.")

    # Configurazione guidata al primo avvio: parte solo se .env manca o la
    # chiave API è ancora il placeholder. Con una chiave valida non fa nulla.
    run_first_time_setup()

    while True:
        try:
            print("\nMenu principale:")
            print("1) Cerca stella/regione")
            print("2) Visualizza grafici")
            print("3) Assistente IA")
            print("4) Esci")
            print("5) Configura provider IA (chiave API e modello)")
            print("6) Togli tutte le chiavi API dal progetto")
            choice = input("Seleziona un'opzione: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nSessione interrotta, torno al menu principale")
            continue

        if choice == "1":
            df = _search_region_session()
            if df is not None and isinstance(df, pd.DataFrame) and not df.empty:
                current_df = df
        elif choice == "2":
            if current_df is None:
                print("Devi prima cercare una stella o regione (opzione 1).")
            else:
                _plots_menu(current_df)
        elif choice == "3":
            status = get_assistant_status()
            print(status)
            # `get_assistant_status()` returns a clear Italian message such as
            # "Assistente IA: configurazione API valida." when the API is usable.
            # Only launch the interactive session when the configuration is valid.
            if "configurazione api valida" in status.lower():
                interactive_session(df=current_df)
        elif choice == "4":
            print("Uscita da AstroNew. Arrivederci!")
            break
        elif choice == "5":
            configure_ai_provider()
        elif choice == "6":
            remove_all_api_keys()
        else:
            print("Opzione non valida. Inserisci 1, 2, 3, 4, 5 o 6.")


if __name__ == "__main__":
    main()
