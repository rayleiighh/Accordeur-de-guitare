"""
Pipeline complet de détection f₀ avec prétraitement
====================================================

Ce script démontre l'utilisation de tous les modules ensemble :
1. Génération ou chargement de signal
2. Prétraitement (filtres)
3. Détection f₀ (ACF ou YIN)
4. Conversion musicale (Hz → Note + cents)
5. Évaluation de l'accordage

Auteur : Projet Signaux III - EPHEC
Date : Novembre 2025
"""

import sys
import numpy as np
import soundfile as sf
from typing import Optional, Dict

# Ajouter src au path
sys.path.insert(0, 'src')

from src.signal_generation import generate_detuned_string, GUITAR_NOTES
from src.preprocessing import preprocess_frame, DEFAULT_FS
from src.pitch_detection import detect_f0_yin, detect_f0_autocorrelation
from src.music_theory import (
    hz_to_note, 
    identify_guitar_string, 
    evaluate_tuning,
    get_tuning_instruction
)


# =============================================================================
# PIPELINE COMPLET
# =============================================================================

def analyze_audio_frame(
    frame: np.ndarray,
    fs: int = DEFAULT_FS,
    method: str = 'yin',
    preprocess: bool = True
) -> Optional[Dict]:
    """
    Pipeline complet d'analyse d'une trame audio.
    
    Étapes :
    1. Prétraitement (optionnel)
    2. Détection f₀
    3. Identification de la note
    4. Identification de la corde
    5. Évaluation de l'accordage
    
    Parameters
    ----------
    frame : np.ndarray
        Trame audio (4096 échantillons recommandé)
    fs : int
        Fréquence d'échantillonnage
    method : str
        Méthode de détection ('yin' ou 'acf')
    preprocess : bool
        Activer le prétraitement
    
    Returns
    -------
    result : dict or None
        Dictionnaire avec tous les résultats, ou None si échec
    """
    # Étape 1 : Prétraitement
    if preprocess:
        frame_processed = preprocess_frame(
            frame,
            fs=fs,
            apply_bandpass_filter=True,
            apply_notch_filter=True,
            apply_windowing=True
        )
    else:
        frame_processed = frame
    
    # Étape 2 : Détection f₀
    if method == 'yin':
        f0 = detect_f0_yin(frame_processed, fs=fs)
    elif method == 'acf':
        f0 = detect_f0_autocorrelation(frame_processed, fs=fs)
    else:
        raise ValueError(f"Méthode inconnue : {method}")
    
    if f0 is None:
        return None
    
    # Étape 3 : Identification de la note
    note_name, cents_offset = hz_to_note(f0, return_cents=True)
    
    # Étape 4 : Identification de la corde de guitare
    string_info = identify_guitar_string(f0)
    
    if string_info is None:
        return {
            'f0': f0,
            'note': note_name,
            'cents_offset': cents_offset,
            'string': None,
            'tuning_status': 'out_of_range'
        }
    
    # Étape 5 : Évaluation de l'accordage
    tuning_eval = evaluate_tuning(f0, string_info['note'])
    instruction = get_tuning_instruction(tuning_eval['cents_offset'])
    
    return {
        'f0': f0,
        'note': note_name,
        'cents_offset': cents_offset,
        'string_number': string_info['string_number'],
        'string_note': string_info['note'],
        'string_cents': string_info['cents_offset'],
        'tuning_status': tuning_eval['status'],
        'instruction': instruction
    }


# =============================================================================
# EXEMPLES D'UTILISATION
# =============================================================================

def example_1_synthetic_signal():
    """
    Exemple 1 : Analyse d'un signal synthétique.
    """
    print("=" * 70)
    print("EXEMPLE 1 : Analyse d'un signal synthétique")
    print("=" * 70)
    print()
    
    # Générer une corde E2 désaccordée de -30 cents
    signal, _ = generate_detuned_string('E2', cents_offset=-30, duration=1.0)
    
    # Prendre une fenêtre de 4096 échantillons
    frame = signal[10000:14096]
    
    print("Signal généré : E2 à -30 cents")
    print()
    
    # Analyser avec et sans prétraitement
    for preprocess in [False, True]:
        print(f"{'AVEC' if preprocess else 'SANS'} prétraitement :")
        print("-" * 70)
        
        result = analyze_audio_frame(
            frame,
            fs=DEFAULT_FS,
            method='yin',
            preprocess=preprocess
        )
        
        if result:
            print(f"  • Fréquence détectée : {result['f0']:.2f} Hz")
            print(f"  • Note : {result['note']} ({result['cents_offset']:+.1f} cents)")
            print(f"  • Corde : {result['string_number']} ({result['string_note']})")
            print(f"  • Écart par rapport à la corde : {result['string_cents']:+.1f} cents")
            print(f"  • Status : {result['tuning_status']}")
            print(f"  • Instruction : {result['instruction']}")
        else:
            print("  ✗ Aucune fréquence détectée")
        
        print()


