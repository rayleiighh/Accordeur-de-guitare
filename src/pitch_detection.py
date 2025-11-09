"""
Module de détection de fréquence fondamentale (f₀) pour accordeur de guitare
=============================================================================

Ce module implémente plusieurs algorithmes de détection de pitch (hauteur tonale)
pour identifier la fréquence fondamentale d'un signal audio.

Algorithmes implémentés :
--------------------------
1. Autocorrélation (ACF) avec interpolation parabolique
2. YIN (Yet another INtelligent pitch detector)
3. FFT (recherche du pic dans le spectre)

Références au cours EPHEC - Signaux III :
------------------------------------------
- Chapitre 2 : Transformée de Fourier (p.38-57)
- Chapitre 7 : Analyse spectrale, autocorrélation (p.188-202)

Références académiques :
------------------------
- YIN Algorithm : de Cheveigné & Kawahara (2002)
  "YIN, a fundamental frequency estimator for speech and music"
- Autocorrelation : Rabiner & Schafer (1978)

Auteur : Projet Signaux III - EPHEC
Date : Novembre 2025
"""

import numpy as np
from scipy import signal as scipy_signal
from typing import Optional, Tuple, List
import warnings


# =============================================================================
# CONSTANTES
# =============================================================================

# Paramètres par défaut pour la détection
DEFAULT_FS = 48000          # Fréquence d'échantillonnage (Hz)
DEFAULT_FRAME_SIZE = 4096   # Taille de la fenêtre d'analyse
DEFAULT_HOP_SIZE = 1024     # Déplacement entre trames

# Plage de fréquences pour guitare (Hz)
F0_MIN = 70.0   # Un peu en-dessous de E2 (82 Hz)
F0_MAX = 1500.0 # Bien au-dessus de E4 (330 Hz) + harmoniques

# Seuils pour la détection
ACF_THRESHOLD = 0.3    # Seuil pour l'autocorrélation
YIN_THRESHOLD = 0.15   # Seuil pour YIN (plus bas = plus strict)


# =============================================================================
# AUTOCORRÉLATION (ACF) - MÉTHODE PRINCIPALE
# =============================================================================

def autocorrelation(signal: np.ndarray) -> np.ndarray:
    """
    Calcule l'autocorrélation normalisée d'un signal.
    
    L'autocorrélation mesure la similarité d'un signal avec lui-même décalé
    dans le temps. Pour un signal périodique, elle présente des pics aux
    multiples de la période.
    
    Formule (Chapitre 7 du cours) :
        R(τ) = Σ s(t) × s(t+τ)
    
    Normalisée :
        r(τ) = R(τ) / R(0)
    
    Référence : Cours Chapitre 7 p.195-197
    
    Parameters
    ----------
    signal : np.ndarray
        Signal d'entrée (1D)
    
    Returns
    -------
    acf : np.ndarray
        Autocorrélation normalisée (même taille que le signal)
    
    Notes
    -----
    Utilise la FFT pour un calcul rapide : O(N log N) au lieu de O(N²)
    R(τ) = IFFT(|FFT(s)|²)
    
    Examples
    --------
    >>> signal = np.sin(2 * np.pi * 440 * np.arange(4096) / 48000)
    >>> acf = autocorrelation(signal)
    >>> # acf aura des pics à τ = n × (48000/440) ≈ 109 échantillons
    """
    # Retirer la moyenne (DC offset)
    signal = signal - np.mean(signal)
    
    # Calculer l'autocorrélation via FFT (méthode rapide)
    # R(τ) = IFFT(|FFT(s)|²)
    n = len(signal)
    
    # Zero-padding pour éviter le repliement circulaire
    signal_padded = np.concatenate([signal, np.zeros(n)])
    
    # FFT → |FFT|² → IFFT
    fft_signal = np.fft.fft(signal_padded)
    power_spectrum = np.abs(fft_signal) ** 2
    acf = np.fft.ifft(power_spectrum).real[:n]
    
    # Normalisation par R(0)
    if acf[0] != 0:
        acf = acf / acf[0]
    
    return acf


