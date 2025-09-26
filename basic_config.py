import serial
import time
import pandas as pd

def configurar_dispositivo(puerto, baudios, nombre, usuario, contrasena, dominio):
    """Configura un dispositivo de red mediante consola serial."""
    try:
        ser = serial.Serial(puerto, baudios, timeout=1)
        time.sleep(2)  # Esperar a que el dispositivo responda

        # Despertar la consola
        ser.write(b'\n')
        time.sleep(1)

        # Enviar comandos de configuración
        comandos = [
            "configure terminal",
            f"hostname {nombre}",
            f"username {usuario} password {contrasena}",
            f"ip domain-name {dominio}",
            "crypto key generate rsa",
        ]

        for cmd in comandos:
            ser.write(f"{cmd}\n".encode())
            time.sleep(1)

        # Enviar tamaño de clave RSA (si lo pide)
        ser.write(b"1024\n")
        time.sleep(2)

        # Configuración SSH y líneas
        extra_cmds = [
            "ip ssh version 2",
            "line console 0",
            "login local",
            "line vty 0 4",
            "login local",
            "transport input ssh",
            "transport output ssh",
            "end",
            "write memory"
        ]

        for cmd in extra_cmds:
            ser.write(f"{cmd}\n".encode())
            time.sleep(1)

        # Leer salida final
        time.sleep(1)
        if ser.in_waiting:
            salida = ser.read(ser.in_waiting).decode(errors="ignore")
            print(f"[{puerto}] Salida:\n{salida}")

        ser.close()
        print(f"[{puerto}] ✅ Configuración completada para {nombre}.")

    except Exception as e:
        print(f"[{puerto}] ❌ Error al configurar {nombre}: {e}")


def cargar_y_configurar(ruta_excel):
    """Lee el archivo Excel y configura cada dispositivo listado."""
    df = pd.read_excel(ruta_excel)

    # Verificar columnas necesarias
    columnas = {"puerto", "baudios", "nombre", "usuario", "contrasena", "dominio"}
    if not columnas.issubset(df.columns):
        raise ValueError(f"El Excel debe tener las columnas: {columnas}")

    for _, fila in df.iterrows():
        puerto = fila["puerto"]
        baudios = int(fila["baudios"])
        nombre = fila["nombre"]
        usuario = fila["usuario"]
        contrasena = fila["contrasena"]
        dominio = fila["dominio"]

        print(f"\n➡️ Configurando {nombre} en {puerto}...")
        configurar_dispositivo(puerto, baudios, nombre, usuario, contrasena, dominio)
        time.sleep(1)  # descanso entre equipos


if __name__ == "__main__":
    # Cambia la ruta si el Excel está en otra ubicación
    cargar_y_configurar("dispositivos_ejemplo.xlsx")
