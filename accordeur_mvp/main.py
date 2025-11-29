"""
Accordeur de guitare numérique - Interface unifiée
==================================================

Application complète combinant l'analyse de fichiers WAV et l'enregistrement
en direct via microphone.

Références cours EPHEC - Signaux III :
- Chapitre 6 (p.165-166) : Théorème de Shannon-Nyquist → Justifie Fs = 48 kHz
- Chapitre 7 (p.184-188) : FFT Cooley-Tukey → Optimise calcul autocorrélation
- Chapitre 5 (p.156)     : Convolution → Principe du filtrage numérique

Extensions pratiques (hors cours) appliquées au projet :
- Autocorrélation : Application de la FFT pour détecter la périodicité du signal
- Filtre Butterworth passe-bande : Filtre standard en traitement audio
- Fenêtre de Hann : Réduction des effets de bord (pratique DSP)
- Interpolation parabolique : Améliore la précision de détection (sub-échantillon)

Architecture :
- Module pitch_detector : Détection f₀ par autocorrélation optimisée (FFT)
- Module music_utils : Conversions Hz ↔ Note + calcul cents
- Interface unifiée : 2 modes (enregistrement live + analyse fichiers WAV)

Usage :
    python main.py

Auteur : Projet Signaux III - EPHEC
Date : Novembre 2025
"""

import sys
import os
import numpy as np
import soundfile as sf
import sounddevice as sd
from datetime import datetime

# Ajouter src au path pour imports
sys.path.insert(0, 'src')

from src.pitch_detector import detect_f0, FS
from src.music_utils import identify_string, get_tuning_status


# =============================================================================
# CONSTANTES
# =============================================================================

# Paramètres d'enregistrement
# Reference: Course Chapter 6, p.165-166 (Shannon-Nyquist theorem: Fs >= 2*fmax)
# Justification: fmax_guitar ≈ 1500 Hz → Fs_min = 3000 Hz → 48 kHz (marge ×16)
SAMPLE_RATE = FS          # 48000 Hz
CHANNELS = 1              # Mono
DTYPE = 'float32'         # Type de données audio
FRAME_SIZE = 4096         # Taille fenêtre pour analyse (~85 ms à 48 kHz)
                          # Reference: Course Chapter 7, p.190 (time-freq resolution)


# =============================================================================
# MODE 1 : ENREGISTREMENT EN DIRECT (Méthode synchrone sd.rec)
# =============================================================================
# Note: Utilise sd.rec() au lieu de InputStream + callback
#       Plus simple, plus fiable, inspiré du code GUI qui fonctionne


def sauvegarder_enregistrement(signal, fs=SAMPLE_RATE, dossier='enregistrements'):
    """
    Sauvegarde l'enregistrement dans un fichier WAV avec timestamp.

    Parameters
    ----------
    signal : ndarray
        Signal audio à sauvegarder
    fs : int
        Fréquence d'échantillonnage
    dossier : str
        Dossier de destination (créé si inexistant)

    Returns
    -------
    filepath : str
        Chemin complet du fichier sauvegardé
    """
    # Créer le dossier s'il n'existe pas
    os.makedirs(dossier, exist_ok=True)

    # Nom du fichier avec timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"enreg_{timestamp}.wav"
    filepath = os.path.join(dossier, filename)

    # Sauvegarder au format WAV
    sf.write(filepath, signal, fs)

    return filepath


