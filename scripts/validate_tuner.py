"""
Script de validation de la détection f₀ sur enregistrements réels
===================================================================

Ce script teste les algorithmes de détection de pitch sur les fichiers
WAV enregistrés et mesure la précision (MAE en cents).

Auteur : Projet Signaux III - EPHEC
Date : Novembre 2025
"""

import sys
import os
from pathlib import Path
import numpy as np
import soundfile as sf
import csv
from typing import List, Dict

# Ajouter le répertoire racine du projet au path afin que les imports "src.*" fonctionnent
# Ceci permet d'exécuter le script depuis le dossier `scripts` ou depuis la racine du projet.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    # insérer en début pour prioriser le code du repo
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pitch_detection import detect_f0_autocorrelation, detect_f0_yin, PitchDetector
from src.music_theory import cents_difference, evaluate_tuning, GUITAR_TUNING


# =============================================================================
# CONFIGURATION
# =============================================================================

DATA_DIR = str(PROJECT_ROOT / 'data' / 'raw')
METADATA_FILE = str(PROJECT_ROOT / 'data' / 'metadata.csv')
RESULTS_DIR = str(PROJECT_ROOT / 'results' / 'metrics')

# Créer le dossier de résultats
os.makedirs(RESULTS_DIR, exist_ok=True)


# =============================================================================
# CHARGEMENT DES MÉTADONNÉES
# =============================================================================

