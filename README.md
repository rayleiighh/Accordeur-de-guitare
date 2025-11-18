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
├── src/
│   ├── pitch_detector.py    # Détection f₀ (autocorrélation)
│   └── music_utils.py       # Conversions Hz → Note + cents
│
├── test_accordeur.py        # Script avec menu de sélection
├── enregistrer_live.py      # Enregistrement micro en direct
├── requirements.txt         # Dépendances Python
└── README.md               # Ce fichier
```

---

## 🚀 Installation

### Prérequis
- Python 3.10+
- pip
- **Micro fonctionnel** (pour enregistrement live)

### Dépendances

```bash
pip install -r requirements.txt
```

**Note Windows** : Si `sounddevice` pose problème, installez d'abord :
```bash
pip install pipwin
pipwin install pyaudio
```

---

## 💻 Utilisation

### Mode 1 : Analyse de fichiers WAV (menu interactif)

```bash
python test_accordeur.py
```

**Menu** :
```
=== MENU ===
1. bonne_accord.wav
2. accord_basse.wav  
3. accord_haute.wav
4. Analyser TOUS les fichiers
0. Quitter

Votre choix : _
```

Le menu détecte automatiquement tous les fichiers `.wav` dans `data/raw/`.

---

### Mode 2 : Enregistrement en direct

```bash
python enregistrer_live.py
```

**Étapes** :
1. Le script détecte votre micro
2. Appuyez sur **Entrée** pour démarrer
3. **Jouez UNE corde** de guitare
4. Appuyez sur **Entrée** pour arrêter
5. Analyse automatique + résultats

**Sortie exemple** :
```
🔴 ENREGISTREMENT EN COURS...

📊 ANALYSE DE L'ENREGISTREMENT
   Fenêtre 1 :  82.18 Hz → E2 (  -4.9 cents) ✓ JUSTE
   📊 Erreur absolue moyenne : 4.87 cents
   ✓ EXCELLENT (objectif ≤ 10 cents)
```

**Conseil** : Jouez UNE seule corde à la fois, pas d'accord complet !

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
