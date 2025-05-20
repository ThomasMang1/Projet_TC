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

class RobotPacket:
    """Classe pour gérer les paquets de communication avec le robot"""
    
    @staticmethod
    def parse_packet(data_string: str) -> Optional[Dict]:
        """Parse un paquet reçu du robot"""
        try:
            # Vérifier si le paquet commence par $$$
            if not data_string.startswith('$$$'):
                return None
                
            # Extraire la partie JSON après $$$
            json_str = data_string[3:]
            
            # Vérifier si le paquet est valide
            if not (json_str.startswith('{') and json_str.endswith('}')):
                return None
                
            # Parser le JSON
            data = json.loads(json_str)
            print("parsed")
            
            # Vérifier le type de paquet
            if 'type' not in data:
                return None
                
            return data
            
        except Exception as e:
            logger.error(f"Erreur lors du parsing du paquet: {e}")
            return None
    
    @staticmethod
    def create_water_cmd(val: bool, amount: int = 0) -> str:
        """Crée un paquet de commande d'arrosage"""
        packet = {
            'type': 'water_cmd',
            'val': str(val).lower()
        }
        if val and amount > 0:
            packet['amount'] = amount
        return '$$$' + json.dumps(packet)
    
    @staticmethod
    def create_config(val: str) -> str:
        """Crée un paquet de configuration"""
        if val not in ['stop', 'go', 'calibrate']:
            raise ValueError("Valeur de configuration invalide")
        return '$$$' + json.dumps({
            'type': 'config',
            'val': val
        })

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
            self.ser.write((packet + '\n').encode('ascii'))
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du paquet: {e}")
            return False
    
    def read_line(self) -> Optional[str]:
        """Lit une ligne complète du port série"""
        try:
            while self.ser.in_waiting:
                byte = self.ser.read(1)
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
        packet_type = packet['type']
        
        if packet_type == 'colour':
            self.current_color = packet
            is_plant, water_volume = self.check_plant_by_color(packet)
            
            if is_plant and water_volume:
                # Envoyer la commande d'arrosage
                water_cmd = RobotPacket.create_water_cmd(True, water_volume)
                self.send_packet(water_cmd)
            else:
                # Envoyer une commande d'arrosage négative
                water_cmd = RobotPacket.create_water_cmd(False)
                self.send_packet(water_cmd)
                
        elif packet_type == 'acknowledge':
            if packet.get('status') == 'success':
                logger.info("Commande exécutée avec succès")
            else:
                logger.warning(f"Échec de la commande: {packet.get('status')}")
                
        elif packet_type == 'status':
            # Envoyer le status à l'API
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
    
    def run(self):
        """Boucle principale de communication"""
        if not self.connect():
            return
        
        while True:
            try:
                # Lire une ligne du port série
                line = self.read_line()
                
                if line:
                    # Parser le paquet
                    packet = RobotPacket.parse_packet(line)
                    if packet:
                        logger.info(f"Paquet reçu: {packet}")
                        self.handle_packet(packet)
                
                # Vérifier si c'est le moment d'envoyer un status
                current_time = time.time()
                if current_time - self.last_status_time >= STATUS_INTERVAL:
                    config = RobotPacket.create_config('go')
                    self.send_packet(config)
                    self.last_status_time = current_time
                
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
