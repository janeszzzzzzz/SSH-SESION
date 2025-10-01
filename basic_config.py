import serial
import time
import pandas as pd
import re


# ========= FUNCIONES =========

def obtener_modelo_serie(ser):
    """Ejecuta 'show inventory' y extrae modelo (PID) y serie (SN)."""
    # 🔥 Asegurar que no hay comandos abiertos
    ser.write(b"\x03\n")  # Ctrl+C
    time.sleep(1)
    ser.write(b"\n")      # Enter
    time.sleep(1)

    ser.write(b"show inventory\n")
    time.sleep(2)

    salida = ""
    if ser.in_waiting:
        salida = ser.read(ser.in_waiting).decode(errors="ignore")

    regex_modelo = re.search(r"PID:\s*([\w\-/]+)", salida)
    regex_serie = re.search(r"SN:\s*([\w\d]+)", salida)

    modelo = regex_modelo.group(1) if regex_modelo else None
    serie = regex_serie.group(1) if regex_serie else None

    return modelo, serie, salida


def configurar_dispositivo(ser, fila):
    """Envía comandos de configuración al dispositivo con los datos de la fila."""

    # 🔥 Asegurar que siempre partimos de modo EXEC privilegiado
    ser.write(b"\x03\n")  # Ctrl+C
    time.sleep(1)
    ser.write(b"enable\n")
    time.sleep(1)
    ser.write(b"\n")
    time.sleep(1)

    comandos = [
        "configure terminal",
        f"hostname {fila['nombre']}",
        f"username {fila['usuario']} password {fila['contrasena']}",
        f"ip domain-name {fila['dominio']}",
        "crypto key generate rsa modulus 1024",
    ]

    for cmd in comandos:
        ser.write(f"{cmd}\n".encode())
        time.sleep(1)

    # Tamaño de clave
    ser.write(b"1024\n")
    time.sleep(2)

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

    print(f"✅ Configuración aplicada a {fila['nombre']}")


def cargar_y_configurar():
    """Lee todo el Excel y configura los dispositivos que coincidan."""
    df = pd.read_excel(
        r"C:\Users\janet\OneDrive\Documentos\Pragramcion de redes\GIT LEARNING\dispositivos_ejemplo.xlsx"
    )

    columnas = {"modelo", "serie", "puerto", "baudios", "nombre", "usuario", "contrasena", "dominio"}
    if not columnas.issubset(df.columns):
        raise ValueError(f"El Excel debe tener las columnas: {columnas}")

    for puerto, baudios in df[["puerto", "baudios"]].drop_duplicates().values:
        try:
            print(f"\n🔌 Conectando al puerto {puerto}...")
            ser = serial.Serial(puerto, int(baudios), timeout=2)
            time.sleep(2)

            modelo_real, serie_real, salida = obtener_modelo_serie(ser)
            print(f"📋 Modelo detectado: {modelo_real}, Serie: {serie_real}")

            coincidencias = df[(df["modelo"] == modelo_real) & (df["serie"] == serie_real)]

            if not coincidencias.empty:
                for _, fila in coincidencias.iterrows():
                    print("✅ Coincidencia encontrada, configurando...")
                    configurar_dispositivo(ser, fila)
            else:
                print("⚠️ No hay coincidencia en el Excel, se omite configuración.")
                print("Salida completa de 'show inventory':\n", salida)

            ser.close()

        except Exception as e:
            print(f"❌ Error en {puerto}: {e}")


# ========= MAIN =========

if __name__ == "__main__":
    cargar_y_configurar()
