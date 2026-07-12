"""Scientific plotting helpers for the AstroNew application.

The plotting functions create scientific visualizations of Gaia DR3 data using
astrofisical calculations from the analysis module.
"""

from __future__ import annotations

import warnings

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ..analysis.calculations import (
    parallax_to_distance_pc,
    absolute_magnitude,
    luminosity_ratio,
)

matplotlib.use("Agg")


def _filter_valid_parallax(df: pd.DataFrame) -> pd.DataFrame:
    """Filter out rows with invalid parallax values and return a cleaned DataFrame."""
    if df.empty:
        return df
    
    initial_count = len(df)
    df_clean = df[(df["parallax"] > 0) & (df["parallax"].notna())].copy()
    removed = initial_count - len(df_clean)
    
    if removed > 0:
        warnings.warn(
            f"Rimosse {removed} righe con parallasse non valida (<=0 o NaN). "
            f"Rimangono {len(df_clean)} righe per l'analisi.",
            UserWarning,
        )
    
    return df_clean


def plot_hr_diagram(df: pd.DataFrame, save_path: str | None = None) -> None:
    """Create a Hertzsprung-Russell diagram from Gaia data.
    
    Plots BP-RP color (x-axis) vs absolute magnitude (y-axis, inverted).
    Points are colored by apparent magnitude for context.
    
    Parameters
    ----------
    df : pd.DataFrame
        Gaia DR3 data with parallax, phot_g_mean_mag, bp_rp columns.
    save_path : str, optional
        Path to save the figure as PNG. If None, displays with plt.show().
    """
    df_clean = _filter_valid_parallax(df)
    if df_clean.empty:
        print("Nessun dato valido per il diagramma H-R.")
        return
    
    df_clean["distance_pc"] = df_clean["parallax"].apply(parallax_to_distance_pc)
    df_clean["abs_mag"] = df_clean.apply(
        lambda row: absolute_magnitude(row["phot_g_mean_mag"], row["distance_pc"]),
        axis=1,
    )
    
    fig, ax = plt.subplots(figsize=(8, 6))
    scatter = ax.scatter(
        df_clean["bp_rp"],
        df_clean["abs_mag"],
        c=df_clean["phot_g_mean_mag"],
        cmap="viridis",
        alpha=0.6,
        s=50,
    )
    ax.set_xlabel("BP - RP (mag)", fontsize=12)
    ax.set_ylabel("Magnitudine assoluta (mag)", fontsize=12)
    ax.set_title("Diagramma Hertzsprung-Russell (Gaia DR3)", fontsize=14)
    ax.invert_yaxis()
    ax.grid(True, alpha=0.3)
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label("Magnitudine apparente (G)", fontsize=10)
    fig.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=150)
        print(f"Diagramma H-R salvato: {save_path}")
    else:
        plt.show()
    plt.close(fig)


def plot_sky_map(df: pd.DataFrame, save_path: str | None = None) -> None:
    """Create a celestial map from Gaia data.
    
    Plots RA vs Dec with point size proportional to luminosity.
    
    Parameters
    ----------
    df : pd.DataFrame
        Gaia DR3 data with ra, dec, parallax, phot_g_mean_mag columns.
    save_path : str, optional
        Path to save the figure as PNG.
    """
    df_clean = _filter_valid_parallax(df)
    if df_clean.empty:
        print("Nessun dato valido per la mappa celeste.")
        return
    
    df_clean["distance_pc"] = df_clean["parallax"].apply(parallax_to_distance_pc)
    df_clean["abs_mag"] = df_clean.apply(
        lambda row: absolute_magnitude(row["phot_g_mean_mag"], row["distance_pc"]),
        axis=1,
    )
    df_clean["luminosity"] = df_clean["abs_mag"].apply(luminosity_ratio)
    
    fig, ax = plt.subplots(figsize=(10, 8))
    sizes = 20 * np.sqrt(np.maximum(df_clean["luminosity"], 0.1))
    scatter = ax.scatter(
        df_clean["ra"],
        df_clean["dec"],
        s=sizes,
        c=df_clean["phot_g_mean_mag"],
        cmap="cool",
        alpha=0.6,
        edgecolors="k",
        linewidth=0.5,
    )
    ax.set_xlabel("Ascensione retta (°)", fontsize=12)
    ax.set_ylabel("Declinazione (°)", fontsize=12)
    ax.set_title("Mappa celeste (Gaia DR3)", fontsize=14)
    ax.grid(True, alpha=0.3)
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label("Magnitudine apparente (G)", fontsize=10)
    fig.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=150)
        print(f"Mappa celeste salvata: {save_path}")
    else:
        plt.show()
    plt.close(fig)


