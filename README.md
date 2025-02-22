# 🎲 Projet Domino - Jeu Multijoueur  

## 📌 Description  
**Domino** est un jeu de dominos multijoueur développé avec **Godot** pour le front et **Django REST Framework** (DRF) pour l'API.  
Ce projet permet aux joueurs de s'affronter en ligne avec un système de sessions.  

## 🚀 Technologies  
- **Backend (API) :** Python, Django, Django REST Framework (DRF)  
- **Frontend (Jeu) :** Godot Engine (Version 4.3)  
- **Base de données :** PostgreSQL (hébergée sur Neon) et Redis (hébergée sur Northflank)  
- **Déploiement API :** Northflank avec Docker  
- **Worker Celery :** Déployé sur Northflank avec Docker  
- **WebSockets :** Communication en temps réel entre les joueurs  
- **Celery :** Gestion des tâches programmées  
- **Exécutable Godot :** Le jeu peut être utilisé directement via un exécutable généré  

## 🛠️ Installation & Configuration  

### **1️⃣ Installation de l’API (Django DRF)**  

📌 **Prérequis :** Python 3.12, pip, virtualenv  

```bash
cd api
python -m venv venv
source venv/bin/activate  # (ou venv\Scripts\activate sous Windows)
pip install -r requirements.txt
```

📌 **Fichier `.env` à configurer :**  

```env
SECRET_KEY=''
DEBUG=False
DATABASE_URL=''
REDIS_URL=''
EXTERNAL_HOSTNAME=''
```

📌 **Migrations de la base de données :**  
```bash
python manage.py migrate
```

📌 **Lancer le serveur Django :**  
```bash
python manage.py runserver
```
L'API est accessible sur **`http://127.0.0.1:8000/`**  

### **2️⃣ Lancer le Front (Godot)**  

📌 **Prérequis :** Godot Engine 4.3  

Installer Godot 4.3 et importer le dossier Godot_front

Le projet s’ouvre directement, prêt à être lancé en mode debug (une version exécutable est disponible).  


## 📡 Endpoints API (Django DRF)  

### 🔓 **Authentification** (Aucun token requis)

- **`POST /signup`** → Inscription d’un nouvel utilisateur
    - **Champs :**
        - `pseudo` *(string, requis)* → Pseudo unique (UTF-8)
        - `mdp` *(string, requis)* → Mot de passe (8-20 caractères)
        - `image` *(string, optionnel)* → Avatar encodé en Base64
- **`POST /login`** → Connexion à un compte existant
    - **Champs :**
        - `pseudo` *(string, requis)* → Identifiant du joueur
        - `mdp` *(string, requis)* → Mot de passe du compte
- **`POST /access`** → Rafraîchissement du token JWT
    - **Champs :**
        - `refresh_token` *(string, requis)* → Token de rafraîchissement valide

### 📋 **Sessions** (🔒Token requis)

- **`POST /create`** → Créer une session de jeu
    - **Champs :**
        - `session_name` *(string, optionnel)* → Nom de la session
        - `max_players_count` *(int, optionnel)* → Nombre de joueurs max (2-4)
        - `reflexion_time` *(int, optionnel)* → Temps de réflexion (20-90 sec)
        - `definitive_leave` *(bool, optionnel)* → Autoriser les départs définitifs
        - `is_public` *(bool, optionnel)* → Session publique ou privée
- **`GET /sessions`** → Lister les sessions publiques disponibles
- **`GET /join`** → Rejoindre une session existante
    - **Champs :**
        - `code` *(string, requis)* → Code unique de la session
- **`POST /update`** → Modifier les paramètres d’une session
    - **Champs :**
        - `session_name` *(string, optionnel)* → Nouveau nom de session
        - `max_players_count` *(int, optionnel)* → Nombre max de joueurs
        - `reflexion_time` *(int, optionnel)* → Temps de réflexion mis à jour
        - `definitive_leave` *(bool, optionnel)* → Autoriser les départs définitifs
        - `is_public` *(bool, optionnel)* → Rendre la session publique ou privée
        - `order` *(string, optionnel)* → Nouvel ordre de jeu [pseudo, pseudo, …]
        - `hote` *(int, optionnel)* → Nouvel hôte de la session (son pseudo)
- **`GET /kill`** → Quitter et supprimer une session
    - **Champs :**
        - `session_id` *(string, requis)* → Identifiant de la session

### 🎮 **Partie** (🔒Token requis)

- **`GET /start`** → Démarrer une partie
    - **Champs :**
        - `session_id` *(int, requis)* → Identifiant de la session
- **`POST /play`** → Jouer un domino
    - **Champs :**
        - `session_id` *(int, requis)* → Identifiant de la session
        - `round_id` *(int, requis)* → Identifiant du round en cours
        - `domino_id` *(int, requis)* → Identifiant du domino joué
        - `side` *(string, requis)* → Côté où le domino est joué (`"left"` ou `"right"`)
- **`GET /dominos`** → Récupérer la liste des dominos en jeu

### 🌐 **Connexion au WebSocket**

L’API **Domino** utilise **WebSockets** pour assurer la communication en temps réel entre les joueurs. Cette connexion est utilisée pour la gestion des **sessions**, des **parties** et des **interactions en direct**.

---

### 🔗 **URL du WebSocket**

```
ws://<EXTERNAL_HOSTNAME>/ws/session/?session_id=<SESSION_ID>&token=<ACCESS_TOKEN>
```

