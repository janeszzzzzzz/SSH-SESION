import socket
print("HELLO word")

hostname = socket.gethostname()
print(f"HOSTNAME: {hostname}")

ipaddr= socket.gethostbyname(hostname)
print(f"IP ADDRESS:{ipaddr}")

for i in range(10):
    print(f"count:{i}")