from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
CORS(app)

@app.route("/")
def home():
    return {"message": "Bienvenue sur Irrigo"}

if __name__ == "__main__":
    app.run(debug=True)