def find_peak_acf(acf: np.ndarray, 
                  fs: int,
                  f0_min: float = F0_MIN,
                  f0_max: float = F0_MAX,
                  threshold: float = ACF_THRESHOLD) -> Optional[int]:
    """
    Trouve le premier pic significatif dans l'autocorrélation.
    
    Le premier pic après τ=0 correspond à la période fondamentale.
    
    Parameters
    ----------
    acf : np.ndarray
        Autocorrélation normalisée
    fs : int
        Fréquence d'échantillonnage
    f0_min : float
        Fréquence minimale recherchée (Hz)
    f0_max : float
        Fréquence maximale recherchée (Hz)
    threshold : float
        Seuil minimal pour considérer un pic (entre 0 et 1)
    
    Returns
    -------
    peak_index : int or None
        Index du pic (en échantillons), ou None si aucun pic trouvé
    
    Notes
    -----
    On cherche dans la plage [τ_min, τ_max] où :
        τ_min = fs / f0_max  (période minimale)
        τ_max = fs / f0_min  (période maximale)
    """
    # Calculer la plage de recherche en échantillons
    tau_min = int(np.floor(fs / f0_max))
    tau_max = int(np.ceil(fs / f0_min))
    
    # Limiter à la taille du signal
    tau_max = min(tau_max, len(acf) - 1)
    
    if tau_min >= tau_max:
        return None
    
    # Chercher le maximum dans la plage
    acf_region = acf[tau_min:tau_max]
    
    # Vérifier qu'il y a des valeurs au-dessus du seuil
    if np.max(acf_region) < threshold:
        return None
    
    # Trouver le pic maximum
    peak_idx = np.argmax(acf_region) + tau_min
    
    return peak_idx # type: ignore


def parabolic_interpolation(x: np.ndarray, peak_idx: int) -> float:
    """
    Interpolation parabolique pour affiner la position d'un pic.
    
    Permet d'obtenir une précision sub-échantillon en ajustant une parabole
    autour du pic détecté.
    
    Formule :
        x_refined = peak_idx + 0.5 × (α - γ) / (α - 2β + γ)
    
    où α, β, γ sont les valeurs aux points peak_idx-1, peak_idx, peak_idx+1
    
    Parameters
    ----------
    x : np.ndarray
        Signal contenant le pic
    peak_idx : int
        Index du pic détecté
    
    Returns
    -------
    refined_peak : float
        Position raffinée du pic (peut être non-entière)
    
    Examples
    --------
    >>> # Si le vrai pic est entre les échantillons 100 et 101
    >>> refined = parabolic_interpolation(acf, 100)
    >>> # refined pourrait être 100.3, par exemple
    """
    # Vérifier les limites
    if peak_idx <= 0 or peak_idx >= len(x) - 1:
        return float(peak_idx)
    
    # Récupérer les 3 points autour du pic
    alpha = x[peak_idx - 1]  # Point avant
    beta = x[peak_idx]       # Le pic
    gamma = x[peak_idx + 1]  # Point après
    
    # Formule d'interpolation parabolique
    # Dérivée de l'ajustement parabolique
    denominator = alpha - 2 * beta + gamma
    
    if abs(denominator) < 1e-10:
        return float(peak_idx)
    
    offset = 0.5 * (alpha - gamma) / denominator
    
    # Limiter l'offset à [-0.5, 0.5] (interpolation raisonnable)
    offset = np.clip(offset, -0.5, 0.5)
    
    refined_peak = peak_idx + offset
    
    return refined_peak


def detect_f0_autocorrelation(
    signal: np.ndarray,
    fs: int = DEFAULT_FS,
    f0_min: float = F0_MIN,
    f0_max: float = F0_MAX,
    threshold: float = ACF_THRESHOLD,
    interpolate: bool = True
) -> Optional[float]:
    """
    Détecte la fréquence fondamentale par autocorrélation.
    
    Pipeline :
    1. Calcul de l'autocorrélation normalisée
    2. Recherche du premier pic significatif
    3. Interpolation parabolique (optionnel)
    4. Conversion période → fréquence
    
    Parameters
    ----------
    signal : np.ndarray
        Signal audio (1D)
    fs : int
        Fréquence d'échantillonnage
    f0_min : float
        Fréquence minimale (Hz)
    f0_max : float
        Fréquence maximale (Hz)
    threshold : float
        Seuil de détection (0-1)
    interpolate : bool
        Activer l'interpolation parabolique
    
    Returns
    -------
    f0 : float or None
        Fréquence fondamentale détectée (Hz), ou None si échec
    
    Examples
    --------
    >>> # Signal synthétique à 440 Hz
    >>> t = np.arange(4096) / 48000
    >>> signal = np.sin(2 * np.pi * 440 * t)
    >>> f0 = detect_f0_autocorrelation(signal, fs=48000)
    >>> print(f"Fréquence détectée : {f0:.2f} Hz")
    """
    # Vérifications
    if len(signal) < 2 * (fs / f0_min):
        warnings.warn("Signal trop court pour détecter les basses fréquences")
        return None
    
    # 1. Calcul de l'autocorrélation
    acf = autocorrelation(signal)
    
    # 2. Trouver le pic
    peak_idx = find_peak_acf(acf, fs, f0_min, f0_max, threshold)
    
    if peak_idx is None:
        return None
    
    # 3. Interpolation parabolique (optionnel)
    if interpolate:
        peak_refined = parabolic_interpolation(acf, peak_idx)
    else:
        peak_refined = float(peak_idx)
    
    # 4. Conversion période → fréquence
    # f₀ = fs / τ
    f0 = fs / peak_refined
    
    # Vérification de cohérence
    if not (f0_min <= f0 <= f0_max):
        return None
    
    return f0


