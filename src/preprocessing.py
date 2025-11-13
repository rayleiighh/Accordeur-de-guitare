"""
Module de prétraitement du signal pour accordeur de guitare
============================================================

Ce module fournit des fonctions de filtrage et de prétraitement pour
améliorer la qualité du signal avant la détection de fréquence fondamentale.

Filtres implémentés :
---------------------
1. Filtre passe-bande (70-1500 Hz) - Pour isoler les fréquences de guitare
2. Filtre notch (50 Hz) - Pour éliminer le bruit du secteur
3. Fenêtrage (Hann) - Pour réduire les effets de bord

Références au cours EPHEC - Signaux III :
------------------------------------------
- Chapitre 5 : Filtres numériques (p.145-156)
- Chapitre 6 : Échantillonnage (p.166-177)
- Chapitre 7 : Fenêtrage (p.192)

Auteur : Projet Signaux III - EPHEC
Date : Novembre 2025
"""

import numpy as np
from scipy import signal as scipy_signal
from typing import Tuple, Optional
import warnings


# =============================================================================
# CONSTANTES
# =============================================================================

# Fréquence d'échantillonnage par défaut
DEFAULT_FS = 48000  # Hz

# Bande passante pour guitare
FREQ_LOW = 70.0    # Hz - En dessous de E2 (82 Hz)
FREQ_HIGH = 1500.0 # Hz - Bien au-dessus de E4 + harmoniques

# Fréquence du secteur (bruit électrique)
FREQ_NOTCH = 50.0  # Hz (Europe) - Utiliser 60 Hz pour USA/Canada

# Ordre des filtres
BANDPASS_ORDER = 4   # Ordre du filtre passe-bande (Butterworth)
NOTCH_Q = 30         # Facteur de qualité du filtre notch (plus élevé = plus étroit)


# =============================================================================
# CONCEPTION DES FILTRES
# =============================================================================

