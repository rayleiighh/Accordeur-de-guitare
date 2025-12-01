# JOUR J – Présentation Accordeur de Guitare Numérique (Temps Réel)

## 1) Scénario de démo (pas à pas)
- Lancer `python accordeur_mvp/main_gui.py` (déjà en mode dark).
- Onglet contrôles : cliquer **Oscillo temps réel** (montrer le signal live qui bouge).
- Charger un fichier : cliquer **Analyser un fichier wav** → choisir `data/raw/bonne_accord.wav` → afficher note, cents, jauge, 3 graphes (temps, spectre complet, zoom 70‑1500 Hz).
- Montrer l’impact du filtrage : cliquer **Visualiser FFT (script)** → sélectionner un fichier → afficher les deux spectres (avant/après filtrage) et les pics annotés.
- Enregistrement live : cliquer **🔴 Enregistrer avec micro (4s)** → jouer une corde → noter que le fichier apparaît dans `data/enregistrements/`, relancer **Analyser un fichier wav** pour ce nouveau fichier.
- Optionnel : relancer **Oscillo temps réel** pour montrer le flux en direct et la latence faible (~10 ms de traitement).

## 2) Argumentaire technique (théorie + pratique)
- Filtrage Butterworth (ordre 4, 70‑1500 Hz)
  - Théorie : limite de bande pour éviter le repliement et le bruit hors bande, réponse plate (cours Chap. 5).
  - Pratique : couvre E2 (82 Hz) à E4 (330 Hz) + harmoniques utiles, réduit le bruit de manipulation.
- Fenêtre de Hann (N=4096)
  - Théorie : réduit les fuites spectrales (cours Chap. 7, fenêtrage).
  - Pratique : meilleure lisibilité des pics sur guitare, moins de bords abrupts.
- Autocorrélation via FFT (Wiener‑Khinchin)
  - Théorie : R(t)=IFFT(|FFT|²), complexité O(N log N) vs O(N²).
  - Pratique : temps de traitement ~10 ms par fenêtre → quasi temps réel, robuste aux harmoniques.
- Interpolation parabolique
  - Théorie : raffine la position du pic pour précision sub‑échantillon.
  - Pratique : gagne quelques cents de précision (<5 cents observé).
- Fs = 48 kHz (Shannon‑Nyquist)
  - Théorie : Fs ≥ 2*f_max; f_max guitare ~1500 Hz → marge confortable.
  - Pratique : compatible cartes son courantes, latence raisonnable.

## 3) FAQ “Pièges” (Q/R courtes)
1. **Pourquoi 4096 échantillons ?** Compromis temps/fréquence : ~85 ms, résolution ≈11.7 Hz, latence acceptable.
2. **Pourquoi pas juste la FFT pour f0 ?** FFT seule est sensible aux harmoniques; l’autocorrélation détecte la périodicité → plus fiable sur guitare.
3. **Pourquoi Butterworth ordre 4 ?** Pente suffisante pour couper hors bande sans trop de retard de phase; ordre plus élevé complexifie et ajoute latence.
4. **Latence totale ?** Traitement ~10 ms/fenêtre; latence perçue surtout liée à la fenêtre (~85 ms) + audio I/O (quelques ms).
5. **Sensibilité au bruit ?** Filtre bande + notch (50 Hz) + seuil RMS; en environnement très bruyant, préférer mode fichier ou rapprocher le micro.

## 4) Chiffres clés à retenir
- Fs = 48 kHz ; N = 4096 ; bande 70‑1500 Hz ; fenêtrage Hann.
- Résolution fréquentielle ≈ 11.7 Hz (48k / 4096).
- Précision typique : < 5 cents (avec interpolation parabolique).
- Traitement par fenêtre : ~10 ms (autocorrélation via FFT).
- Erreur absolue moyenne (tests) : ~5–6 cents.

---

# Script oral (10 minutes)

**Minute 0‑2 — Membre 1 (Contexte & Objectif)**  
“Bonjour, nous sommes [les 4 noms]. Objectif : un accordeur de guitare numérique en temps réel. Défi : détecter la fondamentale malgré les harmoniques et le bruit, avec faible latence. Présentation rapide de la GUI : jauge cents, note, oscillo live, spectres.”

**Minute 2‑5 — Membre 2 (Théorie du Signal)**  
“FFT seule n’est pas robuste aux harmoniques → on utilise l’autocorrélation. Grâce au théorème de Wiener‑Khinchin, on calcule l’ACF via FFT en O(N log N). Fenêtrage Hann pour limiter les fuites. Filtrage Butterworth 70‑1500 Hz pour éviter repliement et bruit. Fs=48 kHz (Shannon) pour couvrir la guitare avec marge.”

**Minute 5‑7 — Membre 3 (Implémentation & Choix Techniques)**  
“Python + numpy/scipy/sounddevice/customtkinter. Pipeline : prétraitement (notch 50 Hz intégré dans pitch_detector), Butterworth, Hann, autocorr via FFT, interpolation parabolique. Fenêtre 4096 (≈85 ms) → résolution ~11.7 Hz, traitement ~10 ms. Gestion fichiers `data/raw` + enregistrements live; tri par date. GUI Matplotlib pour oscillo + spectres.”

**Minute 7‑10 — Membre 4 (Démo & Conclusion)**  
“Démonstration : lancer GUI, oscillo live, analyser un WAV (note/cents/graphes), montrer visualiser.py pour avant/après filtrage, enregistrer 4 s au micro et ré‑analyser. Résultats : précision <5 cents, robustesse aux harmoniques. Limites : bruit extrême, polyphonie hors scope. Conclusion : temps réel atteint, fondements DSP du cours appliqués.” 

Conseil final : chaque membre enchaîne sans pause, la démo est synchronisée avec le discours du membre 4 pendant les 3 dernières minutes.
