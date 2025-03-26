from flask import Flask, render_template, jsonify, request
from models import db, Plante, Zone, Arrosage, Robot
from datetime import datetime
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

app = Flask(__name__)

# Configuration PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://irrigo_user:irrigo_password@localhost:5432/irrigo_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/plantes', methods=['GET'])
def get_plantes():
    plantes = Plante.query.all()
    return jsonify([{
        'id': p.id,
        'nom': p.nom,
        'humidite_min': p.humidite_min,
        'humidite_max': p.humidite_max,
        'zone': p.zone.nom if p.zone else None
    } for p in plantes])

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
    if not all(k in data for k in ['nom', 'humidite_min', 'humidite_max']):
        return jsonify({'error': 'Données manquantes'}), 400
    
    # Création de la nouvelle plante
    nouvelle_plante = Plante(
        nom=data['nom'],
        humidite_min=data['humidite_min'],
        humidite_max=data['humidite_max'],
        description=data.get('description'),
        zone_id=data.get('zone_id'),
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
        if 'humidite_min' in data:
            plante.humidite_min = data['humidite_min']
        if 'humidite_max' in data:
            plante.humidite_max = data['humidite_max']
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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)