def analyser_enregistrement(signal, fs=SAMPLE_RATE, nom_fichier=None):
    """
    Analyse un signal enregistré et affiche les résultats d'accordage.

    Cette fonction découpe le signal en plusieurs fenêtres temporelles
    et applique la détection f₀ par autocorrélation sur chacune.

    Algorithm:
    1. Vérifier durée minimale (>= 4096 samples = 85 ms)
    2. Découper en N fenêtres uniformément espacées
    3. Pour chaque fenêtre:
       - Détection f₀ par autocorrélation (Chapter 7, p.195-197)
       - Identification de la corde la plus proche
       - Calcul écart en cents
    4. Calcul statistiques (MAE)

    Parameters
    ----------
    signal : ndarray
        Signal audio enregistré
    fs : int
        Fréquence d'échantillonnage
    nom_fichier : str, optional
        Nom du fichier si sauvegardé
    """
    print()
    print("=" * 60)
    print("📊 ANALYSE DE L'ENREGISTREMENT")
    print("=" * 60)
    print()

    # Informations sur l'enregistrement
    duree = len(signal) / fs
    print(f"   • Durée : {duree:.2f} s")
    print(f"   • Échantillons : {len(signal)}")
    print(f"   • Fréquence d'échantillonnage : {fs} Hz")

    # Vérifier qu'il y a assez de données
    # Minimum = FRAME_SIZE = 4096 échantillons (~85 ms à 48 kHz)
    # Reference: Course Chapter 7, p.190 (temporal resolution)
    if len(signal) < FRAME_SIZE:
        print()
        print(f"   ❌ Enregistrement trop court (minimum : {FRAME_SIZE/fs:.3f} s)")
        print("      Veuillez jouer la corde plus longtemps")
        return

    # Vérifier le niveau sonore (méthode optimisée)
    # Utilise la norme L2 (similaire à votre code qui fonctionne)
    niveau = np.linalg.norm(signal) * 10 / len(signal)
    rms = np.sqrt(np.mean(signal ** 2))
    print(f"   • Niveau RMS : {rms:.4f}")
    print(f"   • Niveau normalisé : {niveau:.4f}")

    # Seuil plus réaliste basé sur votre code qui fonctionne
    if niveau < 0.0005 or rms < 0.0001:
        print()
        print("   ⚠️  Signal très faible (presque silence) !")
        print("      Conseils :")
        print("      • Vérifiez que le BON micro est sélectionné")
        print("      • Jouez BEAUCOUP plus fort")
        print("      • Rapprochez le micro à 10-15 cm de la guitare")
        print()
        return  # Arrêter l'analyse si signal trop faible

    print()
    print("   Analyse de plusieurs fenêtres :")
    print()

    # Analyser plusieurs fenêtres pour robustesse
    # Maximum 5 fenêtres, espacées uniformément
    n_analyses = min(5, int(duree / 0.3))
    n_analyses = max(1, n_analyses)

    hop = len(signal) // (n_analyses + 1)
    results = []

    for i in range(1, n_analyses + 1):
        start = i * hop
        end = start + FRAME_SIZE

        if end > len(signal):
            break

        frame = signal[start:end]

        # Détection f₀ par autocorrélation
        # Reference: Course Chapter 7, p.195-197
        f0 = detect_f0(frame, fs=fs)

        if f0 is not None:
            # Identification de la corde
            note, cents = identify_string(f0)
            status = get_tuning_status(cents)

            # Symboles visuels
            status_symbol = {
                'juste': '✓',
                'trop_bas': '↓',
                'trop_haut': '↑'
            }[status]

            status_text = {
                'juste': 'JUSTE',
                'trop_bas': 'TROP_BAS',
                'trop_haut': 'TROP_HAUT'
            }[status]

            print(f"   Fenêtre {i} : {f0:6.2f} Hz → {note} "
                  f"({cents:+6.1f} cents) {status_symbol} {status_text}")

            results.append((f0, note, cents, status))
        else:
            print(f"   Fenêtre {i} : Aucune fréquence détectée")

    # Résumé statistique
    if results:
        print()
        cents_values = [abs(c) for _, _, c, _ in results]
        mean_abs_error = np.mean(cents_values)

        print(f"   📊 Erreur absolue moyenne (MAE) : {mean_abs_error:.2f} cents")

        # Évaluation qualité (seuil objectif: 10 cents)
        if mean_abs_error < 10:
            print(f"   ✓ EXCELLENT (objectif ≤ 10 cents atteint)")
        elif mean_abs_error < 20:
            print(f"   ✓ BON")
        else:
            print(f"   ⚠ À améliorer (serrez ou desserrez la corde)")

        # Note dominante (mode statistique)
        notes = [n for _, n, _, _ in results]
        note_dominante = max(set(notes), key=notes.count)
        print()
        print(f"   🎸 Note détectée : {note_dominante}")
    else:
        print()
        print("   ❌ Aucune fréquence détectée dans l'enregistrement")
        print("      Conseils :")
        print("      • Jouez une seule corde à la fois")
        print("      • Jouez plus fort")
        print("      • Rapprochez le micro de la guitare")

    print()

    if nom_fichier:
        print(f"   💾 Enregistrement sauvegardé : {nom_fichier}")
        print()


