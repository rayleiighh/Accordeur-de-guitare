"""
Script de vérification rapide - Accordeur de guitare
====================================================

Vérifie que tout est correctement installé et configuré avant la présentation.

Usage :
    python test_setup.py

Auteur : Projet Signaux III - EPHEC
Date : Novembre 2025
"""

import sys
from pathlib import Path

def test_imports():
    """Vérifie que tous les modules nécessaires sont installés."""
    print("🔍 TEST 1/5 : Vérification des imports...")

    try:
        import numpy
        print("   ✅ numpy OK")
    except ImportError:
        print("   ❌ numpy manquant - pip install numpy")
        return False

    try:
        import scipy
        print("   ✅ scipy OK")
    except ImportError:
        print("   ❌ scipy manquant - pip install scipy")
        return False

    try:
        import soundfile
        print("   ✅ soundfile OK")
    except ImportError:
        print("   ❌ soundfile manquant - pip install soundfile")
        return False

    try:
        import sounddevice
        print("   ✅ sounddevice OK")
    except ImportError:
        print("   ❌ sounddevice manquant - pip install sounddevice")
        return False

    try:
        import matplotlib
        print("   ✅ matplotlib OK")
    except ImportError:
        print("   ❌ matplotlib manquant - pip install matplotlib")
        return False

    print("   ✅ Tous les modules nécessaires sont installés\n")
    return True


def test_audio_devices():
    """Vérifie que des devices audio sont détectés."""
    print("🔍 TEST 2/5 : Vérification des devices audio...")

    try:
        import sounddevice as sd

        devices = sd.query_devices()
        input_devices = [dev for dev in devices if dev['max_input_channels'] > 0]

        if not input_devices:
            print("   ⚠️  Aucun micro détecté")
            print("      → Utilisez Mode 2 (fichiers WAV) pour la démo")
            return True

        print(f"   ✅ {len(input_devices)} micro(s) détecté(s)")

        # Vérifier si WASAPI disponible (Windows)
        wasapi_count = sum(1 for dev in devices
                          if 'wasapi' in dev['name'].lower()
                          and dev['max_input_channels'] > 0)

        if wasapi_count > 0:
            print(f"   ⭐ {wasapi_count} device(s) WASAPI trouvé(s) (recommandé)")

        print()
        return True

    except Exception as e:
        print(f"   ❌ Erreur lors de la détection : {e}\n")
        return False


def test_src_modules():
    """Vérifie que les modules src/ sont accessibles."""
    print("🔍 TEST 3/5 : Vérification des modules src/...")

    sys.path.insert(0, 'src')

    try:
        from src.pitch_detector import detect_f0, FS, FRAME_SIZE
        print("   ✅ pitch_detector OK")
    except ImportError as e:
        print(f"   ❌ pitch_detector manquant : {e}")
        return False

    try:
        from src.music_utils import identify_string, cents_difference
        print("   ✅ music_utils OK")
    except ImportError as e:
        print(f"   ❌ music_utils manquant : {e}")
        return False

    try:
        from src.visualiser import plot_signal_fft
        print("   ✅ visualiser OK")
    except ImportError as e:
        print(f"   ❌ visualiser manquant : {e}")
        return False

    print("   ✅ Tous les modules src/ sont accessibles\n")
    return True


def test_data_files():
    """Vérifie que les fichiers de test WAV existent."""
    print("🔍 TEST 4/5 : Vérification des fichiers de test...")

    data_dir = Path('data/raw')

    if not data_dir.exists():
        print("   ⚠️  Dossier data/raw/ manquant")
        print("      → Créez-le ou utilisez Mode 1 (micro) pour la démo")
        print()
        return True

    expected_files = ['bonne_accord.wav', 'accord_basse.wav', 'accord_haute.wav']
    found_files = []

    for filename in expected_files:
        filepath = data_dir / filename
        if filepath.exists():
            found_files.append(filename)
            print(f"   ✅ {filename}")
        else:
            print(f"   ⚠️  {filename} manquant (optionnel)")

    if len(found_files) >= 1:
        print(f"\n   ✅ {len(found_files)}/3 fichiers WAV trouvés (suffisant pour démo)\n")
    else:
        print("\n   ⚠️  Aucun fichier WAV trouvé")
        print("      → Utilisez Mode 1 (micro) pour la démo\n")

    return True


def test_output_folder():
    """Vérifie que le dossier resultats/ peut être créé."""
    print("🔍 TEST 5/5 : Vérification du dossier de sortie...")

    results_dir = Path('resultats')

    try:
        results_dir.mkdir(exist_ok=True)

        # Tester écriture
        test_file = results_dir / '_test.txt'
        test_file.write_text("test")
        test_file.unlink()

        print("   ✅ Dossier resultats/ créé et accessible")
        print(f"      → eval_pitch.py sauvegardera ici les résultats\n")
        return True

    except Exception as e:
        print(f"   ❌ Erreur création resultats/ : {e}\n")
        return False


def main():
    """Exécute tous les tests."""
    print()
    print("=" * 70)
    print("   VÉRIFICATION SETUP - ACCORDEUR DE GUITARE")
    print("=" * 70)
    print()

    results = []

    results.append(test_imports())
    results.append(test_audio_devices())
    results.append(test_src_modules())
    results.append(test_data_files())
    results.append(test_output_folder())

    print("=" * 70)

    if all(results):
        print("✅ RÉSULTAT : Tous les tests sont passés !")
        print()
        print("Vous êtes prêt pour la démonstration du 9 décembre 🎉")
        print()
        print("Prochaines étapes :")
        print("  1. Testez main.py : python main.py")
        print("  2. Testez eval_pitch.py : python eval_pitch.py")
        print("  3. Relisez DEMO_CHECKLIST.md et ANTISECH_PRESENTATION.md")
        print()
    else:
        print("⚠️  RÉSULTAT : Certains tests ont échoué")
        print()
        print("Vérifiez les messages ci-dessus et corrigez les problèmes.")
        print()
        print("Aide :")
        print("  • Modules manquants : pip install -r requirements.txt")
        print("  • Modules src/ : vérifiez que vous êtes dans accordeur_mvp/")
        print("  • Audio : Vérifiez permissions Windows (Confidentialité > Micro)")
        print()

    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
