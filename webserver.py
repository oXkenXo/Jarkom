import socket
import threading
import os

# =========================================
# CONFIGURATION
# =========================================
TCP_PORT = 8000
UDP_PORT = 9000
HTML_DIR = "HTML"
BUFFER_SIZE = 4096

# =========================================
# UDP ECHO SERVER (QoS TESTING)
# =========================================
def udp_echo_server():
    """
    Echo server sederhana untuk menguji QoS menggunakan protokol UDP.
    Menerima paket dari client dan langsung mengirimkannya kembali.
    """
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Bind ke 0.0.0.0 agar bisa menerima paket dari IP lokal mana saja
        udp_socket.bind(("0.0.0.0", UDP_PORT))
        print(f"[UDP Server] Berjalan di port {UDP_PORT} (Echo QoS)...")
        
        while True:
            data, addr = udp_socket.recvfrom(BUFFER_SIZE)
            # Pantulkan kembali data ke pengirim (echo)
            udp_socket.sendto(data, addr)
    except Exception as e:
        print(f"[UDP Server] Error: {e}")
    finally:
        udp_socket.close()

# =========================================
# CLIENT HANDLER (TCP WEBSERVER)
# =========================================
def handle_client(client_socket, client_address):
    """
    Menangani request HTTP TCP dari client/proxy secara multi-threaded.
    Membaca file di folder HTML/ dan mengirimkannya sebagai response HTTP.
    """
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
        
        # Mapping root path "/" ke "/index.html"
        if path == "/" or path == "":
            path = "/index.html"
            
        # Tentukan file path di folder HTML
        filepath = os.path.join(HTML_DIR, path.lstrip("/"))
        
        # Mencegah akses file di luar directory HTML
        filepath = os.path.abspath(filepath)
        html_dir_abs = os.path.abspath(HTML_DIR)
        
        if not filepath.startswith(html_dir_abs):
            # 403 Forbidden jika mencoba melompat folder
            send_error(client_socket, 403, "Forbidden")
            return

        if os.path.exists(filepath) and os.path.isfile(filepath):
            # Membaca konten file
            with open(filepath, "rb") as f:
                content = f.read()
                
            # Deteksi content type sederhana
            content_type = "text/html"
            if filepath.endswith(".css"):
                content_type = "text/css"
            elif filepath.endswith(".png"):
                content_type = "image/png"
            elif filepath.endswith(".ico"):
                content_type = "image/x-icon"
                
            # Kirim response 200 OK
            response_headers = (
                "HTTP/1.1 200 OK\r\n"
                f"Content-Type: {content_type}\r\n"
                f"Content-Length: {len(content)}\r\n"
                "Connection: close\r\n\r\n"
            ).encode('utf-8')
            client_socket.sendall(response_headers + content)
            print(f"[Web Server] 200 OK - Mengirim {path} ke {client_address[0]}")
        else:
            # 404 Not Found jika file tidak ada
            send_error(client_socket, 404, "Not Found")
            
    except Exception as e:
        print(f"[Web Server] Error melayani client: {e}")
        send_error(client_socket, 500, "Internal Server Error")
    finally:
        client_socket.close()

def send_error(client_socket, status_code, status_message):
    """
    Mengirim file halaman error HTML dari folder HTML/status/
    """
    try:
        error_file = os.path.join(HTML_DIR, "status", f"{status_code}.html")
        if os.path.exists(error_file):
            with open(error_file, "rb") as f:
                content = f.read()
        else:
            content = f"<h1>{status_code} {status_message}</h1>".encode('utf-8')
            
        headers = (
            f"HTTP/1.1 {status_code} {status_message}\r\n"
            "Content-Type: text/html\r\n"
            f"Content-Length: {len(content)}\r\n"
            "Connection: close\r\n\r\n"
        ).encode('utf-8')
        client_socket.sendall(headers + content)
        print(f"[Web Server] Error {status_code} sent.")
    except Exception as e:
        print(f"[Web Server] Gagal mengirim error: {e}")

# =========================================
# SERVER STARTUP
# =========================================
def start_server():
    """
    Memulai Web Server TCP dan menjalankan thread UDP Echo Server di background.
    """
    # Jalankan UDP Echo Server di thread terpisah (background)
    udp_thread = threading.Thread(target=udp_echo_server, daemon=True)
    udp_thread.start()

    # Inisialisasi TCP Server
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        # Bind ke 0.0.0.0 agar mendengarkan koneksi dari IP lokal manapun
        tcp_socket.bind(("0.0.0.0", TCP_PORT))
        tcp_socket.listen(10)
        print(f"[Web Server] TCP Server berjalan di port {TCP_PORT}...")
        
        while True:
            client_socket, client_address = tcp_socket.accept()
            # Membuat thread baru untuk menangani request client
            client_thread = threading.Thread(
                target=handle_client,
                args=(client_socket, client_address)
            )
            client_thread.start()
    except Exception as e:
        print(f"[Web Server] Gagal memulai TCP server: {e}")
    finally:
        tcp_socket.close()

if __name__ == "__main__":
    start_server()