def mode_enregistrement():
    """
    Mode 1 : Enregistrement en direct via microphone.

    Workflow:
    1. Détection du micro par défaut
    2. Enregistrement déclenché par utilisateur (Entrée)
    3. Arrêt manuel (Entrée)
    4. Option sauvegarde WAV
    5. Analyse et affichage résultats
    """
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  MODE 1 : ENREGISTREMENT EN DIRECT".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    print("Enregistrez le son de votre guitare via le micro")
    print()
    print("=" * 60)
    print()

    # Détecter et afficher les micros disponibles
    device_id = None
    try:
        devices = sd.query_devices()
        input_devices = [(i, dev) for i, dev in enumerate(devices) if dev['max_input_channels'] > 0]

        if not input_devices:
            print("❌ Erreur : Aucun micro détecté")
            print()
            return

        print("🎤 Micros disponibles :")
        for i, dev in input_devices:
            marker = ""
            # Préférer les devices WASAPI sur Windows
            if 'wasapi' in dev['name'].lower():
                marker = " ⭐ (WASAPI - recommandé)"
                if device_id is None:
                    device_id = i
            print(f"   [{i}] {dev['name']}{marker}")

        # Si pas de WASAPI trouvé, utiliser le premier micro
        if device_id is None:
            device_id = input_devices[0][0]
            print(f"\n   → Micro par défaut sélectionné : ID {device_id}")
        else:
            print(f"\n   → Micro WASAPI auto-sélectionné : ID {device_id}")

        # Option pour changer de micro
        print()
        reponse = input("Utiliser un autre micro ? (Tapez le numéro, ou Entrée pour continuer) : ").strip()
        if reponse.isdigit():
            new_id = int(reponse)
            if any(i == new_id for i, _ in input_devices):
                device_id = new_id
                print(f"✓ Micro {device_id} sélectionné")
            else:
                print("⚠️  ID invalide, utilisation du micro par défaut")

        print()
    except Exception as e:
        print(f"❌ Erreur : Impossible de détecter le micro")
        print(f"   {e}")
        print()
        return

    # Configuration de l'enregistrement
    duree_enregistrement = 4  # secondes (assez pour capturer le son d'une corde)

    print("📝 INSTRUCTIONS :")
    print("   1. Appuyez sur Entrée pour DÉMARRER l'enregistrement")
    print(f"   2. Jouez UNE corde de guitare (enregistrement {duree_enregistrement}s)")
    print("   3. L'enregistrement s'arrêtera automatiquement")
    print()

    input("Appuyez sur Entrée pour démarrer l'enregistrement...")

    print()
    print("🔴 ENREGISTREMENT EN COURS...")
    print(f"   Jouez une corde maintenant ! ({duree_enregistrement}s)")
    print()

    # Enregistrement synchrone (bloquant) - MÉTHODE SIMPLE QUI FONCTIONNE
    try:
        n_samples = int(duree_enregistrement * SAMPLE_RATE)
        recording = sd.rec(
            n_samples,
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype='float64',
            device=device_id  # KEY FIX: Device explicite
        )
        sd.wait()  # Attendre la fin de l'enregistrement

        # Convertir en 1D si nécessaire
        if recording.ndim == 2:
            signal = recording[:, 0]
        else:
            signal = recording

        print("⏹️  Enregistrement terminé !")
        print()

    except Exception as e:
        print(f"❌ Erreur lors de l'enregistrement : {e}")
        print()
        return

    if len(signal) == 0:
        print("❌ Aucun signal enregistré")
        return

    duree = len(signal) / SAMPLE_RATE
    print(f"✓ Enregistrement terminé ({duree:.2f} secondes)")

    # Demander si on sauvegarde
    print()
    reponse = input("Sauvegarder l'enregistrement ? (o/n) : ").strip().lower()

    nom_fichier = None
    if reponse in ['o', 'oui', 'y', 'yes']:
        nom_fichier = sauvegarder_enregistrement(signal, SAMPLE_RATE)
        print(f"✓ Sauvegardé : {nom_fichier}")

    # Analyser l'enregistrement
    analyser_enregistrement(signal, SAMPLE_RATE, nom_fichier)


# =============================================================================
# MODE 2 : ANALYSE DE FICHIERS WAV
# =============================================================================

