import socket
import threading

# =========================================
# CONFIGURATION & GLOBAL CACHE
# =========================================
PROXY_PORT = 8080
BUFFER_SIZE = 4096

# Dictionary RAM untuk menyimpan cache (key: path, value: response_bytes)
cache = {}
# Lock untuk sinkronisasi thread agar aman dari race condition (thread-safe)
cache_lock = threading.Lock()

# =========================================
# CACHE OPERATIONS
# =========================================
def check_cache(path):
    """
    Memeriksa apakah path request sudah tersimpan di cache RAM.
    """
    with cache_lock:
        if path in cache:
            return cache[path]
    return None

def save_to_cache(path, response):
    """
    Menyimpan response data Web Server ke dalam cache RAM.
    """
    with cache_lock:
        cache[path] = response

def add_cache_header(response, cache_status):
    """
    Menyisipkan custom header X-Cache (HIT/MISS) ke HTTP response.
    Memungkinkan browser/JavaScript membaca status cache proxy.
    """
    try:
        parts = response.split(b"\r\n\r\n", 1)
        if len(parts) == 2:
            headers, body = parts[0], parts[1]
            new_headers = headers + f"\r\nX-Cache: {cache_status}\r\nAccess-Control-Expose-Headers: X-Cache".encode('utf-8')
            return new_headers + b"\r\n\r\n" + body
    except:
        pass
    return response

# =========================================
# FORWARD REQUEST TO WEB SERVER
# =========================================
def send_request(web_server_ip, web_server_port, request_data):
    """
    Membuka socket TCP ke Web Server, meneruskan request client,
    dan mengembalikan seluruh response dari Web Server.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect((web_server_ip, web_server_port))
    server_socket.sendall(request_data)
    
    response = b""
    while True:
        data = server_socket.recv(BUFFER_SIZE)
        if not data:
            break
        response += data
        
    server_socket.close()
    return response

# =========================================
# CLIENT HANDLER (TCP PROXY)
# =========================================
def handle_client(client_socket, client_address, web_server_ip, web_server_port):
    """
    Menangani request TCP Client:
    1. Membaca HTTP request dari client.
    2. Jika request GET, memeriksa RAM Cache (HIT/MISS).
    3. Jika MISS, forward ke Web Server, simpan ke cache jika sukses, lalu kirim balik.
    """
    print(f"[Proxy] Koneksi masuk dari client: {client_address[0]}:{client_address[1]}")
    try:
        request_data = client_socket.recv(BUFFER_SIZE)
        if not request_data:
            return
            
        request_text = request_data.decode('utf-8', errors='ignore')
        lines = request_text.split("\r\n")
        if len(lines) == 0 or not lines[0]:
            return
            
        first_line = lines[0]
        parts = first_line.split()
        if len(parts) < 2:
            return
            
        method, path = parts[0], parts[1]
        print(f"[Proxy] Request: {method} {path}")
        
        if method == "GET":
            # 1. Cek Cache
            cached_response = check_cache(path)
            
            if cached_response:
                print(f"[CACHE HIT] Melayani request '{path}' langsung dari RAM Cache.")
                response_to_send = add_cache_header(cached_response, "HIT")
                client_socket.sendall(response_to_send)
            else:
                print(f"[CACHE MISS] Mengambil '{path}' dari Web Server...")
                # 2. Forward ke Web Server
                server_response = send_request(web_server_ip, web_server_port, request_data)
                
                # 3. Simpan ke Cache jika respon 200 OK
                if b"200 OK" in server_response:
                    save_to_cache(path, server_response)
                    print(f"[Proxy] Sukses menyimpan '{path}' ke RAM Cache.")
                    
                # 4. Kirim balik ke client
                response_to_send = add_cache_header(server_response, "MISS")
                client_socket.sendall(response_to_send)
        else:
            # Kirim error jika bukan request GET
            error_body = "<h1>501 Not Implemented</h1>"
            error_response = (
                "HTTP/1.1 501 Not Implemented\r\n"
                "Content-Type: text/html\r\n"
                f"Content-Length: {len(error_body)}\r\n"
                "Connection: close\r\n\r\n"
                f"{error_body}"
            ).encode('utf-8')
            client_socket.sendall(error_response)
    except Exception as e:
        print(f"[Proxy] Error melayani client: {e}")
    finally:
        client_socket.close()
        print("-" * 50)

# =========================================
# PROXY STARTUP
# =========================================
def start_server():
    """
    Memulai Proxy Server TCP. Meminta input IP dan Port Web Server tujuan,
    lalu mendengarkan koneksi dari client secara multi-threaded.
    """
    print("=== PENGATURAN PROXY SERVER ===")
    web_server_ip = input("Masukkan IP Web Server (default: 127.0.0.1): ").strip() or "127.0.0.1"
    web_server_port_str = input("Masukkan Port Web Server (default: 8000): ").strip() or "8000"
    web_server_port = int(web_server_port_str)

    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        # Bind ke 0.0.0.0 agar mendengarkan dari IP lokal WiFi/Hotspot
        proxy_socket.bind(("0.0.0.0", PROXY_PORT))
        proxy_socket.listen(10)
        print(f"\n[Proxy Server] Berjalan di port {PROXY_PORT}...")
        print(f"[Proxy Server] Meneruskan request ke Web Server di {web_server_ip}:{web_server_port}")
        print("-" * 50)
        
        while True:
            client_socket, client_address = proxy_socket.accept()
            client_thread = threading.Thread(
                target=handle_client,
                args=(client_socket, client_address, web_server_ip, web_server_port)
            )
            client_thread.start()
    except Exception as e:
        print(f"[Proxy Server] Gagal berjalan: {e}")
    finally:
        proxy_socket.close()

if __name__ == "__main__":
    start_server()