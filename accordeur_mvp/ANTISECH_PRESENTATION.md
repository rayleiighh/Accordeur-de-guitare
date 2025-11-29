# 📄 Anti-Sèche Présentation - Accordeur de Guitare

**À imprimer et garder sous les yeux pendant la présentation (9 déc)**

---

## 🎯 **LES 3 CHIFFRES MAGIQUES**

| Métrique | Objectif | Résultat | Symbole |
|----------|----------|----------|---------|
| **MAE** | ≤ 10 cents | **2.80 cents** | ✅ **×3.5 mieux** |
| **Latence** | ≤ 150 ms | **~100 ms** | ✅ **33% plus rapide** |
| **Détection** | ≥ 95% | **100%** | ✅ **Parfait** |

---

## 🔧 **PIPELINE EN 4 ÉTAPES**

```
1. NOTCH 50 Hz     → Retire bruit secteur (Q=30)
2. PASSE-BANDE     → Garde 70-1500 Hz (Butterworth ordre 4)
3. AUTOCORRÉLATION → Détecte période (FFT O(N log N))
4. INTERPOLATION   → Précision sub-échantillon (parabolique)
```

---

## 📚 **RÉFÉRENCES COURS (à citer)**

| Chapitre | Page | Utilisation |
|----------|------|-------------|
| **Chap. 2** | p.52 | Wiener-Khinchin (FFT pour ACF) |
| **Chap. 5** | p.150 | Butterworth (réponse plate) |
| **Chap. 6** | p.166 | Shannon-Nyquist (Fs ≥ 2×fmax) |
| **Chap. 7** | p.195 | Autocorrélation (détection f₀) |

---

## 🎬 **DÉROULÉ DÉMO (5 min)**

### **Min 0-1 : Lancement**
```bash
cd accordeur_mvp
python main.py → 1 (Mode micro)
```
**Dire :** "Voici l'interface avec les 4 chapitres du cours."

### **Min 1-3 : Enregistrement**
- Jouer **6ème corde (E2)** désaccordée
- Montrer résultat : `↓ TROP_BAS (-23.5 cents)`
**Dire :** "Pipeline : notch 50 Hz → passe-bande → autocorrélation → résultat."

### **Min 3-4 : Correction**
- Resserrer la mécanique
- Rejouer → `✓ JUSTE (-1.2 cents)`
**Dire :** "MAE = 1.2 cents, largement sous l'objectif de 10 cents."

### **Min 4-5 : Validation**
```bash
python eval_pitch.py
```
**Dire :** "3 fichiers testés. Corde juste : MAE = 2.80 cents. Taux détection : 100%."

---

## 💡 **RÉPONSES AUX 5 QUESTIONS PROBABLES**

### **Q1 : Pourquoi autocorrélation > FFT ?**
**R :** "Harmoniques fortes sur guitare. FFT confond 2×f₀ avec f₀ (erreur d'octave). ACF détecte la **période** → robuste."

### **Q2 : Pourquoi N = 4096 ?**
**R :** "Compromis :
- Δf = 11.7 Hz → suffisant (E2-A2 = 27 Hz)
- Δt = 85 ms → acceptable (<150 ms)"

### **Q3 : Limites ?**
**R :** "1) Mono (1 corde à la fois), 2) Bruit ambiant, 3) Cordes graves moins stables."

### **Q4 : Testé sur combien de guitares ?**
**R :** "1 guitare, 3 états (juste/±50 cents). Validation principe OK. Pour robustesse complète : 54+ prises (doc `strategies_validation.md`)."

### **Q5 : Code reproductible ?**
**R :** "Oui : `requirements.txt` + README + `eval_pitch.py`. N'importe qui peut lancer."

---

## 🚨 **PLAN B (si problème micro)**

**Symptôme :** `❌ Impossible de détecter le micro`

**Action immédiate :**
```bash
python main.py → 2 (Mode fichiers) → 4 (Tous)
```

**Dire :** "Problème micro. Je bascule sur les **fichiers de test préparés**."

**Résultat affiché :**
- `bonne_accord.wav` → MAE = 2.80 cents ✓
- `accord_basse.wav` → -47 cents ↓
- `accord_haute.wav` → +51 cents ↑

**Dire :** "Système détecte correctement les 3 états. Taux détection 100%."

---

## 📊 **PARAMÈTRES TECHNIQUES (si question)**

| Paramètre | Valeur | Justification |
|-----------|--------|---------------|
| **Fs** | 48 kHz | Shannon : Fs ≥ 2×1500 Hz |
| **N** | 4096 | Compromis temps/fréquence |
| **Filtre PB** | 70-1500 Hz | Plage guitare + harmoniques |
| **Filtre notch** | 50 Hz, Q=30 | Bruit secteur Europe |
| **Fenêtre** | Hann | Réduit effets de bord (p.192) |
| **Interpolation** | Parabolique | Précision sub-échantillon |

---

## ✅ **CHECKLIST DERNIÈRE MINUTE**

- [ ] Micro branché et testé (`sd.query_devices()`)
- [ ] Guitare 6ème corde désaccordée volontairement
- [ ] Terminal ouvert dans `accordeur_mvp/`
- [ ] Applis audio fermées (Spotify, YouTube)
- [ ] Fichiers WAV dans `data/raw/` (plan B)

---

## 🎯 **PHRASE D'INTRODUCTION**

> "Bonjour, je présente notre **accordeur de guitare numérique** basé sur l'**autocorrélation**. L'objectif est de détecter la **fréquence fondamentale** d'une corde et d'indiquer si elle est **juste, trop basse ou trop haute**. Notre système atteint une précision de **2.80 cents**, soit **3.5× mieux** que l'objectif de 10 cents."

---

## 🎯 **PHRASE DE CONCLUSION**

> "Notre accordeur respecte tous les critères :
> - **MAE = 2.80 cents** (objectif ≤10 cents)
> - **Latence ~100 ms** (objectif ≤150 ms)
> - **Détection 100%** (objectif ≥95%)
>
> Tous les choix techniques sont **justifiés par le cours** (4 chapitres cités). Le code est **reproductible** avec `requirements.txt`. Merci !"

---

## 🔑 **MOTS-CLÉS À PLACER**

- ✅ Autocorrélation (Chap. 7)
- ✅ Wiener-Khinchin (Chap. 2)
- ✅ Butterworth (Chap. 5)
- ✅ Shannon-Nyquist (Chap. 6)
- ✅ Interpolation parabolique
- ✅ Robustesse aux harmoniques
- ✅ MAE = 2.80 cents
- ✅ Taux détection 100%

---

## 💪 **MESSAGE FINAL**

**VOUS ÊTES PRÊT !**

Votre code fonctionne. Vos résultats sont excellents. Vos justifications sont solides.

Même si un problème technique survient, vous avez un **plan B**.

**Respirez, souriez, et montrez votre travail !** 🚀

---

**Dernière mise à jour** : 29 novembre 2025
**À imprimer en 1 page recto-verso**
