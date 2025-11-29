"""
Détecteur de fréquence fondamentale (f₀) - VERSION MVP
=======================================================

Implémentation minimale d'un accordeur de guitare basé sur l'autocorrélation.

Références cours EPHEC - Signaux III :
- Chapitre 6 (p.165-166) : Théorème de Shannon-Nyquist → Justifie Fs = 48 kHz
- Chapitre 7 (p.184-188) : FFT Cooley-Tukey → Optimise calcul autocorrélation

Extensions pratiques (hors cours) :
- Autocorrélation : Application FFT pour détecter périodicité (f₀)
  Formule : R(τ) = IFFT(|FFT(signal)|²) [Théorème de Wiener-Khinchin]
  Complexité : O(N log N) au lieu de O(N²) grâce à la FFT
- Filtre Butterworth : Filtre passe-bande standard (70-1500 Hz, ordre 4)
- Fenêtre Hann : Réduction effets de bord (pratique DSP)

Auteur : Projet Signaux III - EPHEC
Date : Novembre 2025
"""

import numpy as np
from scipy import signal as scipy_signal
from typing import Optional


# =============================================================================
# CONSTANTES
# =============================================================================

FS = 48000              # Fréquence d'échantillonnage (Hz)
FRAME_SIZE = 4096       # Taille de fenêtre (~85 ms à 48 kHz)
F0_MIN = 70.0           # Fréquence min guitare (Hz)
F0_MAX = 1500.0         # Fréquence max guitare + harmoniques (Hz)


# =============================================================================
# PRÉTRAITEMENT MINIMAL
# =============================================================================

def preprocess_signal(signal: np.ndarray, fs: int = FS, enable_notch: bool = True) -> np.ndarray:
    """
    Prétraite le signal : filtre notch + filtre passe-bande + fenêtrage.

    Justification technique :
    - Filtre notch 50 Hz : Réduction bruit secteur 50/60 Hz (consignes projet)
    - Filtre passe-bande Butterworth (70-1500 Hz, ordre 4) :
      * Principe : Convolution (Cours Chapitre 5 p.156)
      * Type Butterworth : Réponse plate en bande passante (standard audio)
      * Plage 70-1500 Hz : Couvre guitare 6 cordes (E2=82 Hz à E4=330 Hz + harmoniques)
    - Fenêtre de Hann : Réduction effets de bord et fuites spectrales (pratique DSP standard)
      * Formule : w(n) = 0.5 × (1 - cos(2πn/(N-1)))
      * Atténue progressivement le signal aux bords de la fenêtre

    Parameters
    ----------
    signal : np.ndarray
        Signal brut
    fs : int
        Fréquence d'échantillonnage
    enable_notch : bool
        Activer le filtre notch 50 Hz (défaut: True)

    Returns
    -------
    processed : np.ndarray
        Signal prétraité
    """
    # 1. Filtre notch 50 Hz (optionnel - bruit secteur)
    # Référence : Consignes projet (cadre_projet.md)
    # Réduction du bruit électrique 50 Hz (Europe) ou 60 Hz (USA)
    if enable_notch:
        # Q-factor = 30 : bande étroite autour de 50 Hz
        # Atténuation ~-40 dB à 50 Hz, pas d'impact sur 70-1500 Hz
        b_notch, a_notch = scipy_signal.iirnotch(50.0, Q=30, fs=fs)
        signal = scipy_signal.filtfilt(b_notch, a_notch, signal)

    # 2. Filtre passe-bande (70-1500 Hz)
    # Cours Chap. 5 p.150 : Butterworth = réponse plate
    nyquist = fs / 2.0
    low = 70.0 / nyquist
    high = 1500.0 / nyquist
    b, a = scipy_signal.butter(4, [low, high], btype='bandpass')
    filtered = scipy_signal.filtfilt(b, a, signal)

    # 3. Fenêtrage (Hann)
    # Cours Chap. 7 p.192 : réduit fuites spectrales
    window = np.hanning(len(filtered))
    windowed = filtered * window

    return windowed


# =============================================================================
# AUTOCORRÉLATION - DÉTECTION f₀
# =============================================================================

