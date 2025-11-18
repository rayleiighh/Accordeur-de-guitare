"""
Utilitaires musicaux - VERSION MVP
===================================

Conversions fréquence ↔ note et calcul d'écarts en cents.

Référence cours : Chapitre 2 p.190 (gammes musicales)

Auteur : Projet Signaux III - EPHEC
Date : Novembre 2025
"""

import numpy as np
from typing import Tuple


# =============================================================================
# CONSTANTES
# =============================================================================

# Diapason standard
A4_FREQ = 440.0  # Hz
A4_MIDI = 69

# Fréquences des cordes de guitare (accord standard EADGBE)
GUITAR_STRINGS = {
    'E2': 82.41,   # 6ème corde (grave)
    'A2': 110.00,  # 5ème corde
    'D3': 146.83,  # 4ème corde
    'G3': 196.00,  # 3ème corde
    'B3': 246.94,  # 2ème corde
    'E4': 329.63   # 1ère corde (aiguë)
}


# =============================================================================
# CONVERSIONS
# =============================================================================

def cents_difference(freq_measured: float, freq_target: float) -> float:
    """
    Calcule l'écart en cents entre deux fréquences.
    
    Formule :
        cents = 1200 × log₂(f_measured / f_target)
    
    Définition du cent :
        - 1 cent = 1/100 de demi-ton
        - 1 demi-ton = 100 cents
        - 1 octave = 1200 cents
    
    Parameters
    ----------
    freq_measured : float
        Fréquence mesurée (Hz)
    freq_target : float
        Fréquence cible (Hz)
    
    Returns
    -------
    cents : float
        Écart en cents (positif = trop haut, négatif = trop bas)
    
    Examples
    --------
    >>> cents_difference(440.0, 440.0)
    0.0
    >>> cents_difference(466.16, 440.0)  # 1 demi-ton
    100.0
    """
    return 1200 * np.log2(freq_measured / freq_target)


def identify_string(frequency: float) -> Tuple[str, float]:
    """
    Identifie la corde de guitare la plus proche.
    
    Parameters
    ----------
    frequency : float
        Fréquence mesurée (Hz)
    
    Returns
    -------
    note : str
        Note de la corde ('E2', 'A2', etc.)
    cents : float
        Écart en cents par rapport à la corde
    
    Examples
    --------
    >>> note, cents = identify_string(82.41)
    >>> print(f"{note} : {cents:+.1f} cents")
    E2 : +0.0 cents
    """
    min_diff = float('inf')
    best_note = None
    best_cents = 0.0
    
    for note, freq_target in GUITAR_STRINGS.items():
        cents = cents_difference(frequency, freq_target)
        if abs(cents) < abs(min_diff):
            min_diff = cents
            best_note = note
            best_cents = cents
    
    return best_note, best_cents


def get_tuning_status(cents: float, threshold: float = 5.0) -> str:
    """
    Détermine le status d'accordage.
    
    Parameters
    ----------
    cents : float
        Écart en cents
    threshold : float
        Seuil pour considérer "juste" (défaut: ±5 cents)
    
    Returns
    -------
    status : str
        'juste', 'trop_bas' ou 'trop_haut'
    """
    if abs(cents) <= threshold:
        return 'juste'
    elif cents < 0:
        return 'trop_bas'
    else:
        return 'trop_haut'


# =============================================================================
# TESTS
# =============================================================================

if __name__ == "__main__":
    """Tests basiques."""
    print("=" * 60)
    print("TEST - Utilitaires musicaux (MVP)")
    print("=" * 60)
    print()
    
    # Test 1 : Calcul de cents
    print("Test 1 : Calcul d'écarts en cents")
    test_cases = [
        (440.0, 440.0, 0.0),
        (466.16, 440.0, 100.0),
        (415.30, 440.0, -100.0)
    ]
    
    for f1, f2, expected in test_cases:
        cents = cents_difference(f1, f2)
        print(f"  {f1:.2f} Hz vs {f2:.2f} Hz = {cents:+.1f} cents "
              f"(attendu: {expected:+.1f})")
    
    print()
    
    # Test 2 : Identification de cordes
    print("Test 2 : Identification des cordes")
    for note, freq in GUITAR_STRINGS.items():
        identified, cents = identify_string(freq)
        print(f"  {freq:.2f} Hz → {identified} ({cents:+.1f} cents)")
    
    print()
    print("=" * 60)