def plot_distance_histogram(df: pd.DataFrame, save_path: str | None = None) -> None:
    """Create a distance distribution histogram from Gaia data.
    
    Parameters
    ----------
    df : pd.DataFrame
        Gaia DR3 data with parallax column.
    save_path : str, optional
        Path to save the figure as PNG.
    """
    df_clean = _filter_valid_parallax(df)
    if df_clean.empty:
        print("Nessun dato valido per l'istogramma delle distanze.")
        return
    
    distances = df_clean["parallax"].apply(parallax_to_distance_pc)
    
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.hist(distances, bins=20, color="steelblue", edgecolor="black", alpha=0.7)
    ax.set_xlabel("Distanza (pc)", fontsize=12)
    ax.set_ylabel("Numero di oggetti", fontsize=12)
    ax.set_title("Distribuzione delle distanze (Gaia DR3)", fontsize=14)
    ax.grid(True, alpha=0.3, axis="y")
    
    mean_dist = distances.mean()
    median_dist = distances.median()
    ax.axvline(mean_dist, color="red", linestyle="--", linewidth=2, label=f"Media: {mean_dist:.1f} pc")
    ax.axvline(median_dist, color="orange", linestyle="--", linewidth=2, label=f"Mediana: {median_dist:.1f} pc")
    ax.legend()
    fig.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=150)
        print(f"Istogramma distanze salvato: {save_path}")
    else:
        plt.show()
    plt.close(fig)


def plot_proper_motion_vectors(df: pd.DataFrame, save_path: str | None = None) -> None:
    """Create a celestial map with proper motion vectors.
    
    Plots RA vs Dec with arrows representing proper motion direction and magnitude.
    
    Parameters
    ----------
    df : pd.DataFrame
        Gaia DR3 data with ra, dec, pmra, pmdec columns.
    save_path : str, optional
        Path to save the figure as PNG.
    """
    if df.empty:
        print("Nessun dato per i vettori di moto proprio.")
        return
    
    df_plot = df[(df["pmra"].notna()) & (df["pmdec"].notna())].copy()
    if df_plot.empty:
        print("Nessun dato valido per i vettori di moto proprio.")
        return
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Scala i vettori per la visualizzazione
    scale_factor = 0.02
    
    ax.scatter(df_plot["ra"], df_plot["dec"], c="lightgray", s=30, alpha=0.5, label="Stelle")
    ax.quiver(
        df_plot["ra"],
        df_plot["dec"],
        df_plot["pmra"],
        df_plot["pmdec"],
        scale=1.0 / scale_factor,
        scale_units="xy",
        angles="xy",
        color="red",
        alpha=0.7,
        width=0.003,
        label="Moto proprio",
    )
    
    ax.set_xlabel("Ascensione retta (°)", fontsize=12)
    ax.set_ylabel("Declinazione (°)", fontsize=12)
    ax.set_title("Vettori di moto proprio (Gaia DR3)", fontsize=14)
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=150)
        print(f"Vettori di moto proprio salvati: {save_path}")
    else:
        plt.show()
    plt.close(fig)


if __name__ == "__main__":
    print("Test plotting con dati intorno a Sirio...")
    try:
        from ..data.gaia_client import query_by_name
        
        df = query_by_name("Sirius", radius_deg=0.5, max_rows=200)
        print(f"Query completata: {len(df)} oggetti recuperati.\n")
        
        print("Generazione diagramma H-R...")
        plot_hr_diagram(df, save_path="hr_diagram.png")
        
        print("Generazione mappa celeste...")
        plot_sky_map(df, save_path="sky_map.png")
        
        print("Generazione istogramma distanze...")
        plot_distance_histogram(df, save_path="distance_histogram.png")
        
        print("Generazione vettori moto proprio...")
        plot_proper_motion_vectors(df, save_path="proper_motion_vectors.png")
        
        print("\nTutti i grafici sono stati generati con successo!")
    except Exception as exc:
        print(f"Errore durante il test: {exc}")
