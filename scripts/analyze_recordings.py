"""
Script d'analyse des enregistrements audio réels
=================================================

Ce script charge et analyse les fichiers WAV de guitare enregistrés.

Auteur : Projet Signaux III - EPHEC
Date : Novembre 2025
"""

import numpy as np
import matplotlib.pyplot as plt
import soundfile as sf
from scipy import signal as scipy_signal
import sys
import os

# Ajouter le dossier src au path pour importer nos modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# =============================================================================
# CONFIGURATION
# =============================================================================

DATA_DIR = 'data/raw'
FS_TARGET = 48000  # Fréquence d'échantillonnage attendue

FILES = {
    'Bien accordée (0 cents)': 'bonne_accord.wav',
    'Trop basse (-50 cents)': 'accord_basse.wav',
    'Trop haute (+50 cents)': 'accord_haute.wav'
}

# =============================================================================
# FONCTIONS D'ANALYSE
# =============================================================================

def load_audio(filepath):
    """
    Charge un fichier audio et le convertit en mono si nécessaire.
    
    Parameters
    ----------
    filepath : str
        Chemin vers le fichier WAV
    
    Returns
    -------
    signal : np.ndarray
        Signal audio (mono)
    fs : int
        Fréquence d'échantillonnage
    """
    data, fs = sf.read(filepath)
    
    # Convertir en mono si stéréo
    if data.ndim == 2:
        signal = np.mean(data, axis=1)
        print(f"   ℹ️  Fichier stéréo converti en mono")
    else:
        signal = data
    
    return signal, fs


def analyze_recording(filepath, label):
    """
    Analyse complète d'un enregistrement audio.
    
    Parameters
    ----------
    filepath : str
        Chemin vers le fichier
    label : str
        Label descriptif
    """
    print(f"\n{'='*70}")
    print(f"📁 {label}")
    print(f"   Fichier : {os.path.basename(filepath)}")
    print(f"{'='*70}")
    
    # Charger le signal
    signal, fs = load_audio(filepath)
    
    duration = len(signal) / fs
    
    # Statistiques de base
    print(f"\n📊 Statistiques de base :")
    print(f"   • Durée : {duration:.2f} secondes")
    print(f"   • Échantillons : {len(signal):,}")
    print(f"   • Fréquence d'échantillonnage : {fs} Hz")
    print(f"   • Amplitude max : {np.max(np.abs(signal)):.3f}")
    print(f"   • RMS : {np.sqrt(np.mean(signal**2)):.3f}")
    
    # Analyse énergétique
    energy = np.sum(signal**2)
    power_avg = np.mean(signal**2)
    
    print(f"\n⚡ Énergie :")
    print(f"   • Énergie totale : {energy:.2e}")
    print(f"   • Puissance moyenne : {power_avg:.6f}")
    
    # Détection de clipping
    clipping_threshold = 0.99
    clipped_samples = np.sum(np.abs(signal) > clipping_threshold)
    
    if clipped_samples > 0:
        print(f"\n⚠️  ATTENTION : {clipped_samples} échantillons clippés détectés !")
    else:
        print(f"\n✓ Pas de clipping détecté")
    
    return signal, fs