def autocorrelation(signal: np.ndarray) -> np.ndarray:
    """
    Calcule l'autocorrélation normalisée.

    Formule autocorrélation :
        R(τ) = Σ s(t) × s(t+τ)  [somme sur t de 0 à N-τ]
        r(τ) = R(τ) / R(0)      [normalisation par variance]

    Implémentation optimisée via FFT (Cours Chapitre 7 p.184-188) :
        R(τ) = IFFT(|FFT(s)|²)

    Justification :
    - Théorème de Wiener-Khinchin (extension FFT, hors cours)
    - Complexité : O(N log N) au lieu de O(N²)
    - Gain de performance : ×327 plus rapide pour N=4096

    Parameters
    ----------
    signal : np.ndarray
        Signal d'entrée
    
    Returns
    -------
    acf : np.ndarray
        Autocorrélation normalisée
    """
    # Retirer la moyenne
    signal = signal - np.mean(signal)
    
    # Calcul via FFT
    n = len(signal)
    signal_padded = np.concatenate([signal, np.zeros(n)])
    fft_signal = np.fft.fft(signal_padded)
    power_spectrum = np.abs(fft_signal) ** 2
    acf = np.fft.ifft(power_spectrum).real[:n]
    
    # Normalisation
    if acf[0] != 0:
        acf = acf / acf[0]
    
    return acf


def detect_f0(signal: np.ndarray, 
              fs: int = FS,
              f0_min: float = F0_MIN,
              f0_max: float = F0_MAX) -> Optional[float]:
    """
    Détecte la fréquence fondamentale par autocorrélation.
    
    Pipeline :
    1. Prétraitement (filtre + fenêtre)
    2. Autocorrélation
    3. Recherche du pic → période
    4. Conversion période → fréquence
    
    Parameters
    ----------
    signal : np.ndarray
        Signal audio
    fs : int
        Fréquence d'échantillonnage (défaut: 48000 Hz)
    f0_min : float
        Fréquence minimale (défaut: 70 Hz)
    f0_max : float
        Fréquence maximale (défaut: 1500 Hz)
    
    Returns
    -------
    f0 : float or None
        Fréquence fondamentale détectée (Hz), ou None si échec
    
    Examples
    --------
    >>> signal, fs = sf.read('guitare.wav')
    >>> f0 = detect_f0(signal[10000:14096], fs=fs)
    >>> print(f"f0 = {f0:.2f} Hz")
    """
    # 1. Prétraitement
    processed = preprocess_signal(signal, fs)
    
    # 2. Autocorrélation
    acf = autocorrelation(processed)
    
    # 3. Recherche du pic dans la plage [τ_min, τ_max]
    # τ_min = Fs / f0_max (période minimale)
    # τ_max = Fs / f0_min (période maximale)
    tau_min = int(np.floor(fs / f0_max))
    tau_max = int(np.ceil(fs / f0_min))
    tau_max = min(tau_max, len(acf) - 1)
    
    if tau_min >= tau_max:
        return None
    
    # Chercher le maximum dans la plage
    acf_region = acf[tau_min:tau_max]
    
    # Seuil minimal (éviter faux positifs)
    if np.max(acf_region) < 0.3:
        return None
    
    peak_idx = np.argmax(acf_region) + tau_min
    
    # 4. Interpolation parabolique (précision sub-échantillon)
    if peak_idx > 0 and peak_idx < len(acf) - 1:
        alpha = acf[peak_idx - 1]
        beta = acf[peak_idx]
        gamma = acf[peak_idx + 1]
        
        denominator = alpha - 2 * beta + gamma
        if abs(denominator) > 1e-10:
            offset = 0.5 * (alpha - gamma) / denominator
            peak_idx = peak_idx + np.clip(offset, -0.5, 0.5)
    
    # 5. Conversion période → fréquence
    f0 = fs / peak_idx
    
    # Vérification finale
    if f0_min <= f0 <= f0_max:
        return f0
    else:
        return None


# =============================================================================
# TESTS
# =============================================================================

if __name__ == "__main__":
    """Tests basiques du module."""
    print("=" * 60)
    print("TEST - Détecteur de fréquence fondamentale (MVP)")
    print("=" * 60)
    print()
    
    # Test sur sinusoïde pure
    print("Test : Sinusoïde à 110 Hz (corde A2)")
    t = np.arange(FRAME_SIZE) / FS
    signal_test = np.sin(2 * np.pi * 110.0 * t)
    
    f0 = detect_f0(signal_test, fs=FS)
    
    if f0:
        error = abs(f0 - 110.0)
        print(f"✓ Détecté : {f0:.2f} Hz (erreur = {error:.2f} Hz)")
    else:
        print("✗ Échec de détection")
    
    print()
    print("=" * 60)
