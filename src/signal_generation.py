"""
Module de génération de signaux synthétiques pour accordeur de guitare
========================================================================

Ce module permet de générer des signaux de test pour valider les algorithmes
de détection de fréquence fondamentale (f₀).

Références au cours EPHEC - Signaux III :
------------------------------------------
- Chapitre 1 : Représentation des signaux analogiques (p.11-19)
- Chapitre 2 : Transformée de Fourier (p.38-57)
- Chapitre 6 : Échantillonnage (p.166-177)
- Chapitre 7 : Analyse spectrale (p.188-202)

Auteur : Projet Signaux III - EPHEC
Date : Novembre 2025
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Tuple, Optional
from scipy import signal as scipy_signal


# =============================================================================
# CONSTANTES GLOBALES
# =============================================================================

# Fréquences des 6 cordes de guitare en accord standard
# Référence : Chapitre 2 p.190 (gammes musicales)
GUITAR_NOTES = {
    'E2': 82.41,   # 6ème corde (la plus grave)
    'A2': 110.00,  # 5ème corde
    'D3': 146.83,  # 4ème corde
    'G3': 196.00,  # 3ème corde
    'B3': 246.94,  # 2ème corde
    'E4': 329.63   # 1ère corde (la plus aiguë)
}

# Paramètres d'échantillonnage
# Référence : Chapitre 6 p.166-167 (Théorème de Shannon-Nyquist)
FS = 48000  # Fréquence d'échantillonnage (Hz)
            # Justification : FS >> 2 × fmax (Shannon-Nyquist)
            # fmax ≈ 1500 Hz (corde E4 + harmoniques) → FS/2 = 24000 Hz >> 1500 Hz

TE = 1 / FS  # Période d'échantillonnage (s) ≈ 20.83 μs


# =============================================================================
# GÉNÉRATION DE SIGNAUX DE BASE
# =============================================================================

def generate_pure_sine(
    frequency: float,
    duration: float = 2.0,
    amplitude: float = 1.0,
    fs: int = FS
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Génère une sinusoïde pure.
    
    Formule mathématique (Chapitre 2 p.38) :
        s(t) = A × cos(2π × f₀ × t)
    
    Chapitre 1 p.16-17 : Signal à puissance moyenne finie
        P_moy = A²/2 (pour une sinusoïde)
    
    Parameters
    ----------
    frequency : float
        Fréquence fondamentale en Hz
    duration : float, optional
        Durée du signal en secondes (défaut: 2.0)
    amplitude : float, optional
        Amplitude du signal (défaut: 1.0)
    fs : int, optional
        Fréquence d'échantillonnage en Hz (défaut: 48000)
    
    Returns
    -------
    signal : np.ndarray
        Signal généré
    time : np.ndarray
        Axe temporel correspondant
    
    Examples
    --------
    >>> signal, time = generate_pure_sine(440.0, duration=1.0)
    >>> print(f"Signal de {len(signal)} échantillons à {440.0} Hz")
    """
    # Génération de l'axe temporel
    # Chapitre 6 p.167 : échantillonnage uniforme avec Te = 1/Fs
    n_samples = int(duration * fs)
    time = np.arange(n_samples) / fs  # t = n × Te
    
    # Génération du signal sinusoïdal
    # Chapitre 2 p.38 : forme générale cos(2πf₀t)
    signal = amplitude * np.cos(2 * np.pi * frequency * time)
    
    return signal, time


