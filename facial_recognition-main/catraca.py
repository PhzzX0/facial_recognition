import serial
from tkinter import *


# Configure a porta serial conforme sua ESP32
esp32 = serial.Serial('COM6', 9600)


def enviar_comando(comando):
    esp32.write(comando.encode())  # Envia comando como b'1', b'2', etc.