- **`<EXTERNAL_HOSTNAME>`** : URL du serveur.
- **`<SESSION_ID>`** : Identifiant unique de la session en cours.
- **`<ACCESS_TOKEN>`** : Token JWT valide pour l’authentification.

Si le token est **absent ou invalide**, la connexion est refusée.


### 📩 **Format des Messages WebSocket**
---

Tous les messages WebSocket respectent le format suivant :

```json
{
  "action": "string",
  "data": { ... } | null
}

```

- **`action`** : Nom de l’action exécutée.
- **`data`** : Objet contenant les informations associées (ou `null` si aucune donnée).


### 📡 **Messages WebSocket Reçus par Tous les Joueurs**
---

Le serveur envoie les messages suivants à **tous les joueurs** connectés à la session :

| **Action** | **Description** |
| --- | --- |
| `session.player_join` | Un joueur a rejoint la session |
| `session.player_leave` | Un joueur a quitté la session |
| `session.hote_leave` | L’hôte a quitté, la session est fermée |
| `session.player_statut` | Statut d’un joueur mis à jour |
| `session.start_game` | Début d’une partie |
| `session.end_game` | Fin de la session |
| `game.someone_mix_the_dominoes` | Un joueur a mélangé les dominos |
| `game.new_round` | Nouveau round démarré |
| `game.someone_played` | Un joueur a joué un domino |
| `game.someone_pass` | Un joueur a passé son tour |
| `game.someone_win` | Un joueur a gagné la partie |
| `game.blocked` | La partie est bloquée, tous les joueurs sont boudés |

---

### 🎯 **Messages WebSocket Reçus Uniquement par un Joueur**

---

Le serveur envoie certains messages **uniquement au joueur concerné** :

| **Action** | **Description** |
| --- | --- |
| `game.your_turn` | C'est le tour du joueur |
| `game.your_turn_no_match` | C'est le tour du joueur, mais aucun domino jouable |

---

### 📤 **Messages WebSocket Envoyés par le Client**
---

Le client peut envoyer les messages suivants au serveur :

| **Action** | **Description** |
| --- | --- |
| `game.pass` | Passer son tour |
| `session.player_statut` | Modifier son statut (prêt ou non) |
| `game.mix_the_dominoes` | Mélanger les dominos |

## 🎮 Fonctionnalités du Jeu  

### **1️⃣ Authentification**  
- Inscription et connexion des joueurs.  

### **2️⃣ Gestion des Sessions**  
- **Créer une session** avec :  
  - Nom de session  
  - Temps de réflexion configurable  
  - Option de reconnexion à une partie quittée ou non  
  - Choix de 2, 3 ou 4 joueurs max  
  - Session publique ou privée  
- **Rejoindre une session** 
  - **privée** en saisissant un code (si aucune partie n’a encore commencé).
  - **publique** depuis le menu qui affiche toutes les sessions disponibles. 
- **Lancer une partie** depuis le lobby (hôte uniquement).  
- **Gestion des départs :**  
  - **Hôte quitte → Session supprimée entièrement.**  
  - **Quitter en cours de partie → Statut Hors Ligne → Auto Play activé.**
  - **Reconnexion possible si "Quitter définitivement" n’est pas coché.**   
- **Statuts de Joueurs**
  - **AFK (30s d'inactivité) → Statut AFK**  
  - **Inactivité sur plusieurs tours → Statut Hors ligne → Auto Play activé.**  
- **Une session peut avoir X parties.**  
- **Une partie est gagnée en remportant 3 manches.**  
- **Suivi des statistiques par session :**  
  - Nombre de parties gagnées par joueur.  
  - Nombre de "cochons" (joueurs ayant gagné 0 manches durant une partie).  

### **3️⃣ Déroulement d’une Partie**  
#### **Début de partie**  
- Distribution de **7 dominos par joueur**.  
- **Premier joueur :**  
  - **À 4 joueurs → Celui qui a le double 6 commence.**  
  - **À 2 ou 3 joueurs → Celui qui a le plus grand domino commence.**  

#### **Durant la partie**  
- **Si temps de réflexion écoulé → Un domino valide est joué au hasard par le serveur.**  
- **Boudé :**  
  - Affichage du message *"Vous êtes boudé"*, délai de 3 à 5s avant de passer son tour.  
- **Seuls les dominos jouables sur la table peuvent être posés**.  
- **Possibilité de jouer un domino à droite ou à gauche**.  

#### **Fin de Partie & Conditions de Victoire**  
- **Un joueur pose son dernier domino → Victoire immédiate.**  
- **Le jeu est "mort" (tout le monde boudé) → Décompte des points de chaque main.**  
  - Le joueur ayant **le moins de points gagne la manche**.  
- **Un joueur remporte 3 manches → Victoire de la partie.**  
  - **Si un joueur n’a gagné aucune manche durant cette partie → il obtient un cochon (Il est COCHON!).**  
- **Retour au lobby avec possibilité de relancer une partie.**  

## 🔗 Liens utiles  
- **Documentation API :** [Disponible via Postman]  
- **Rapport académique :** *(ajouter un lien si applicable)*  

---

🎲 **Projet réalisé en MASTER MIAGE 2ème Année**  
📅 Dates : **1 Décembre 2024 → 7 mars 2025**  
👤 **Développeurs :** 
- Bastien SINITAMBIRIVOUTIN
- Nicolas BARBEU
- Julio GERMADE 
- Obed HALIAR
