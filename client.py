import socket
import time

PROXY_HOST = "192.168.1.11"
PROXY_PORT = 8080

UDP_HOST = "192.168.1.10"
UDP_PORT = 9090

UDP_PACKET_COUNT = 10
UDP_TIMEOUT = 3

def send_http_request(path):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try: 
        start_time = time.time()

        client_socket.connect((PROXY_HOST, PROXY_PORT))

        request = f"GET {path} HTTP/1.1\r\nHost: {PROXY_HOST}\r\n\r\n"

        client_socket.sendall(request.encode('utf-8'))

        response = b""

        while True:
            data = client_socket.recv(4096)
            if not data:
                break
            response += data
        
        end_time = time.time()

        response_time = end_time - start_time