def plot_waveform_comparison(signals_dict, fs, zoom_duration=0.2):
    """
    Compare les formes d'onde de plusieurs enregistrements.
    
    Parameters
    ----------
    signals_dict : dict
        Dictionnaire {label: signal}
    fs : int
        Fréquence d'échantillonnage
    zoom_duration : float
        Durée du zoom en secondes (défaut: 0.2s)
    """
    fig, axes = plt.subplots(len(signals_dict), 2, figsize=(15, 4*len(signals_dict)))
    
    if len(signals_dict) == 1:
        axes = axes.reshape(1, -1)
    
    for idx, (label, sig) in enumerate(signals_dict.items()):
        time_full = np.arange(len(sig)) / fs
        time_zoom = time_full[:int(zoom_duration * fs)]
        sig_zoom = sig[:int(zoom_duration * fs)]
        
        # Graphique 1 : Signal complet
        axes[idx, 0].plot(time_full, sig, linewidth=0.5, color='steelblue')
        axes[idx, 0].set_xlabel('Temps (s)')
        axes[idx, 0].set_ylabel('Amplitude')
        axes[idx, 0].set_title(f'{label} - Signal complet')
        axes[idx, 0].grid(True, alpha=0.3)
        
        # Graphique 2 : Zoom
        axes[idx, 1].plot(time_zoom, sig_zoom, linewidth=1, color='darkorange')
        axes[idx, 1].set_xlabel('Temps (s)')
        axes[idx, 1].set_ylabel('Amplitude')
        axes[idx, 1].set_title(f'{label} - Zoom ({zoom_duration}s)')
        axes[idx, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('results/waveform_comparison.png', dpi=150, bbox_inches='tight')
    print(f"\n✓ Graphique sauvegardé : results/waveform_comparison.png")
    plt.show()


def plot_spectrogram_comparison(signals_dict, fs):
    """
    Compare les spectrogrammes de plusieurs enregistrements.
    
    Parameters
    ----------
    signals_dict : dict
        Dictionnaire {label: signal}
    fs : int
        Fréquence d'échantillonnage
    """
    fig, axes = plt.subplots(len(signals_dict), 1, figsize=(12, 4*len(signals_dict)))
    
    if len(signals_dict) == 1:
        axes = [axes]
    
    for idx, (label, sig) in enumerate(signals_dict.items()):
        # Calculer le spectrogramme
        nperseg = 4096
        noverlap = nperseg // 2
        
        f, t, Sxx = scipy_signal.spectrogram(
            sig,
            fs=fs,
            nperseg=nperseg,
            noverlap=noverlap
        )
        
        # Échelle logarithmique (dB)
        Sxx_db = 10 * np.log10(Sxx + 1e-10)
        
        # Affichage
        im = axes[idx].pcolormesh(t, f, Sxx_db, shading='gouraud', cmap='viridis')
        axes[idx].set_ylabel('Fréquence (Hz)')
        axes[idx].set_xlabel('Temps (s)')
        axes[idx].set_title(f'{label} - Spectrogramme')
        axes[idx].set_ylim([0, 1500])  # Bande utile pour la guitare
        plt.colorbar(im, ax=axes[idx], label='Magnitude (dB)')
    
    plt.tight_layout()
    plt.savefig('results/spectrogram_comparison.png', dpi=150, bbox_inches='tight')
    print(f"✓ Graphique sauvegardé : results/spectrogram_comparison.png")
    plt.show()


def plot_fft_comparison(signals_dict, fs):
    """
    Compare les spectres FFT de plusieurs enregistrements.
    
    Parameters
    ----------
    signals_dict : dict
        Dictionnaire {label: signal}
    fs : int
        Fréquence d'échantillonnage
    """
    plt.figure(figsize=(14, 6))
    
    for label, sig in signals_dict.items():
        # Calculer la FFT (sur une fenêtre)
        window_size = min(4096, len(sig))
        sig_windowed = sig[:window_size] * np.hanning(window_size)
        
        fft_result = np.fft.fft(sig_windowed)
        fft_magnitude = np.abs(fft_result)
        freqs = np.fft.fftfreq(window_size, 1/fs)
        
        # Spectre unilatéral
        positive_freqs = freqs[:window_size//2]
        positive_magnitude = fft_magnitude[:window_size//2]
        
        # Normalisation
        positive_magnitude = positive_magnitude / np.max(positive_magnitude)
        
        # Affichage
        plt.plot(positive_freqs, positive_magnitude, label=label, alpha=0.7, linewidth=2)
    
    plt.xlabel('Fréquence (Hz)')
    plt.ylabel('Magnitude normalisée')
    plt.title('Comparaison des spectres FFT')
    plt.xlim([50, 500])  # Zoom sur la zone d'intérêt (E2 ≈ 82 Hz)
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Ajouter des lignes verticales pour les fréquences attendues
    plt.axvline(x=80.06, color='blue', linestyle='--', alpha=0.3, label='E2 à -50c (80.06 Hz)')
    plt.axvline(x=82.41, color='green', linestyle='--', alpha=0.3, label='E2 juste (82.41 Hz)')
    plt.axvline(x=84.82, color='red', linestyle='--', alpha=0.3, label='E2 à +50c (84.82 Hz)')
    
    plt.tight_layout()
    plt.savefig('results/fft_comparison.png', dpi=150, bbox_inches='tight')
    print(f"✓ Graphique sauvegardé : results/fft_comparison.png")
    plt.show()


# =============================================================================
# SCRIPT PRINCIPAL
# =============================================================================

def main():
    """
    Fonction principale : analyse tous les enregistrements.
    """
    print("="*70)
    print("ANALYSE DES ENREGISTREMENTS AUDIO - Accordeur de Guitare")
    print("="*70)
    
    # Créer le dossier de résultats si nécessaire
    os.makedirs('results', exist_ok=True)
    
    # Charger et analyser tous les fichiers
    signals = {}
    
    for label, filename in FILES.items():
        filepath = os.path.join(DATA_DIR, filename)
        
        if not os.path.exists(filepath):
            print(f"\n⚠️  Fichier introuvable : {filepath}")
            continue
        
        signal, fs = analyze_recording(filepath, label)
        signals[label] = signal
    
    # Vérifications
    print(f"\n{'='*70}")
    print("✓ Tous les fichiers chargés avec succès")
    print(f"{'='*70}")
    
    # Générer les graphiques de comparaison
    print("\n📊 Génération des graphiques de comparaison...")
    print("-"*70)
    
    plot_waveform_comparison(signals, fs)
    plot_fft_comparison(signals, fs)
    plot_spectrogram_comparison(signals, fs)
    
    print("\n" + "="*70)
    print("✓ ANALYSE TERMINÉE")
    print("="*70)
    print(f"\nLes graphiques ont été sauvegardés dans le dossier 'results/'")


if __name__ == "__main__":
    main()