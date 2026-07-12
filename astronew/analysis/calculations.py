"""Astrophysical calculations and conversions for the AstroNew application.

The formulas implemented here are standard astrophysical relations such as the
parallax-distance relation and the distance modulus.
"""

from __future__ import annotations

import math


def parallax_to_distance_pc(parallax_mas: float) -> float:
    """Convert a parallax in milliarcseconds to a distance in parsec.

    Formula: d[pc] = 1 / p[arcsec]
    """
    if parallax_mas <= 0:
        raise ValueError("La parallasse deve essere positiva.")
    parallax_arcsec = parallax_mas / 1000.0
    return 1.0 / parallax_arcsec


def absolute_magnitude(apparent_mag: float, distance_pc: float) -> float:
    """Compute the absolute magnitude from the apparent magnitude and distance.

    Formula: M = m - 5 log10(d/10 pc)
    """
    if distance_pc <= 0:
        raise ValueError("La distanza deve essere positiva.")
    return apparent_mag - 5 * math.log10(distance_pc / 10.0)


def proper_motion_total(mua_mas_yr: float, mud_mas_yr: float) -> float:
    """Compute the total proper motion amplitude from the components.

    Formula: mu = sqrt(mu_alpha^2 + mu_delta^2)
    """
    return math.hypot(mua_mas_yr, mud_mas_yr)


def tangential_velocity(pmra_mas_yr: float, pmdec_mas_yr: float, distance_pc: float) -> float:
    """Compute the tangential velocity from proper motion and distance.

    Formula: v_t[km/s] = 4.74 * mu[arcsec/yr] * d[pc]
    When mu is in mas/yr, use: v_t[km/s] = 4.74 * mu[mas/yr] * d[pc] / 1000
    """
    if distance_pc <= 0:
        raise ValueError("La distanza deve essere positiva.")
    
    mu_total = proper_motion_total(pmra_mas_yr, pmdec_mas_yr)
    return 4.74 * mu_total * distance_pc / 1000.0


def luminosity_ratio(abs_mag: float) -> float:
    """Compute the luminosity ratio relative to the Sun using the magnitude scale.

    Formula: L/L_sun = 10^(-(M - M_sun)/2.5)
    where M_sun = 4.83 (absolute visual magnitude of the Sun).
    """
    M_sun = 4.83
    return 10 ** (-(abs_mag - M_sun) / 2.5)


if __name__ == "__main__":
    print("=== Test con valori noti di Sirio (Alpha Canis Majoris) ===\n")
    
    # Sirio: parallasse ~379 mas
    sirio_parallax_mas = 379.0
    sirio_distance_pc = parallax_to_distance_pc(sirio_parallax_mas)
    print(f"Parallasse Sirio: {sirio_parallax_mas} mas")
    print(f"Distanza: {sirio_distance_pc:.3f} pc\n")
    
    # Sirio: magnitudine apparente -1.46, assoluta ~1.42
    sirio_apparent_mag = -1.46
    sirio_abs_mag_calc = absolute_magnitude(sirio_apparent_mag, sirio_distance_pc)
    print(f"Magnitudine apparente: {sirio_apparent_mag}")
    print(f"Magnitudine assoluta (calcolata): {sirio_abs_mag_calc:.2f}\n")
    
    # Sirio: moto proprio componenti
    sirio_pmra = -546.01  # mas/yr
    sirio_pmdec = -1223.08  # mas/yr
    sirio_mu_total = proper_motion_total(sirio_pmra, sirio_pmdec)
    print(f"Moto proprio RA: {sirio_pmra:.2f} mas/yr")
    print(f"Moto proprio Dec: {sirio_pmdec:.2f} mas/yr")
    print(f"Moto proprio totale: {sirio_mu_total:.2f} mas/yr\n")
    
    # Velocità tangenziale
    sirio_v_t = tangential_velocity(sirio_pmra, sirio_pmdec, sirio_distance_pc)
    print(f"Velocità tangenziale: {sirio_v_t:.2f} km/s\n")
    
    # Luminosità relativa
    sirio_abs_mag = 1.42  # valore noto per Sirio
    sirio_lum = luminosity_ratio(sirio_abs_mag)
    print(f"Magnitudine assoluta (nota): {sirio_abs_mag}")
    print(f"Luminosità relativa al Sole: {sirio_lum:.2f} L_sun")
