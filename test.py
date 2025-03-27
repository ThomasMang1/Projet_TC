import psycopg2
import os
os.environ["PYTHONIOENCODING"] = "utf-8"

conn = psycopg2.connect(dbname="irrigo_db", user="irrigo_user", password="irrigo_password", host="localhost", port="5432")

print(conn)