"""
Script d'évaluation automatique - Accordeur de guitare
=======================================================

Évalue la précision de détection f₀ sur tous les fichiers WAV du dossier data/raw/
et génère un rapport CSV avec les métriques de performance.

Métriques calculées :
- MAE (Mean Absolute Error) en cents
- RMSE (Root Mean Square Error) en cents
- Écart-type (stabilité)
- Taux de détection (% de fenêtres avec f₀ détecté)

Références :
- Stratégie de validation : docs/strategies_de_validation.md
- Critère évaluation : MAE ≤ 10 cents (objectif MVP)

Usage :
    python eval_pitch.py

Sortie :
    - resultats/resultats_evaluation.csv (par fichier)
    - resultats/resume_global.txt (statistiques agrégées)

Auteur : Projet Signaux III - EPHEC
Date : Novembre 2025
"""

import sys
import os
import csv
import numpy as np
import soundfile as sf
from pathlib import Path

# Ajouter src au path
sys.path.insert(0, 'src')

from src.pitch_detector import detect_f0, FS, FRAME_SIZE
from src.music_utils import identify_string, cents_difference, GUITAR_STRINGS


# =============================================================================
# CONFIGURATION DES FICHIERS DE TEST
# =============================================================================

# Métadonnées des fichiers de test
# Format : {nom_fichier: (note_cible, cents_attendu)}
TEST_FILES_META = {
    'bonne_accord.wav': ('E2', 0),       # Corde bien accordée
    'accord_basse.wav': ('E2', -50),     # ~50 cents trop bas
    'accord_haute.wav': ('E2', +50),     # ~50 cents trop haut
}


# =============================================================================
# FONCTIONS D'ÉVALUATION
# =============================================================================

def evaluate_file(filepath, note_cible, cents_attendu):
    """
    Évalue la précision de détection f₀ sur un fichier WAV.

    Parameters
    ----------
    filepath : str
        Chemin vers le fichier WAV
    note_cible : str
        Note attendue (ex: 'E2', 'A2')
    cents_attendu : int
        Écart en cents attendu (0 = juste, -50 = trop bas, +50 = trop haut)

    Returns
    -------
    results : dict
        Dictionnaire avec métriques calculées :
        - mae : erreur absolue moyenne (cents)
        - rmse : erreur quadratique moyenne (cents)
        - std : écart-type (cents)
        - detection_rate : % fenêtres avec f₀ détecté
        - n_frames : nombre total de fenêtres analysées
    """
    print(f"  Analyse : {os.path.basename(filepath)}...", end=' ')

    try:
        # 1. Charger le fichier
        signal, fs = sf.read(filepath)

        # Convertir en mono si stéréo
        if signal.ndim == 2:
            signal = np.mean(signal, axis=1)

        # 2. Ignorer le transitoire initial (200 ms)
        # Référence : strategies_de_validation.md ligne 123
        start_idx = int(0.2 * fs)
        signal = signal[start_idx:]

        # 3. Fréquence de référence (note cible + écart attendu)
        f_ref = GUITAR_STRINGS[note_cible]  # Fréquence de base
        f_ref_adjusted = f_ref * (2 ** (cents_attendu / 1200.0))  # Ajusté selon écart

        # 4. Analyser plusieurs fenêtres (comme dans main.py)
        n_analyses = max(3, int(len(signal) / fs / 0.3))  # Fenêtres espacées de 0.3s
        hop = len(signal) // (n_analyses + 1)

        cents_list = []
        f0_detections = 0
        total_frames = 0

        for i in range(1, n_analyses + 1):
            start = i * hop
            end = start + FRAME_SIZE

            if end > len(signal):
                break

            frame = signal[start:end]
            total_frames += 1

            # Détection f₀
            f0 = detect_f0(frame, fs=fs)

            if f0 is not None:
                f0_detections += 1

                # Calculer l'écart en cents par rapport à la référence ajustée
                cents = cents_difference(f0, f_ref_adjusted)
                cents_list.append(cents)

        # 5. Calculer les métriques
        if not cents_list:
            print("❌ Aucune détection")
            return None

        cents_array = np.array(cents_list)

        results = {
            'fichier': os.path.basename(filepath),
            'note_cible': note_cible,
            'cents_attendu': cents_attendu,
            'mae': float(np.mean(np.abs(cents_array))),
            'rmse': float(np.sqrt(np.mean(cents_array ** 2))),
            'std': float(np.std(cents_array)),
            'mean_cents': float(np.mean(cents_array)),
            'detection_rate': float(100 * f0_detections / total_frames),
            'n_frames': total_frames,
            'n_detections': f0_detections
        }

        print(f"✓ MAE={results['mae']:.2f} cents")

        return results

    except Exception as e:
        print(f"❌ Erreur : {e}")
        return None