def analyser_fichier(filepath):
    """
    Analyse un fichier audio WAV et affiche le résultat d'accordage.

    Cette fonction charge un fichier WAV existant et applique le même
    pipeline d'analyse que pour l'enregistrement en direct.

    Algorithm:
    1. Charger fichier WAV (mono ou stéréo)
    2. Convertir en mono si nécessaire
    3. Découper en N fenêtres uniformément espacées
    4. Pour chaque fenêtre:
       - Détection f₀ par autocorrélation (Chapter 7, p.195-197)
       - Identification de la corde
       - Calcul écart en cents
    5. Calcul statistiques (MAE)

    Parameters
    ----------
    filepath : str
        Chemin vers le fichier WAV
    """
    print(f"\n📁 Fichier : {os.path.basename(filepath)}")
    print("-" * 60)

    try:
        # Charger le fichier WAV
        signal, fs = sf.read(filepath)

        # Convertir en mono si stéréo
        if signal.ndim == 2:
            signal = np.mean(signal, axis=1)

        print(f"   • Durée : {len(signal)/fs:.2f} s")
        print(f"   • Fréquence d'échantillonnage : {fs} Hz")

        # Analyser plusieurs fenêtres pour robustesse
        n_analyses = 3
        hop = len(signal) // (n_analyses + 1)

        print(f"\n   Analyse de {n_analyses} fenêtres :")
        print()

        results = []

        for i in range(1, n_analyses + 1):
            start = i * hop
            frame = signal[start:start + FRAME_SIZE]

            # Détection f₀ par autocorrélation
            # Reference: Course Chapter 7, p.195-197
            f0 = detect_f0(frame, fs=fs)

            if f0 is not None:
                # Identification de la corde la plus proche
                note, cents = identify_string(f0)
                status = get_tuning_status(cents)

                # Affichage
                status_symbol = {
                    'juste': '✓',
                    'trop_bas': '↓',
                    'trop_haut': '↑'
                }[status]

                print(f"   Fenêtre {i} : {f0:6.2f} Hz → {note} "
                      f"({cents:+6.1f} cents) {status_symbol} {status.upper()}")

                results.append((f0, note, cents, status))
            else:
                print(f"   Fenêtre {i} : Aucune fréquence détectée")

        # Résumé statistique (MAE)
        if results:
            print()
            cents_values = [abs(c) for _, _, c, _ in results]
            mean_abs_error = np.mean(cents_values)

            print(f"   📊 Erreur absolue moyenne (MAE) : {mean_abs_error:.2f} cents")

            # Évaluation qualité (objectif: ≤10 cents)
            if mean_abs_error < 10:
                print(f"   ✓ EXCELLENT (objectif ≤ 10 cents atteint)")
            elif mean_abs_error < 20:
                print(f"   ✓ BON")
            else:
                print(f"   ⚠ À améliorer")

    except FileNotFoundError:
        print(f"   ✗ Fichier introuvable")
    except Exception as e:
        print(f"   ✗ Erreur : {e}")


def afficher_menu_fichiers(fichiers_wav):
    """
    Affiche le menu de sélection des fichiers WAV disponibles.

    Parameters
    ----------
    fichiers_wav : list of str
        Liste des chemins complets vers les fichiers WAV

    Returns
    -------
    choix : int or None
        - None : Quitter
        - -1 : Analyser tous les fichiers
        - i >= 0 : Index du fichier à analyser
    """
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  MENU DE SÉLECTION".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "═" * 58 + "╝")
    print()

    if not fichiers_wav:
        print("❌ Aucun fichier WAV trouvé dans data/raw/")
        return None

    print("Fichiers disponibles :")
    print()

    for i, filepath in enumerate(fichiers_wav, 1):
        filename = os.path.basename(filepath)
        print(f"  {i}. {filename}")

    print(f"  {len(fichiers_wav) + 1}. Analyser TOUS les fichiers")
    print(f"  0. Quitter")
    print()

    # Boucle de saisie avec validation
    while True:
        try:
            choix_str = input("Votre choix : ").strip()
            choix = int(choix_str)

            if choix == 0:
                return None
            elif choix == len(fichiers_wav) + 1:
                return -1  # Code pour "tous les fichiers"
            elif 1 <= choix <= len(fichiers_wav):
                return choix - 1  # Index du fichier (0-based)
            else:
                print(f"❌ Choix invalide. Entrez un nombre entre 0 et {len(fichiers_wav) + 1}")
        except ValueError:
            print("❌ Veuillez entrer un nombre valide")
        except KeyboardInterrupt:
            print("\n\n⚠️  Interruption par l'utilisateur")
            return None


