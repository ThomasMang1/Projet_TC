from flask import Flask, render_template, jsonify, request
from models import db, Plante, Zone, Arrosage, Robot
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///irrigo.db'
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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)