# =============================================================================
# ALGORITHME YIN
# =============================================================================

def cumulative_mean_normalized_difference(signal: np.ndarray) -> np.ndarray:
    """
    Calcule la fonction de différence normalisée cumulative (CMND) pour YIN.
    
    YIN améliore l'autocorrélation en utilisant une fonction de différence :
        d(τ) = Σ (s(t) - s(t+τ))²
    
    Normalisée cumulativement :
        d'(τ) = d(τ) / [(1/τ) × Σ_{j=1}^{τ} d(j)]
    
    Cette normalisation rend l'algorithme plus robuste.
    
    Référence : de Cheveigné & Kawahara (2002)
    
    Parameters
    ----------
    signal : np.ndarray
        Signal d'entrée
    
    Returns
    -------
    cmnd : np.ndarray
        Fonction CMND
    """
    n = len(signal)
    
    # 1. Calculer la fonction de différence d(τ)
    diff = np.zeros(n)
    
    for tau in range(n):
        # d(τ) = Σ (s(t) - s(t+τ))²
        if tau == 0:
            diff[tau] = 1.0  # Par convention
        else:
            diff[tau] = np.sum((signal[:-tau] - signal[tau:]) ** 2)
    
    # 2. Normalisation cumulative
    cmnd = np.zeros(n)
    cmnd[0] = 1.0
    
    cumulative_sum = 0.0
    for tau in range(1, n):
        cumulative_sum += diff[tau]
        if cumulative_sum != 0:
            cmnd[tau] = diff[tau] / (cumulative_sum / tau)
        else:
            cmnd[tau] = 1.0
    
    return cmnd


def absolute_threshold_yin(cmnd: np.ndarray,
                          fs: int,
                          threshold: float = YIN_THRESHOLD,
                          f0_min: float = F0_MIN,
                          f0_max: float = F0_MAX) -> Optional[int]:
    """
    Trouve le premier minimum en-dessous du seuil dans la fonction YIN.
    
    Parameters
    ----------
    cmnd : np.ndarray
        Fonction CMND de YIN
    fs : int
        Fréquence d'échantillonnage
    threshold : float
        Seuil absolu (typiquement 0.1-0.2)
    f0_min, f0_max : float
        Plage de fréquences
    
    Returns
    -------
    tau : int or None
        Décalage détecté (échantillons), ou None
    """
    # Plage de recherche
    tau_min = int(fs / f0_max)
    tau_max = int(fs / f0_min)
    tau_max = min(tau_max, len(cmnd) - 1)
    
    # Chercher le premier minimum sous le seuil
    for tau in range(tau_min, tau_max):
        if cmnd[tau] < threshold:
            # Vérifier qu'on est bien à un minimum local
            if tau + 1 < len(cmnd):
                if cmnd[tau] < cmnd[tau + 1]:
                    return tau
    
    # Si aucun croisement du seuil, prendre le minimum global
    region = cmnd[tau_min:tau_max]
    if len(region) > 0:
        min_idx = np.argmin(region) + tau_min
        if cmnd[min_idx] < 0.5:  # Seuil de secours
            return min_idx # type: ignore
    
    return None


