# 🟡 Pac-Man — Python / Pygame

<p align="center">
  🎮 Reproduction moderne du célèbre jeu d’arcade <b>Pac-Man</b><br>
  Développée en <b>Python</b> avec <b>Pygame</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.x-blue?logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/Pygame-Game%20Engine-green">
  <img src="https://img.shields.io/badge/Status-In%20Development-orange">
  <img src="https://img.shields.io/badge/Platform-Windows-lightgrey">
</p>

---

## 🎮 Présentation

Ce projet est une recréation du jeu mythique **Pac-Man**, développée en Python avec le moteur graphique Pygame.

Il repose sur une architecture modulaire permettant une évolution simple et claire du projet.

### ✨ Fonctionnalités principales

- 🟡 Déplacement fluide du joueur  
- 👻 Fantômes avec comportements distincts  
- 🧠 Logique d’intelligence artificielle  
- 💥 Détection des collisions  
- 🎬 Animations directionnelles  
- 🔊 Gestion audio  
- 🗺 Carte basée sur une grille  

🎯 **Objectif :**  
Manger toutes les pastilles tout en évitant les fantômes.

---

## 🛠 Technologies utilisées

| Technologie | Description |
|------------|------------|
| 🐍 Python 3 | Langage principal |
| 🎮 Pygame | Moteur graphique |
| 🔧 Git | Gestion de version |
| 🌍 GitHub | Hébergement du projet |

---

## 📂 Structure du projet

```text
Pac-Man/
│
├── assets/              # Sprites et ressources
│
├── script/              # Logique du jeu
│   ├── ai.py
│   ├── animation.py
│   ├── audio.py
│   ├── game_play.py
│   ├── ghost.py
│   ├── map.py
│   ├── player.py
│   └── render.py
│
├── main.py              # Point d’entrée
└── .gitignore
```

---

## ⚙️ Installation

### 1️⃣ Cloner le projet

```bash
git clone https://github.com/wargriff/Pac-Man.git
cd Pac-Man
```

### 2️⃣ Installer les dépendances

```bash
pip install pygame
```

### 3️⃣ Lancer le jeu

```bash
python main.py
```

---

## 🧠 Architecture technique

Le projet suit une séparation claire des responsabilités :

- `player.py` → Gestion du joueur  
- `ghost.py` → Comportement des fantômes  
- `ai.py` → Logique décisionnelle  
- `map.py` → Gestion de la grille  
- `render.py` → Affichage graphique  
- `game_play.py` → Boucle principale  

Cette organisation permet :

- ✔ Une maintenance simplifiée  
- ✔ L’ajout facile de nouvelles fonctionnalités  
- ✔ Une évolution vers un projet plus complexe  

---

## 🚀 Générer un exécutable (.exe)

Pour créer une version Windows :

```bash
pip install pyinstaller
pyinstaller --onefile --windowed main.py
```

Le fichier final sera disponible dans :

```
dist/
```

📌 Recommandation :  
Publier le `.exe` dans **GitHub → Releases** plutôt que dans le dépôt principal.

---

## 🔮 Améliorations futures

- 🎮 Menu principal
- 🏆 Système de High Score
- 📈 Niveaux progressifs
- ⚡ Mode Power-Up
- 🤖 IA plus avancée
- 🌍 Version multi-plateforme

---

## 👤 Auteur

**Wargriff**

Projet personnel réalisé dans le cadre de l’apprentissage du développement de jeux en Python.