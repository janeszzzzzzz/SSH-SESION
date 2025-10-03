import serial
import time
import pandas as pd
import textfsm
from ntc_templates.parse import parse_output


# ========= FUNCIONES =========

def obtener_modelo_serie(ser):
    """Ejecuta 'show inventory' y obtiene modelo y serie con TextFSM."""
    ser.write(b"\x03\n")  # Ctrl+C para limpiar
    time.sleep(1)
    ser.write(b"show inventory\n")
    time.sleep(3)
 
    salida = ""
    if ser.in_waiting:
        salida = ser.read(ser.in_waiting).decode(errors="ignore")

    try:
        parsed = parse_output(platform="cisco_ios", command="show inventory", data=salida)
        if parsed:
            modelo = parsed[0].get("pid")
            serie = parsed[0].get("sn")
            return modelo, serie, salida
    except Exception as e:
        print("⚠️ Error al parsear con TextFSM:", e)

    return None, None, salida


def obtener_interfaces(ser):
    """Ejecuta 'show ip interface brief' y lo parsea con TextFSM."""
    ser.write(b"\x03\n")
    time.sleep(1)
    ser.write(b"show ip interface brief\n")
    time.sleep(3)

    salida = ""
    if ser.in_waiting:
        salida = ser.read(ser.in_waiting).decode(errors="ignore")

    try:
        parsed = parse_output(platform="cisco_ios", command="show ip interface brief", data=salida)
        return parsed  # Lista de diccionarios
    except Exception as e:
        print("⚠️ Error al parsear interfaces:", e)

    return []


def limpiar_interfaces(parsed):
    """
    Filtra solo FastEthernet y GigabitEthernet.
    Devuelve dos listas con texto bonito: Fast y Giga.
    """
    fast, giga = [], []

    for i in parsed:
        if not i["interface"].startswith(("FastEthernet", "GigabitEthernet")):
            continue  # ignorar seriales y otros

        estado_admin = "up" if "up" in i["status"] else "down"
        estado_proto = i["proto"]
        resumen = f"administration: {estado_admin}, protocol: {estado_proto}"

        if i["interface"].startswith("FastEthernet"):
            fast.append(f"{i['interface']} ({resumen})")
        elif i["interface"].startswith("GigabitEthernet"):
            giga.append(f"{i['interface']} ({resumen})")

    # Asegurar que ambas listas tengan mismo largo
    max_len = max(len(fast), len(giga)) if (fast or giga) else 0
    fast.extend([""] * (max_len - len(fast)))
    giga.extend([""] * (max_len - len(giga)))

    return fast, giga


def configurar_dispositivo(ser, fila):
    """Configura el dispositivo a partir de la fila del Excel."""
    ser.write(b"\x03\n")
    time.sleep(1)
    ser.write(b"enable\n")
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
        "write memory",
    ]
    for cmd in extra_cmds:
        ser.write(f"{cmd}\n".encode())
        time.sleep(1)

    print(f"✅ Configuración aplicada a {fila['nombre']}")


def cargar_y_configurar():
    """Lee Excel, configura dispositivos coincidentes y exporta interfaces."""
    ruta_excel = r"C:\Users\janet\OneDrive\Documentos\Pragramcion de redes\GIT LEARNING\dispositivos_ejemplo.xlsx"
    df = pd.read_excel(ruta_excel)

    columnas = {"modelo", "serie", "puerto", "baudios", "nombre", "usuario", "contrasena", "dominio"}
    if not columnas.issubset(df.columns):
        raise ValueError(f"El Excel debe tener las columnas: {columnas}")

    for puerto, baudios in df[["puerto", "baudios"]].drop_duplicates().values:
        try:
            print(f"\n🔌 Conectando al puerto {puerto}...")
            ser = serial.Serial(puerto, int(baudios), timeout=3)
            time.sleep(2)

            modelo_real, serie_real, salida = obtener_modelo_serie(ser)
            print(f"📋 Modelo detectado: {modelo_real}, Serie: {serie_real}")

            coincidencias = df[(df["modelo"] == modelo_real) & (df["serie"] == serie_real)]

            if not coincidencias.empty:
                for idx, fila in coincidencias.iterrows():
                    print("✅ Coincidencia encontrada, configurando...")
                    configurar_dispositivo(ser, fila)

                    # 🔥 Obtener interfaces y limpiar
                    interfaces = obtener_interfaces(ser)
                    if interfaces:
                        fast, giga = limpiar_interfaces(interfaces)
                        # Guardar como texto unido por salto de línea
                        df.at[idx, "FastEthernet"] = "\n".join(fast)
                        df.at[idx, "GigabitEthernet"] = "\n".join(giga)
                    else:
                        df.at[idx, "FastEthernet"] = "No detectadas"
                        df.at[idx, "GigabitEthernet"] = "No detectadas"

            else:
                print("⚠️ No hay coincidencia en el Excel, se omite configuración.")
                print("Salida completa de 'show inventory':\n", salida)

            ser.close()

        except Exception as e:
            print(f"❌ Error en {puerto}: {e}")

    # Guardar resultados en Excel actualizado
    df.to_excel(ruta_excel, index=False)
    print(f"\n📂 Archivo Excel actualizado en: {ruta_excel}")


# ========= MAIN =========
if __name__ == "__main__":
    cargar_y_configurar()