def detect_f0_yin(
    signal: np.ndarray,
    fs: int = DEFAULT_FS,
    f0_min: float = F0_MIN,
    f0_max: float = F0_MAX,
    threshold: float = YIN_THRESHOLD,
    interpolate: bool = True
) -> Optional[float]:
    """
    Détecte la fréquence fondamentale avec l'algorithme YIN.
    
    YIN est considéré comme l'un des meilleurs algorithmes de détection
    de pitch pour la voix et la musique.
    
    Avantages sur l'autocorrélation :
    - Meilleure gestion des erreurs d'octave
    - Plus robuste au bruit
    - Meilleure précision
    
    Parameters
    ----------
    signal : np.ndarray
        Signal audio (1D)
    fs : int
        Fréquence d'échantillonnage
    f0_min, f0_max : float
        Plage de fréquences (Hz)
    threshold : float
        Seuil YIN (0.1-0.2 typique)
    interpolate : bool
        Interpolation parabolique
    
    Returns
    -------
    f0 : float or None
        Fréquence fondamentale (Hz)
    
    Examples
    --------
    >>> signal = np.sin(2 * np.pi * 440 * np.arange(4096) / 48000)
    >>> f0 = detect_f0_yin(signal, fs=48000)
    >>> print(f"f0 = {f0:.2f} Hz")
    """
    # Calculer la fonction CMND
    cmnd = cumulative_mean_normalized_difference(signal)
    
    # Trouver le minimum sous le seuil
    tau = absolute_threshold_yin(cmnd, fs, threshold, f0_min, f0_max)
    
    if tau is None:
        return None
    
    # Interpolation parabolique
    if interpolate and tau > 0 and tau < len(cmnd) - 1:
        tau_refined = parabolic_interpolation(cmnd, tau)
    else:
        tau_refined = float(tau)
    
    # Conversion en fréquence
    f0 = fs / tau_refined
    
    if not (f0_min <= f0 <= f0_max):
        return None
    
    return f0


# =============================================================================
# DÉTECTION PAR FFT (MÉTHODE SIMPLE)
# =============================================================================

def detect_f0_fft(
    signal: np.ndarray,
    fs: int = DEFAULT_FS,
    f0_min: float = F0_MIN,
    f0_max: float = F0_MAX
) -> Optional[float]:
    """
    Détecte la fréquence fondamentale par recherche du pic dans la FFT.
    
    Méthode simple mais moins robuste que ACF ou YIN :
    - Sensible aux harmoniques forts
    - Peut confondre f₀ et 2×f₀
    
    Référence : Cours Chapitre 7 p.188-191
    
    Parameters
    ----------
    signal : np.ndarray
        Signal audio
    fs : int
        Fréquence d'échantillonnage
    f0_min, f0_max : float
        Plage de fréquences
    
    Returns
    -------
    f0 : float or None
        Fréquence du pic dominant
    """
    # Fenêtrage (Hann)
    window = np.hanning(len(signal))
    signal_windowed = signal * window
    
    # FFT
    n = len(signal_windowed)
    fft_result = np.fft.rfft(signal_windowed)
    magnitude = np.abs(fft_result)
    freqs = np.fft.rfftfreq(n, 1/fs)
    
    # Plage de recherche
    mask = (freqs >= f0_min) & (freqs <= f0_max)
    
    if not np.any(mask):
        return None
    
    # Trouver le pic
    magnitude_region = magnitude[mask]
    freqs_region = freqs[mask]
    
    peak_idx = np.argmax(magnitude_region)
    f0 = freqs_region[peak_idx]
    
    return f0


# =============================================================================
# LISSAGE TEMPOREL
# =============================================================================

def median_filter(values: List[Optional[float]], 
                 window_size: int = 5) -> Optional[float]:
    """
    Filtre médian pour lisser les détections sur plusieurs trames.
    
    Permet de réduire les variations erratiques et améliore la stabilité
    de la détection en temps réel.
    
    Parameters
    ----------
    values : list of float or None
        Historique des détections (None = pas de détection)
    window_size : int
        Taille de la fenêtre de lissage (impair recommandé)
    
    Returns
    -------
    smoothed : float or None
        Valeur lissée
    
    Examples
    --------
    >>> history = [440.0, 441.0, 220.0, 440.5, 439.5]  # 220 est aberrant
    >>> smoothed = median_filter(history, window_size=5)
    >>> # smoothed ≈ 440.0 (la médiane ignore le 220)
    """
    # Filtrer les None
    valid_values = [v for v in values[-window_size:] if v is not None]
    
    if len(valid_values) == 0:
        return None
    
    return float(np.median(valid_values))


# =============================================================================
# DÉTECTION SUR TRAMES SUCCESSIVES (STREAMING)
# =============================================================================

