from flask import Flask, render_template, jsonify, request, send_file
from models import db, Plante, Zone, Arrosage, Robot
from datetime import datetime, timezone, timedelta
import csv
import io
import os
import logging
from models import DatasetData
from meteomatics.api import query_time_series
import requests
from sqlalchemy import func
from flask import request
from flask import Flask, render_template, jsonify, request
from sqlalchemy import create_engine, text
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configuration de la base de données (PostgreSQL)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://irrigo_user:irrigo_password@localhost:5432/irrigo_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialisation de SQLAlchemy
db = SQLAlchemy(app)

# Route principale
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/plantes', methods=['GET'])
def get_plantes():
    result = db.session.execute(text("SELECT plantes, humidite_min, humidite_max FROM tableau_plantes"))
    plantes_disponibles = result.fetchall()
    plantes = [{
        'nom': p[0],
        'humidite_min': p[1],
        'humidite_max': p[2]
    } for p in plantes_disponibles]
    return jsonify(plantes)


@app.route('/api/plantes', methods=['POST'])
def add_plante():
    data = request.get_json()
    nom = data.get('nom')
    humidite_min = data.get('humidite_min')
    humidite_max = data.get('humidite_max')

    if not nom:
        return jsonify({'error': 'Nom de plante manquant'}), 400

    # Vérifier que la plante existe bien dans tableau_plantes
    result = db.session.execute(
        text("SELECT * FROM tableau_plantes WHERE plantes = :nom"),
        {'nom': nom}
    )
    plante_existante = result.fetchone()

    if not plante_existante:
        return jsonify({'error': "Cette plante n'existe pas dans la base de référence"}), 400

    new_plante = Plante(
        nom=nom,
        humidite_min=humidite_min,
        humidite_max=humidite_max
    )
    db.session.add(new_plante)
    db.session.commit()

    return jsonify({'message': 'Plante ajoutée avec succès'}), 201

@app.route('/api/robot/status', methods=['GET'])
def get_robot_status():
    robot = Robot.query.first()
    if robot:
        return jsonify({
            'batterie': robot.niveau_batterie,
            'eau': robot.niveau_eau,
            'etat': robot.etat,
            'position': {'x': robot.position_x, 'y': robot.position_y}
        })
    return jsonify({'error': 'Robot non trouvé'}), 404

@app.route('/api/zones', methods=['GET'])
def get_zones():
    zones = Zone.query.all()
    return jsonify([{
        'id': z.id,
        'nom': z.nom,
        'humidite_actuelle': z.humidite_actuelle,
        'nombre_plantes': len(z.plantes)
    } for z in zones])

@app.route('/api/arrosages', methods=['GET'])
def get_arrosages():
    arrosages = Arrosage.query.order_by(Arrosage.date.desc()).limit(10).all()
    return jsonify([{
        'id': a.id,
        'date': a.date.isoformat(),
        'plante': a.plante.nom,
        'quantite': a.quantite_eau,
        'humidite_avant': a.humidite_avant,
        'humidite_apres': a.humidite_apres
    } for a in arrosages])

