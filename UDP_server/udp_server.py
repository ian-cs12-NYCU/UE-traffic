# udp_server.py
import socket

HOST = "0.0.0.0"   
PORT = 9000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))

print(f"[UDP Server] Listening on {HOST}:{PORT}...")

while True:
    data, addr = sock.recvfrom(2048)  # 最多收 2KB 封包
    print(f"Received {len(data)} bytes from {addr}")