def mode_fichiers():
    """
    Mode 2 : Analyse de fichiers WAV existants.

    Workflow:
    1. Scan automatique du dossier data/raw/ pour fichiers .wav
    2. Affichage menu de sélection
    3. Choix utilisateur : un fichier / tous / quitter
    4. Analyse et affichage résultats
    """
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  MODE 2 : ANALYSE DE FICHIERS WAV".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    print("Analysez des enregistrements audio existants")
    print()
    print("=" * 60)

    # Détecter automatiquement les fichiers WAV dans data/raw/
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, 'data', 'raw')

    # Scanner le dossier pour les fichiers .wav
    if os.path.exists(data_dir):
        fichiers_wav = sorted([
            os.path.join(data_dir, f)
            for f in os.listdir(data_dir)
            if f.lower().endswith('.wav')
        ])
    else:
        print()
        print(f"❌ Dossier introuvable : {data_dir}")
        print("   Veuillez créer le dossier data/raw/ et y placer vos fichiers WAV")
        print()
        return

    # Afficher le menu de sélection
    choix = afficher_menu_fichiers(fichiers_wav)

    if choix is None:
        print("\n👋 Retour au menu principal")
        return

    print("\n" + "=" * 60)

    # Analyser selon le choix
    if choix == -1:
        # Analyser tous les fichiers
        print("\n📊 Analyse de TOUS les fichiers :")
        for filepath in fichiers_wav:
            analyser_fichier(filepath)
    else:
        # Analyser un seul fichier
        analyser_fichier(fichiers_wav[choix])

    print()
    print("=" * 60)
    print("✓ ANALYSE TERMINÉE")
    print("=" * 60)
    print()


# =============================================================================
# MENU PRINCIPAL
# =============================================================================

def afficher_menu_principal():
    """
    Affiche le menu principal de l'application.

    Returns
    -------
    choix : int or None
        1 : Mode enregistrement
        2 : Mode fichiers
        0 ou None : Quitter
    """
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  ACCORDEUR DE GUITARE NUMÉRIQUE".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    print("Détection de fréquence fondamentale par autocorrélation")
    print("Cours : Signaux III - EPHEC")
    print()
    print("Références académiques :")
    print("  • Chap. 6 p.165 : Shannon-Nyquist → Fs = 48 kHz")
    print("  • Chap. 7 p.184 : FFT Cooley-Tukey → Optimisation ACF")
    print("  • Chap. 5 p.156 : Convolution → Principe filtrage")
    print()
    print("Extensions pratiques (hors cours) :")
    print("  • Autocorrélation via FFT pour périodicité")
    print("  • Butterworth passe-bande (70-1500 Hz)")
    print()
    print("=" * 60)
    print()
    print("  1. Enregistrer avec le micro")
    print("  2. Charger un fichier WAV")
    print("  0. Quitter")
    print()

    while True:
        try:
            choix_str = input("Votre choix : ").strip()
            choix = int(choix_str)

            if choix in [0, 1, 2]:
                return choix
            else:
                print("❌ Choix invalide. Entrez 0, 1 ou 2")
        except ValueError:
            print("❌ Veuillez entrer un nombre valide")
        except KeyboardInterrupt:
            print("\n\n⚠️  Interruption par l'utilisateur")
            return 0


def main():
    """
    Fonction principale : boucle sur le menu principal.

    Architecture:
    - Menu principal avec 2 modes + quitter
    - Mode 1 : Enregistrement microphone temps réel
    - Mode 2 : Analyse fichiers WAV existants
    - Boucle jusqu'à choix "Quitter"

    Technical details:
    - Autocorrelation-based pitch detection (Chapter 7, p.195-197)
    - Butterworth bandpass filter 70-1500 Hz (Chapter 5, p.150)
    - Sampling rate: 48 kHz (Shannon-Nyquist, Chapter 6, p.166)
    - Window size: 4096 samples → Δf = 11.7 Hz resolution (Chapter 7, p.190)
    """
    while True:
        choix = afficher_menu_principal()

        if choix == 0:
            # Quitter
            print()
            print("=" * 60)
            print("👋 Au revoir !")
            print("=" * 60)
            print()
            break

        elif choix == 1:
            # Mode enregistrement
            try:
                mode_enregistrement()
            except Exception as e:
                print(f"\n❌ Erreur dans le mode enregistrement : {e}\n")

            # Pause avant retour au menu
            print()
            input("Appuyez sur Entrée pour revenir au menu principal...")

        elif choix == 2:
            # Mode fichiers
            try:
                mode_fichiers()
            except Exception as e:
                print(f"\n❌ Erreur dans le mode fichiers : {e}\n")

            # Pause avant retour au menu
            print()
            input("Appuyez sur Entrée pour revenir au menu principal...")


# =============================================================================
# POINT D'ENTRÉE
# =============================================================================

if __name__ == "__main__":
    main()
