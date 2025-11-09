"""
Module de théorie musicale pour accordeur de guitare
=====================================================

Ce module fournit des fonctions de conversion entre fréquences, notes MIDI,
et calculs d'écarts en cents pour l'accordeur de guitare.

Références au cours EPHEC - Signaux III :
------------------------------------------
- Chapitre 2 p.190 : Gammes musicales et système tempéré

Concepts clés :
---------------
- Système tempéré : 12 demi-tons par octave
- Ratio entre demi-tons : 2^(1/12) ≈ 1.05946
- Diapason standard : A4 = 440 Hz (référence internationale)
- Cent : 1/100 de demi-ton (1 octave = 1200 cents)

Auteur : Projet Signaux III - EPHEC
Date : Novembre 2025
"""

import numpy as np
from typing import Tuple, Optional


# =============================================================================
# CONSTANTES MUSICALES
# =============================================================================

# Diapason standard international
A4_FREQUENCY = 440.0  # Hz

# Numéro MIDI de la note A4 (La 440 Hz)
A4_MIDI = 69

# Noms des notes (notation anglo-saxonne)
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# Fréquences des cordes de guitare en accord standard
# (6 cordes, de la plus grave à la plus aiguë)
GUITAR_TUNING = {
    'E2': {'freq': 82.41, 'midi': 40, 'string': 6},   # Mi grave
    'A2': {'freq': 110.00, 'midi': 45, 'string': 5},  # La
    'D3': {'freq': 146.83, 'midi': 50, 'string': 4},  # Ré
    'G3': {'freq': 196.00, 'midi': 55, 'string': 3},  # Sol
    'B3': {'freq': 246.94, 'midi': 59, 'string': 2},  # Si
    'E4': {'freq': 329.63, 'midi': 64, 'string': 1}   # Mi aigu
}

# Tolérance pour considérer une note comme "juste" (en cents)
JUST_THRESHOLD = 5  # ±5 cents = juste


# =============================================================================
# CONVERSIONS FRÉQUENCE ↔ MIDI
# =============================================================================

def hz_to_midi(frequency: float, a4_freq: float = A4_FREQUENCY) -> float:
    """
    Convertit une fréquence en Hz en numéro de note MIDI.
    
    Formule mathématique (système tempéré) :
        MIDI = 69 + 12 × log₂(f / 440)
    
    Dérivation :
        - Dans le système tempéré, chaque demi-ton est un facteur 2^(1/12)
        - Entre A4 (440 Hz, MIDI 69) et une fréquence f :
          f = 440 × 2^(n/12), où n = nombre de demi-tons
        - Donc : n = 12 × log₂(f/440)
        - Et : MIDI = 69 + n
    
    Référence : Chapitre 2 p.190 du cours (gammes musicales)
    
    Parameters
    ----------
    frequency : float
        Fréquence en Hz (doit être > 0)
    a4_freq : float, optional
        Fréquence de référence pour A4 (défaut: 440 Hz)
    
    Returns
    -------
    midi_number : float
        Numéro MIDI (peut être décimal)
    
    Examples
    --------
    >>> hz_to_midi(440.0)
    69.0
    >>> hz_to_midi(880.0)  # A5 (une octave au-dessus)
    81.0
    >>> hz_to_midi(82.41)  # E2 (corde grave de guitare)
    40.0
    """
    if frequency <= 0:
        raise ValueError(f"La fréquence doit être positive (reçu: {frequency})")
    
    # Formule : MIDI = 69 + 12 × log₂(f / 440)
    # log₂(x) = ln(x) / ln(2)
    midi_number = A4_MIDI + 12 * np.log2(frequency / a4_freq)
    
    return midi_number