def load_metadata() -> List[Dict]:
    """
    Charge les métadonnées des enregistrements.
    
    Returns
    -------
    metadata : list of dict
        Liste des infos par fichier
    """
    metadata = []
    
    with open(METADATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            metadata.append({
                'filename': row['filename'],
                'note_target': row['note_target'],
                'freq_target': float(row['freq_target']),
                'cents_offset': float(row['cents_offset']),
                'duration': float(row['duration']),
                'fs': int(row['fs']),
                'description': row['description']
            })
    
    return metadata


# =============================================================================
# DÉTECTION SUR FICHIER COMPLET
# =============================================================================

def analyze_audio_file(filepath: str,
                      freq_target: float,
                      method: str = 'yin',
                      skip_initial: float = 0.2) -> Dict:
    """
    Analyse un fichier audio complet et calcule les métriques.
    
    Parameters
    ----------
    filepath : str
        Chemin vers le fichier WAV
    freq_target : float
        Fréquence cible attendue (Hz)
    method : str
        Méthode de détection ('acf' ou 'yin')
    skip_initial : float
        Secondes à ignorer au début (transitoire)
    
    Returns
    -------
    results : dict
        Métriques calculées (MAE, std, etc.)
    """
    # Charger le fichier
    signal, fs = sf.read(filepath)
    
    # Convertir en mono si nécessaire
    if signal.ndim == 2:
        signal = np.mean(signal, axis=1)
    
    # Ignorer le transitoire initial
    skip_samples = int(skip_initial * fs)
    signal = signal[skip_samples:]
    
    # Paramètres de traitement
    frame_size = 4096
    hop_size = 1024
    
    # Créer le détecteur
    detector = PitchDetector(
        fs=fs,
        frame_size=frame_size,
        hop_size=hop_size,
        method=method,
        smooth_window=5
    )
    
    # Traiter par trames
    f0_list = []
    cents_list = []
    
    for i in range(0, len(signal) - frame_size, hop_size):
        frame = signal[i:i + frame_size]
        
        f0 = detector.process_frame(frame)
        
        if f0 is not None and 70 < f0 < 1500:
            # Calculer l'écart en cents
            cents = cents_difference(f0, freq_target)
            
            # Filtrer les valeurs aberrantes (±2 demi-tons)
            if abs(cents) < 200:
                f0_list.append(f0)
                cents_list.append(cents)
    
    # Calculer les métriques
    if len(cents_list) == 0:
        return {
            'n_frames': 0,
            'detection_rate': 0.0,
            'mae_cents': 999.0,
            'std_cents': 999.0,
            'median_f0': None,
            'median_cents': None
        }
    
    cents_array = np.array(cents_list)
    f0_array = np.array(f0_list)
    
    mae = np.mean(np.abs(cents_array))
    std = np.std(cents_array)
    median_cents = np.median(cents_array)
    median_f0 = np.median(f0_array)
    
    n_total_frames = (len(signal) - frame_size) // hop_size
    detection_rate = len(f0_list) / n_total_frames
    
    return {
        'n_frames': len(f0_list),
        'n_total_frames': n_total_frames,
        'detection_rate': detection_rate * 100,
        'mae_cents': mae,
        'std_cents': std,
        'median_f0': median_f0,
        'median_cents': median_cents,
        'min_cents': np.min(cents_array),
        'max_cents': np.max(cents_array),
        'p25_cents': np.percentile(cents_array, 25),
        'p75_cents': np.percentile(cents_array, 75)
    }


# =============================================================================
# SCRIPT PRINCIPAL
# =============================================================================

def main():
    """
    Fonction principale : validation sur tous les fichiers.
    """
    print("=" * 80)
    print("VALIDATION DE LA DÉTECTION f₀ SUR ENREGISTREMENTS RÉELS")
    print("=" * 80)
    print()
    
    # Charger les métadonnées
    metadata = load_metadata()
    
    print(f"✓ {len(metadata)} fichiers à analyser")
    print()
    
    # Tester les deux méthodes
    methods = ['acf', 'yin']
    
    all_results = []
    
    for method in methods:
        print("=" * 80)
        print(f"MÉTHODE : {method.upper()}")
        print("=" * 80)
        print()
        
        for meta in metadata:
            filepath = os.path.join(DATA_DIR, meta['filename'])
            
            if not os.path.exists(filepath):
                print(f"⚠️  Fichier introuvable : {filepath}")
                continue
            
            print(f"📁 {meta['filename']}")
            print(f"   Description : {meta['description']}")
            print(f"   Fréquence cible : {meta['freq_target']:.2f} Hz "
                  f"({meta['cents_offset']:+.0f} cents)")
            
            # Analyser le fichier
            results = analyze_audio_file(
                filepath,
                freq_target=meta['freq_target'],
                method=method
            )
            
            # Afficher les résultats
            print(f"\n   📊 Résultats :")
            print(f"      • Trames détectées : {results['n_frames']} / "
                  f"{results['n_total_frames']} ({results['detection_rate']:.1f}%)")
            print(f"      • f₀ médiane : {results['median_f0']:.2f} Hz")
            print(f"      • Écart médian : {results['median_cents']:+.2f} cents")
            print(f"      • MAE : {results['mae_cents']:.2f} cents")
            print(f"      • Std : {results['std_cents']:.2f} cents")
            print(f"      • Plage : [{results['min_cents']:+.1f}, "
                  f"{results['max_cents']:+.1f}] cents")
            
            # Évaluation
            if results['mae_cents'] < 10:
                status = "✓ EXCELLENT"
            elif results['mae_cents'] < 20:
                status = "✓ BON"
            elif results['mae_cents'] < 30:
                status = "⚠️ ACCEPTABLE"
            else:
                status = "✗ INSUFFISANT"
            
            print(f"\n   {status} (MAE < 10 cents = EXCELLENT)")
            print()
            
            # Sauvegarder pour export
            all_results.append({
                'method': method,
                'filename': meta['filename'],
                'note_target': meta['note_target'],
                'freq_target': meta['freq_target'],
                'cents_target': meta['cents_offset'],
                'description': meta['description'],
                **results
            })
    
    # =========================================================================
    # Résumé global
    # =========================================================================
    print("=" * 80)
    print("RÉSUMÉ GLOBAL")
    print("=" * 80)
    print()
    
    for method in methods:
        method_results = [r for r in all_results if r['method'] == method]
        
        if len(method_results) == 0:
            continue
        
        mae_values = [r['mae_cents'] for r in method_results if r['mae_cents'] < 100]
        
        if len(mae_values) > 0:
            mae_mean = np.mean(mae_values)
            mae_max = np.max(mae_values)
            
            print(f"{method.upper()} :")
            print(f"  • MAE moyenne : {mae_mean:.2f} cents")
            print(f"  • MAE max : {mae_max:.2f} cents")
            
            if mae_mean < 10:
                print(f"  → ✓ EXCELLENT (objectif : MAE ≤ 10 cents)")
            elif mae_mean < 15:
                print(f"  → ✓ BON (objectif : MAE ≤ 15 cents)")
            else:
                print(f"  → ⚠️ À améliorer (objectif : MAE ≤ 10 cents)")
            print()
    
    # =========================================================================
    # Export CSV
    # =========================================================================
    output_file = os.path.join(RESULTS_DIR, 'validation_results.csv')
    
    with open(output_file, 'w', newline='') as f:
        if len(all_results) > 0:
            fieldnames = all_results[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_results)
    
    print(f"✓ Résultats exportés : {output_file}")
    print()
    print("=" * 80)
    print("✓ VALIDATION TERMINÉE")
    print("=" * 80)


if __name__ == "__main__":
    main()