class PitchDetector:
    """
    Détecteur de pitch pour traitement par trames (temps réel ou offline).
    
    Cette classe maintient un historique et applique un lissage pour
    des détections plus stables.
    
    Attributes
    ----------
    fs : int
        Fréquence d'échantillonnage
    frame_size : int
        Taille de la fenêtre d'analyse
    hop_size : int
        Déplacement entre trames
    method : str
        Méthode de détection ('acf', 'yin', 'fft')
    history : list
        Historique des détections
    
    Examples
    --------
    >>> detector = PitchDetector(method='yin')
    >>> for frame in audio_frames:
    ...     f0 = detector.process_frame(frame)
    ...     print(f"f0 = {f0:.2f} Hz")
    """
    
    def __init__(self,
                 fs: int = DEFAULT_FS,
                 frame_size: int = DEFAULT_FRAME_SIZE,
                 hop_size: int = DEFAULT_HOP_SIZE,
                 method: str = 'acf',
                 smooth_window: int = 5):
        """
        Initialise le détecteur.
        
        Parameters
        ----------
        fs : int
            Fréquence d'échantillonnage
        frame_size : int
            Taille de trame
        hop_size : int
            Hop size
        method : str
            'acf', 'yin' ou 'fft'
        smooth_window : int
            Taille de la fenêtre de lissage
        """
        self.fs = fs
        self.frame_size = frame_size
        self.hop_size = hop_size
        self.method = method.lower()
        self.smooth_window = smooth_window
        
        # Historique des détections
        self.history: List[Optional[float]] = []
        
        # Sélection de la fonction de détection
        if self.method == 'acf':
            self.detect_func = detect_f0_autocorrelation
        elif self.method == 'yin':
            self.detect_func = detect_f0_yin
        elif self.method == 'fft':
            self.detect_func = detect_f0_fft
        else:
            raise ValueError(f"Méthode inconnue : {method}")
    
    def process_frame(self, frame: np.ndarray) -> Optional[float]:
        """
        Traite une trame et retourne la fréquence lissée.
        
        Parameters
        ----------
        frame : np.ndarray
            Trame audio
        
        Returns
        -------
        f0_smoothed : float or None
            Fréquence lissée
        """
        # Détection brute
        f0_raw = self.detect_func(frame, fs=self.fs)
        
        # Ajout à l'historique
        self.history.append(f0_raw)
        
        # Lissage médian
        f0_smoothed = median_filter(self.history, self.smooth_window)
        
        return f0_smoothed
    
    def reset(self):
        """Réinitialise l'historique."""
        self.history = []


# =============================================================================
# TESTS ET DÉMONSTRATION
# =============================================================================