def generate_guitar_string(
    fundamental_freq: float,
    duration: float = 2.0,
    n_harmonics: int = 8,
    decay_rate: float = 0.3,
    fs: int = FS
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Génère un signal réaliste de corde de guitare avec harmoniques et décroissance.
    
    Modèle physique simplifié :
    - Fréquence fondamentale f₀
    - Harmoniques à 2f₀, 3f₀, ..., nf₀ (Chapitre 2 p.38-41)
    - Enveloppe exponentielle décroissante (réalisme acoustique)
    
    Référence : Chapitre 2 p.38
        "Les coefficients a₁ et b₁ représentent la fréquence fondamentale
         et les coefficients aₙ et bₙ représentent les harmoniques."
    
    Parameters
    ----------
    fundamental_freq : float
        Fréquence fondamentale (f₀) en Hz
    duration : float, optional
        Durée du signal en secondes (défaut: 2.0)
    n_harmonics : int, optional
        Nombre d'harmoniques à inclure (défaut: 8)
    decay_rate : float, optional
        Taux de décroissance exponentielle (défaut: 0.3)
    fs : int, optional
        Fréquence d'échantillonnage en Hz (défaut: 48000)
    
    Returns
    -------
    signal : np.ndarray
        Signal généré avec harmoniques
    time : np.ndarray
        Axe temporel correspondant
    
    Examples
    --------
    >>> # Générer la corde A2 (110 Hz) avec harmoniques
    >>> signal, time = generate_guitar_string(110.0, n_harmonics=8)
    """
    n_samples = int(duration * fs)
    time = np.arange(n_samples) / fs
    
    # Initialisation du signal
    signal = np.zeros(n_samples)
    
    # Ajout de la fondamentale et des harmoniques
    # Chapitre 2 p.38 : Série de Fourier avec harmoniques à n×f₀
    for n in range(1, n_harmonics + 1):
        # Fréquence de l'harmonique n
        freq_n = n * fundamental_freq
        
        # Amplitude décroissante : 1/n (approximation physique)
        # Les harmoniques supérieures ont moins d'énergie
        amplitude_n = 1.0 / n
        
        # Ajout de l'harmonique au signal
        signal += amplitude_n * np.cos(2 * np.pi * freq_n * time)
    
    # Normalisation pour éviter le clipping
    signal = signal / np.max(np.abs(signal))
    
    # Application d'une enveloppe exponentielle décroissante
    # Chapitre 1 p.14-17 : Signal à énergie finie (note de guitare transitoire)
    envelope = np.exp(-decay_rate * time)
    signal = signal * envelope
    
    return signal, time


def generate_detuned_string(
    note_name: str,
    cents_offset: float,
    duration: float = 2.0,
    n_harmonics: int = 8,
    fs: int = FS
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Génère un signal de corde désaccordée (avec décalage en cents).
    
    Formule de conversion cents → ratio de fréquence :
        f_detuned = f₀ × 2^(cents/1200)
    
    Référence musicale :
        - 100 cents = 1 demi-ton
        - 1 octave = 12 demi-tons = 1200 cents
        - Chapitre 2 p.190 : système tempéré avec 2^(1/12)
    
    Parameters
    ----------
    note_name : str
        Nom de la note ('E2', 'A2', 'D3', 'G3', 'B3', 'E4')
    cents_offset : float
        Décalage en cents (ex: -50 = trop bas, +50 = trop haut)
    duration : float, optional
        Durée du signal en secondes (défaut: 2.0)
    n_harmonics : int, optional
        Nombre d'harmoniques (défaut: 8)
    fs : int, optional
        Fréquence d'échantillonnage (défaut: 48000)
    
    Returns
    -------
    signal : np.ndarray
        Signal désaccordé
    time : np.ndarray
        Axe temporel
    
    Examples
    --------
    >>> # Générer la corde E2 désaccordée de -50 cents
    >>> signal, time = generate_detuned_string('E2', cents_offset=-50)
    """
    # Récupérer la fréquence de base
    if note_name not in GUITAR_NOTES:
        raise ValueError(f"Note inconnue : {note_name}. "
                        f"Notes disponibles : {list(GUITAR_NOTES.keys())}")
    
    f0 = GUITAR_NOTES[note_name]
    
    # Calcul de la fréquence désaccordée
    # Formule : f_detuned = f₀ × 2^(cents/1200)
    f_detuned = f0 * (2 ** (cents_offset / 1200.0))
    
    # Génération du signal
    signal, time = generate_guitar_string(
        f_detuned,
        duration=duration,
        n_harmonics=n_harmonics,
        fs=fs
    )
    
    return signal, time


# =============================================================================
# AJOUT DE BRUIT
# =============================================================================

def add_noise(
    signal: np.ndarray,
    snr_db: float = 20.0
) -> np.ndarray:
    """
    Ajoute du bruit blanc gaussien à un signal.
    
    Le rapport signal sur bruit (SNR) est défini par :
        SNR_dB = 10 × log₁₀(P_signal / P_noise)
    
    Référence : Chapitre 1 p.14-15 (Puissance moyenne)
        P_moy = (1/T) × ∫ s²(t) dt
    
    Parameters
    ----------
    signal : np.ndarray
        Signal d'entrée
    snr_db : float, optional
        Rapport signal/bruit en dB (défaut: 20 dB)
        - 30 dB : très peu de bruit
        - 20 dB : bruit léger
        - 10 dB : bruit modéré
        - 5 dB : bruit important
    
    Returns
    -------
    noisy_signal : np.ndarray
        Signal bruité
    
    Examples
    --------
    >>> signal, _ = generate_pure_sine(440.0)
    >>> noisy = add_noise(signal, snr_db=15)
    """
    # Calcul de la puissance du signal
    signal_power = np.mean(signal ** 2)
    
    # Calcul de la puissance du bruit souhaitée
    # SNR_dB = 10 log₁₀(P_signal / P_noise)
    # → P_noise = P_signal / 10^(SNR_dB/10)
    noise_power = signal_power / (10 ** (snr_db / 10))
    
    # Génération du bruit blanc gaussien
    # Chapitre 1 p.11 : bruit = signal aléatoire
    noise = np.random.normal(0, np.sqrt(noise_power), size=signal.shape)
    
    # Addition du bruit au signal
    noisy_signal = signal + noise
    
    return noisy_signal


# =============================================================================
# FENÊTRAGE
# =============================================================================

def apply_window(
    signal: np.ndarray,
    window_type: str = 'hann',
    window_size: Optional[int] = None
) -> np.ndarray:
    """
    Applique une fenêtre au signal.
    
    Référence : Chapitre 7 p.192
        "Fenêtre de Hann (ou Hamming) pour réduire les effets de bord"
    
    Parameters
    ----------
    signal : np.ndarray
        Signal d'entrée
    window_type : str, optional
        Type de fenêtre ('hann', 'hamming', 'blackman') (défaut: 'hann')
    window_size : int, optional
        Taille de la fenêtre. Si None, utilise len(signal)
    
    Returns
    -------
    windowed_signal : np.ndarray
        Signal fenêtré
    
    Examples
    --------
    >>> signal, _ = generate_pure_sine(440.0, duration=0.1)
    >>> windowed = apply_window(signal, window_type='hann')
    """
    if window_size is None:
        window_size = len(signal)
    
    # Génération de la fenêtre
    if window_type == 'hann':
        window = np.hanning(window_size)
    elif window_type == 'hamming':
        window = np.hamming(window_size)
    elif window_type == 'blackman':
        window = np.blackman(window_size)
    else:
        raise ValueError(f"Type de fenêtre inconnu : {window_type}")
    
    # Application de la fenêtre
    # Si le signal est plus long que la fenêtre, on ne fenêtre que le début
    if len(signal) >= window_size:
        windowed_signal = signal.copy()
        windowed_signal[:window_size] *= window
    else:
        windowed_signal = signal * window[:len(signal)]
    
    return windowed_signal


# =============================================================================
# VISUALISATION
# =============================================================================

def plot_signal_analysis(
    signal: np.ndarray,
    fs: int = FS,
    title: str = "Analyse du signal",
    figsize: Tuple[int, int] = (14, 10)
) -> None:
    """
    Affiche une analyse complète du signal (temporel, FFT, spectrogramme).
    
    Références au cours :
    - Chapitre 2 p.51 : Transformée de Fourier
    - Chapitre 7 p.188-191 : FFT et spectrogramme
    
    Parameters
    ----------
    signal : np.ndarray
        Signal à analyser
    fs : int, optional
        Fréquence d'échantillonnage (défaut: 48000)
    title : str, optional
        Titre du graphique
    figsize : tuple, optional
        Taille de la figure (défaut: (14, 10))
    
    Examples
    --------
    >>> signal, _ = generate_guitar_string(110.0)
    >>> plot_signal_analysis(signal, title="Corde A2")
    """
    fig, axes = plt.subplots(3, 1, figsize=figsize)
    
    # Axe temporel
    time = np.arange(len(signal)) / fs
    
    # =========================
    # 1. Signal temporel
    # =========================
    # Référence : Chapitre 1 p.11-19 (représentation temporelle)
    axes[0].plot(time, signal, linewidth=0.5)
    axes[0].set_xlabel('Temps (s)')
    axes[0].set_ylabel('Amplitude')
    axes[0].set_title(f'{title} - Domaine temporel')
    axes[0].grid(True, alpha=0.3)
    axes[0].set_xlim([0, min(0.1, time[-1])])  # Zoom sur 100 ms
    
    # =========================
    # 2. Spectre de Fourier (FFT)
    # =========================
    # Référence : Chapitre 7 p.188
    # "La FFT (Fast Fourier Transform) est un algorithme rapide pour calculer la TFD"
    
    # Calcul de la FFT
    N = len(signal)
    fft_result = np.fft.fft(signal)
    fft_magnitude = np.abs(fft_result)
    
    # Axe des fréquences (Chapitre 7 p.188)
    # freqs = k × Fs / N, où k = 0, 1, ..., N-1
    freqs = np.fft.fftfreq(N, 1/fs)
    
    # Spectre unilatéral (fréquences positives uniquement)
    # Référence : Chapitre 2 p.45-46 (spectre bilatéral vs unilatéral)
    positive_freqs = freqs[:N//2]
    positive_magnitude = fft_magnitude[:N//2]
    
    axes[1].plot(positive_freqs, positive_magnitude)
    axes[1].set_xlabel('Fréquence (Hz)')
    axes[1].set_ylabel('Magnitude')
    axes[1].set_title(f'{title} - Spectre de Fourier (FFT)')
    axes[1].grid(True, alpha=0.3)
    axes[1].set_xlim([0, 1500])  # Bande utile pour la guitare
    
    # =========================
    # 3. Spectrogramme
    # =========================
    # Référence : Chapitre 7 p.191
    # "Le spectrogramme montre l'évolution du spectre dans le temps"
    
    # Paramètres du spectrogramme (Chapitre 7 p.199-200)
    nperseg = 1024  # Taille de fenêtre pour STFT
    noverlap = nperseg // 2  # Chevauchement de 50%
    
    f, t, Sxx = scipy_signal.spectrogram(
        signal,
        fs=fs,
        nperseg=nperseg,
        noverlap=noverlap
    )
    
    # Affichage en échelle logarithmique (dB)
    Sxx_db = 10 * np.log10(Sxx + 1e-10)  # +epsilon pour éviter log(0)
    
    im = axes[2].pcolormesh(t, f, Sxx_db, shading='gouraud', cmap='viridis')
    axes[2].set_ylabel('Fréquence (Hz)')
    axes[2].set_xlabel('Temps (s)')
    axes[2].set_title(f'{title} - Spectrogramme')
    axes[2].set_ylim([0, 1500])
    plt.colorbar(im, ax=axes[2], label='Magnitude (dB)')
    
    plt.tight_layout()
    plt.show()


def plot_comparison(
    signals_dict: dict,
    fs: int = FS,
    title: str = "Comparaison de signaux"
) -> None:
    """
    Compare plusieurs signaux dans le domaine temporel.
    
    Parameters
    ----------
    signals_dict : dict
        Dictionnaire {label: signal}
    fs : int, optional
        Fréquence d'échantillonnage
    title : str, optional
        Titre du graphique
    
    Examples
    --------
    >>> sig1, _ = generate_pure_sine(440.0, duration=0.05)
    >>> sig2, _ = generate_guitar_string(440.0, duration=0.05)
    >>> plot_comparison({'Sinusoïde pure': sig1, 'Avec harmoniques': sig2})
    """
    plt.figure(figsize=(12, 6))
    
    for label, sig in signals_dict.items():
        time = np.arange(len(sig)) / fs
        plt.plot(time, sig, label=label, alpha=0.7)
    
    plt.xlabel('Temps (s)')
    plt.ylabel('Amplitude')
    plt.title(title)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()


# =============================================================================
# TESTS ET DÉMONSTRATION
# =============================================================================

def run_tests():
    """
    Exécute une série de tests pour vérifier le bon fonctionnement du module.
    
    Cette fonction génère divers signaux et affiche leurs caractéristiques
    pour validation visuelle et vérification des paramètres.
    """
    print("=" * 70)
    print("MODULE signal_generation.py - TESTS")
    print("=" * 70)
    print()
    
    # =========================================================================
    # Test 1 : Sinusoïde pure
    # =========================================================================
    print("[TEST 1] Génération d'une sinusoïde pure (A4 = 440 Hz)")
    print("-" * 70)
    
    sig_pure, time = generate_pure_sine(440.0, duration=1.0)
    
    print(f"✓ Signal généré : {len(sig_pure)} échantillons")
    print(f"✓ Durée : {len(sig_pure)/FS:.3f} s")
    print(f"✓ Amplitude max : {np.max(np.abs(sig_pure)):.3f}")
    print(f"✓ Puissance moyenne : {np.mean(sig_pure**2):.3f}")
    print()
    
    # =========================================================================
    # Test 2 : Corde de guitare avec harmoniques
    # =========================================================================
    print("[TEST 2] Génération d'une corde de guitare (E2 = 82.41 Hz)")
    print("-" * 70)
    
    sig_guitar, time = generate_guitar_string(GUITAR_NOTES['E2'], duration=2.0)
    
    print(f"✓ Signal généré : {len(sig_guitar)} échantillons")
    print(f"✓ Harmoniques : 8 (82 Hz, 164 Hz, 247 Hz, ...)")
    print(f"✓ Enveloppe : décroissance exponentielle")
    print()
    
    # =========================================================================
    # Test 3 : Cordes désaccordées
    # =========================================================================
    print("[TEST 3] Génération de cordes désaccordées")
    print("-" * 70)
    
    for note in ['E2', 'A2', 'E4']:
        for cents in [-50, 0, +50]:
            sig, _ = generate_detuned_string(note, cents, duration=0.5)
            f_expected = GUITAR_NOTES[note] * (2 ** (cents/1200))
            print(f"✓ {note:3s} {cents:+3d} cents → {f_expected:6.2f} Hz")
    print()
    
    # =========================================================================
    # Test 4 : Ajout de bruit
    # =========================================================================
    print("[TEST 4] Ajout de bruit blanc gaussien")
    print("-" * 70)
    
    sig_clean, _ = generate_pure_sine(440.0, duration=0.1)
    
    for snr in [30, 20, 10, 5]:
        sig_noisy = add_noise(sig_clean, snr_db=snr)
        noise_actual = sig_noisy - sig_clean
        snr_measured = 10 * np.log10(
            np.mean(sig_clean**2) / np.mean(noise_actual**2)
        )
        print(f"✓ SNR cible = {snr:2d} dB → SNR mesuré = {snr_measured:.1f} dB")
    print()
    
    # =========================================================================
    # Test 5 : Vérification du théorème de Shannon
    # =========================================================================
    print("[TEST 5] Vérification du théorème de Shannon-Nyquist")
    print("-" * 70)
    print(f"Fréquence d'échantillonnage : Fs = {FS} Hz")
    print(f"Fréquence de Nyquist : Fs/2 = {FS/2} Hz")
    print()
    
    for note, freq in GUITAR_NOTES.items():
        freq_max_harmonic = freq * 8  # 8ème harmonique
        nyquist_ok = freq_max_harmonic < (FS / 2)
        status = "✓" if nyquist_ok else "✗"
        print(f"{status} {note:3s} : f₀={freq:6.2f} Hz, "
              f"8ème harm.={freq_max_harmonic:7.2f} Hz")
    print()
    
    # =========================================================================
    # Génération des graphiques de démonstration
    # =========================================================================
    print("[VISUALISATION] Génération des graphiques...")
    print("-" * 70)
    
    # Graphique 1 : Analyse complète d'une corde
    sig_demo, _ = generate_guitar_string(GUITAR_NOTES['A2'], duration=2.0)
    plot_signal_analysis(sig_demo, title="Corde A2 (110 Hz) avec harmoniques")
    
    # Graphique 2 : Comparaison sinusoïde pure vs avec harmoniques
    sig1, _ = generate_pure_sine(110.0, duration=0.05)
    sig2, _ = generate_guitar_string(110.0, duration=0.05)
    plot_comparison(
        {
            'Sinusoïde pure (f₀ = 110 Hz)': sig1,
            'Avec harmoniques (réaliste)': sig2
        },
        title="Comparaison : sinusoïde pure vs corde réaliste"
    )
    
    # Graphique 3 : Effet du bruit
    sig_clean, _ = generate_guitar_string(GUITAR_NOTES['E2'], duration=0.1)
    sig_noisy_20 = add_noise(sig_clean, snr_db=20)
    sig_noisy_10 = add_noise(sig_clean, snr_db=10)
    
    plot_comparison(
        {
            'Signal propre': sig_clean,
            'SNR = 20 dB': sig_noisy_20,
            'SNR = 10 dB': sig_noisy_10
        },
        title="Effet du bruit sur le signal"
    )
    
    print("\n✓ Tests terminés avec succès !")
    print("=" * 70)


# =============================================================================
# POINT D'ENTRÉE PRINCIPAL
# =============================================================================

if __name__ == "__main__":
    """
    Point d'entrée pour tester le module.
    
    Usage :
        python signal_generation.py
    """
    run_tests()