"""
Enregistrement et analyse en direct - Accordeur guitare
========================================================

Ce script permet d'enregistrer le son du micro en temps réel,
puis d'analyser l'accordage de la corde jouée.

Usage :
    python enregistrer_live.py

Auteur : Projet Signaux III - EPHEC
Date : Novembre 2025
"""

import sys
import numpy as np
import sounddevice as sd
import soundfile as sf
from datetime import datetime
import os

# Ajouter src au path
sys.path.insert(0, 'src')

from pitch_detector import detect_f0
from music_utils import identify_string, get_tuning_status


# =============================================================================
# PARAMÈTRES D'ENREGISTREMENT
# =============================================================================

FS = 48000              # Fréquence d'échantillonnage (Hz)
CHANNELS = 1            # Mono
DTYPE = 'float32'       # Type de données


# =============================================================================
# ENREGISTREMENT
# =============================================================================

class RecordingSession:
    """
    Gère une session d'enregistrement audio.
    """
    
    def __init__(self, fs=FS, channels=CHANNELS):
        """
        Initialise la session d'enregistrement.
        
        Parameters
        ----------
        fs : int
            Fréquence d'échantillonnage
        channels : int
            Nombre de canaux (1 = mono)
        """
        self.fs = fs
        self.channels = channels
        self.recording = []
        self.is_recording = False
    
    def callback(self, indata, frames, time, status):
        """
        Callback appelé à chaque bloc audio capturé.
        
        Parameters
        ----------
        indata : ndarray
            Données audio captées
        frames : int
            Nombre de frames
        time : CData
            Timestamp
        status : CallbackFlags
            Status du stream
        """
        if status:
            print(f"⚠️  {status}", file=sys.stderr)
        
        # Ajouter les données à l'enregistrement
        self.recording.append(indata.copy())
    
    def start(self):
        """Démarre l'enregistrement."""
        self.recording = []
        self.is_recording = True
        self.stream = sd.InputStream(
            samplerate=self.fs,
            channels=self.channels,
            dtype=DTYPE,
            callback=self.callback
        )
        self.stream.start()
    
    def stop(self):
        """Arrête l'enregistrement et retourne le signal."""
        self.is_recording = False
        self.stream.stop()
        self.stream.close()
        
        # Concaténer tous les blocs
        if self.recording:
            signal = np.concatenate(self.recording, axis=0)
            # Convertir en 1D si mono
            if signal.ndim == 2 and signal.shape[1] == 1:
                signal = signal[:, 0]
            return signal
        else:
            return np.array([])
    
    def get_duration(self):
        """Retourne la durée actuelle de l'enregistrement."""
        if self.recording:
            total_samples = sum(len(block) for block in self.recording)
            return total_samples / self.fs
        return 0.0


# =============================================================================
# ANALYSE DU SIGNAL ENREGISTRÉ
# =============================================================================

def analyser_enregistrement(signal, fs=FS, nom_fichier=None):
    """
    Analyse le signal enregistré et affiche les résultats.
    
    Parameters
    ----------
    signal : np.ndarray
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
    if len(signal) < 4096:
        print()
        print("   ❌ Enregistrement trop court (minimum : 0.085 s)")
        print("      Veuillez jouer la corde plus longtemps")
        return
    
    # Vérifier le niveau sonore
    rms = np.sqrt(np.mean(signal ** 2))
    print(f"   • Niveau RMS : {rms:.4f}")
    
    if rms < 0.001:
        print()
        print("   ⚠️  Signal très faible !")
        print("      Vérifiez que le micro fonctionne et que vous jouez assez fort")
        print()
    
    print()
    print("   Analyse de plusieurs fenêtres :")
    print()
    
    # Analyser plusieurs fenêtres
    n_analyses = min(5, int(duree / 0.3))  # Maximum 5 fenêtres
    n_analyses = max(1, n_analyses)  # Minimum 1 fenêtre
    
    hop = len(signal) // (n_analyses + 1)
    
    results = []
    
    for i in range(1, n_analyses + 1):
        start = i * hop
        end = start + 4096
        
        if end > len(signal):
            break
        
        frame = signal[start:end]
        
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
            print(f"   ⚠ À améliorer (serrez ou desserrez la corde)")
        
        # Note dominante
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


# =============================================================================
# SAUVEGARDE
# =============================================================================

def sauvegarder_enregistrement(signal, fs, dossier='enregistrements'):
    """
    Sauvegarde l'enregistrement dans un fichier WAV.
    
    Parameters
    ----------
    signal : np.ndarray
        Signal audio
    fs : int
        Fréquence d'échantillonnage
    dossier : str
        Dossier de destination
    
    Returns
    -------
    filepath : str
        Chemin du fichier sauvegardé
    """
    # Créer le dossier s'il n'existe pas
    os.makedirs(dossier, exist_ok=True)
    
    # Nom du fichier avec timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"enreg_{timestamp}.wav"
    filepath = os.path.join(dossier, filename)
    
    # Sauvegarder
    sf.write(filepath, signal, fs)
    
    return filepath


# =============================================================================
# FONCTION PRINCIPALE
# =============================================================================

def main():
    """
    Fonction principale : enregistrement et analyse en direct.
    """
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  ENREGISTREMENT EN DIRECT - ACCORDEUR".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    print("Enregistrez le son de votre guitare via le micro")
    print("Cours : Signaux III - EPHEC")
    print()
    print("=" * 60)
    print()
    
    # Vérifier les périphériques audio
    try:
        devices = sd.query_devices()
        default_input = sd.query_devices(kind='input')
        print("🎤 Micro détecté :")
        print(f"   {default_input['name']}")
        print()
    except Exception as e:
        print(f"❌ Erreur : Impossible de détecter le micro")
        print(f"   {e}")
        print()
        return
    
    # Créer la session d'enregistrement
    session = RecordingSession(fs=FS)
    
    print("📝 INSTRUCTIONS :")
    print("   1. Appuyez sur Entrée pour DÉMARRER l'enregistrement")
    print("   2. Jouez UNE corde de guitare")
    print("   3. Appuyez à nouveau sur Entrée pour ARRÊTER")
    print()
    
    input("Appuyez sur Entrée pour démarrer l'enregistrement...")
    
    # Démarrer l'enregistrement
    session.start()
    print()
    print("🔴 ENREGISTREMENT EN COURS...")
    print("   (Jouez une corde, puis appuyez sur Entrée)")
    print()
    
    try:
        input()  # Attendre que l'utilisateur appuie sur Entrée
    except KeyboardInterrupt:
        print("\n⚠️  Interruption par l'utilisateur")
    
    # Arrêter l'enregistrement
    print()
    print("⏹️  Arrêt de l'enregistrement...")
    signal = session.stop()
    
    if len(signal) == 0:
        print("❌ Aucun signal enregistré")
        return
    
    duree = len(signal) / FS
    print(f"✓ Enregistrement terminé ({duree:.2f} secondes)")
    
    # Demander si on sauvegarde
    print()
    reponse = input("Sauvegarder l'enregistrement ? (o/n) : ").strip().lower()
    
    nom_fichier = None
    if reponse in ['o', 'oui', 'y', 'yes']:
        nom_fichier = sauvegarder_enregistrement(signal, FS)
        print(f"✓ Sauvegardé : {nom_fichier}")
    
    # Analyser
    analyser_enregistrement(signal, FS, nom_fichier)
    
    print("=" * 60)
    print("✓ SESSION TERMINÉE")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()