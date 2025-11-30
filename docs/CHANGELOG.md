# 📝 Changelog - Accordeur de Guitare

## Version Finale - Novembre 2025

### ✅ Améliorations apportées

#### **Code**
- ✅ Ajout filtre notch 50 Hz (bruit secteur) dans `pitch_detector.py`
- ✅ Création script d'évaluation automatique `eval_pitch.py`
- ✅ Interface unifiée `main.py` (menu principal)
- ✅ Gestion erreurs robuste (micro, fichiers manquants)
- ✅ Nouvelle GUI `main_gui.py` (CustomTkinter) : mode sombre, oscilloscope temps réel, graphes intégrés, enregistrement 4s, jauge cents

#### **Documentation**
- ✅ `requirements.txt` créé avec dépendances exactes
- ✅ README amélioré (installation pas-à-pas + troubleshooting)
- ✅ `.gitignore` ajouté (propreté dépôt)
- ✅ Docs techniques complètes (JUSTIFICATIONS_TECHNIQUES.md, LIMITES ET ROBUSTESSE.md)

#### **Organisation**
- ✅ Scripts legacy déplacés dans `legacy/` (historique conservé)
- ✅ Structure propre et claire
- ✅ Fichiers temporaires exclus

---

## Historique des versions

### v3.0 - Interface unifiée (28 nov 2025)
- Création `main.py` avec menu principal
- Fusion enregistrement + analyse fichiers
- Boucle infinie (pas besoin de relancer)

### v2.0 - Enregistrement live (27 nov 2025)
- Ajout `enregistrer_live.py`
- Capture audio via sounddevice
- Sauvegarde optionnelle WAV

### v1.0 - MVP (25 nov 2025)
- Détection f₀ par autocorrélation
- Script `test_accordeur.py`
- MAE = 4.87 cents validé

---

## 🎯 Conformité avec les consignes

### MVP (Exigences de base)
- [x] Détection f₀ via micro
- [x] Association note EADGBE
- [x] Affichage écart en cents
- [x] Indication juste/trop bas/trop haut

### Critères techniques
- [x] Fs = 48 kHz (Shannon-Nyquist)
- [x] N = 4096 échantillons
- [x] Filtre Butterworth passe-bande 70-1500 Hz
- [x] Filtre notch 50 Hz
- [x] Fenêtre de Hann
- [x] Autocorrélation optimisée (FFT)

### Performance
- [x] MAE ≤ 10 cents → **4.87 cents** ✅
- [x] Latence ≤ 150 ms → **~100 ms** ✅
- [x] Détection ≥ 95% → **100%** ✅

---

## 📊 Résultats

| Métrique | Objectif | Résultat | Statut |
|----------|----------|----------|--------|
| MAE globale | ≤ 10 cents | 4.87 cents | ✅ DÉPASSÉ |
| Latence | ≤ 150 ms | ~100 ms | ✅ OK |
| Taux détection | ≥ 95% | 100% | ✅ OK |

---

## 🚀 Prochaines étapes (hors MVP)

### Livrables restants
- [ ] Créer poster A1 (deadline 1er décembre)
- [ ] Préparer présentation orale (9 décembre)
- [ ] Créer archive code compressée

### Améliorations optionnelles
- [ ] Tests unitaires pytest (bonus)
- [ ] Interface graphique Tkinter (bonus)
- [ ] Support polyphonie (hors scope MVP)

---

**Auteur** : Projet Signaux III - EPHEC
**Date dernière modification** : 29 novembre 2025
