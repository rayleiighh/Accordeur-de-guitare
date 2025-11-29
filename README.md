# 🎸 Accordeur de Guitare Numérique - VERSION MVP

## 📋 Projet Signaux III - EPHEC

**Objectif** : Détection de la fréquence fondamentale (f₀) d'une corde de guitare et indication de l'accordage (juste/trop bas/trop haut).

**Étudiant** : Bac 3 TI - EPHEC  
**Cours** : Signaux III  
**Date** : Novembre 2025

---

## 🎯 Fonctionnalités (MVP)

✅ Détection de f₀ par autocorrélation  
✅ Association à la note de guitare (EADGBE)  
✅ Calcul de l'écart en cents  
✅ Indication : juste / trop bas / trop haut  
✅ **Menu de sélection** de fichier (nouveau !)  
✅ **Enregistrement en direct** via micro (nouveau !)

---

## 📦 Structure du projet

```
accordeur_mvp/
├── main.py                  # 🎯 INTERFACE PRINCIPALE (Menu unifié)
├── eval_pitch.py            # 📊 Script d'évaluation automatique
├── src/
│   ├── pitch_detector.py    # Détection f₀ (autocorrélation + notch 50Hz)
│   ├── music_utils.py       # Conversions Hz → Note + cents
│   └── visualiser.py        # Graphiques FFT (bonus)
├── data/raw/                # Fichiers de test WAV
├── legacy/                  # Anciens scripts (obsolètes)
├── requirements.txt         # Dépendances Python
└── README.md               # Ce fichier
```

---

## 🚀 Installation

### Étape 1 : Vérifier Python

**Version requise** : Python 3.10 ou supérieur

```bash
python --version
```

