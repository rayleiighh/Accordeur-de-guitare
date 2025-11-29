# ✅ Checklist de Démonstration - Accordeur de Guitare

## 📋 Préparation avant la présentation (9 décembre)

### 🔴 **CRITIQUE (À faire absolument)**

- [ ] **Tester le micro** (10 min avant)
  ```bash
  python -c "import sounddevice as sd; print(sd.query_devices())"
  ```
  → Vérifier que le micro apparaît dans la liste

- [ ] **Tester main.py** (1 corde complète)
  ```bash
  cd accordeur_mvp
  python main.py → Mode 1 → Jouer 1 corde → Vérifier résultat
  ```
  → Si ça marche : ✅ Prêt
  → Si ça échoue : Utiliser Mode 2 (fichiers WAV)

- [ ] **Fermer les autres applis audio**
  - ❌ Fermer Spotify, YouTube, Discord
  - ❌ Fermer Teams, Zoom (si ouverts)
  - ✅ Garder seulement le terminal Python

- [ ] **Préparer la guitare**
  - [ ] Désaccorder volontairement la 6ème corde (E2) de ~30 cents
  - [ ] Scénario : "Je vais montrer comment corriger une corde désaccordée"

- [ ] **Avoir un plan B**
  - [ ] Copier `data/raw/*.wav` sur le Bureau (secours si micro défaillant)
  - [ ] Tester `python main.py → Mode 2 → Fichier 4 (Tous)`

---

### 🟡 **RECOMMANDÉ (Optionnel mais utile)**

- [ ] **Chronométrer la démo**
  - Objectif : **4-5 minutes de démo** + 5 min d'explications
  - Répéter 1× à la maison avec minuteur

- [ ] **Préparer les réponses aux questions**
  - "Pourquoi autocorrélation et pas FFT ?"
  - "Pourquoi N = 4096 ?"
  - "Quelles sont les limites ?"
  - → Voir [SCENARIO_UTILISATION.md](SCENARIO_UTILISATION.md) section "Script présentation"

- [ ] **Imprimer le poster A1**
  - Format : PDF sur clé USB
  - Prévoir : impression A1 couleur OU projection écran

---

## 🎬 **Scénario de Démo Recommandé (5 minutes)**

### **Minute 0-1 : Lancement + Explications**

**Action :**
```bash
cd accordeur_mvp
python main.py
```

**💬 Dire :**
> "Voici notre accordeur basé sur l'**autocorrélation**. Le menu affiche les **4 chapitres du cours** utilisés. Je choisis **Mode 1** pour une démonstration en temps réel."

---

### **Minute 1-3 : Enregistrement + Analyse**

**Action :**
1. Taper `1` (Mode 1)
2. Appuyer sur Entrée
3. Jouer la **6ème corde** (E2) désaccordée
4. Appuyer sur Entrée pour arrêter
5. Taper `n` (ne pas sauvegarder)

**💬 Dire pendant l'analyse :**
> "Le programme analyse **3 fenêtres** de 4096 échantillons. Voici le pipeline :
> 1. **Filtre notch 50 Hz** : retire le bruit électrique
> 2. **Passe-bande 70-1500 Hz** : garde seulement la plage guitare
> 3. **Autocorrélation FFT** : détecte la période du signal
> 4. **Interpolation parabolique** : précision sub-échantillon"

**Résultat affiché :**
```
Fenêtre 1 :  80.12 Hz → E2 ( -23.5 cents) ↓ TROP_BAS
```

**💬 Dire :**
> "On voit que la corde est **23.5 cents trop basse** (symbole ↓). Je vais la **resserrer**."

---

### **Minute 3-4 : Correction + Re-test**

**Action :**
1. Resserrer la mécanique de la guitare
2. Retour au menu (Entrée)
3. Refaire Mode 1
4. Rejouer la même corde

**Résultat attendu :**
```
Fenêtre 1 :  82.35 Hz → E2 (  -1.2 cents) ✓ JUSTE
MAE : 1.2 cents
```

**💬 Dire :**
> "Maintenant la corde est **juste** (symbole ✓). Erreur de seulement **1.2 cents**, largement sous l'objectif de **10 cents**."

---

### **Minute 4-5 : Validation automatique (optionnel)**

**Action :**
1. Quitter le programme (taper `0` × 2)
2. Lancer `python eval_pitch.py`

**💬 Dire :**
> "Le script d'évaluation teste **3 fichiers WAV** : corde juste, trop basse, trop haute. Sur la corde bien accordée, **MAE = 2.80 cents**. Taux de détection **100%**, aucune erreur d'octave."

---

## 🚨 **Gestion des Problèmes (Plan B)**

### **PROBLÈME 1 : Micro non détecté**

**Symptôme :**
```
❌ Erreur : Impossible de détecter le micro
```

**Solution immédiate :**
1. Dire au jury : "J'ai un problème de micro, je bascule sur les **fichiers de test**"
2. Lancer `python main.py → Mode 2 → Choix 4 (Tous)`
3. Expliquer les résultats affichés

**💬 Dire :**
> "J'ai préparé des fichiers WAV pour valider la robustesse. On voit que le système détecte correctement les 3 états."

---

### **PROBLÈME 2 : Signal trop faible**

