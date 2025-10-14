import io
import textfsm
from netmiko import ConnectHandler
from getpass import getpass

# ============================= #
# Plantillas TextFSM corregidas
# ============================= #

# Para 'show ip arp' según salida real de tu SW2
TEMPLATE_ARP = """\
Value IP (\d+\.\d+\.\d+\.\d+)
Value MAC ([0-9a-fA-F.]+)
Value INTERFACE (\S+)

Start
  ^Internet\s+${IP}\s+\S+\s+${MAC}\s+ARPA\s+${INTERFACE} -> Record
"""

# Para 'show mac address-table' estándar Cisco
TEMPLATE_MAC = """\
Value VLAN (\d+)
Value MAC ([0-9a-fA-F.]+)
Value TYPE (\S+)
Value PORT (\S+)

Start
  ^\s*${VLAN}\s+${MAC}\s+${TYPE}\s+${PORT} -> Record
"""

# ============================= #
# Funciones auxiliares
# ============================= #

def compilar_plantilla(texto):
    """Compila una plantilla TextFSM desde un string."""
    return textfsm.TextFSM(io.StringIO(texto))

def buscar_mac_por_ip(salida_arp, ip_objetivo):
    """Busca la MAC de una IP en la tabla ARP."""
    fsm = compilar_plantilla(TEMPLATE_ARP)
    registros = fsm.ParseText(salida_arp)
    for ip, mac, interfaz in registros:
        if ip == ip_objetivo:
            return mac
    return None

def buscar_puerto_por_mac(salida_mac, mac_objetivo):
    """Busca el puerto asociado a una MAC en la tabla MAC."""
    fsm = compilar_plantilla(TEMPLATE_MAC)
    registros = fsm.ParseText(salida_mac)
    for vlan, mac, tipo, puerto in registros:
        if mac.lower() == mac_objetivo.lower():
            return puerto
    return None

# ============================= #
# Programa principal
# ============================= #

def main():
    print("\n=== Localizador de dispositivos por IP (usa switch como fuente) ===\n")

    ip_switch = input("¿Qué IP del switch quieres usar para buscar? (ej. 192.168.1.11): ").strip()
    ip_objetivo = input("¿Qué IP del dispositivo quieres encontrar? (ej. 192.168.1.50): ").strip()
    usuario = input("Usuario SSH (por defecto 'admin'): ").strip() or "admin"
    contrasena = getpass("Contraseña SSH: ")

    dispositivo = {
        "device_type": "cisco_ios",
        "host": ip_switch,
        "username": usuario,
        "password": contrasena,
    }

    try:
        print("\nConectando al switch... aguanta, que ya casi llegamos. 🤖")
        conexion = ConnectHandler(**dispositivo)
    except Exception as e:
        print("\n💥 Error al conectar por SSH:", e)
        print("\nVerifica:")
        print("1️⃣ Que el switch tenga habilitado SSH (ip domain-name, crypto key generate rsa, transport input ssh)")
        print("2️⃣ Que el usuario tenga privilegios 15.")
        print("3️⃣ Que el puerto 22 no esté bloqueado por firewall.\n")
        return

    print("\n📡 Ejecutando comandos 'show ip arp' y 'show mac address-table'...\n")
    salida_arp = conexion.send_command("show ip arp")
    salida_mac = conexion.send_command("show mac address-table")

    mac_encontrada = buscar_mac_por_ip(salida_arp, ip_objetivo)

    if mac_encontrada:
        print(f"✅ IP {ip_objetivo} tiene la MAC {mac_encontrada}")
        puerto = buscar_puerto_por_mac(salida_mac, mac_encontrada)
        if puerto:
            print(f"🔌 El dispositivo está conectado al puerto: {puerto}\n")
        else:
            print("⚠️ No se encontró el puerto en la tabla MAC.\n")
    else:
        print("❌ No se encontró esa IP en la tabla ARP.\n")

    conexion.disconnect()
    print("🔌 Conexión cerrada.\n")

# ============================= #
# Punto de entrada
# ============================= #

if __name__ == "__main__":
    main()
