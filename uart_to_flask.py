#!/usr/bin/env python3
# script_uart_to_flask.py
import serial
import requests
import time
import json
import re
import logging
import sys
import os
from datetime import datetime

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("uart_bridge.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration
SERIAL_PORT = os.environ.get('SERIAL_PORT', '/dev/ttyUSB0')  # Port série par défaut
BAUD_RATE = int(os.environ.get('BAUD_RATE', '9600'))  # Vitesse de communication
API_URL = os.environ.get('API_URL', 'http://localhost:5000')  # URL de l'API
RETRY_INTERVAL = int(os.environ.get('RETRY_INTERVAL', '10'))  # Intervalle entre les tentatives en secondes
MAX_RETRIES = int(os.environ.get('MAX_RETRIES', '3'))  # Nombre maximum de tentatives en cas d'échec

def parse_data(data_string):
    """Parse les données reçues du robot au format T=22.4;H=51.0;BATT=83.2;WATER=15.0"""
    try:
        # Utiliser une expression régulière pour extraire les valeurs
        pattern = r'([A-Z]+)=([0-9.]+)'
        matches = re.findall(pattern, data_string)
        
        if not matches:
            logger.warning(f"Format de données invalide: {data_string}")
            return None
            
        # Convertir en dictionnaire
        data = {}
        for key, value in matches:
            data[key] = float(value)
            
        # Vérifier que toutes les données attendues sont présentes
        required_keys = ['T', 'H', 'BATT', 'WATER']
        if not all(key in data for key in required_keys):
            logger.warning(f"Données incomplètes: {data}")
            return None
            
        return data
    except Exception as e:
        logger.error(f"Erreur lors du parsing des données: {e}")
        return None

def send_to_api(data):
    """Envoie les données à l'API Flask"""
    if not data:
        return False
        
    # Préparer les données pour l'API
    api_data = {
        "temperature": data.get('T'),
        "humidity": data.get('H'),
        "battery": data.get('BATT'),
        "water_level": data.get('WATER'),
        "timestamp": datetime.now().isoformat()
    }
    
    # Tentatives d'envoi avec retry
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                f"{API_URL}/api/data", 
                json=api_data,
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info(f"Données envoyées avec succès: {api_data}")
                return True
            else:
                logger.warning(f"Erreur HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur de connexion (tentative {attempt+1}/{MAX_RETRIES}): {e}")
            
        # Attendre avant de réessayer
        if attempt < MAX_RETRIES - 1:
            time.sleep(2)
            
    return False

def main():
    """Fonction principale"""
    logger.info(f"Démarrage du bridge UART vers API sur {SERIAL_PORT} à {BAUD_RATE} bauds")
    
    # Configuration du port série
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    except serial.SerialException as e:
        logger.error(f"Impossible d'ouvrir le port série {SERIAL_PORT}: {e}")
        return
    
    # Boucle principale
    while True:
        try:
            # Lire une ligne du port série
            line = ser.readline().decode().strip()
            
            if line:
                logger.info(f"Reçu du robot: {line}")
                
                # Parser les données
                parsed_data = parse_data(line)
                
                if parsed_data:
                    # Envoyer à l'API
                    send_to_api(parsed_data)
            
            # Attendre avant la prochaine lecture
            time.sleep(RETRY_INTERVAL)
            
        except serial.SerialException as e:
            logger.error(f"Erreur de communication série: {e}")
            # Attendre plus longtemps en cas d'erreur
            time.sleep(30)
            
        except Exception as e:
            logger.error(f"Erreur inattendue: {e}")
            time.sleep(10)
    
    # Fermer le port série (ne sera jamais atteint dans cette boucle infinie)
    ser.close()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Arrêt du programme par l'utilisateur")
    except Exception as e:
        logger.critical(f"Erreur critique: {e}")