def example_2_real_recording():
    """
    Exemple 2 : Analyse d'un enregistrement réel.
    """
    print("=" * 70)
    print("EXEMPLE 2 : Analyse d'un enregistrement réel")
    print("=" * 70)
    print()
    
    # Charger un fichier
    filepath = 'data/raw/bonne_accord.wav'
    
    try:
        signal, fs = sf.read(filepath)
        
        # Convertir en mono si nécessaire
        if signal.ndim == 2:
            signal = np.mean(signal, axis=1)
        
        print(f"Fichier chargé : {filepath}")
        print(f"  • Durée : {len(signal)/fs:.2f} s")
        print(f"  • Fréquence d'échantillonnage : {fs} Hz")
        print()
        
        # Analyser plusieurs fenêtres
        n_windows = 5
        hop = len(signal) // (n_windows + 1)
        
        print(f"Analyse de {n_windows} fenêtres :")
        print("-" * 70)
        
        for i in range(1, n_windows + 1):
            start = i * hop
            frame = signal[start:start + 4096]
            
            result = analyze_audio_frame(
                frame,
                fs=fs,
                method='yin',
                preprocess=True
            )
            
            if result:
                if result.get('string_note'):
                    print(f"  Fenêtre {i} : {result['f0']:6.2f} Hz → "
                          f"{result['string_note']} ({result['string_cents']:+6.1f} cents) "
                          f"[{result['tuning_status']}]")
                else:
                    print(f"  Fenêtre {i} : {result['f0']:6.2f} Hz → "
                          f"{result['note']} (hors plage guitare)")
            else:
                print(f"  Fenêtre {i} : Pas de détection")
        
        print()
    
    except FileNotFoundError:
        print(f"⚠️  Fichier introuvable : {filepath}")
        print("   Exemple ignoré.")
        print()


def example_3_comparison_methods():
    """
    Exemple 3 : Comparaison ACF vs YIN.
    """
    print("=" * 70)
    print("EXEMPLE 3 : Comparaison ACF vs YIN")
    print("=" * 70)
    print()
    
    # Tester sur toutes les cordes
    for note_name, freq in GUITAR_NOTES.items():
        signal, _ = generate_detuned_string(note_name, cents_offset=0, duration=0.5)
        frame = signal[5000:9096]
        
        # Méthode ACF
        result_acf = analyze_audio_frame(frame, method='acf', preprocess=True)
        
        # Méthode YIN
        result_yin = analyze_audio_frame(frame, method='yin', preprocess=True)
        
        print(f"{note_name} ({freq:.2f} Hz) :")
        
        if result_acf:
            err_acf = abs(result_acf['f0'] - freq)
            print(f"  ACF : {result_acf['f0']:6.2f} Hz (erreur = {err_acf:.2f} Hz)")
        else:
            print(f"  ACF : Pas de détection")
        
        if result_yin:
            err_yin = abs(result_yin['f0'] - freq)
            print(f"  YIN : {result_yin['f0']:6.2f} Hz (erreur = {err_yin:.2f} Hz)")
        else:
            print(f"  YIN : Pas de détection")
        
        print()


# =============================================================================
# SCRIPT PRINCIPAL
# =============================================================================

def main():
    """
    Fonction principale : exécute tous les exemples.
    """
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  PIPELINE COMPLET - ACCORDEUR DE GUITARE NUMÉRIQUE".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    # Exemple 1
    example_1_synthetic_signal()
    
    # Exemple 2
    example_2_real_recording()
    
    # Exemple 3
    example_3_comparison_methods()
    
    print("=" * 70)
    print("✓ TOUS LES EXEMPLES TERMINÉS")
    print("=" * 70)
    print()
    print("Ce script démontre l'utilisation des 4 modules :")
    print("  1. signal_generation.py  - Génération de signaux")
    print("  2. preprocessing.py      - Filtrage et fenêtrage")
    print("  3. pitch_detection.py    - Détection f₀ (ACF/YIN)")
    print("  4. music_theory.py       - Conversions musicales")
    print()


if __name__ == "__main__":
    main()