def generate_summary(all_results):
    """
    Génère un résumé global des résultats.

    Parameters
    ----------
    all_results : list of dict
        Liste des résultats par fichier

    Returns
    -------
    summary : dict
        Statistiques globales
    """
    if not all_results:
        return None

    mae_values = [r['mae'] for r in all_results]
    rmse_values = [r['rmse'] for r in all_results]
    detection_rates = [r['detection_rate'] for r in all_results]

    summary = {
        'mae_global': np.mean(mae_values),
        'mae_min': np.min(mae_values),
        'mae_max': np.max(mae_values),
        'rmse_global': np.mean(rmse_values),
        'detection_rate_avg': np.mean(detection_rates),
        'n_files': len(all_results),
        'total_frames': sum(r['n_frames'] for r in all_results)
    }

    return summary


# =============================================================================
# FONCTION PRINCIPALE
# =============================================================================

def main():
    """
    Fonction principale : évalue tous les fichiers et génère les rapports.
    """
    print()
    print("=" * 70)
    print("📊 ÉVALUATION AUTOMATIQUE - ACCORDEUR DE GUITARE")
    print("=" * 70)
    print()
    print("Objectif : MAE ≤ 10 cents (référence MVP)")
    print("Critères : Taux détection ≥ 95%, Stabilité σ ≤ 5 cents")
    print()
    print("-" * 70)
    print()

    # 1. Localiser le dossier data/raw/
    script_dir = Path(__file__).parent
    data_dir = script_dir / 'data' / 'raw'

    if not data_dir.exists():
        print(f"❌ Erreur : Dossier introuvable : {data_dir}")
        print("   Veuillez créer le dossier data/raw/ et y placer vos fichiers WAV")
        return

    # 2. Analyser chaque fichier
    all_results = []

    for filename, (note_cible, cents_attendu) in TEST_FILES_META.items():
        filepath = data_dir / filename

        if not filepath.exists():
            print(f"  ⚠️  Fichier manquant : {filename}")
            continue

        result = evaluate_file(str(filepath), note_cible, cents_attendu)

        if result:
            all_results.append(result)

    print()
    print("-" * 70)
    print()

    # 3. Créer le dossier de résultats
    results_dir = script_dir / 'resultats'
    results_dir.mkdir(exist_ok=True)

    # 4. Générer le rapport CSV
    if all_results:
        csv_path = results_dir / 'resultats_evaluation.csv'

        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['fichier', 'note_cible', 'cents_attendu', 'mae', 'rmse',
                         'std', 'mean_cents', 'detection_rate', 'n_frames', 'n_detections']
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()
            for result in all_results:
                writer.writerow(result)

        print(f"✓ Résultats détaillés : {csv_path}")
        print()

    # 5. Générer le résumé global
    summary = generate_summary(all_results)

    if summary:
        print("📊 RÉSUMÉ GLOBAL")
        print("=" * 70)
        print()
        print(f"   Fichiers analysés       : {summary['n_files']}")
        print(f"   Fenêtres totales        : {summary['total_frames']}")
        print()
        print(f"   MAE globale             : {summary['mae_global']:.2f} cents")
        print(f"   MAE min/max             : {summary['mae_min']:.2f} / {summary['mae_max']:.2f} cents")
        print(f"   RMSE globale            : {summary['rmse_global']:.2f} cents")
        print(f"   Taux détection moyen    : {summary['detection_rate_avg']:.1f} %")
        print()

        # Évaluation par rapport aux critères
        print("🎯 ÉVALUATION PAR RAPPORT AUX CRITÈRES MVP")
        print("-" * 70)
        print()

        mae_ok = summary['mae_global'] <= 10.0
        detection_ok = summary['detection_rate_avg'] >= 95.0

        print(f"   MAE ≤ 10 cents          : {'✅ PASSÉ' if mae_ok else '❌ ÉCHEC'} ({summary['mae_global']:.2f} cents)")
        print(f"   Détection ≥ 95%         : {'✅ PASSÉ' if detection_ok else '❌ ÉCHEC'} ({summary['detection_rate_avg']:.1f}%)")
        print()

        if mae_ok and detection_ok:
            print("   🎉 RÉSULTAT FINAL : ✅ TOUS LES CRITÈRES PASSÉS !")
        else:
            print("   ⚠️  RÉSULTAT FINAL : Certains critères non atteints")

        print()

        # Sauvegarder le résumé
        summary_path = results_dir / 'resume_global.txt'

        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("RÉSUMÉ GLOBAL - ÉVALUATION ACCORDEUR\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"MAE globale       : {summary['mae_global']:.2f} cents\n")
            f.write(f"MAE min/max       : {summary['mae_min']:.2f} / {summary['mae_max']:.2f} cents\n")
            f.write(f"RMSE globale      : {summary['rmse_global']:.2f} cents\n")
            f.write(f"Taux détection    : {summary['detection_rate_avg']:.1f} %\n")
            f.write(f"Fichiers analysés : {summary['n_files']}\n")
            f.write(f"Fenêtres totales  : {summary['total_frames']}\n")
            f.write("\n")
            f.write(f"Critère MAE ≤ 10c : {'PASSÉ' if mae_ok else 'ÉCHEC'}\n")
            f.write(f"Critère Détection : {'PASSÉ' if detection_ok else 'ÉCHEC'}\n")

        print(f"✓ Résumé sauvegardé : {summary_path}")

    print()
    print("=" * 70)
    print("✓ ÉVALUATION TERMINÉE")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
