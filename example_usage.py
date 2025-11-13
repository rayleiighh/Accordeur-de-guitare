"""
Exemple d'utilisation du module signal_generation.py
=====================================================

Ce script montre comment générer et analyser des signaux de test
pour l'accordeur de guitare.

Auteur : Projet Signaux III - EPHEC
Date : Novembre 2025
"""

from src.signal_generation import *
import numpy as np

print("=" * 70)
print("EXEMPLES D'UTILISATION - signal_generation.py")
print("=" * 70)
print()

# =============================================================================
# Exemple 1 : Génération d'une sinusoïde pure
# =============================================================================
print("Exemple 1 : Génération d'une sinusoïde pure (La = 440 Hz)")
print("-" * 70)

signal_pure, time = generate_pure_sine(440.0, duration=1.0)
print(f"✓ Signal de {len(signal_pure)} échantillons généré")
print(f"✓ Durée : 1.0 seconde")
print(f"✓ Fréquence : 440 Hz (La standard)")
print()

# Analyse du signal
print("Visualisation de l'analyse complète...")
plot_signal_analysis(signal_pure, title="Sinusoïde pure - La (440 Hz)")
print()

# =============================================================================
# Exemple 2 : Simulation d'une corde de guitare réaliste
# =============================================================================
print("Exemple 2 : Simulation d'une corde de guitare (A2 = 110 Hz)")
print("-" * 70)

# Générer la corde A2 avec 8 harmoniques
signal_guitar, time = generate_guitar_string(
    fundamental_freq=110.0,
    duration=2.0,
    n_harmonics=8,
    decay_rate=0.3
)

print(f"✓ Signal de {len(signal_guitar)} échantillons généré")
print(f"✓ Fréquence fondamentale : 110 Hz")
print(f"✓ Nombre d'harmoniques : 8")
print(f"✓ Harmoniques présentes :")
for n in range(1, 9):
    print(f"   - {n}×110 Hz = {n*110} Hz (amplitude = 1/{n})")
print()

# Visualisation
print("Visualisation de l'analyse complète...")
plot_signal_analysis(signal_guitar, title="Corde A2 réaliste (110 Hz)")
print()

# =============================================================================
# Exemple 3 : Génération de cordes désaccordées
# =============================================================================
print("Exemple 3 : Génération de cordes désaccordées")
print("-" * 70)

# Générer la corde E2 dans 3 états
signal_low, _ = generate_detuned_string('E2', cents_offset=-50, duration=1.0)
signal_just, _ = generate_detuned_string('E2', cents_offset=0, duration=1.0)
signal_high, _ = generate_detuned_string('E2', cents_offset=+50, duration=1.0)

print("✓ E2 à -50 cents (trop bas) : ~80.06 Hz")
print("✓ E2 à   0 cents (juste)    :  82.41 Hz")
print("✓ E2 à +50 cents (trop haut): ~84.82 Hz")
print()

# Comparaison visuelle
print("Comparaison des 3 états d'accordage...")
plot_comparison(
    {
        'Trop bas (-50 cents)': signal_low[:2400],  # Zoom sur 50 ms
        'Juste (0 cents)': signal_just[:2400],
        'Trop haut (+50 cents)': signal_high[:2400]
    },
    title="E2 : Comparaison de 3 états d'accordage"
)
print()

# =============================================================================
# Exemple 4 : Ajout de bruit
# =============================================================================
print("Exemple 4 : Effet du bruit sur le signal")
print("-" * 70)

# Générer un signal propre
signal_clean, _ = generate_guitar_string(GUITAR_NOTES['D3'], duration=0.5)

# Ajouter différents niveaux de bruit
signal_snr30 = add_noise(signal_clean, snr_db=30)  # Bruit très faible
signal_snr20 = add_noise(signal_clean, snr_db=20)  # Bruit léger
signal_snr10 = add_noise(signal_clean, snr_db=10)  # Bruit modéré

print("✓ Signal propre généré")
print("✓ Ajout de bruit à SNR = 30 dB (très propre)")
print("✓ Ajout de bruit à SNR = 20 dB (léger)")
print("✓ Ajout de bruit à SNR = 10 dB (modéré)")
print()

# Comparaison
print("Comparaison de l'effet du bruit...")
plot_comparison(
    {
        'Signal propre': signal_clean[:2400],
        'SNR = 30 dB': signal_snr30[:2400],
        'SNR = 20 dB': signal_snr20[:2400],
        'SNR = 10 dB': signal_snr10[:2400]
    },
    title="Effet du bruit sur la corde D3"
)
print()

# =============================================================================
# Exemple 5 : Génération d'un dataset complet pour tests
# =============================================================================
print("Exemple 5 : Génération d'un dataset de validation")
print("-" * 70)

# Générer les 6 cordes dans 3 états (juste, -50c, +50c)
dataset = {}

for note_name in GUITAR_NOTES.keys():
    for cents in [-50, 0, +50]:
        key = f"{note_name}_{cents:+03d}c"
        signal, _ = generate_detuned_string(
            note_name,
            cents_offset=cents,
            duration=2.0
        )
        dataset[key] = signal
        
        freq = GUITAR_NOTES[note_name] * (2 ** (cents/1200))
        print(f"✓ {key:10s} : {freq:6.2f} Hz")

print()
print(f"✓ Dataset complet : {len(dataset)} signaux générés")
print(f"✓ Prêt pour tests de validation de l'algorithme de détection f₀")
print()

# =============================================================================
# Exemple 6 : Vérification du respect du théorème de Shannon
# =============================================================================
print("Exemple 6 : Vérification du critère de Nyquist")
print("-" * 70)

print(f"Fréquence d'échantillonnage : Fs = {FS} Hz")
print(f"Fréquence de Nyquist : fₙ = Fs/2 = {FS/2} Hz")
print()
print("Vérification pour chaque corde (avec 8 harmoniques) :")
print()

all_ok = True
for note, f0 in GUITAR_NOTES.items():
    fmax = f0 * 8  # 8ème harmonique
    margin = (FS/2) / fmax
    ok = margin > 1.0
    
    status = "✓" if ok else "✗"
    print(f"{status} {note:3s} : f₀={f0:6.2f} Hz, "
          f"fₘₐₓ={fmax:7.2f} Hz, "
          f"marge={margin:.1f}×")
    
    if not ok:
        all_ok = False

print()
if all_ok:
    print("✓ Toutes les fréquences respectent le critère de Nyquist")
    print("✓ Aucun repliement spectral (aliasing) attendu")
else:
    print("✗ ATTENTION : Certaines harmoniques dépassent la fréquence de Nyquist !")

print()
print("=" * 70)
print("FIN DES EXEMPLES")
print("=" * 70)