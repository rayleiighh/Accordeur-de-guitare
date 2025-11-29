"""
Script de démonstration - Accordeur de guitare MVP
===================================================

Démontre le fonctionnement complet de l'accordeur sur fichiers audio.

Usage :
    python test_accordeur.py

Auteur : Projet Signaux III - EPHEC
Date : Novembre 2025
"""

import sys
import os
import numpy as np
import soundfile as sf

# Ajouter src au path
sys.path.insert(0, 'src')

from src.pitch_detector import detect_f0
from src.music_utils import identify_string, get_tuning_status, cents_difference


# =============================================================================
# FONCTION PRINCIPALE D'ANALYSE
# =============================================================================

def analyser_fichier(filepath: str):
    """
    Analyse un fichier audio et affiche le résultat d'accordage.
    
    Parameters
    ----------
    filepath : str
        Chemin vers le fichier WAV
    """
    print(f"\n📁 Fichier : {os.path.basename(filepath)}")
    print("-" * 60)
    
    try:
        # Charger le fichier
        signal, fs = sf.read(filepath)
        
        # Convertir en mono si nécessaire
        if signal.ndim == 2:
            signal = np.mean(signal, axis=1)
        
        print(f"   • Durée : {len(signal)/fs:.2f} s")
        print(f"   • Fréquence d'échantillonnage : {fs} Hz")
        
        # Analyser plusieurs fenêtres
        n_analyses = 3
        hop = len(signal) // (n_analyses + 1)
        
        print(f"\n   Analyse de {n_analyses} fenêtres :")
        print()
        
        results = []
        
        for i in range(1, n_analyses + 1):
            start = i * hop
            frame = signal[start:start + 4096]
            
            # Détection f₀
            f0 = detect_f0(frame, fs=fs)
            
            if f0 is not None:
                # Identification de la corde
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
        
        # Résumé
        if results:
            print()
            cents_values = [abs(c) for _, _, c, _ in results]
            mean_abs_error = np.mean(cents_values)
            
            print(f"   📊 Erreur absolue moyenne : {mean_abs_error:.2f} cents")
            
            if mean_abs_error < 10:
                print(f"   ✓ EXCELLENT (objectif ≤ 10 cents)")
            elif mean_abs_error < 20:
                print(f"   ✓ BON")
            else:
                print(f"   ⚠ À améliorer")
    
    except FileNotFoundError:
        print(f"   ✗ Fichier introuvable")
    except Exception as e:
        print(f"   ✗ Erreur : {e}")


# =============================================================================
# SCRIPT PRINCIPAL
# =============================================================================

def afficher_menu(fichiers_wav):
    """
    Affiche le menu de sélection des fichiers.
    
    Parameters
    ----------
    fichiers_wav : list of str
        Liste des chemins vers les fichiers WAV
    
    Returns
    -------
    choix : int or None
        Index du fichier choisi, -1 pour tous, None pour quitter
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
    
    while True:
        try:
            choix_str = input("Votre choix : ").strip()
            choix = int(choix_str)
            
            if choix == 0:
                return None
            elif choix == len(fichiers_wav) + 1:
                return -1  # Code pour "tous"
            elif 1 <= choix <= len(fichiers_wav):
                return choix - 1  # Index du fichier
            else:
                print(f"❌ Choix invalide. Entrez un nombre entre 0 et {len(fichiers_wav) + 1}")
        except ValueError:
            print("❌ Veuillez entrer un nombre valide")
        except KeyboardInterrupt:
            print("\n\n⚠️  Interruption par l'utilisateur")
            return None


def main():
    """
    Fonction principale : teste l'accordeur sur les fichiers disponibles.
    """
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  ACCORDEUR DE GUITARE NUMÉRIQUE - MVP".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    print("Détection de fréquence fondamentale par autocorrélation")
    print("Cours : Signaux III - EPHEC")
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
        print(f"\n❌ Dossier introuvable : {data_dir}")
        print("   Veuillez créer le dossier data/raw/ et y placer vos fichiers WAV")
        return
    
    # Afficher le menu
    choix = afficher_menu(fichiers_wav)
    
    if choix is None:
        print("\n👋 Au revoir !")
        return
    
    print("\n" + "=" * 60)
    
    # Analyser selon le choix
    if choix == -1:
        # Tous les fichiers
        print("\n📊 Analyse de TOUS les fichiers :")
        for filepath in fichiers_wav:
            analyser_fichier(filepath)
    else:
        # Un seul fichier
        analyser_fichier(fichiers_wav[choix])
    
    print()
    print("=" * 60)
    print("✓ ANALYSE TERMINÉE")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()