# SSH-SESION
# 🧠 Localizador de Dispositivos por IP usando SSH y Netmiko

## 📜 Descripción

Este proyecto permite conectarse a un **switch Cisco** mediante **SSH** para ejecutar los comandos:

- `show ip arp`
- `show mac address-table`

Con estos resultados, el script identifica **en qué puerto está conectado un dispositivo** a partir de su **dirección IP**, mostrando su **MAC** y **puerto físico**.  

Es una herramienta útil para tareas de **diagnóstico**, **resolución de conflictos de IP/MAC** o **mapeo de red**.

---

## ⚙️ Requisitos

- Python **3.8 o superior**
- Acceso a la red del switch
- SSH habilitado en el switch
- Usuario con privilegios (`privilege 15`)

---

## 📦 Instalación de dependencias

Ejecuta en tu entorno virtual o consola:

```bash
pip install netmiko textfsm
