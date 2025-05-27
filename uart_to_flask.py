#!/usr/bin/env python3
# script_uart_to_flask.py
import serial
import requests
import time
import json
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Optional, Tuple

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
SERIAL_PORT = os.environ.get('SERIAL_PORT', 'COM3')
BAUD_RATE = int(os.environ.get('BAUD_RATE', '19200'))
API_URL = os.environ.get('API_URL', 'http://localhost:5000')
RETRY_INTERVAL = int(os.environ.get('RETRY_INTERVAL', '10'))
MAX_RETRIES = int(os.environ.get('MAX_RETRIES', '3'))
STATUS_INTERVAL = 10  # Intervalle d'envoi du status en secondes

class RobotBridge:
    """Classe principale pour gérer la communication avec le robot"""
    
    def __init__(self):
        self.ser = None
        self.last_status_time = 0
        self.current_color = None
        self.buffer = bytearray()
        
    def connect(self) -> bool:
        """Établit la connexion série avec le robot"""
        try:
            self.ser = serial.Serial(
                port=SERIAL_PORT,
                baudrate=BAUD_RATE,
                timeout=1,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            logger.info(f"Connexion établie sur {SERIAL_PORT} à {BAUD_RATE} bauds")
            return True
        except serial.SerialException as e:
            logger.error(f"Erreur de connexion série: {e}")
            return False
    
    def send_packet(self, packet: str) -> bool:
        """Envoie un paquet au robot"""
        try:
            if not self.ser:
                return False
            self.ser.write((packet).encode("ASCII"))
            logger.info("paquet ", packet, " envoyé dans l'UART")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du paquet: {e}")
            return False
    
    def read_line(self) -> Optional[str]: # Optional : retourne soit un str soit rien
        """Lit une ligne complète du port série"""
        try:
            while self.ser.in_waiting:
                byte = self.ser.read(1) # read(1) : lit un octet
                if byte:
                    if byte == b'\n':
                        # Fin de ligne trouvée
                        line = self.buffer.decode('ascii', errors='ignore').strip()
                        self.buffer.clear()
                        return line
                    else:
                        self.buffer.extend(byte)
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la lecture: {e}")
            self.buffer.clear()
            return None
    
    def parse_packet(self, data_string: str) -> Optional[Dict]:
        """Parse un paquet reçu du robot"""
        try:
            if not data_string.startswith('$$$'):
                return None
                
            json_str = data_string[3:]
            if not (json_str.startswith('{') and json_str.endswith('}')):
                return None
                
            data = json.loads(json_str)
            if 'type' not in data:
                return None
                
            return data
                
        except Exception as e:
            logger.error(f"Erreur lors du parsing du paquet: {e}")
            return None
    
    def check_plant_by_color(self, color: Dict) -> Tuple[bool, Optional[int]]:
        """Vérifie si une plante correspond à la couleur détectée"""
        try:
            # Appel à l'API pour vérifier la plante
            response = requests.post(
                f"{API_URL}/api/check_plant",
                json={'color': color},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('is_plant', False), data.get('water_volume')
            return False, None
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de la plante: {e}")
            return False, None
    
    def handle_packet(self, packet: Dict) -> None:
        """Gère un paquet reçu du robot"""
        try:
            packet_type = packet['type']
            
            if packet_type == 'colour':
                self.current_color = packet
                is_plant = True  # pour le test
                water_volume = "1"  # pour le test

                if is_plant and water_volume:
                    self.send_packet("1")
                else:
                    self.send_packet("0")
                    
            elif packet_type == 'humidity':
                self.send_packet("100")
                logger.info("Commande d'humidité exécutée avec succès")
                    
            elif packet_type == 'status':
                try:
                    response = requests.post(
                        f"{API_URL}/api/robot/status",
                        json=packet,
                        timeout=5
                    )
                    if response.status_code != 200:
                        logger.warning(f"Erreur lors de l'envoi du status: {response.text}")
                except Exception as e:
                    logger.error(f"Erreur lors de l'envoi du status: {e}")
            else:
                logger.warning(f"Type de paquet inconnu: {packet_type}")
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement du paquet: {e}")
    
    def run(self):
        """Boucle principale de communication"""
        logger.info("Démarrage du bridge UART")
        if not self.connect():
            return
        
        while True:
            try:
                # Lire une ligne du port série
                line = self.read_line()
                
                if line:
                    packet = self.parse_packet(line)
                    if packet:
                        logger.info(f"Paquet reçu: {packet}")
                        self.handle_packet(packet)
                
                # Petit délai pour éviter de surcharger le CPU
                time.sleep(0.1)
                
            except serial.SerialException as e:
                logger.error(f"Erreur de communication série: {e}")
                time.sleep(5)
                if not self.connect():
                    return
                    
            except Exception as e:
                logger.error(f"Erreur inattendue: {e}")
                time.sleep(1)
        
        # Fermer le port série (ne sera jamais atteint dans cette boucle infinie)
        if self.ser:
            self.ser.close()

if __name__ == "__main__":
    try:
        bridge = RobotBridge()
        bridge.run()
    except KeyboardInterrupt:
        logger.info("Arrêt du programme par l'utilisateur")
    except Exception as e:
        logger.critical(f"Erreur critique: {e}")
