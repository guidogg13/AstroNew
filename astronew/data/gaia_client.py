"""Client for querying the ESA Gaia DR3 archive through the official TAP/ADQL service.

The Gaia data are retrieved from the official ESA Gaia Archive:
https://gea.esac.esa.int

This client uses astroquery.gaia and anonymous TAP/ADQL queries. No unauthorized
scraping is performed, and no authentication is required for anonymous queries to
the public Gaia DR3 catalogue.
"""

from __future__ import annotations

import pandas as pd
from astropy.coordinates import SkyCoord
from astropy import units as u
from astroquery.gaia import Gaia
from astroquery.exceptions import TimeoutError
from requests.exceptions import ConnectionError


def _adql_cone_query(ra: float, dec: float, radius_deg: float, max_rows: int) -> str:
    return (
        f"SELECT TOP {max_rows} source_id, ra, dec, parallax, parallax_error, "
        "phot_g_mean_mag, bp_rp, pmra, pmdec "
        "FROM gaiadr3.gaia_source "
        "WHERE 1=CONTAINS(POINT('ICRS', ra, dec), "
        f"CIRCLE('ICRS', {ra}, {dec}, {radius_deg})) "
        "ORDER BY phot_g_mean_mag"
    )


def _to_dataframe(table) -> pd.DataFrame:
    if table is None:
        return pd.DataFrame(
            columns=[
                "source_id",
                "ra",
                "dec",
                "parallax",
                "parallax_error",
                "phot_g_mean_mag",
                "bp_rp",
                "pmra",
                "pmdec",
            ]
        )
    return table.to_pandas()


def query_region(
    ra: float,
    dec: float,
    radius_deg: float,
    max_rows: int = 100,
) -> pd.DataFrame:
    """Query Gaia DR3 for objects in a sky region around a given coordinate.

    Parameters
    ----------
    ra : float
        Right ascension in degrees.
    dec : float
        Declination in degrees.
    radius_deg : float
        Search radius in degrees.
    max_rows : int
        Maximum number of rows to retrieve.

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing Gaia source measurements.
    """
    if radius_deg <= 0:
        raise ValueError("Il raggio di ricerca deve essere positivo.")
    if max_rows <= 0:
        raise ValueError("max_rows deve essere un intero positivo.")

    row_limit = getattr(Gaia, "ROW_LIMIT", None)
    if row_limit is not None and max_rows > row_limit:
        print(
            f"Attenzione: Gaia.ROW_LIMIT limitato a {row_limit}. "
            f"Usando max_rows={row_limit}."
        )
        max_rows = row_limit

    query = _adql_cone_query(ra=ra, dec=dec, radius_deg=radius_deg, max_rows=max_rows)
    try:
        job = Gaia.launch_job(query)
        result = job.get_results()
        return _to_dataframe(result)
    except ConnectionError:
        raise ConnectionError(
            "Connessione a Gaia fallita. Controlla la rete e riprova."
        )
    except TimeoutError:
        raise TimeoutError(
            "La query Gaia ha superato il tempo limite. "
            "Prova a ridurre il raggio o il numero di righe.")
    except Exception as exc:
        raise RuntimeError(
            f"Errore durante la query Gaia: {exc}"
        ) from exc


def query_by_name(star_name: str, radius_deg: float = 0.1, max_rows: int = 100) -> pd.DataFrame:
    """Resolve a star name to coordinates and query Gaia DR3 around that position."""
    if not star_name:
        raise ValueError("Il nome della stella non può essere vuoto.")

    try:
        coord = SkyCoord.from_name(star_name)
    except Exception as exc:
        raise RuntimeError(
            f"Impossibile risolvere il nome della stella '{star_name}': {exc}"
        ) from exc

    return query_region(
        ra=coord.ra.degree,
        dec=coord.dec.degree,
        radius_deg=radius_deg,
        max_rows=max_rows,
    )


if __name__ == "__main__":
    print("Esempio di query Gaia DR3 del catalogo ufficiale ESA.")
    try:
        df = query_by_name("Sirius", radius_deg=0.05, max_rows=10)
        print(df.head())
    except Exception as exc:
        print(f"Errore di test: {exc}")
