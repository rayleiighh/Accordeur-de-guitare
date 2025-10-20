
# Accordeur de guitare numérique 

## Présentation  
Ce projet vise à développer un **accordeur de guitare numérique** capable de détecter en temps réel la fréquence fondamentale (f₀) d’une corde jouée et de l’associer à la note la plus proche selon le diapason standard (A4 = 440 Hz).  
L’utilisateur est informé si la corde est **trop basse**, **juste** ou **trop haute**.  

## Fonctionnalités  
- Acquisition audio via micro (44,1 ou 48 kHz).  
- Filtrage et prétraitement du signal.  
- Détection de f₀ par **autocorrélation** ou **YIN**.  
- Conversion fréquence → note + écart en cents.  
- Affichage simple et en temps réel.  

## Objectifs  
- **Précision** : erreur ≤ 10 cents.  
- **Latence** : délai ≤ 150 ms.  
- **Robustesse** : stabilité en présence de bruit modéré.  

## Livrables  
- Code source (Python 3 + bibliothèques scientifiques).  
- Poster A1 et présentation orale.  
- Démonstration live ou via fichiers audio.  
