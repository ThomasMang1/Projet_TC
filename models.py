from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Plante(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    humidite_min = db.Column(db.Float, nullable=False)
    humidite_max = db.Column(db.Float, nullable=False)