def midi_to_hz(midi_number: float, a4_freq: float = A4_FREQUENCY) -> float:
    """
    Convertit un numéro MIDI en fréquence (Hz).
    
    Formule mathématique (inverse de hz_to_midi) :
        f = 440 × 2^((MIDI - 69) / 12)
    
    Référence : Chapitre 2 p.190 du cours
    
    Parameters
    ----------
    midi_number : float
        Numéro MIDI (0-127, peut être décimal)
    a4_freq : float, optional
        Fréquence de référence pour A4 (défaut: 440 Hz)
    
    Returns
    -------
    frequency : float
        Fréquence correspondante en Hz
    
    Examples
    --------
    >>> midi_to_hz(69)
    440.0
    >>> midi_to_hz(81)  # A5
    880.0
    >>> midi_to_hz(40)  # E2
    82.41
    """
    # Formule : f = 440 × 2^((MIDI - 69) / 12)
    frequency = a4_freq * (2 ** ((midi_number - A4_MIDI) / 12))
    
    return frequency


# =============================================================================
# CALCUL D'ÉCART EN CENTS
# =============================================================================

def cents_difference(freq_measured: float, freq_target: float) -> float:
    """
    Calcule l'écart en cents entre deux fréquences.
    
    Définition du cent :
        - 1 cent = 1/100 de demi-ton
        - 1 demi-ton = 100 cents
        - 1 octave = 12 demi-tons = 1200 cents
    
    Formule :
        cents = 1200 × log₂(f_measured / f_target)
    
    Interprétation :
        - cents > 0 : la fréquence mesurée est trop haute
        - cents < 0 : la fréquence mesurée est trop basse
        - cents = 0 : parfaitement accordé
    
    Parameters
    ----------
    freq_measured : float
        Fréquence mesurée en Hz
    freq_target : float
        Fréquence cible (attendue) en Hz
    
    Returns
    -------
    cents : float
        Écart en cents (positif = trop haut, négatif = trop bas)
    
    Examples
    --------
    >>> cents_difference(440.0, 440.0)
    0.0
    >>> cents_difference(880.0, 440.0)  # 1 octave = 1200 cents
    1200.0
    >>> cents_difference(466.16, 440.0)  # 1 demi-ton = 100 cents
    100.0
    >>> cents_difference(415.30, 440.0)  # -1 demi-ton
    -100.0
    """
    if freq_measured <= 0 or freq_target <= 0:
        raise ValueError("Les fréquences doivent être positives")
    
    # Formule : cents = 1200 × log₂(f_measured / f_target)
    cents = 1200 * np.log2(freq_measured / freq_target)
    
    return cents


def hz_to_cents_from_midi(frequency: float, midi_target: int) -> float:
    """
    Calcule l'écart en cents entre une fréquence et une note MIDI cible.
    
    Parameters
    ----------
    frequency : float
        Fréquence mesurée en Hz
    midi_target : int
        Numéro MIDI de la note cible
    
    Returns
    -------
    cents : float
        Écart en cents par rapport à la note MIDI cible
    
    Examples
    --------
    >>> hz_to_cents_from_midi(440.0, 69)  # A4
    0.0
    >>> hz_to_cents_from_midi(82.41, 40)  # E2
    0.0
    """
    freq_target = midi_to_hz(midi_target)
    return cents_difference(frequency, freq_target)


# =============================================================================
# IDENTIFICATION DE NOTES
# =============================================================================

