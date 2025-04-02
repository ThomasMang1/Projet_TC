from sqlalchemy import create_engine
from sqlalchemy import text

#Mettre future=True lors de l'appel à create_engine() pour utiliser la fonctionnalité "commit as you go" 
engine = create_engine("postgresql+psycopg2://irrigo_user:irrigo_password@irrigo_postgres:5432/irrigo_db", echo=False)
##Afficher nom des tables de la base de données 
#print(engine.table_names())
#La méthode .connect() fait le lien entre notre script et la base de données
with engine.connect() as conn:
  ##Effectuons une première requête : selection des 10 premières lignes
    result = conn.execute(text("SELECT * from lieu LIMIT 10"))
    for row in result:
        print(f"x: {row[0]}  y: {row[1]}, z: {row[2]}")
    #Liste des différents lieux
    result2 = conn.execute(text("SELECT COUNT(DISTINCT id) FROM lieu"))
    print([x for x in result2])
    # Ordonner les différents sites par ordre alphabétique
    result3 = conn.execute(text("SELECT DISTINCT(id) FROM lieu ORDER BY id DESC"))
    #print([x for x in result3])

#INSERT : insérer de nouvelles lignes dans la base de données
with engine.begin() as conn:

    conn.execute(text("DELETE FROM lieu WHERE id IN (622,623)"))
    conn.execute(
      text("INSERT INTO lieu (id, nom, region) VALUES (:id, :city_name,:region)"),
       [{"id": 622, "city_name": "Bourg Bon Air","region":"Furansu"}, {"id": 623, "city_name": "New Cergy","region":"Furansu"}],
   )