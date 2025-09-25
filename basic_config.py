import time
import serial

def configure_device(port,baudrate,hostname,user,password,domain):
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        ser.write(f"{port}\n".encode())
        time.sleep(1)
        ser.write(f"enable\n".encode())

        time.sleep(1)
        ser.write(f"configure terminal\n".encode())
        time.sleep(1) 
        ser.write(f"hostname {hostname}\n".encode())  
        time.sleep(1)
        ser.write(f"ip domain-name {domain}\n".encode())
        time.sleep(1)
        ser.write(f"username {user} privilege 15 secret {password}\n".encode())
        time.sleep(1)
        ser.write(f"crypto key generate rsa\n".encode())
        time.sleep(1)
        ser.write(f"line vty 0 4\n".encode())
        time.sleep(1)
        ser.write(f"login local\n".encode())
        time.sleep(1)
        ser.write(f"transport input ssh\n".encode())        
        time.sleep(1)
        ser.write(f"transport output ssh\n".encode())
        time.sleep(1)
        ser.write(f"exit\n".encode())
        time.sleep(1)
        ser.write(f"write memory\n".encode())
        time.sleep(1)
    except serial.SerialException as e:
        print(f"Error configuring device: {e}") 
      

r1= configure_device("COM3",9600,"R1","cisco","cisco","cisco.com")
        
