# Irrigo - Robot d'Arrosage Intelligent

## Contributors
Bououdina Kenzi
Parriault Lyse 
Mangin Thomas
Meyer Robin
Nouri Lisa
Ross Jonathan

## Description
Irrigo est une application web permettant de gérer un robot d'arrosage autonome pour jardin. L'application permet de :
- Surveiller l'état du robot (batterie, niveau d'eau, position)
- Gérer les zones d'arrosage
- Suivre les plantes et leurs besoins en eau
- Visualiser la consommation d'eau
- Intégrer les données météorologiques

## Installation

1. Cloner le repository :
```bash
git clone [URL_DU_REPO]
cd irrigo
```

2. Initialiser et lancer le conteneur docker (avec le docker-compose) :

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

4. Initialiser la base de données :
```bash
python app.py
```

## Structure du Projet
- `app.py` : Application Flask principale
- `models.py` : Modèles de données SQLAlchemy
- `templates/` : Templates HTML
- `static/` : Fichiers statiques (CSS, JS, images)
- `requirements.txt` : Dépendances Python

## Fonctionnalités
- Interface utilisateur responsive
- Mise à jour en temps réel des données
- Gestion des zones d'arrosage
- Suivi des plantes
- Visualisation des données météorologiques
- Historique des arrosages

## API Endpoints
- `GET /api/plantes` : Liste des plantes
- `GET /api/robot/status` : État du robot
- `GET /api/zones` : Liste des zones
- `GET /api/arrosages` : Historique des arrosages

## Technologies Utilisées
- HTML/CSS
- Python 3.8+
- Flask
- SQLAlchemy
- PostgreSQL
