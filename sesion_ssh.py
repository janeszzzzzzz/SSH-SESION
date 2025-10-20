import io
import textfsm
from netmiko import ConnectHandler
from getpass import getpass

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

def compilar(plantilla):
    return textfsm.TextFSM(io.StringIO(plantilla))

def buscar_mac_por_ip(salida_arp, ip):
    fsm = compilar(TEMPLATE_ARP)
    for registro in fsm.ParseText(salida_arp):
        if registro[0] == ip:
            return registro[1]
    return None

def buscar_puerto_por_mac(salida_mac, mac):
    fsm = compilar(TEMPLATE_MAC)
    for vlan, mac_reg, tipo, puerto in fsm.ParseText(salida_mac):
        if mac_reg.lower() == mac.lower():
            return puerto
    return None

def buscar_dispositivo(ip_switch, usuario, contrasena, ip_objetivo, visitados=None):
    if visitados is None: visitados=set()
    if ip_switch in visitados: return None
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
        print(f"⚠️ No se pudo conectar: {e}")
        return None

    hostname = conexion.send_command("show run | i hostname").replace("hostname","").strip()
    salida_arp = conexion.send_command("show ip arp")
    salida_mac = conexion.send_command("show mac address-table")

    mac = buscar_mac_por_ip(salida_arp, ip_objetivo)
    if not mac:
        conexion.disconnect()
        return None

    puerto = buscar_puerto_por_mac(salida_mac, mac)
    if not puerto:
        conexion.disconnect()
        return None

    # revisamos si ese puerto tiene vecino CDP
    cdp_cmd = f"show cdp neighbors {puerto} detail"
    salida_cdp = conexion.send_command(cdp_cmd)

    if "IP address:" in salida_cdp:
        for line in salida_cdp.splitlines():
            if "IP address:" in line:
                vecino_ip = line.split(":")[1].strip()
                print(f"↪️ La MAC está por {puerto}, conectado a otro switch ({vecino_ip})")
                conexion.disconnect()
                return buscar_dispositivo(vecino_ip, usuario, contrasena, ip_objetivo, visitados)

    # si no hay vecino CDP en ese puerto, es el host final
    print(f"\n✅ Dispositivo final encontrado en {hostname} ({ip_switch})")
    print(f"🔌 Puerto físico: {puerto}")
    print(f"💾 MAC Address: {mac}")
    conexion.disconnect()
    return {"switch": hostname, "ip": ip_switch, "puerto": puerto, "mac": mac}

def main():
    print("\n=== 🚀 Localizador por CDP en modo access ===\n")
    ip_inicial = input("IP de un switch inicial: ").strip()
    ip_objetivo = input("IP del dispositivo a buscar: ").strip()
    usuario = input("Usuario SSH: ").strip() or "admin"
    contrasena = getpass("Contraseña SSH: ")

    resultado = buscar_dispositivo(ip_inicial, usuario, contrasena, ip_objetivo)
    if not resultado:
        print("\n❌ No se encontró el dispositivo.\n")

if __name__ == "__main__":
    main()
