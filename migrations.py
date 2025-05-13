from app import app, db
from models import Robot
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def migrate_database():
    """Ajoute les nouvelles colonnes à la table Robot"""
    with app.app_context():
        try:
            # Créer les nouvelles colonnes
            db.engine.execute('ALTER TABLE robot ADD COLUMN IF NOT EXISTS niveau_eau_max FLOAT')
            db.engine.execute('ALTER TABLE robot ADD COLUMN IF NOT EXISTS niveau_eau_min FLOAT')
            db.engine.execute('ALTER TABLE robot ADD COLUMN IF NOT EXISTS couleur_actuelle VARCHAR(50)')
            
            print("Migration réussie : Nouvelles colonnes ajoutées à la table Robot")
            
        except Exception as e:
            print(f"Erreur lors de la migration : {e}")
            raise

def reset_robot_table():
    """Réinitialise la table Robot"""
    with app.app_context():
        try:
            # Supprimer la table existante
            Robot.__table__.drop(db.engine, checkfirst=True)
            
            # Recréer la table avec le nouveau schéma
            Robot.__table__.create(db.engine)
            
            # Créer un robot par défaut
            robot = Robot(
                nom="Robot Principal",
                niveau_batterie=100.0,
                niveau_eau=0.0,
                niveau_eau_max=5.0,  # 5 litres par défaut
                niveau_eau_min=0.5,  # 0.5 litres par défaut
                position_x=0.0,
                position_y=0.0,
                etat="en_attente",
                couleur_actuelle=None
            )
            
            db.session.add(robot)
            db.session.commit()
            
            print("Réinitialisation réussie : Table Robot recréée avec le nouveau schéma")
            
        except Exception as e:
            print(f"Erreur lors de la réinitialisation : {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    # Choisir l'action à effectuer
    action = input("Que souhaitez-vous faire ? (1: Migration, 2: Réinitialisation) : ")
    
    if action == "1":
        migrate_database()
    elif action == "2":
        confirm = input("ATTENTION: La réinitialisation va supprimer toutes les données de la table Robot. Continuer ? (o/n) : ")
        if confirm.lower() == 'o':
            reset_robot_table()
        else:
            print("Opération annulée")
    else:
        print("Action non reconnue") 