**Symptôme :**
```
⚠️  Signal très faible !
Aucune fréquence détectée
```

**Solution immédiate :**
1. Rapprocher le micro de la guitare (~10 cm)
2. Jouer **plus fort**
3. Réessayer

**Si ça persiste :**
→ Basculer sur Mode 2 (fichiers WAV)

---

### **PROBLÈME 3 : Fréquence bizarre détectée**

**Symptôme :**
```
Fenêtre 1 :  523.25 Hz → ? (erreur)
```

**Cause probable :** Bruit ambiant (voix, ventilateur)

**Solution :**
1. Attendre le silence
2. Réessayer
3. Si ça persiste → Mode 2

---

## 📊 **Points Clés à Mettre en Avant**

### ✅ **Résultats Techniques**
- **MAE = 2.80 cents** (objectif ≤10 cents → **dépassé**)
- **Latence ~100 ms** (objectif ≤150 ms → **OK**)
- **Taux détection 100%** (objectif ≥95% → **parfait**)

### ✅ **Choix Techniques Justifiés**
- **Autocorrélation** > FFT : robuste aux harmoniques fortes
- **Filtre notch 50 Hz** : bruit secteur européen
- **N = 4096** : compromis résolution temps/fréquence
- **Fs = 48 kHz** : Shannon-Nyquist (fmax = 1500 Hz)

### ✅ **Références au Cours**
- Chap. 2 p.52 : Wiener-Khinchin (FFT)
- Chap. 5 p.150 : Butterworth
- Chap. 6 p.166 : Shannon-Nyquist
- Chap. 7 p.195 : Autocorrélation

---

## 🎯 **Après la Démo : Questions Probables**

### **Question 1 : "Pourquoi autocorrélation et pas FFT ?"**

**Réponse :**
> "Les cordes de guitare ont des **harmoniques fortes**. Avec la FFT pure, le 2ème harmonique (2×f₀) peut être plus fort que la fondamentale, causant une **erreur d'octave**. L'autocorrélation détecte la **période** du signal, qui est identique pour f₀ et tous ses harmoniques → plus robuste."

---

### **Question 2 : "Pourquoi N = 4096 ?"**

**Réponse :**
> "Compromis résolution temps-fréquence :
> - **Résolution fréquentielle** : Δf = 48000/4096 = **11.7 Hz** → suffisant (écart E2-A2 = 27 Hz)
> - **Résolution temporelle** : 4096/48000 = **85 ms** → acceptable (<150 ms)
> - Si N plus petit → moins précis. Si N plus grand → latence trop élevée."

---

### **Question 3 : "Quelles sont les limites ?"**

**Réponse :**
> "3 limites principales :
> 1. **Mono** : une seule corde à la fois (pas d'accords)
> 2. **Bruit ambiant** : environnement calme recommandé
> 3. **Cordes graves** : E2 (82 Hz) proche de la limite basse (70 Hz) → moins stable
>
> Solutions possibles : séparation de sources (hors scope MVP), filtrage adaptatif."

---

### **Question 4 : "Avez-vous testé sur plusieurs guitares ?"**

**Réponse :**
> "Testé sur **1 guitare classique** avec 3 états d'accordage (juste/±50 cents). Pour une validation plus robuste, il faudrait tester sur :
> - Guitare électrique (harmoniques différents)
> - Guitare folk (cordes acier)
> - Différentes distances micro
>
> C'est prévu dans `strategies_de_validation.md` (54+ prises), mais par manque de temps, on a validé le **principe** sur 3 fichiers."

---

### **Question 5 : "Votre code est-il reproductible ?"**

**Réponse :**
> "Oui, totalement :
> - **requirements.txt** : dépendances exactes
> - **README.md** : installation pas-à-pas + troubleshooting
> - **eval_pitch.py** : script d'évaluation automatique
> - **Fichiers test** : 3 WAV fournis dans `data/raw/`
>
> N'importe qui peut lancer `pip install -r requirements.txt` puis `python main.py`."

---

## ✅ **Checklist Finale (Jour J)**

### **10 minutes avant**
- [ ] Brancher le micro USB
- [ ] Tester `python main.py → Mode 1` (1 essai)
- [ ] Fermer toutes les applis audio
- [ ] Ouvrir le terminal dans `accordeur_mvp/`

### **5 minutes avant**
- [ ] Désaccorder la 6ème corde volontairement
- [ ] Préparer la guitare à portée de main
- [ ] Relire les 3 points clés (MAE, latence, détection)

### **Juste avant de commencer**
- [ ] Respirer profondément
- [ ] Sourire 😊
- [ ] Se rappeler : **votre code fonctionne !**

---

## 🎉 **Message de Confiance**

Vous avez :
- ✅ Un code fonctionnel avec **MAE = 2.80 cents**
- ✅ Une documentation complète (485 lignes)
- ✅ Des justifications académiques solides
- ✅ Un scénario de démo préparé

**Vous êtes PRÊT !** 🚀

Même si un problème technique arrive (micro défaillant), vous avez un **plan B** (Mode 2 avec fichiers WAV) et vous savez **expliquer le pourquoi** de chaque choix.

**Bonne chance pour la présentation ! 🎸**

---

**Dernière mise à jour** : 29 novembre 2025