@app.route('/api/plantes', methods=['POST'])
def create_plante():
    data = request.get_json()
    
    # Vérification des données requises
    if not all(k in data for k in ['nom', 'humidite_min', 'humidite_max', 'zone_id']):
        return jsonify({'error': 'Données manquantes. La zone est obligatoire.'}), 400
    
    # Validation des contraintes d'humidité
    humidite_min = float(data['humidite_min'])
    humidite_max = float(data['humidite_max'])
    
    if humidite_min < 0:
        return jsonify({'error': 'L\'humidité minimale doit être positive'}), 400
    if humidite_max > 100:
        return jsonify({'error': 'L\'humidité maximale ne peut pas dépasser 100%'}), 400
    if humidite_min >= humidite_max:
        return jsonify({'error': 'L\'humidité minimale doit être inférieure à l\'humidité maximale'}), 400
    
    # Vérification que la zone existe
    zone = Zone.query.get(data['zone_id'])
    if not zone:
        return jsonify({'error': 'Zone non trouvée'}), 404
    
    # Création de la nouvelle plante
    nouvelle_plante = Plante(
        nom=data['nom'],
        humidite_min=humidite_min,
        humidite_max=humidite_max,
        description=data.get('description'),
        zone_id=data['zone_id'],
        qr_code=data.get('qr_code')
    )
    
    try:
        db.session.add(nouvelle_plante)
        db.session.commit()
        return jsonify({
            'id': nouvelle_plante.id,
            'nom': nouvelle_plante.nom,
            'message': 'Plante créée avec succès'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/plantes/<int:plante_id>', methods=['PUT'])
def update_plante(plante_id):
    plante = Plante.query.get_or_404(plante_id)
    data = request.get_json()
    
    try:
        if 'nom' in data:
            plante.nom = data['nom']
        
        # Validation des contraintes d'humidité si modifiées
        if 'humidite_min' in data:
            humidite_min = float(data['humidite_min'])
            if humidite_min < 0:
                return jsonify({'error': 'L\'humidité minimale doit être positive'}), 400
            if humidite_min >= plante.humidite_max:
                return jsonify({'error': 'L\'humidité minimale doit être inférieure à l\'humidité maximale'}), 400
            plante.humidite_min = humidite_min
            
        if 'humidite_max' in data:
            humidite_max = float(data['humidite_max'])
            if humidite_max > 100:
                return jsonify({'error': 'L\'humidité maximale ne peut pas dépasser 100%'}), 400
            if humidite_max <= plante.humidite_min:
                return jsonify({'error': 'L\'humidité maximale doit être supérieure à l\'humidité minimale'}), 400
            plante.humidite_max = humidite_max
            
        if 'description' in data:
            plante.description = data['description']
        if 'zone_id' in data:
            plante.zone_id = data['zone_id']
        if 'qr_code' in data:
            plante.qr_code = data['qr_code']
            
        db.session.commit()
        return jsonify({
            'id': plante.id,
            'nom': plante.nom,
            'message': 'Plante mise à jour avec succès'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/plantes/<int:plante_id>', methods=['DELETE'])
def delete_plante(plante_id):
    plante = Plante.query.get_or_404(plante_id)
    
    try:
        db.session.delete(plante)
        db.session.commit()
        return jsonify({'message': 'Plante supprimée avec succès'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/plantes/<int:plante_id>', methods=['GET'])
def get_plante(plante_id):
    plante = Plante.query.get_or_404(plante_id)
    return jsonify({
        'id': plante.id,
        'nom': plante.nom,
        'humidite_min': plante.humidite_min,
        'humidite_max': plante.humidite_max,
        'description': plante.description,
        'zone_id': plante.zone_id,
        'qr_code': plante.qr_code
    })

@app.route('/api/zones', methods=['POST'])
def create_zone():
    data = request.get_json()
    
    if not all(k in data for k in ['nom']):
        return jsonify({'error': 'Le nom de la zone est obligatoire'}), 400
    
    nouvelle_zone = Zone(
        nom=data['nom'],
        humidite_actuelle=data.get('humidite_actuelle', 0)
    )
    
    try:
        db.session.add(nouvelle_zone)
        db.session.commit()
        return jsonify({
            'id': nouvelle_zone.id,
            'nom': nouvelle_zone.nom,
            'message': 'Zone créée avec succès'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/zones/<int:zone_id>', methods=['PUT'])
def update_zone(zone_id):
    zone = Zone.query.get_or_404(zone_id)
    data = request.get_json()
    
    try:
        if 'nom' in data:
            zone.nom = data['nom']
        if 'humidite_actuelle' in data:
            zone.humidite_actuelle = data['humidite_actuelle']
            
        db.session.commit()
        return jsonify({
            'id': zone.id,
            'nom': zone.nom,
            'message': 'Zone mise à jour avec succès'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/zones/<int:zone_id>', methods=['DELETE'])
def delete_zone(zone_id):
    zone = Zone.query.get_or_404(zone_id)
    
    # Vérifier si la zone contient des plantes
    if zone.plantes:
        return jsonify({'error': 'Impossible de supprimer une zone contenant des plantes'}), 400
    
    try:
        db.session.delete(zone)
        db.session.commit()
        return jsonify({'message': 'Zone supprimée avec succès'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/zones/<int:zone_id>', methods=['GET'])
def get_zone(zone_id):
    zone = Zone.query.get_or_404(zone_id)
    return jsonify({
        'id': zone.id,
        'nom': zone.nom,
        'humidite_actuelle': zone.humidite_actuelle,
        'plantes': [{
            'id': p.id,
            'nom': p.nom,
            'humidite_min': p.humidite_min,
            'humidite_max': p.humidite_max
        } for p in zone.plantes]
    })

@app.route('/api/plantes/export', methods=['GET'])
def export_plantes():
    # Créer un buffer en mémoire pour le fichier CSV
    si = io.StringIO()
    writer = csv.writer(si, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    
    # Écrire l'en-tête avec les colonnes
    writer.writerow([
        'ID',
        'Nom de la plante',
        'Humidité minimale (%)',
        'Humidité maximale (%)',
        'Description',
        'Zone',
        'Date de plantation',
        'QR Code'
    ])
    
    # Récupérer toutes les plantes
    plantes = Plante.query.all()
    
    # Écrire les données
    for plante in plantes:
        writer.writerow([
            str(plante.id),
            plante.nom,
            str(plante.humidite_min),
            str(plante.humidite_max),
            plante.description or '',
            plante.zone.nom if plante.zone else 'Non assignée',
            plante.date_plantation.strftime('%Y-%m-%d %H:%M:%S'),
            plante.qr_code or ''
        ])
    
    # Créer la réponse
    output = si.getvalue()
    si.close()
    
    return send_file(
        io.BytesIO(output.encode('utf-8-sig')),  # Utiliser utf-8-sig pour Excel
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'plantes_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )

@app.route('/api/data', methods=['POST'])
def receive_data():
    """Reçoit les données du robot via UART et met à jour la base de données"""
    try:
        data = request.get_json()
        
        # Vérifier que toutes les données requises sont présentes
        required_fields = ['temperature', 'humidity', 'battery', 'water_level']
        if not all(field in data for field in required_fields):
            return jsonify({"status": "error", "message": "Données incomplètes"}), 400
        
        # Récupérer le robot (on suppose qu'il n'y en a qu'un pour l'instant)
        robot = Robot.query.first()
        if not robot:
            # Créer un robot s'il n'existe pas
            robot = Robot(
                nom="Robot Principal",
                niveau_batterie=data['battery'],
                niveau_eau=data['water_level'],
                position_x=0,
                position_y=0,
                etat="en_attente"
            )
            db.session.add(robot)
        else:
            # Mettre à jour les données du robot
            robot.niveau_batterie = data['battery']
            robot.niveau_eau = data['water_level']
            robot.derniere_mise_a_jour = datetime.now()
        
        # Mettre à jour l'humidité des zones
        zones = Zone.query.all()
        for zone in zones:
            # Pour l'exemple, on met à jour toutes les zones avec la même humidité
            # Dans un cas réel, il faudrait identifier la zone concernée
            zone.humidite_actuelle = data['humidity']
            zone.derniere_mesure = datetime.now()
        
        # Enregistrer les modifications
        db.session.commit()
        
        return jsonify({"status": "ok", "message": "Données reçues et traitées"})
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Erreur lors du traitement des données: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    



@app.route('/api/meteo', methods=['GET'])
def get_meteo():
    try:
        # Récupération des paramètres lat et lon depuis l'URL
        lat = float(request.args.get('lat', 43.6045))  # Coordonnée par défaut : Toulouse, France
        lon = float(request.args.get('lon', 1.4442))

        api_key = "faac6c1944bff8f1353c89e2b45b646d"  # Remplacez par votre clé API

        # Vérification que la clé API existe
        if not api_key:
            return jsonify({'error': 'API key missing or invalid.'}), 400

        # Construction de l'URL de l'API OpenWeatherMap
        url = f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric'
    

        # Envoi de la requête GET
        response = requests.get(url)
        data = response.json()

        if response.status_code != 200:
            raise Exception(f"Erreur API: {data.get('message', 'Erreur inconnue')}")

        # Traitement de la réponse
        # OpenWeatherMap renvoie des informations sous une structure différente
        # Extraction des données principales
        main = data.get('main', {})
        weather = data.get('weather', [{}])[0]  # La liste "weather" contient un dictionnaire avec les informations météo

        # Si les données principales ne sont pas disponibles
        if not main or not weather:
            return jsonify({'error': 'Aucune donnée météo disponible pour cette localisation'}), 404

        # Création de la réponse avec les données extraites
        result = {
            'heure': datetime.utcfromtimestamp(data['dt']).isoformat(),  # Heure de la prévision en UTC
            'temperature_C': main.get('temp', 'Non disponible'),  # Température en Celsius
            'precipitations_mm': data.get('rain', {}).get('1h', 0),  # Précipitations sur la dernière heure (s'il y en a)
            'description': weather.get('description', 'Non disponible'),  # Description des conditions météorologiques (par ex. 'clair')
            'pluie': data.get('rain', {}).get('1h', 0),
            'humidity': main.get('humidity', 'Non disponible'),
            'wind_speed': data.get('wind', {}).get('speed', 'Non disponible')
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/consommation-eau', methods=['GET'])
def get_consommation_eau():
    try:
        # Récupérer la date d'il y a 7 jours
        date_limite = datetime.now(timezone.utc) - timedelta(days=7)
        
        # Requête pour obtenir la somme de l'eau consommée par jour
        resultats = db.session.query(
            func.date(Arrosage.date).label('date'),
            func.sum(Arrosage.quantite_eau).label('total_eau')
        ).filter(
            Arrosage.date >= date_limite
        ).group_by(
            func.date(Arrosage.date)
        ).all()
        
        # Créer un dictionnaire avec toutes les dates des 7 derniers jours
        dates = {}
        for i in range(7):
            date = (datetime.now(timezone.utc) - timedelta(days=i)).date()
            dates[date.isoformat()] = 0
        
        # Remplir avec les données de la base
        for date, total in resultats:
            dates[date.isoformat()] = float(total)
        
        # Convertir en liste triée par date
        consommation = [
            {'date': date, 'total_eau': total}
            for date, total in sorted(dates.items())
        ]
        
        return jsonify(consommation)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/check_plant', methods=['POST'])
def check_plant():
    """Vérifie si une plante correspond à la couleur détectée"""
    try:
        data = request.get_json()
        
        # Vérifier que les données de couleur sont présentes
        if not all(k in data for k in ['r', 'g', 'b']):
            return jsonify({'error': 'Données de couleur incomplètes'}), 400
            
        # Ici, vous devrez implémenter la logique pour vérifier si la couleur
        # correspond à une plante dans votre base de données
        # Pour l'exemple, nous retournons des valeurs fictives
        is_plant = True  # À remplacer par votre logique
        water_volume = 100  # Volume en ml
        
        return jsonify({
            'is_plant': is_plant,
            'water_volume': water_volume if is_plant else 0
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/robot/status', methods=['POST'])
def update_robot_status():
    """Met à jour le statut du robot"""
    try:
        data = request.get_json()
        
        # Récupérer le robot
        robot = Robot.query.first()
        if not robot:
            robot = Robot(nom="Robot Principal")
            db.session.add(robot)
            
        # Mettre à jour les données
        if 'full_wt' in data:
            robot.niveau_eau_max = data['full_wt']
        if 'empty_wt' in data:
            robot.niveau_eau_min = data['empty_wt']
        if 'cur_wt' in data:
            robot.niveau_eau = data['cur_wt']
            
        robot.derniere_mise_a_jour = datetime.now()
        
        db.session.commit()
        return jsonify({'status': 'ok'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/robot/humidity', methods=['POST'])
def update_humidity():
    """Met à jour les données d'humidité"""
    try:
        data = request.get_json()
        
        # Vérifier les données requises
        required_fields = ['dry_val', 'wet_val', 'humidity']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Données incomplètes'}), 400
            
        # Mettre à jour l'humidité de la zone actuelle
        # Note: Dans un cas réel, vous devrez déterminer la zone actuelle
        zones = Zone.query.all()
        for zone in zones:
            zone.humidite_actuelle = data['humidity']
            zone.derniere_mesure = datetime.now()
            
        db.session.commit()
        return jsonify({'status': 'ok'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
