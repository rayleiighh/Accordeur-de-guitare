# 🎸 Accordeur de Guitare Numérique

## 📚 Projet Signaux III - EPHEC

Accordeur numérique capable de détecter la fréquence fondamentale (f₀) d'une corde de guitare et d'indiquer si elle est juste, trop basse ou trop haute.

---

## 🎯 Objectifs du projet

- **Acquisition** : Capturer le signal audio via microphone (48 kHz, mono)
- **Prétraitement** : Filtrage anti-bruit (bande 70-1500 Hz, notch 50 Hz)
- **Détection f₀** : Algorithmes autocorrélation et YIN
- **Mapping musical** : Conversion fréquence → note + écart en cents
- **Interface** : Affichage temps réel "trop bas / juste / trop haut"

---

## 📚 Références au cours

Ce projet applique les concepts des chapitres suivants :

- **Chapitre 1** : Représentation des signaux analogiques
- **Chapitre 2** : Transformée de Fourier
- **Chapitre 5** : Filtres numériques
- **Chapitre 6** : Échantillonnage (théorème de Shannon-Nyquist)
- **Chapitre 7** : Analyse spectrale (FFT, spectrogramme)

---

## 🚀 Installation

### Prérequis

- Python 3.10 ou supérieur
- pip

### Installation des dépendances

```bash
pip install -r requirements.txt
```

---

## 📦 Structure du projet

```text
accordeur-guitare/
├── signal_generation.py     # ✅ Module de génération de signaux (FAIT)
├── music_theory.py          # 🔜 Utilitaires musicaux (À FAIRE)
├── preprocessing.py         # 🔜 Filtrage (À FAIRE)
├── pitch_detection.py       # 🔜 Détection f₀ (À FAIRE)
├── requirements.txt
└── README.md
```

---

## 🎯 Module 1 : Génération de signaux (TERMINÉ)

### Utilisation

```python
from signal_generation import *

# Générer une sinusoïde pure (corde E2)
signal, time = generate_pure_sine(82.41, duration=2.0)

# Générer un signal réaliste de guitare avec harmoniques
signal_guitar, time = generate_guitar_string(110.0, n_harmonics=8)

# Ajouter du bruit
signal_noisy = add_noise(signal_guitar, snr_db=15)

# Visualiser
plot_signal_analysis(signal_guitar, title="Corde A2")
```

### Tests intégrés

Pour tester le module :

```bash
python signal_generation.py
```

Cela exécute tous les tests automatiques et génère les visualisations.

---

## 🎼 Fréquences des cordes de guitare

| Corde | Note | Fréquence (Hz) |
|-------|------|----------------|
| 6ème  | E2   | 82.41          |
| 5ème  | A2   | 110.00         |
| 4ème  | D3   | 146.83         |
| 3ème  | G3   | 196.00         |
| 2ème  | B3   | 246.94         |
| 1ère  | E4   | 329.63         |

---

## 📊 Paramètres d'échantillonnage

- **Fréquence d'échantillonnage (Fs)** : 48 000 Hz
- **Période d'échantillonnage (Te)** : 20.83 μs
- **Justification** : Fs >> 2 × fmax (théorème de Shannon, Cours Chap. 6 p.166-167)

---

## 🔜 Prochaines étapes

1. ✅ **Module 1** : Génération de signaux → **TERMINÉ**
2. 🔜 **Module 2** : Utilitaires musicaux (Hz ↔ Note, cents)
3. 🔜 **Module 3** : Prétraitement (filtres passe-bande, notch)
4. 🔜 **Module 4** : Détection f₀ (autocorrélation, YIN)
5. 🔜 **Module 5** : Temps réel

---

## 📖 Documentation

Chaque module contient :

- ✅ Docstrings détaillées
- ✅ Références explicites au cours EPHEC
- ✅ Exemples d'utilisation
- ✅ Tests intégrés

---

## 👨‍🎓 Auteur

Étudiant en Bac 3 TI - EPHEC  
Cours : Signaux III  
Date : Novembre 2025

---

## 📝 Licence

Projet académique - EPHEC
