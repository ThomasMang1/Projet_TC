from migrations import migrate_database, reset_robot_table
import sys

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        print("ATTENTION: Cette action va supprimer toutes les données de la table Robot.")
        confirmation = input("Êtes-vous sûr de vouloir continuer ? (oui/non): ")
        if confirmation.lower() == "oui":
            reset_robot_table()
            print("La table Robot a été réinitialisée avec succès.")
        else:
            print("Opération annulée.")
    else:
        migrate_database()

if __name__ == "__main__":
    main() 