from flask import Blueprint, request, jsonify
from app import db
from models import Plante

bp = Blueprint("routes", __name__)

@bp.route("/plantes", methods=["GET"])
def get_plantes():
    plantes = Plante.query.all()
    return jsonify([{"id": p.id, "nom": p.nom, "humidite_min": p.humidite_min, "humidite_max": p.humidite_max} for p in plantes])

@bp.route("/plantes", methods=["POST"])
def add_plante():
    data = request.json
    nouvelle_plante = Plante(nom=data["nom"], humidite_min=data["humidite_min"], humidite_max=data["humidite_max"])
    db.session.add(nouvelle_plante)
    db.session.commit()
    return jsonify({"message": "Plante ajoutée"}), 201