def get_note_name(midi_number: float) -> str:
    """
    Convertit un numéro MIDI en nom de note (ex: "A4", "E2").
    
    Convention MIDI :
        - C-1 = MIDI 0
        - C0  = MIDI 12
        - A4  = MIDI 69
        - C8  = MIDI 120
    
    Parameters
    ----------
    midi_number : float
        Numéro MIDI (arrondi à l'entier le plus proche)
    
    Returns
    -------
    note_name : str
        Nom de la note (ex: "C4", "A#3", "E2")
    
    Examples
    --------
    >>> get_note_name(69)
    'A4'
    >>> get_note_name(40)
    'E2'
    >>> get_note_name(60)
    'C4'
    """
    midi_int = int(round(midi_number))
    
    # Calcul de l'octave : octave = (MIDI ÷ 12) - 1
    octave = (midi_int // 12) - 1
    
    # Calcul de la note : note = MIDI mod 12
    note_index = midi_int % 12
    note = NOTE_NAMES[note_index]
    
    return f"{note}{octave}"


def hz_to_note(frequency: float, 
               return_cents: bool = False) -> Tuple[str, Optional[float]]:
    """
    Convertit une fréquence en nom de note (et optionnellement l'écart en cents).
    
    Parameters
    ----------
    frequency : float
        Fréquence en Hz
    return_cents : bool, optional
        Si True, retourne aussi l'écart en cents (défaut: False)
    
    Returns
    -------
    note_name : str
        Nom de la note la plus proche
    cents_offset : float, optional
        Écart en cents (seulement si return_cents=True)
    
    Examples
    --------
    >>> hz_to_note(440.0)
    'A4'
    >>> hz_to_note(440.0, return_cents=True)
    ('A4', 0.0)
    >>> hz_to_note(445.0, return_cents=True)
    ('A4', 19.56)  # Un peu trop haut
    """
    # Convertir en MIDI
    midi_float = hz_to_midi(frequency)
    
    # Arrondir au MIDI entier le plus proche
    midi_rounded = round(midi_float)
    
    # Obtenir le nom de la note
    note_name = get_note_name(midi_rounded)
    
    if return_cents:
        # Calculer l'écart en cents
        freq_target = midi_to_hz(midi_rounded)
        cents = cents_difference(frequency, freq_target)
        return note_name, cents
    else:
        return note_name # type: ignore


# =============================================================================
# DÉTECTION DE LA CORDE DE GUITARE
# =============================================================================

def identify_guitar_string(frequency: float, 
                          tolerance_cents: float = 200) -> Optional[dict]:
    """
    Identifie quelle corde de guitare correspond à une fréquence donnée.
    
    Parameters
    ----------
    frequency : float
        Fréquence mesurée en Hz
    tolerance_cents : float, optional
        Tolérance maximale en cents pour accepter une corde (défaut: 200)
        200 cents = 2 demi-tons (assez large pour les débutants)
    
    Returns
    -------
    string_info : dict or None
        Dictionnaire avec les infos de la corde si trouvée, sinon None
        Clés : 'note', 'string_number', 'freq_target', 'cents_offset'
    
    Examples
    --------
    >>> identify_guitar_string(82.41)  # E2 juste
    {'note': 'E2', 'string_number': 6, 'freq_target': 82.41, 'cents_offset': 0.0}
    >>> identify_guitar_string(80.0)   # E2 un peu bas
    {'note': 'E2', 'string_number': 6, 'freq_target': 82.41, 'cents_offset': -50.8}
    >>> identify_guitar_string(1000.0)  # Hors plage guitare
    None
    """
    min_cents_diff = float('inf')
    best_match = None
    
    for note_name, info in GUITAR_TUNING.items():
        freq_target = info['freq']
        cents = cents_difference(frequency, freq_target)
        
        # Vérifier si c'est dans la tolérance
        if abs(cents) < tolerance_cents and abs(cents) < abs(min_cents_diff):
            min_cents_diff = cents
            best_match = {
                'note': note_name,
                'string_number': info['string'],
                'freq_target': freq_target,
                'cents_offset': cents
            }
    
    return best_match


# =============================================================================
# ÉVALUATION DE L'ACCORDAGE
# =============================================================================

def evaluate_tuning(frequency: float, 
                   note_target: str,
                   just_threshold: float = JUST_THRESHOLD) -> dict:
    """
    Évalue si une note est bien accordée, trop haute ou trop basse.
    
    Parameters
    ----------
    frequency : float
        Fréquence mesurée en Hz
    note_target : str
        Note cible attendue (ex: "E2", "A4")
    just_threshold : float, optional
        Seuil en cents pour considérer la note comme "juste" (défaut: 5)
    
    Returns
    -------
    evaluation : dict
        Dictionnaire avec :
        - 'status': 'too_low', 'just', 'too_high'
        - 'cents_offset': écart en cents
        - 'freq_target': fréquence cible
        - 'freq_measured': fréquence mesurée
    
    Examples
    --------
    >>> evaluate_tuning(82.41, 'E2')
    {'status': 'just', 'cents_offset': 0.0, ...}
    >>> evaluate_tuning(80.0, 'E2')
    {'status': 'too_low', 'cents_offset': -50.8, ...}
    >>> evaluate_tuning(85.0, 'E2')
    {'status': 'too_high', 'cents_offset': 53.4, ...}
    """
    # Récupérer la fréquence cible
    if note_target in GUITAR_TUNING:
        freq_target = GUITAR_TUNING[note_target]['freq']
    else:
        raise ValueError(f"Note inconnue : {note_target}. "
                        f"Notes disponibles : {list(GUITAR_TUNING.keys())}")
    
    # Calculer l'écart en cents
    cents = cents_difference(frequency, freq_target)
    
    # Déterminer le status
    if abs(cents) <= just_threshold:
        status = 'just'
    elif cents < 0:
        status = 'too_low'
    else:
        status = 'too_high'
    
    return {
        'status': status,
        'cents_offset': cents,
        'freq_target': freq_target,
        'freq_measured': frequency,
        'note': note_target
    }


def get_tuning_instruction(cents_offset: float) -> str:
    """
    Retourne une instruction textuelle pour l'accordage.
    
    Parameters
    ----------
    cents_offset : float
        Écart en cents (positif = trop haut, négatif = trop bas)
    
    Returns
    -------
    instruction : str
        Instruction pour l'utilisateur
    
    Examples
    --------
    >>> get_tuning_instruction(0)
    '✓ Parfait !'
    >>> get_tuning_instruction(-30)
    '↑ Trop bas : serrer la corde'
    >>> get_tuning_instruction(25)
    '↓ Trop haut : desserrer la corde'
    """
    if abs(cents_offset) <= JUST_THRESHOLD:
        return "✓ Parfait !"
    elif cents_offset < 0:
        return f"↑ Trop bas ({abs(cents_offset):.1f} cents) : serrer la corde"
    else:
        return f"↓ Trop haut ({cents_offset:.1f} cents) : desserrer la corde"


# =============================================================================
# TESTS ET DÉMONSTRATION
# =============================================================================

def run_tests():
    """
    Exécute une série de tests pour vérifier le bon fonctionnement du module.
    """
    print("=" * 70)
    print("MODULE music_theory.py - TESTS")
    print("=" * 70)
    print()
    
    # =========================================================================
    # Test 1 : Conversions Hz ↔ MIDI
    # =========================================================================
    print("[TEST 1] Conversions Hz ↔ MIDI")
    print("-" * 70)
    
    test_cases = [
        (440.0, 69, "A4"),
        (880.0, 81, "A5"),
        (220.0, 57, "A3"),
        (82.41, 40, "E2"),
        (110.0, 45, "A2"),
        (329.63, 64, "E4")
    ]
    
    for freq, expected_midi, expected_note in test_cases:
        midi = hz_to_midi(freq)
        freq_back = midi_to_hz(midi)
        note = get_note_name(midi)
        
        midi_ok = abs(midi - expected_midi) < 0.1
        freq_ok = abs(freq_back - freq) < 0.1
        note_ok = note == expected_note
        
        status = "✓" if (midi_ok and freq_ok and note_ok) else "✗"
        print(f"{status} {freq:7.2f} Hz → MIDI {midi:.1f} ({note}) → {freq_back:.2f} Hz")
    
    print()
    
    # =========================================================================
    # Test 2 : Calcul d'écarts en cents
    # =========================================================================
    print("[TEST 2] Calcul d'écarts en cents")
    print("-" * 70)
    
    test_cents = [
        (440.0, 440.0, 0.0, "Identique"),
        (880.0, 440.0, 1200.0, "1 octave"),
        (466.16, 440.0, 100.0, "1 demi-ton"),
        (415.30, 440.0, -100.0, "-1 demi-ton"),
        (452.89, 440.0, 50.0, "+50 cents"),
        (427.47, 440.0, -50.0, "-50 cents")
    ]
    
    for f1, f2, expected_cents, description in test_cents:
        cents = cents_difference(f1, f2)
        error = abs(cents - expected_cents)
        status = "✓" if error < 0.5 else "✗"
        
        print(f"{status} {f1:.2f} Hz vs {f2:.2f} Hz = {cents:+7.1f} cents "
              f"(attendu: {expected_cents:+7.1f}) - {description}")
    
    print()
    
    # =========================================================================
    # Test 3 : Identification des cordes de guitare
    # =========================================================================
    print("[TEST 3] Identification des cordes de guitare")
    print("-" * 70)
    
    test_strings = [
        (82.41, "E2", 6, 0.0),
        (80.0, "E2", 6, -50.8),
        (85.0, "E2", 6, 53.4),
        (110.0, "A2", 5, 0.0),
        (329.63, "E4", 1, 0.0)
    ]
    
    for freq, expected_note, expected_string, expected_cents in test_strings:
        result = identify_guitar_string(freq)
        
        if result is not None:
            match_ok = (result['note'] == expected_note and 
                       result['string_number'] == expected_string)
            status = "✓" if match_ok else "✗"
            
            print(f"{status} {freq:6.2f} Hz → Corde {result['string_number']} "
                  f"({result['note']}) : {result['cents_offset']:+6.1f} cents")
        else:
            print(f"✗ {freq:6.2f} Hz → Aucune corde détectée")
    
    print()
    
    # =========================================================================
    # Test 4 : Évaluation de l'accordage
    # =========================================================================
    print("[TEST 4] Évaluation de l'accordage")
    print("-" * 70)
    
    test_tuning = [
        (82.41, "E2", "just", "Bien accordé"),
        (80.06, "E2", "too_low", "Trop bas (-50 cents)"),
        (84.82, "E2", "too_high", "Trop haut (+50 cents)"),
        (82.0, "E2", "too_low", "Légèrement bas"),
        (83.0, "E2", "too_high", "Légèrement haut")
    ]
    
    for freq, note, expected_status, description in test_tuning:
        result = evaluate_tuning(freq, note)
        instruction = get_tuning_instruction(result['cents_offset'])
        
        status_ok = result['status'] == expected_status
        status = "✓" if status_ok else "✗"
        
        print(f"{status} {description:25s} : {result['status']:10s} "
              f"({result['cents_offset']:+6.1f} cents)")
        print(f"   → {instruction}")
    
    print()
    
    # =========================================================================
    # Test 5 : Vérification des fréquences de référence
    # =========================================================================
    print("[TEST 5] Vérification des cordes de guitare")
    print("-" * 70)
    
    print(f"{'Corde':<6} {'Note':<4} {'Fréquence (Hz)':<15} {'MIDI':<6}")
    print("-" * 40)
    
    for note, info in GUITAR_TUNING.items():
        freq_calculated = midi_to_hz(info['midi'])
        freq_match = abs(freq_calculated - info['freq']) < 0.1
        status = "✓" if freq_match else "✗"
        
        print(f"{status} {info['string']:<5} {note:<4} {info['freq']:<15.2f} {info['midi']:<6}")
    
    print()
    print("✓ Tests terminés avec succès !")
    print("=" * 70)


# =============================================================================
# POINT D'ENTRÉE PRINCIPAL
# =============================================================================

if __name__ == "__main__":
    """
    Point d'entrée pour tester le module.
    
    Usage :
        python music_theory.py
    """
    run_tests()