Si Python n'est pas installé :
- **Windows** : [python.org/downloads](https://www.python.org/downloads/)
- **Mac** : `brew install python3`
- **Linux** : `sudo apt install python3 python3-pip`

---

### Étape 2 : Installer les dépendances

**Dans le dossier du projet :**

```bash
cd accordeur_mvp
pip install -r requirements.txt
```

**Dépendances installées :**
- `numpy` : Calculs numériques
- `scipy` : Filtres (Butterworth, notch)
- `soundfile` : Lecture/écriture fichiers WAV
- `sounddevice` : Capture audio microphone
- `matplotlib` : Visualisations (optionnel)

---

### Étape 3 : Vérifier l'installation

**Test rapide :**

```bash
python -c "import numpy, scipy, soundfile, sounddevice; print('✓ Toutes les dépendances sont installées !')"
```

---

### ⚠️ Troubleshooting

#### Problème : `sounddevice` ne s'installe pas (Windows)

**Solution 1** : Installer via pipwin
```bash
pip install pipwin
pipwin install pyaudio
pip install sounddevice
```

**Solution 2** : Utiliser l'installeur binaire
- Télécharger [PortAudio](http://www.portaudio.com/)
- Réessayer `pip install sounddevice`

#### Problème : "No module named 'src'"

**Cause** : Vous n'êtes pas dans le bon dossier

**Solution** :
```bash
cd accordeur_mvp  # Se placer dans le dossier du projet
python main.py    # Lancer depuis ce dossier
```

#### Problème : Micro non détecté

**Vérifier les périphériques audio :**
```python
import sounddevice as sd
print(sd.query_devices())
```

Si le micro n'apparaît pas :
- Vérifier les permissions micro (Paramètres système)
- Réinstaller les pilotes audio
- Utiliser le mode fichiers WAV à la place

---

## 💻 Utilisation

### 🎯 INTERFACE PRINCIPALE (Recommandé)

**Lancer l'accordeur :**

```bash
cd accordeur_mvp
python main.py
```

**Menu principal :**
```
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║          ACCORDEUR DE GUITARE NUMÉRIQUE                  ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝

Détection de fréquence fondamentale par autocorrélation
Cours : Signaux III - EPHEC

Références académiques :
  • Chap. 2 p.52  : Théorème de Wiener-Khinchin (FFT)
  • Chap. 5 p.150 : Filtre Butterworth passe-bande
  • Chap. 6 p.166 : Théorème de Shannon-Nyquist (Fs=48kHz)
  • Chap. 7 p.195 : Autocorrélation pour détection f₀

============================================================

  1. Enregistrer avec le micro
  2. Charger un fichier WAV
  0. Quitter

Votre choix : _
```

---

### Mode 1 : Enregistrement en direct (micro)

**Étapes** :
1. Choisir option **1** dans le menu principal
2. Le script détecte votre micro automatiquement
3. Appuyez sur **Entrée** pour démarrer l'enregistrement
4. **Jouez UNE corde** de guitare (laissez sonner ~2 secondes)
5. Appuyez sur **Entrée** pour arrêter
6. Optionnel : Sauvegarder l'enregistrement
7. Résultats affichés automatiquement

**Sortie exemple** :
```
🔴 ENREGISTREMENT EN COURS...

📊 ANALYSE DE L'ENREGISTREMENT
   • Durée : 2.34 s
   • Échantillons : 112320
   • Fréquence d'échantillonnage : 48000 Hz

   Analyse de plusieurs fenêtres :

   Fenêtre 1 :  82.18 Hz → E2 (  -4.9 cents) ✓ JUSTE
   Fenêtre 2 :  82.05 Hz → E2 (  -7.3 cents) ✓ JUSTE
   Fenêtre 3 :  82.41 Hz → E2 (  +0.0 cents) ✓ JUSTE

   📊 Erreur absolue moyenne (MAE) : 4.07 cents
   ✓ EXCELLENT (objectif ≤ 10 cents atteint)

   🎸 Note détectée : E2
```

---

### Mode 2 : Analyse de fichiers WAV

**Étapes** :
1. Placer vos fichiers WAV dans `data/raw/`
2. Choisir option **2** dans le menu principal
3. Sélectionner un fichier ou analyser tous

**Menu fichiers :**
```
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║                  MENU DE SÉLECTION                       ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝

Fichiers disponibles :

  1. bonne_accord.wav
  2. accord_basse.wav
  3. accord_haute.wav
  4. Analyser TOUS les fichiers
  0. Quitter

Votre choix : _
```

---

### 📊 Évaluation automatique

**Tester la précision sur tous les fichiers :**

```bash
cd accordeur_mvp
python eval_pitch.py
```

**Sortie :**
- `resultats_evaluation.csv` : Métriques par fichier (MAE, RMSE, etc.)
- `resume_global.txt` : Statistiques agrégées
- Affichage console : Validation critères MVP

**Exemple de sortie** :
```
📊 ÉVALUATION AUTOMATIQUE - ACCORDEUR DE GUITARE
============================================================

  Analyse : bonne_accord.wav... ✓ MAE=4.87 cents
  Analyse : accord_basse.wav... ✓ MAE=5.12 cents
  Analyse : accord_haute.wav... ✓ MAE=6.23 cents

📊 RÉSUMÉ GLOBAL
============================================================

   Fichiers analysés       : 3
   Fenêtres totales        : 9

   MAE globale             : 5.41 cents
   MAE min/max             : 4.87 / 6.23 cents
   RMSE globale            : 6.52 cents
   Taux détection moyen    : 100.0 %

🎯 ÉVALUATION PAR RAPPORT AUX CRITÈRES MVP
--------------------------------------------------------------------

   MAE ≤ 10 cents          : ✅ PASSÉ (5.41 cents)
   Détection ≥ 95%         : ✅ PASSÉ (100.0%)

   🎉 RÉSULTAT FINAL : ✅ TOUS LES CRITÈRES PASSÉS !
```

---

### Mode 3 : Utilisation dans votre code

```python
import soundfile as sf
from src.pitch_detector import detect_f0
from src.music_utils import identify_string, get_tuning_status

# 1. Charger un fichier audio
signal, fs = sf.read('guitare.wav')

# 2. Prendre une fenêtre (4096 échantillons)
frame = signal[10000:14096]

# 3. Détecter la fréquence
f0 = detect_f0(frame, fs=fs)

# 4. Identifier la corde
if f0:
    note, cents = identify_string(f0)
    status = get_tuning_status(cents)
    
    print(f"Note : {note}")
    print(f"Écart : {cents:+.1f} cents")
    print(f"Status : {status}")
```

---

## 📊 Algorithme

### Pipeline complet

```
🎤 Signal audio (48 kHz)
    ↓
🔧 Prétraitement
    • Filtre notch 50 Hz (bruit secteur)
    • Filtre passe-bande (70-1500 Hz)
    • Fenêtrage de Hann
    ↓
🎯 Détection f₀
    • Autocorrélation : R(τ) = Σ s(t)×s(t+τ)
    • Recherche du pic → période
    • Interpolation parabolique
    ↓
🎼 Conversion musicale
    • Identification de la corde (E2, A2, D3, G3, B3, E4)
    • Calcul de l'écart : cents = 1200 × log₂(f/f₀)
    ↓
💬 Affichage
    • Note + écart en cents
    • Status : juste / trop bas / trop haut
```

### Formules clés

**Autocorrélation** (Cours Chap. 7 p.195-197) :
```
R(τ) = Σ s(t) × s(t+τ)
```

**Cents** (écart musical) :
```
cents = 1200 × log₂(f_mesurée / f_cible)
```

**Shannon-Nyquist** (Cours Chap. 6 p.166-167) :
```
Fs ≥ 2 × fmax
48000 Hz ≥ 2 × 1500 Hz ✓
```

---

## 📚 Références au cours

- **Chapitre 2** : Transformée de Fourier (p.38-57)
- **Chapitre 5** : Filtres numériques (p.145-156)
- **Chapitre 6** : Échantillonnage (p.166-177)
- **Chapitre 7** : Autocorrélation (p.195-197)

---

## 🎯 Résultats

**Objectif** : MAE ≤ 10 cents

**Résultats obtenus** :
- Corde bien accordée : **MAE = 5-6 cents** ✓ EXCELLENT
- Détection stable et robuste
- Temps de traitement : <100 ms par fenêtre

---

## 🔧 Paramètres techniques

| Paramètre | Valeur | Justification |
|-----------|--------|---------------|
| Fréquence d'échantillonnage | 48 kHz | Shannon : Fs ≥ 2×fmax |
| Taille de fenêtre | 4096 échantillons | ~85 ms (compromis temps/fréquence) |
| Bande passante | 70-1500 Hz | Plage guitare + harmoniques |
| Fenêtre | Hann | Réduction effets de bord (Cours p.192) |
| Filtre | Butterworth ordre 4 | Réponse plate (Cours p.150) |

---

## ⚠️ Limites

- Signal mono uniquement (1 corde à la fois)
- Environnement calme recommandé
- Pas de polyphonie (plusieurs notes simultanées)

---

## 📝 Licence

Projet académique - EPHEC
