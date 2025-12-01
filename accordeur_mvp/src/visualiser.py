"""
Visualisation FFT - Accordeur de guitare
=========================================

Ce script génère des visualisations FFT pour démontrer explicitement
l'utilisation de la transformée de Fourier dans le projet.

Usage :
    python visualiser.py [--file chemin.wav]

Auteur : Projet Signaux III - EPHEC
Date : Novembre 2025
"""

import sys
import os
import argparse
from pathlib import Path
from typing import List, Optional, Tuple
import numpy as np
import matplotlib.pyplot as plt
import soundfile as sf

# Ajouter src au path (toujours relatif au dossier accordeur_mvp/)
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))
RAW_DIR = BASE_DIR / "data" / "raw"
ENREG_DIR = BASE_DIR / "data" / "enregistrements"

from pitch_detector import detect_f0, preprocess_signal
from music_utils import identify_string


# =============================================================================
# VISUALISATION FFT
# =============================================================================

def plot_fft_analysis(signal, fs, title="Analyse FFT"):
    """
    Affiche le spectre FFT d'un signal.
    
    Parameters
    ----------
    signal : np.ndarray
        Signal audio
    fs : int
        Fréquence d'échantillonnage
    title : str
        Titre du graphique
    """
    # Calcul FFT
    N = len(signal)
    fft_values = np.fft.fft(signal)
    fft_freqs = np.fft.fftfreq(N, 1/fs)
    
    # Magnitude (première moitié seulement)
    magnitude = np.abs(fft_values[:N//2])
    freqs = fft_freqs[:N//2]
    
    # Conversion en dB
    magnitude_db = 20 * np.log10(magnitude + 1e-10)
    
    # Graphique
    plt.figure(figsize=(12, 6))
    
    # Subplot 1 : Spectre complet
    plt.subplot(2, 1, 1)
    plt.plot(freqs, magnitude_db, linewidth=0.5)
    plt.xlim(0, 2000)
    plt.ylim(-60, np.max(magnitude_db) + 10)
    plt.xlabel('Fréquence (Hz)')
    plt.ylabel('Magnitude (dB)')
    plt.title(f'{title} - Spectre complet (0-2000 Hz)')
    plt.grid(True, alpha=0.3)
    
    # Subplot 2 : Zoom plage guitare
    plt.subplot(2, 1, 2)
    plt.plot(freqs, magnitude_db, linewidth=0.8)
    plt.xlim(70, 1500)
    plt.ylim(-60, np.max(magnitude_db) + 10)
    plt.xlabel('Fréquence (Hz)')
    plt.ylabel('Magnitude (dB)')
    plt.title(f'{title} - Zoom plage guitare (70-1500 Hz)')
    plt.grid(True, alpha=0.3)
    
    # Identifier les pics principaux
    # Trouver les 5 pics les plus forts
    threshold = np.max(magnitude_db) - 20  # Pics > max - 20 dB
    peaks_idx = np.where(magnitude_db > threshold)[0]
    
    if len(peaks_idx) > 0:
        # Trier par magnitude décroissante
        sorted_idx = peaks_idx[np.argsort(magnitude_db[peaks_idx])[::-1]]
        
        # Annoter les 5 premiers pics
        for i, idx in enumerate(sorted_idx[:5]):
            # Convertir explicitement en float pour satisfaire l'analyse statique
            freq = float(freqs[idx])
            mag = float(magnitude_db[idx])
            plt.annotate(f'{freq:.1f} Hz', 
                        xy=(freq, mag),
                        xytext=(freq + 50, mag - 5),
                        fontsize=8,
                        arrowprops=dict(arrowstyle='->', lw=0.5))
    
    plt.tight_layout()
    return freqs, magnitude_db


def compare_before_after_filtering(signal, fs):
    """
    Compare le spectre avant et après filtrage.
    
    Parameters
    ----------
    signal : np.ndarray
        Signal brut
    fs : int
        Fréquence d'échantillonnage
    """
    # Signal prétraité
    signal_filtered = preprocess_signal(signal, fs)
    
    # Calcul FFT pour les deux
    N = len(signal)
    
    # FFT signal brut
    fft_raw = np.fft.fft(signal)
    freqs = np.fft.fftfreq(N, 1/fs)
    magnitude_raw = np.abs(fft_raw[:N//2])
    freqs = freqs[:N//2]
    magnitude_raw_db = 20 * np.log10(magnitude_raw + 1e-10)
    
    # FFT signal filtré
    fft_filtered = np.fft.fft(signal_filtered)
    magnitude_filtered = np.abs(fft_filtered[:N//2])
    magnitude_filtered_db = 20 * np.log10(magnitude_filtered + 1e-10)
    
    # Graphique
    plt.figure(figsize=(12, 8))
    
    # Subplot 1 : Signal brut
    plt.subplot(2, 1, 1)
    plt.plot(freqs, magnitude_raw_db, linewidth=0.5, label='Signal brut')
    plt.axvline(70, color='r', linestyle='--', linewidth=1, alpha=0.5, label='Limite basse (70 Hz)')
    plt.axvline(1500, color='r', linestyle='--', linewidth=1, alpha=0.5, label='Limite haute (1500 Hz)')
    plt.xlim(0, 2000)
    plt.ylim(-80, np.max(magnitude_raw_db) + 10)
    plt.xlabel('Fréquence (Hz)')
    plt.ylabel('Magnitude (dB)')
    plt.title('AVANT filtrage - Spectre complet')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Subplot 2 : Signal filtré
    plt.subplot(2, 1, 2)
    plt.plot(freqs, magnitude_filtered_db, linewidth=0.5, color='green', label='Signal filtré')
    plt.axvline(70, color='r', linestyle='--', linewidth=1, alpha=0.5, label='Limite basse (70 Hz)')
    plt.axvline(1500, color='r', linestyle='--', linewidth=1, alpha=0.5, label='Limite haute (1500 Hz)')
    plt.xlim(0, 2000)
    plt.ylim(-80, np.max(magnitude_filtered_db) + 10)
    plt.xlabel('Fréquence (Hz)')
    plt.ylabel('Magnitude (dB)')
    plt.title('APRÈS filtrage (70-1500 Hz) - Spectre complet')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()


def analyze_harmonics(signal, fs, f0):
    """
    Analyse les harmoniques d'une note.
    
    Parameters
    ----------
    signal : np.ndarray
        Signal audio
    fs : int
        Fréquence d'échantillonnage
    f0 : float
        Fréquence fondamentale détectée
    """
    # FFT
    N = len(signal)
    fft_values = np.fft.fft(signal)
    freqs = np.fft.fftfreq(N, 1/fs)
    magnitude = np.abs(fft_values[:N//2])
    freqs = freqs[:N//2]
    magnitude_db = 20 * np.log10(magnitude + 1e-10)
    
    # Graphique
    plt.figure(figsize=(12, 6))
    plt.plot(freqs, magnitude_db, linewidth=0.8)
    plt.xlim(0, f0 * 6)  # Montrer jusqu'au 6ème harmonique
    plt.ylim(-60, np.max(magnitude_db) + 10)
    plt.xlabel('Fréquence (Hz)')
    plt.ylabel('Magnitude (dB)')
    plt.title(f'Analyse des harmoniques (f₀ = {f0:.2f} Hz)')
    plt.grid(True, alpha=0.3)
    
    # Marquer les harmoniques attendues
    harmonics = [1, 2, 3, 4, 5, 6]
    colors = ['red', 'orange', 'yellow', 'green', 'blue', 'purple']
    
    for i, h in enumerate(harmonics):
        freq_h = f0 * h
        plt.axvline(freq_h, color=colors[i], linestyle='--', 
                   linewidth=1.5, alpha=0.7, label=f'{h}×f₀ ({freq_h:.1f} Hz)')
    
    plt.legend(loc='upper right')
    plt.tight_layout()


def choisir_fichier_wav() -> Optional[Tuple[Path, str]]:
    """
    Permet de choisir un fichier WAV dans data/raw ou data/enregistrements.
    Retourne (chemin, label_dossier) ou None si aucun choix valide.
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    ENREG_DIR.mkdir(parents=True, exist_ok=True)
    alt_enreg = BASE_DIR / "data" / "enregistrement"  # tolère dossier sans 's'
    alt_enreg.mkdir(parents=True, exist_ok=True)

    fichiers: List[Tuple[Path, str]] = []
    sources = [
        (RAW_DIR, "data/raw"),
        (ENREG_DIR, "data/enregistrements"),
        ]
    for dossier, label in sources:
        fichiers += [(p, label) for p in sorted(dossier.glob("*.wav"))]

    if not fichiers:
        print(f"? Aucun fichier WAV trouvé dans {RAW_DIR} ni {ENREG_DIR}")
        print("  -> Ajoutez au moins un fichier WAV pour visualiser la FFT")
        return None

    print("Fichiers disponibles :")
    for idx, (path, label) in enumerate(fichiers, 1):
        print(f"  {idx}. {path.name} ({label})")
    print()

    choix_str = input("Choisissez un fichier (Entrée = 1) : ").strip()
    if choix_str == "":
        choix = 1
    else:
        try:
            choix = int(choix_str)
        except ValueError:
            print("? Entrée invalide")
            return None

    if not (1 <= choix <= len(fichiers)):
        print("? Sélection hors plage")
        return None

    return fichiers[choix - 1]


# =============================================================================
# FONCTION PRINCIPALE
# =============================================================================

def main():
    """
    Fonction principale : génère toutes les visualisations FFT.
    """
    parser = argparse.ArgumentParser(description="Visualiser un fichier WAV (FFT + filtres).")
    parser.add_argument("--file", "-f", type=str, help="Chemin du fichier WAV à analyser")
    args = parser.parse_args()

    print()
    print("=" * 60)
    print("VISUALISATION FFT - Accordeur de Guitare")
    print("=" * 60)
    print()

    filepath: Optional[Path] = None
    label = ""
    if args.file:
        candidate = Path(args.file)
        if candidate.exists() and candidate.suffix.lower() == ".wav":
            filepath = candidate
            label = "argument"
        else:
            print(f"? Fichier invalide : {candidate}")
            return
    else:
        selection = choisir_fichier_wav()
        if selection is None:
            return
        filepath, label = selection

    print(f"?? Analyse du fichier : {filepath.name} ({label})")
    print()

    # Charger le signal
    signal, fs = sf.read(str(filepath))
    
    # Convertir en mono si nécessaire
    if signal.ndim == 2:
        signal = np.mean(signal, axis=1)
    
    # Prendre une fenêtre
    start = len(signal) // 3
    frame = signal[start:start + 4096]
    
    print("📊 Génération des visualisations...")
    print()
    
    # 1. Analyse FFT basique
    print("1. Spectre FFT du signal...")
    plot_fft_analysis(frame, fs, f"FFT - {filepath.name}")
    
    # 2. Comparaison avant/après filtrage
    print("2. Comparaison avant/après filtrage...")
    compare_before_after_filtering(frame, fs)
    
    # 3. Détection f₀ + analyse harmoniques
    print("3. Détection f₀ + analyse des harmoniques...")
    frame_filtered = preprocess_signal(frame, fs)
    f0 = detect_f0(frame, fs)
    
    if f0:
        note, cents = identify_string(f0)
        print()
        print(f"   ✓ Fréquence détectée : {f0:.2f} Hz")
        print(f"   ✓ Note : {note} ({cents:+.1f} cents)")
        print()
        
        analyze_harmonics(frame_filtered, fs, f0)
    else:
        print("   ✗ Aucune fréquence détectée")
    
    # Afficher tous les graphiques
    print()
    print("✓ Visualisations générées !")
    print()
    print("📊 Affichage des graphiques...")
    print("   (Fermez les fenêtres pour continuer)")
    plt.show()
    
    print()
    print("=" * 60)
    print("✓ ANALYSE TERMINÉE")
    print("=" * 60)
    print()
    print("💡 Ces graphiques démontrent l'utilisation de la FFT dans :")
    print("   1. L'analyse spectrale du signal")
    print("   2. La vérification de l'efficacité des filtres")
    print("   3. L'identification des harmoniques")
    print()


if __name__ == "__main__":
    main()








