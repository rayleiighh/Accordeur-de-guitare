"""
Détecteur de fréquence fondamentale (f₀) - VERSION MVP
=======================================================

Implémentation minimale d'un accordeur de guitare basé sur l'autocorrélation.

Références cours EPHEC - Signaux III :
- Chapitre 6 : Échantillonnage (p.166-177) - Théorème de Shannon
- Chapitre 7 : Autocorrélation (p.195-197)

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

def preprocess_signal(signal: np.ndarray, fs: int = FS) -> np.ndarray:
    """
    Prétraite le signal : filtre passe-bande + fenêtrage.
    
    Justification (Cours) :
    - Filtre passe-bande : Chapitre 5 p.150 (Butterworth)
    - Fenêtre de Hann : Chapitre 7 p.192 (réduction effets de bord)
    
    Parameters
    ----------
    signal : np.ndarray
        Signal brut
    fs : int
        Fréquence d'échantillonnage
    
    Returns
    -------
    processed : np.ndarray
        Signal prétraité
    """
    # 1. Filtre passe-bande (70-1500 Hz)
    # Cours Chap. 5 p.150 : Butterworth = réponse plate
    nyquist = fs / 2.0
    low = 70.0 / nyquist
    high = 1500.0 / nyquist
    b, a = scipy_signal.butter(4, [low, high], btype='bandpass')
    filtered = scipy_signal.filtfilt(b, a, signal)
    
    # 2. Fenêtrage (Hann)
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
    
    Formule (Cours Chap. 7) :
        R(τ) = Σ s(t) × s(t+τ)
        r(τ) = R(τ) / R(0)  (normalisée)
    
    Implémentation via FFT : R(τ) = IFFT(|FFT(s)|²)
    Complexité : O(N log N) au lieu de O(N²)
    
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