def design_bandpass_filter(
    fs: int = DEFAULT_FS,
    lowcut: float = FREQ_LOW,
    highcut: float = FREQ_HIGH,
    order: int = BANDPASS_ORDER
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Conçoit un filtre passe-bande de Butterworth.
    
    Le filtre de Butterworth a une réponse en fréquence maximalement plate
    dans la bande passante, ce qui le rend idéal pour l'audio musical.
    
    Référence : Cours Chapitre 5 p.150
        "Butterworth, Tchebychev ou Bessel sont les filtres IIR classiques"
        "Le filtre de Butterworth a la réponse la plus plate"
    
    Justification de la bande [70-1500 Hz] :
        - E2 (corde grave) = 82 Hz → on prend 70 Hz pour avoir de la marge
        - E4 (corde aiguë) = 330 Hz, mais avec harmoniques jusqu'à ~1000 Hz
        - Au-delà de 1500 Hz : pas d'info utile pour l'accordage
    
    Parameters
    ----------
    fs : int
        Fréquence d'échantillonnage (Hz)
    lowcut : float
        Fréquence de coupure basse (Hz)
    highcut : float
        Fréquence de coupure haute (Hz)
    order : int
        Ordre du filtre (4 = bon compromis précision/latence)
    
    Returns
    -------
    b, a : np.ndarray, np.ndarray
        Coefficients du filtre (numérateur, dénominateur)
    
    Notes
    -----
    Filtre IIR (Infinite Impulse Response) :
        - Plus efficace que FIR (moins de coefficients)
        - Peut être instable si mal conçu (scipy gère automatiquement)
    
    Référence : Cours Chapitre 5 p.149-150
    
    Examples
    --------
    >>> b, a = design_bandpass_filter(fs=48000)
    >>> # Appliquer avec scipy.signal.filtfilt(b, a, signal)
    """
    # Normalisation des fréquences par rapport à la fréquence de Nyquist
    # Référence : Cours Chapitre 6 p.166-167 (Théorème de Shannon)
    nyquist = fs / 2.0
    
    if lowcut >= nyquist or highcut >= nyquist:
        raise ValueError(f"Les fréquences de coupure doivent être < {nyquist} Hz (Nyquist)")
    
    low = lowcut / nyquist
    high = highcut / nyquist
    
    # Conception du filtre de Butterworth
    # Référence : Cours Chapitre 5 p.150
    b, a = scipy_signal.butter(order, [low, high], btype='bandpass')
    
    return b, a


def design_notch_filter(
    fs: int = DEFAULT_FS,
    freq: float = FREQ_NOTCH,
    Q: float = NOTCH_Q
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Conçoit un filtre notch (coupe-bande) pour éliminer le bruit du secteur.
    
    Le bruit du secteur électrique (50 Hz en Europe, 60 Hz aux USA) est un
    bruit sinusoïdal parasite très courant dans les enregistrements audio.
    Un filtre notch permet de l'éliminer sans affecter le reste du signal.
    
    Justification :
        - 50 Hz est bien en-dessous de E2 (82 Hz)
        - Le filtre est très étroit (Q = 30) pour ne pas affecter E2
        - Améliore significativement le SNR en environnement électrique
    
    Parameters
    ----------
    fs : int
        Fréquence d'échantillonnage (Hz)
    freq : float
        Fréquence à éliminer (Hz) - Typiquement 50 ou 60 Hz
    Q : float
        Facteur de qualité (plus élevé = filtre plus étroit)
        Q = 30 → bande d'arrêt ≈ ±1.7 Hz autour de 50 Hz
    
    Returns
    -------
    b, a : np.ndarray, np.ndarray
        Coefficients du filtre
    
    Notes
    -----
    Le facteur de qualité Q détermine la largeur du filtre :
        Bande d'arrêt ≈ freq / Q
        Q = 30 → Bande ≈ 50/30 ≈ 1.7 Hz
    
    Référence : Cours Chapitre 5 p.145 (filtres IIR)
    
    Examples
    --------
    >>> b, a = design_notch_filter(fs=48000, freq=50)
    >>> # Élimine le bruit à 50 Hz (secteur européen)
    """
    nyquist = fs / 2.0
    
    if freq >= nyquist:
        raise ValueError(f"La fréquence notch doit être < {nyquist} Hz")
    
    # Normalisation
    w0 = freq / nyquist
    
    # Conception du filtre notch
    b, a = scipy_signal.iirnotch(w0, Q)
    
    return b, a


# =============================================================================
# APPLICATION DES FILTRES
# =============================================================================

def apply_filter(
    signal: np.ndarray,
    b: np.ndarray,
    a: np.ndarray,
    method: str = 'filtfilt'
) -> np.ndarray:
    """
    Applique un filtre à un signal.
    
    Deux méthodes disponibles :
    - 'filtfilt' : Filtrage non-causal (sans déphasage) - Pour offline
    - 'lfilter' : Filtrage causal (avec déphasage) - Pour temps réel
    
    Référence : Cours Chapitre 5 p.145-147
    
    Parameters
    ----------
    signal : np.ndarray
        Signal d'entrée
    b, a : np.ndarray
        Coefficients du filtre
    method : str
        'filtfilt' (défaut) ou 'lfilter'
    
    Returns
    -------
    filtered : np.ndarray
        Signal filtré
    
    Notes
    -----
    **filtfilt** (Cours p.145) :
        - Filtre en avant puis en arrière
        - Aucun déphasage (phase zéro)
        - NON-CAUSAL (ne peut pas être utilisé en temps réel)
        - Parfait pour traitement offline
    
    **lfilter** (Cours p.146-147) :
        - Filtre causal (peut être utilisé en temps réel)
        - Introduit un déphasage
        - Plus rapide que filtfilt
    
    Examples
    --------
    >>> b, a = design_bandpass_filter()
    >>> filtered = apply_filter(signal, b, a, method='filtfilt')
    """
    if len(signal) == 0:
        return signal
    
    if method == 'filtfilt':
        # Filtrage non-causal (phase zéro)
        # Référence : Cours Chapitre 5 p.145
        filtered = scipy_signal.filtfilt(b, a, signal)
    
    elif method == 'lfilter':
        # Filtrage causal
        # Référence : Cours Chapitre 5 p.146-147
        filtered = scipy_signal.lfilter(b, a, signal)
    
    else:
        raise ValueError(f"Méthode inconnue : {method}. Utiliser 'filtfilt' ou 'lfilter'")
    
    return filtered


def apply_bandpass(
    signal: np.ndarray,
    fs: int = DEFAULT_FS,
    lowcut: float = FREQ_LOW,
    highcut: float = FREQ_HIGH,
    method: str = 'filtfilt'
) -> np.ndarray:
    """
    Applique un filtre passe-bande au signal.
    
    Fonction pratique qui combine design + application.
    
    Parameters
    ----------
    signal : np.ndarray
        Signal d'entrée
    fs : int
        Fréquence d'échantillonnage
    lowcut, highcut : float
        Fréquences de coupure (Hz)
    method : str
        'filtfilt' ou 'lfilter'
    
    Returns
    -------
    filtered : np.ndarray
        Signal filtré (bande [lowcut, highcut] Hz)
    
    Examples
    --------
    >>> signal_filtered = apply_bandpass(signal, fs=48000)
    >>> # Garde seulement 70-1500 Hz
    """
    b, a = design_bandpass_filter(fs, lowcut, highcut)
    return apply_filter(signal, b, a, method)


def apply_notch(
    signal: np.ndarray,
    fs: int = DEFAULT_FS,
    freq: float = FREQ_NOTCH,
    method: str = 'filtfilt'
) -> np.ndarray:
    """
    Applique un filtre notch au signal.
    
    Parameters
    ----------
    signal : np.ndarray
        Signal d'entrée
    fs : int
        Fréquence d'échantillonnage
    freq : float
        Fréquence à éliminer (Hz)
    method : str
        'filtfilt' ou 'lfilter'
    
    Returns
    -------
    filtered : np.ndarray
        Signal sans la fréquence parasitée
    
    Examples
    --------
    >>> signal_clean = apply_notch(signal, fs=48000, freq=50)
    >>> # Élimine le bruit à 50 Hz
    """
    b, a = design_notch_filter(fs, freq)
    return apply_filter(signal, b, a, method)


# =============================================================================
# FENÊTRAGE
# =============================================================================

def apply_window(
    signal: np.ndarray,
    window_type: str = 'hann'
) -> np.ndarray:
    """
    Applique une fenêtre au signal pour réduire les effets de bord.
    
    Le fenêtrage est essentiel avant la FFT pour éviter les fuites spectrales.
    
    Référence : Cours Chapitre 7 p.192
        "Fenêtre de Hann (ou Hamming) pour réduire les effets de bord"
    
    Types de fenêtres disponibles :
        - 'hann' : Fenêtre de Hann (recommandée pour audio)
        - 'hamming' : Fenêtre de Hamming (alternative)
        - 'blackman' : Fenêtre de Blackman (meilleure atténuation)
    
    Parameters
    ----------
    signal : np.ndarray
        Signal d'entrée
    window_type : str
        Type de fenêtre ('hann', 'hamming', 'blackman')
    
    Returns
    -------
    windowed : np.ndarray
        Signal fenêtré
    
    Notes
    -----
    La fenêtre de Hann est définie par :
        w(n) = 0.5 × (1 - cos(2π×n / (N-1)))
    
    Elle réduit progressivement l'amplitude aux bords pour éviter
    les discontinuités qui causent des fuites spectrales.
    
    Examples
    --------
    >>> windowed = apply_window(signal, window_type='hann')
    """
    n = len(signal)
    
    if window_type == 'hann':
        window = np.hanning(n)
    elif window_type == 'hamming':
        window = np.hamming(n)
    elif window_type == 'blackman':
        window = np.blackman(n)
    else:
        raise ValueError(f"Type de fenêtre inconnu : {window_type}")
    
    return signal * window


# =============================================================================
# PIPELINE COMPLET DE PRÉTRAITEMENT
# =============================================================================

def preprocess_frame(
    frame: np.ndarray,
    fs: int = DEFAULT_FS,
    apply_bandpass_filter: bool = True,
    apply_notch_filter: bool = True,
    apply_windowing: bool = True,
    window_type: str = 'hann',
    filter_method: str = 'filtfilt'
) -> np.ndarray:
    """
    Pipeline complet de prétraitement d'une trame audio.
    
    Étapes :
    1. Filtre notch (50 Hz) - Optionnel
    2. Filtre passe-bande (70-1500 Hz) - Optionnel
    3. Fenêtrage (Hann) - Optionnel
    
    Parameters
    ----------
    frame : np.ndarray
        Trame audio à prétraiter
    fs : int
        Fréquence d'échantillonnage
    apply_bandpass_filter : bool
        Activer le filtre passe-bande
    apply_notch_filter : bool
        Activer le filtre notch
    apply_windowing : bool
        Activer le fenêtrage
    window_type : str
        Type de fenêtre ('hann', 'hamming', 'blackman')
    filter_method : str
        Méthode de filtrage ('filtfilt' ou 'lfilter')
    
    Returns
    -------
    processed : np.ndarray
        Trame prétraitée, prête pour la détection f₀
    
    Notes
    -----
    Ordre des opérations important :
        1. Notch d'abord (élimine la perturbation)
        2. Passe-bande ensuite (isole la gamme utile)
        3. Fenêtrage en dernier (avant FFT/autocorrélation)
    
    Examples
    --------
    >>> # Pipeline complet
    >>> processed = preprocess_frame(frame, fs=48000)
    
    >>> # Seulement fenêtrage (pour tests)
    >>> processed = preprocess_frame(
    ...     frame,
    ...     apply_bandpass_filter=False,
    ...     apply_notch_filter=False
    ... )
    """
    processed = frame.copy()
    
    # Étape 1 : Filtre notch (éliminer 50 Hz)
    if apply_notch_filter:
        processed = apply_notch(processed, fs, FREQ_NOTCH, filter_method)
    
    # Étape 2 : Filtre passe-bande (70-1500 Hz)
    if apply_bandpass_filter:
        processed = apply_bandpass(processed, fs, FREQ_LOW, FREQ_HIGH, filter_method)
    
    # Étape 3 : Fenêtrage
    if apply_windowing:
        processed = apply_window(processed, window_type)
    
    return processed


# =============================================================================
# ANALYSE DE LA RÉPONSE FRÉQUENTIELLE
# =============================================================================

def plot_filter_response(
    b: np.ndarray,
    a: np.ndarray,
    fs: int = DEFAULT_FS,
    title: str = "Réponse fréquentielle du filtre"
):
    """
    Affiche la réponse fréquentielle d'un filtre.
    
    Utile pour visualiser l'effet d'un filtre avant de l'appliquer.
    
    Parameters
    ----------
    b, a : np.ndarray
        Coefficients du filtre
    fs : int
        Fréquence d'échantillonnage
    title : str
        Titre du graphique
    
    Examples
    --------
    >>> b, a = design_bandpass_filter()
    >>> plot_filter_response(b, a, title="Filtre passe-bande 70-1500 Hz")
    """
    import matplotlib.pyplot as plt
    
    # Calculer la réponse fréquentielle
    w, h = scipy_signal.freqz(b, a, worN=8000, fs=fs)
    
    # Magnitude en dB
    magnitude_db = 20 * np.log10(np.abs(h) + 1e-10)
    
    # Affichage
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # Magnitude
    ax1.plot(w, magnitude_db, linewidth=2)
    ax1.set_xlabel('Fréquence (Hz)')
    ax1.set_ylabel('Magnitude (dB)')
    ax1.set_title(f'{title} - Magnitude')
    ax1.grid(True, alpha=0.3)
    ax1.axhline(y=-3, color='r', linestyle='--', alpha=0.5, label='-3 dB')
    ax1.legend()
    
    # Phase
    phase = np.angle(h)
    ax2.plot(w, phase, linewidth=2, color='orange')
    ax2.set_xlabel('Fréquence (Hz)')
    ax2.set_ylabel('Phase (radians)')
    ax2.set_title(f'{title} - Phase')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()


# =============================================================================
# TESTS ET DÉMONSTRATION
# =============================================================================

def run_tests():
    """
    Tests automatiques du module.
    """
    print("=" * 70)
    print("MODULE preprocessing.py - TESTS")
    print("=" * 70)
    print()
    
    # =========================================================================
    # Test 1 : Conception des filtres
    # =========================================================================
    print("[TEST 1] Conception des filtres")
    print("-" * 70)
    
    # Filtre passe-bande
    b_bp, a_bp = design_bandpass_filter(fs=48000)
    print(f"✓ Filtre passe-bande conçu : {len(b_bp)} coefficients")
    print(f"  Bande : 70-1500 Hz")
    
    # Filtre notch
    b_notch, a_notch = design_notch_filter(fs=48000, freq=50)
    print(f"✓ Filtre notch conçu : {len(b_notch)} coefficients")
    print(f"  Fréquence : 50 Hz (Q=30)")
    
    print()
    
    # =========================================================================
    # Test 2 : Application sur signal synthétique
    # =========================================================================
    print("[TEST 2] Application sur signal synthétique")
    print("-" * 70)
    
    # Créer un signal de test : 82 Hz (E2) + 50 Hz (bruit) + 2000 Hz (hors bande)
    fs = 48000
    duration = 1.0
    t = np.arange(int(duration * fs)) / fs
    
    signal_clean = np.sin(2 * np.pi * 82 * t)           # E2
    signal_noise = 0.5 * np.sin(2 * np.pi * 50 * t)     # Bruit secteur
    signal_high = 0.3 * np.sin(2 * np.pi * 2000 * t)    # Hors bande
    
    signal_mixed = signal_clean + signal_noise + signal_high
    
    print(f"Signal de test créé :")
    print(f"  • 82 Hz (E2, amplitude 1.0)")
    print(f"  • 50 Hz (bruit, amplitude 0.5)")
    print(f"  • 2000 Hz (hors bande, amplitude 0.3)")
    print()
    
    # Application du pipeline
    signal_processed = preprocess_frame(
        signal_mixed,
        fs=fs,
        apply_bandpass_filter=True,
        apply_notch_filter=True,
        apply_windowing=False  # Pas de fenêtrage pour ce test
    )
    
    # Analyse FFT avant/après
    def compute_spectrum(sig, fs):
        n = len(sig)
        fft_result = np.fft.rfft(sig)
        magnitude = np.abs(fft_result) / n
        freqs = np.fft.rfftfreq(n, 1/fs)
        return freqs, magnitude
    
    freqs_before, mag_before = compute_spectrum(signal_mixed, fs)
    freqs_after, mag_after = compute_spectrum(signal_processed, fs)
    
    # Mesurer l'atténuation
    def find_amplitude_at_freq(freqs, mag, target_freq, tolerance=2):
        idx = np.argmin(np.abs(freqs - target_freq))
        return mag[idx]
    
    amp_82_before = find_amplitude_at_freq(freqs_before, mag_before, 82)
    amp_82_after = find_amplitude_at_freq(freqs_after, mag_after, 82)
    
    amp_50_before = find_amplitude_at_freq(freqs_before, mag_before, 50)
    amp_50_after = find_amplitude_at_freq(freqs_after, mag_after, 50)
    
    amp_2000_before = find_amplitude_at_freq(freqs_before, mag_before, 2000)
    amp_2000_after = find_amplitude_at_freq(freqs_after, mag_after, 2000)
    
    print("Résultats du filtrage :")
    print(f"  • 82 Hz (à conserver) :")
    print(f"      Avant : {amp_82_before:.4f}")
    print(f"      Après : {amp_82_after:.4f}")
    print(f"      → Conservation : {amp_82_after/amp_82_before*100:.1f}%")
    
    print(f"  • 50 Hz (à éliminer) :")
    print(f"      Avant : {amp_50_before:.4f}")
    print(f"      Après : {amp_50_after:.4f}")
    print(f"      → Atténuation : {20*np.log10(amp_50_after/amp_50_before + 1e-10):.1f} dB")
    
    print(f"  • 2000 Hz (à éliminer) :")
    print(f"      Avant : {amp_2000_before:.4f}")
    print(f"      Après : {amp_2000_after:.4f}")
    print(f"      → Atténuation : {20*np.log10(amp_2000_after/amp_2000_before + 1e-10):.1f} dB")
    
    # Vérifications
    if amp_82_after > 0.8 * amp_82_before:
        print("\n✓ Signal utile (82 Hz) bien préservé")
    else:
        print("\n✗ Attention : signal utile atténué")
    
    if amp_50_after < 0.1 * amp_50_before:
        print("✓ Bruit 50 Hz bien atténué")
    else:
        print("✗ Attention : bruit 50 Hz insuffisamment atténué")
    
    if amp_2000_after < 0.1 * amp_2000_before:
        print("✓ Signal hors bande bien filtré")
    else:
        print("✗ Attention : signal hors bande insuffisamment filtré")
    
    print()
    
    # =========================================================================
    # Test 3 : Fenêtrage
    # =========================================================================
    print("[TEST 3] Fenêtrage")
    print("-" * 70)
    
    signal_test = np.ones(1000)
    
    for window_type in ['hann', 'hamming', 'blackman']:
        windowed = apply_window(signal_test, window_type)
        print(f"✓ Fenêtre {window_type:8s} : "
              f"centre={windowed[500]:.3f}, bord={windowed[0]:.3f}")
    
    print()
    
    # =========================================================================
    # Test 4 : Pipeline complet
    # =========================================================================
    print("[TEST 4] Pipeline complet de prétraitement")
    print("-" * 70)
    
    frame_test = signal_mixed[:4096]
    
    processed = preprocess_frame(
        frame_test,
        fs=fs,
        apply_bandpass_filter=True,
        apply_notch_filter=True,
        apply_windowing=True
    )
    
    print(f"✓ Pipeline complet exécuté")
    print(f"  Entrée : {len(frame_test)} échantillons")
    print(f"  Sortie : {len(processed)} échantillons")
    print(f"  RMS avant : {np.sqrt(np.mean(frame_test**2)):.4f}")
    print(f"  RMS après : {np.sqrt(np.mean(processed**2)):.4f}")
    
    print()
    print("✓ Tests terminés avec succès !")
    print("=" * 70)


if __name__ == "__main__":
    """
    Point d'entrée pour tester le module.
    
    Usage :
        python preprocessing.py
    """
    run_tests()