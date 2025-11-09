# 📂 Organisation du Projet - Accordeur de Guitare

## 🗂️ Structure des dossiers recommandée

```
accordeur-guitare/
│
├── data/                          # 📊 Données du projet
│   ├── raw/                       # ✅ Fichiers audio bruts (tes enregistrements)
│   │   ├── bonne_accord.wav       # Corde bien accordée
│   │   ├── accord_basse.wav       # Corde trop basse (~-50 cents)
│   │   └── accord_haute.wav       # Corde trop haute (~+50 cents)
│   │
│   ├── synthetic/                 # Signaux générés synthétiquement
│   │   ├── pure_tones/            # Sinusoïdes pures
│   │   ├── with_harmonics/        # Signaux réalistes
│   │   └── with_noise/            # Signaux bruités
│   │
│   └── metadata.csv               # Métadonnées (note, fréquence, cents, etc.)
│
├── src/                           # 💻 Code source
│   ├── signal_generation.py       # ✅ FAIT - Génération de signaux
│   ├── music_theory.py            # 🔜 TODO - Conversion Hz ↔ Note
│   ├── preprocessing.py           # 🔜 TODO - Filtrage
│   ├── pitch_detection.py         # 🔜 TODO - Détection f₀
│   ├── visualization.py           # 🔜 TODO - Graphiques
│   └── realtime_tuner.py          # 🔜 TODO - Interface temps réel
│
├── tests/                         # 🧪 Tests unitaires
│   ├── test_signal_generation.py
│   ├── test_pitch_detection.py
│   └── test_preprocessing.py
│
├── results/                       # 📈 Résultats et analyses
│   ├── figures/                   # Graphiques générés
│   ├── metrics/                   # MAE, latence, etc.
│   └── validation_report.pdf      # Rapport final
│
├── notebooks/                     # 📓 Jupyter notebooks (optionnel)
│   ├── exploration.ipynb
│   └── validation.ipynb
│
├── docs/                          # 📚 Documentation
│   ├── poster_A1.pdf
│   ├── rapport_final.pdf
│   └── references_cours.md
│
├── requirements.txt               # 📦 Dépendances Python
├── README.md                      # 📖 Documentation principale
└── example_usage.py               # 🎯 Exemples d'utilisation

```

---

## 📊 Tes fichiers audio actuels

### ✅ Fichiers présents dans `data/raw/`

| Fichier | Durée | Fs | Description |
|---------|-------|-----|-------------|
| `bonne_accord.wav` | 29.46s | 48 kHz | ✅ Corde bien accordée (0 cents) |
| `accord_basse.wav` | 27.13s | 48 kHz | 📉 Corde trop basse (~-50 cents) |
| `accord_haute.wav` | 26.36s | 48 kHz | 📈 Corde trop haute (~+50 cents) |

**Note** : Ces fichiers sont parfaits pour valider ton algorithme ! 🎸

---

## 🎯 Métadonnées à créer

Tu devrais créer un fichier `data/metadata.csv` avec ces informations :

```csv
filename,note_target,freq_target,cents_offset,duration,fs,description
bonne_accord.wav,E2,82.41,0,29.46,48000,Corde E2 bien accordée
accord_basse.wav,E2,80.06,-50,27.13,48000,Corde E2 trop basse
accord_haute.wav,E2,84.82,+50,26.36,48000,Corde E2 trop haute
```

**Formule pour calculer la fréquence désaccordée** :
```
f_detuned = f₀ × 2^(cents/1200)

Exemples :
- E2 à -50 cents : 82.41 × 2^(-50/1200) ≈ 80.06 Hz
- E2 à   0 cents : 82.41 × 2^(0/1200)   = 82.41 Hz  
- E2 à +50 cents : 82.41 × 2^(+50/1200) ≈ 84.82 Hz
```

---

## 🔄 Workflow typique

### 1️⃣ Développement (sur signaux synthétiques)
```bash
# Générer des signaux de test
python src/signal_generation.py

# Tester l'algorithme de détection
python src/pitch_detection.py

# Mesurer la précision
python tests/test_pitch_detection.py
```

### 2️⃣ Validation (sur données réelles)
```bash
# Analyser tes enregistrements
python scripts/analyze_recordings.py data/raw/*.wav

# Calculer la MAE (Mean Absolute Error)
python scripts/validate_tuner.py
```

### 3️⃣ Démonstration (temps réel)
```bash
# Lancer l'accordeur en temps réel
python src/realtime_tuner.py
```

---

## 📝 Bonnes pratiques

### ✅ À FAIRE :
- Garder les **fichiers bruts** dans `data/raw/` (jamais modifier)
- Mettre les **signaux générés** dans `data/synthetic/`
- **Versionner** le code (git) mais **pas les gros fichiers WAV**
- Documenter les **métadonnées** (note, fréquence, conditions d'enregistrement)

### ❌ À ÉVITER :
- Modifier directement les fichiers dans `data/raw/`
- Mélanger signaux réels et synthétiques dans le même dossier
- Oublier de noter les conditions d'enregistrement (distance micro, bruit, etc.)

---

## 🎸 Tableau des fréquences (d'après ton image)

| Note | Fréquence (Hz) | Octave |
|------|----------------|--------|
| E    | 82.4 Hz        | E2     |
| A    | 110.0 Hz       | A2     |
| D    | 146.8 Hz       | D3     |
| G    | 196.0 Hz       | G3     |
| B    | 246.9 Hz       | B3     |
| E    | 329.6 Hz       | E4     |

---

## 🚀 Prochaines étapes suggérées

1. **Créer `data/metadata.csv`** avec les infos sur tes enregistrements
2. **Développer `music_theory.py`** pour convertir Hz → Note + cents
3. **Créer un script d'analyse** pour tester ton algorithme sur tes WAV
4. **Mesurer la précision** (MAE en cents) sur tes 3 fichiers

