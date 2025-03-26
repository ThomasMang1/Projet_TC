from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Plante(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    humidite_min = db.Column(db.Float, nullable=False)
    humidite_max = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    date_plantation = db.Column(db.DateTime, default=datetime.now(datetime.UTC))
    qr_code = db.Column(db.String(200))
    zone_id = db.Column(db.Integer, db.ForeignKey('zone.id'))
    arrosages = db.relationship('Arrosage', backref='plante', lazy=True)

class Zone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    plantes = db.relationship('Plante', backref='zone', lazy=True)
    humidite_actuelle = db.Column(db.Float)
    derniere_mesure = db.Column(db.DateTime)

class Arrosage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.now(datetime.UTC))
    quantite_eau = db.Column(db.Float, nullable=False)  # en litres
    plante_id = db.Column(db.Integer, db.ForeignKey('plante.id'), nullable=False)
    humidite_avant = db.Column(db.Float)
    humidite_apres = db.Column(db.Float)

class Robot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    niveau_batterie = db.Column(db.Float)  # en pourcentage
    niveau_eau = db.Column(db.Float)  # en litres
    position_x = db.Column(db.Float)
    position_y = db.Column(db.Float)
    etat = db.Column(db.String(50))  # 'en_charge', 'en_arrosage', 'en_recharge_eau', 'en_attente'
    derniere_mise_a_jour = db.Column(db.DateTime, default=datetime.utcnow)
