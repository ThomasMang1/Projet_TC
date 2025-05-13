from app import app, db
from models import Arrosage
from datetime import datetime, timedelta, timezone

def insert_sample_data():
    with app.app_context():
        # Supprimer les données existantes pour éviter les doublons
        Arrosage.query.delete()
        
        # Créer des données pour les 7 derniers jours
        for i in range(7):
            date = datetime.now(timezone.utc) - timedelta(days=i)
            arrosage = Arrosage(
                date=date,
                quantite_eau=2.5 + (i * 0.5),  # Quantité d'eau variable
                plante_id=2,  # Assurez-vous que cette plante existe dans votre base
                humidite_avant=45.0 - (i * 2),
                humidite_apres=65.0 + (i * 2)
            )
            db.session.add(arrosage)
        
        # Sauvegarder les changements
        db.session.commit()
        print("Données d'exemple insérées avec succès!")

if __name__ == "__main__":
    insert_sample_data() 