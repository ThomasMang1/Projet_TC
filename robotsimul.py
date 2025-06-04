import serial
import time

ser = serial.Serial('COM3', 19200)
print("Connexion établie sur COM3 à 19200 bauds")
while True:
    ser.write(b'$\n')
    print("Envoi du paquet #")
    time.sleep(10)

## TEST STATUS
# ser.write(b'$$${"type":"status","full_wt":2000,"empty_wt":1000,"cur_wt":1800}\n')

## TEST COLOUR
# ser.write(b'$$${"type":"colour","r":1000,"g":3000,"b":1800}\n')

## TEST HUMIDITY
# ser.write(b'$$${"type":"humidity","humidity":15}\n')