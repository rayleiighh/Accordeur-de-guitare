"""
Script de verification rapide - Accordeur de guitare
====================================================

Verifie que tout est correctement installe et configure avant la presentation.

Usage :
    python test_setup.py

Auteurs : El Mazani, Ben Lhaj, Zebiri, Nzeyimana (Groupe 7)
Date : Novembre 2025
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, cast


def test_imports() -> bool:
    """Verifie que tous les modules necessaires sont installes."""
    print("?? TEST 1/5 : Verification des imports...")

    try:
        import numpy  # noqa: F401
        print("   ? numpy OK")
    except ImportError:
        print("   ?? numpy manquant - pip install numpy")
        return False

    try:
        import scipy  # noqa: F401
        print("   ? scipy OK")
    except ImportError:
        print("   ?? scipy manquant - pip install scipy")
        return False

    try:
        import soundfile  # noqa: F401
        print("   ? soundfile OK")
    except ImportError:
        print("   ?? soundfile manquant - pip install soundfile")
        return False

    try:
        import sounddevice  # noqa: F401
        print("   ? sounddevice OK")
    except ImportError:
        print("   ?? sounddevice manquant - pip install sounddevice")
        return False

    try:
        import matplotlib  # noqa: F401
        print("   ? matplotlib OK")
    except ImportError:
        print("   ?? matplotlib manquant - pip install matplotlib")
        return False

    print("   ? Tous les modules necessaires sont installes\n")
    return True


def test_audio_devices() -> bool:
    """Verifie que des devices audio sont detectes."""
    print("?? TEST 2/5 : Verification des devices audio...")

    try:
        import sounddevice as sd

        devices_raw = sd.query_devices()
        devices: List[Dict[str, Any]] = []
        for dev_obj in devices_raw:
            dev_map: Mapping[str, Any] = cast(Mapping[str, Any], dev_obj)
            devices.append({str(k): v for k, v in dev_map.items()})

        input_devices = [dev for dev in devices if dev.get("max_input_channels", 0) > 0]

        if not input_devices:
            print("   ??  Aucun micro detecte")
            print("      -> Utilisez Mode 2 (fichiers WAV) pour la demo")
            return True

        print(f"   ? {len(input_devices)} micro(s) detecte(s)")

        # Verifier si WASAPI disponible (Windows)
        wasapi_count = sum(
            1
            for dev in devices
            if "wasapi" in str(dev.get("name", "")).lower()
            and dev.get("max_input_channels", 0) > 0
        )

        if wasapi_count > 0:
            print(f"   ? {wasapi_count} device(s) WASAPI trouve(s) (recommande)")

        print()
        return True

    except Exception as e:  # noqa: BLE001
        print(f"   ?? Erreur lors de la detection : {e}\n")
        return False


def test_src_modules() -> bool:
    """Verifie que les modules src/ sont accessibles."""
    print("?? TEST 3/5 : Verification des modules src/...")

    sys.path.insert(0, "src")

    try:
        from src.pitch_detector import detect_f0, FS, FRAME_SIZE  # noqa: F401
        print("   ? pitch_detector OK")
    except ImportError as e:
        print(f"   ?? pitch_detector manquant : {e}")
        return False

    try:
        from src.music_utils import identify_string, cents_difference  # noqa: F401
        print("   ? music_utils OK")
    except ImportError as e:
        print(f"   ?? music_utils manquant : {e}")
        return False

    try:
        from src.visualiser import plot_fft_analysis  # noqa: F401
        print("   ? visualiser OK (plot_fft_analysis)")
    except ImportError as e:
        print(f"   ?? visualiser manquant : {e}")
        return False

    print("   ? Tous les modules src/ sont accessibles\n")
    return True


def test_data_files() -> bool:
    """Verifie que les fichiers de test WAV existent."""
    print("?? TEST 4/5 : Verification des fichiers de test...")

    data_dir = Path("data/raw")

    if not data_dir.exists():
        print("   ??  Dossier data/raw/ manquant")
        print("      -> Creez-le ou utilisez Mode 1 (micro) pour la demo")
        print()
        return True

    expected_files = ["bonne_accord.wav", "accord_basse.wav", "accord_haute.wav"]
    found_files: List[str] = []

    for filename in expected_files:
        filepath = data_dir / filename
        if filepath.exists():
            found_files.append(filename)
            print(f"   ? {filename}")
        else:
            print(f"   ??  {filename} manquant (optionnel)")

    if len(found_files) >= 1:
        print(f"\n   ? {len(found_files)}/3 fichiers WAV trouves (suffisant pour demo)\n")
    else:
        print("\n   ??  Aucun fichier WAV trouve")
        print("      -> Utilisez Mode 1 (micro) pour la demo\n")

    return True


def test_output_folder() -> bool:
    """Verifie que le dossier resultats/ peut etre cree."""
    print("?? TEST 5/5 : Verification du dossier de sortie...")

    results_dir = Path("resultats")

    try:
        results_dir.mkdir(exist_ok=True)

        # Tester ecriture
        test_file = results_dir / "_test.txt"
        test_file.write_text("test")
        test_file.unlink()

        print("   ? Dossier resultats/ cree et accessible")
        print("      -> eval_pitch.py sauvegardera ici les resultats\n")
        return True

    except Exception as e:  # noqa: BLE001
        print(f"   ?? Erreur creation resultats/ : {e}\n")
        return False


def main() -> None:
    """Execute tous les tests."""
    print()
    print("=" * 70)
    print("   VERIFICATION SETUP - ACCORDEUR DE GUITARE")
    print("=" * 70)
    print()

    results = [
        test_imports(),
        test_audio_devices(),
        test_src_modules(),
        test_data_files(),
        test_output_folder(),
    ]

    print("=" * 70)

    if all(results):
        print("? RESULTAT : Tous les tests sont passes !")
        print()
        print("Vous etes pret pour la demonstration du 9 decembre !!")
        print()
        print("Prochaines etapes :")
        print("  1. Testez main.py : python main.py")
        print("  2. Testez eval_pitch.py : python eval_pitch.py")
        print("  3. Relisez DEMO_CHECKLIST.md et ANTISECH_PRESENTATION.md")
        print()
    else:
        print("??  RESULTAT : Certains tests ont echoue")
        print()
        print("Verifiez les messages ci-dessus et corrigez les problemes.")
        print()
        print("Aide :")
        print("  - Modules manquants : pip install -r requirements.txt")
        print("  - Modules src/ : verifiez que vous etes dans accordeur_mvp/")
        print("  - Audio : verifiez les permissions Windows (Confidentialite > Micro)")
        print()

    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