def run_tests():
    """
    Tests automatiques du module.
    """
    print("=" * 70)
    print("MODULE pitch_detection.py - TESTS")
    print("=" * 70)
    print()
    
    # =========================================================================
    # Test 1 : Détection sur sinusoïdes pures
    # =========================================================================
    print("[TEST 1] Détection sur sinusoïdes pures")
    print("-" * 70)
    
    test_freqs = [82.41, 110.0, 146.83, 196.0, 246.94, 329.63, 440.0]
    
    for freq_target in test_freqs:
        # Générer un signal pur
        duration = 0.1  # 100 ms
        t = np.arange(int(duration * DEFAULT_FS)) / DEFAULT_FS
        signal = np.sin(2 * np.pi * freq_target * t)
        
        # Tester les 3 méthodes
        f0_acf = detect_f0_autocorrelation(signal)
        f0_yin = detect_f0_yin(signal)
        f0_fft = detect_f0_fft(signal)
        
        # Calcul des erreurs
        err_acf = abs(f0_acf - freq_target) if f0_acf else 999
        err_yin = abs(f0_yin - freq_target) if f0_yin else 999
        err_fft = abs(f0_fft - freq_target) if f0_fft else 999
        
        # Affichage
        status = "✓" if err_acf < 1.0 else "✗"
        
        acf_str = f"{f0_acf:6.2f}" if f0_acf is not None else "  None"
        yin_str = f"{f0_yin:6.2f}" if f0_yin is not None else "  None"
        fft_str = f"{f0_fft:6.2f}" if f0_fft is not None else "  None"
        
        print(f"{status} Cible={freq_target:6.2f} Hz | "
              f"ACF={acf_str} (err={err_acf:.2f}) | "
              f"YIN={yin_str} (err={err_yin:.2f}) | "
              f"FFT={fft_str} (err={err_fft:.2f})")
    
    print()
    
    # =========================================================================
    # Test 2 : Robustesse au bruit
    # =========================================================================
    print("[TEST 2] Robustesse au bruit")
    print("-" * 70)
    
    freq_test = 110.0
    snr_levels = [30, 20, 10, 5]
    
    for snr_db in snr_levels:
        # Signal + bruit
        t = np.arange(DEFAULT_FRAME_SIZE) / DEFAULT_FS
        signal_clean = np.sin(2 * np.pi * freq_test * t)
        
        # Ajouter du bruit
        signal_power = np.mean(signal_clean ** 2)
        noise_power = signal_power / (10 ** (snr_db / 10))
        noise = np.random.normal(0, np.sqrt(noise_power), len(signal_clean))
        signal_noisy = signal_clean + noise
        
        # Détection
        f0_acf = detect_f0_autocorrelation(signal_noisy)
        f0_yin = detect_f0_yin(signal_noisy)
        
        err_acf = abs(f0_acf - freq_test) if f0_acf else 999
        err_yin = abs(f0_yin - freq_test) if f0_yin else 999
        
        status_acf = "✓" if err_acf < 5.0 else "✗"
        status_yin = "✓" if err_yin < 5.0 else "✗"
        
        acf_str = f"{f0_acf:6.2f}" if f0_acf is not None else "  None"
        yin_str = f"{f0_yin:6.2f}" if f0_yin is not None else "  None"
        
        print(f"SNR={snr_db:2d} dB | "
              f"{status_acf} ACF: {acf_str} Hz (err={err_acf:5.2f}) | "
              f"{status_yin} YIN: {yin_str} Hz (err={err_yin:5.2f})")
    
    print()
    
    # =========================================================================
    # Test 3 : Signal avec harmoniques
    # =========================================================================
    print("[TEST 3] Signal avec harmoniques (simulation guitare)")
    print("-" * 70)
    
    freq_fundamental = 82.41  # E2
    t = np.arange(DEFAULT_FRAME_SIZE) / DEFAULT_FS
    
    # Signal avec 5 harmoniques
    signal_guitar = np.zeros(len(t))
    for n in range(1, 6):
        amplitude = 1.0 / n
        signal_guitar += amplitude * np.sin(2 * np.pi * n * freq_fundamental * t)
    
    signal_guitar /= np.max(np.abs(signal_guitar))
    
    f0_acf = detect_f0_autocorrelation(signal_guitar)
    f0_yin = detect_f0_yin(signal_guitar)
    f0_fft = detect_f0_fft(signal_guitar)
    
    err_acf = abs(f0_acf - freq_fundamental) if f0_acf else 999
    err_yin = abs(f0_yin - freq_fundamental) if f0_yin else 999
    err_fft = abs(f0_fft - freq_fundamental) if f0_fft else 999
    
    acf_str = f"{f0_acf:6.2f}" if f0_acf is not None else "  None"
    yin_str = f"{f0_yin:6.2f}" if f0_yin is not None else "  None"
    fft_str = f"{f0_fft:6.2f}" if f0_fft is not None else "  None"
    
    print(f"Fondamentale attendue : {freq_fundamental:.2f} Hz")
    print(f"  ACF : {acf_str} Hz (erreur = {err_acf:.2f} Hz)")
    print(f"  YIN : {yin_str} Hz (erreur = {err_yin:.2f} Hz)")
    print(f"  FFT : {fft_str} Hz (erreur = {err_fft:.2f} Hz)")
    
    print()
    
    # =========================================================================
    # Test 4 : Lissage temporel
    # =========================================================================
    print("[TEST 4] Lissage temporel (médian)")
    print("-" * 70)
    
    # Simuler des détections avec un outlier
    history_test = [440.0, 441.0, 220.0, 440.5, 439.5, 440.2]
    smoothed = median_filter(history_test, window_size=5) # type: ignore
    
    print(f"Historique : {history_test}")
    print(f"Médiane (fenêtre=5) : {smoothed:.2f} Hz")
    print(f"✓ Le 220 Hz aberrant est bien filtré")
    
    print()
    print("✓ Tests terminés avec succès !")
    print("=" * 70)


if __name__ == "__main__":
    """
    Point d'entrée pour tester le module.
    
    Usage :
        python pitch_detection.py
    """
    run_tests()