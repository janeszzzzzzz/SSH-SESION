import io
import textfsm
from netmiko import ConnectHandler
from getpass import getpass

# ============================= #
# Plantillas TextFSM corregidas #
# ============================= #

TEMPLATE_ARP = r"""Value IP (\d+\.\d+\.\d+\.\d+)
Value MAC ([0-9a-fA-F.]+)
Value INTERFACE (\S+)

Start
  ^Internet\s+${IP}\s+\S+\s+${MAC}\s+ARPA\s+${INTERFACE} -> Record
"""

TEMPLATE_MAC = r"""Value VLAN (\d+)
Value MAC ([0-9a-fA-F.]+)
Value TYPE (\S+)
Value PORT (\S+)

Start
  ^\s*${VLAN}\s+${MAC}\s+${TYPE}\s+${PORT} -> Record
"""

TEMPLATE_CDP = r"""Value DEVICE_ID (\S+)
Value LOCAL_INT (\S+)
Value HOLDTIME (\d+)
Value CAPABILITIES (.+?)
Value PLATFORM (\S+)
Value PORT_ID (\S+)

Start
  ^Device ID: ${DEVICE_ID}
  ^Interface: ${LOCAL_INT},  +Port ID \(outgoing port\): ${PORT_ID} -> Record
"""

# ============================= #
# Funciones auxiliares          #
# ============================= #

def compilar(plantilla):
    """Compila un texto TextFSM desde string."""
    return textfsm.TextFSM(io.StringIO(plantilla))

def buscar_mac_por_ip(salida_arp, ip):
    """Devuelve la MAC asociada a una IP."""
    fsm = compilar(TEMPLATE_ARP)
    for registro in fsm.ParseText(salida_arp):
        if registro[0] == ip:
            return registro[1]
    return None

def buscar_puerto_por_mac(salida_mac, mac):
    """Devuelve el puerto asociado a una MAC."""
    fsm = compilar(TEMPLATE_MAC)
    for vlan, mac_reg, tipo, puerto in fsm.ParseText(salida_mac):
        if mac_reg.lower() == mac.lower():
            return puerto
    return None

def obtener_vecinos_cdp(salida_cdp):
    """Devuelve diccionario de puertos locales -> nombres de vecinos CDP."""
    fsm = compilar(TEMPLATE_CDP)
    return {local: device for device, local, *_ in fsm.ParseText(salida_cdp)}

# ============================= #
# Función recursiva principal   #
# ============================= #

def buscar_dispositivo(ip_switch, usuario, contrasena, ip_objetivo, visitados=None):
    if visitados is None:
        visitados = set()
    if ip_switch in visitados:
        return None
    visitados.add(ip_switch)

    print(f"\n🔗 Conectando a {ip_switch}...")
    dispositivo = {
        "device_type": "cisco_ios",
        "host": ip_switch,
        "username": usuario,
        "password": contrasena,
    }

    try:
        conexion = ConnectHandler(**dispositivo)
    except Exception as e:
        print(f"⚠️ Error al conectar a {ip_switch}: {e}")
        return None

    # Obtener hostname del switch
    hostname = conexion.send_command("show run | include hostname").replace("hostname", "").strip() or ip_switch

    salida_arp = conexion.send_command("show ip arp")
    salida_mac = conexion.send_command("show mac address-table")
    salida_cdp = conexion.send_command("show cdp neighbors detail")

    mac = buscar_mac_por_ip(salida_arp, ip_objetivo)
    if not mac:
        conexion.disconnect()
        return None

    puerto = buscar_puerto_por_mac(salida_mac, mac)
    vecinos = obtener_vecinos_cdp(salida_cdp)

    if puerto in vecinos:
        next_switch_name = vecinos[puerto]
        print(f"↪️ MAC aprendida en {puerto} (vecino detectado: {next_switch_name})")
        conexion.disconnect()
        # Aquí podrías mapear el nombre de vecino a su IP manualmente
        # o resolverlo con show cdp entry <name>
        return buscar_dispositivo(ip_switch, usuario, contrasena, ip_objetivo, visitados)
    else:
        print(f"\n✅ Dispositivo encontrado en {hostname} ({ip_switch})")
        print(f"🔌 Puerto: {puerto}")
        print(f"💾 MAC Address: {mac}\n")
        conexion.disconnect()
        return {
            "switch": hostname,
            "ip_switch": ip_switch,
            "puerto": puerto,
            "mac": mac
        }

# ============================= #
# Programa principal            #
# ============================= #

def main():
    print("\n=== 🚀 Localizador inteligente de dispositivos ===\n")
    ip_inicial = input("IP de un switch cualquiera: ").strip()
    ip_objetivo = input("IP del dispositivo que quieres encontrar: ").strip()
    usuario = input("Usuario SSH (por defecto 'admin'): ").strip() or "admin"
    contrasena = getpass("Contraseña SSH: ")

    resultado = buscar_dispositivo(ip_inicial, usuario, contrasena, ip_objetivo)
    if not resultado:
        print("\n❌ No se encontró el dispositivo en la red.\n")

# ============================= #
# Punto de entrada              #
# ============================= #

if __name__ == "__main__":
    main()
