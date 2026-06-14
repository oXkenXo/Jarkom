import socket
import threading
import time

# =========================================
# CONFIGURATION
# =========================================
# Default IP dan Port
proxy_ip = "127.0.0.1"
proxy_port = 8080
server_ip = "127.0.0.1"
udp_port = 9000

# =========================================
# TCP HTTP REQUEST FUNCTIONS
# =========================================
def send_request(p_ip, p_port, path="/index.html", thread_id=None):
    """
    Mengirim request HTTP GET melalui Proxy Server menggunakan TCP Socket.
    """
    start_time = time.time()
    try:
        # Hubungkan TCP ke Proxy Server
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(3.0)
        client_socket.connect((p_ip, p_port))
        
        # Kirim request HTTP GET standard
        request = f"GET {path} HTTP/1.1\r\nHost: {p_ip}\r\nConnection: close\r\n\r\n"
        client_socket.sendall(request.encode('utf-8'))
        
        # Terima response dari Proxy Server
        response = b""
        while True:
            data = client_socket.recv(4096)
            if not data:
                break
            response += data
            
        client_socket.close()
        response_time = (time.time() - start_time) * 1000
        
        # Parsing header response sederhana
        response_text = response.decode('utf-8', errors='ignore')
        lines = response_text.split("\r\n")
        status_line = lines[0] if len(lines) > 0 else "HTTP/1.1 Unknown"
        
        # Cari header X-Cache
        cache_status = "UNKNOWN"
        for line in lines:
            if line.lower().startswith("x-cache:"):
                cache_status = line.split(":")[1].strip()
                break

        if thread_id is not None:
            print(f"[Thread-{thread_id}] Status: {status_line} | Waktu: {response_time:.2f} ms | Cache Proxy: {cache_status}")
        else:
            size_kb = len(response) / 1024.0
            print(f"\n========================================")
            print(f"SINGLE THREAD HTTP REQUEST")
            print(f"==========================")
            print(f"Request Path : {path}")
            print(f"Status       : {status_line}")
            print(f"Cache Proxy  : {cache_status}")
            print(f"Response Time: {response_time:.2f} ms")
            print(f"Response Size: {size_kb:.2f} KB ({len(response)} bytes)")
            print(f"======================\n")
            
            # Tampilkan cuplikan konten HTML jika response 200 OK
            if "200 OK" in status_line:
                body_parts = response_text.split("\r\n\r\n", 1)
                if len(body_parts) == 2:
                    print("=== ISI KONTEN HTML (Cuplikan) ===")
                    body_lines = body_parts[1].split("\n")
                    for line in body_lines[:8]:
                        print(line)
                    if len(body_lines) > 8:
                        print("... (konten dipotong untuk keterbacaan) ...")
                    print("==================================")
            
    except Exception as e:
        if thread_id is not None:
            print(f"[Thread-{thread_id}] Gagal: {e}")
        else:
            print(f"\n[Error] Gagal melakukan request: {e}")

# =========================================
# UDP QoS TEST FUNCTIONS
# =========================================
def test_qos(s_ip, s_udp_port):
    """
    Mengukur kualitas jaringan (QoS) dengan mengirim 10 paket UDP ke Web Server.
    Menghitung Delay (RTT), Jitter, Packet Loss, dan Throughput.
    """
    print(f"\n=== MEMULAI QoS TEST (UDP ke {s_ip}:{s_udp_port}) ===")
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.settimeout(1.0) # Timeout 1 detik untuk packet loss
    
    rtts = []
    lost_packets = 0
    total_packets = 10
    total_bytes = 0
    
    for i in range(total_packets):
        payload = f"QoS-Packet-{i}-{time.time()}"
        data_to_send = payload.encode('utf-8')
        
        send_time = time.time()
        try:
            udp_socket.sendto(data_to_send, (s_ip, s_udp_port))
            # Tunggu echo balik dari server
            data, addr = udp_socket.recvfrom(1024)
            recv_time = time.time()
            
            # Hitung RTT dalam milidetik
            rtt = (recv_time - send_time) * 1000
            rtts.append(rtt)
            total_bytes += len(data)
            print(f"Paket {i+1}: RTT = {rtt:.2f} ms")
        except socket.timeout:
            lost_packets += 1
            print(f"Paket {i+1}: RTO (Request Timeout) - Paket Hilang")
        time.sleep(0.1) # Jeda antar paket
        
    udp_socket.close()
    
    # Kalkulasi Parameter QoS
    print("\n=== HASIL QoS UDP ANALYSIS ===")
    # 1. Packet Loss
    loss_percentage = (lost_packets / total_packets) * 100
    print(f"Packet Loss : {loss_percentage:.1f}% ({lost_packets}/{total_packets} paket hilang)")
    
    if len(rtts) > 0:
        # 2. Delay / RTT
        min_rtt = min(rtts)
        max_rtt = max(rtts)
        avg_rtt = sum(rtts) / len(rtts)
        print(f"RTT (Delay) : Min = {min_rtt:.2f} ms | Max = {max_rtt:.2f} ms | Avg = {avg_rtt:.2f} ms")
        
        # 3. Jitter
        if len(rtts) > 1:
            diffs = [abs(rtts[i] - rtts[i-1]) for i in range(1, len(rtts))]
            jitter = sum(diffs) / len(diffs)
            print(f"Jitter      : {jitter:.2f} ms")
        else:
            print("Jitter      : 0.00 ms (Koneksi tidak stabil untuk menghitung jitter)")
            
        # 4. Throughput Sederhana
        total_time_seconds = sum(rtts) / 1000.0
        throughput_kbps = (total_bytes * 8) / (total_time_seconds * 1024) if total_time_seconds > 0 else 0
        print(f"Throughput  : {throughput_kbps:.2f} Kbps")
    else:
        print("RTT (Delay) : - (Gagal terhubung/100% loss)")
        print("Jitter      : -")
        print("Throughput  : -")
    print("================================")

# =========================================
# MULTI CLIENT SIMULATION
# =========================================
def run_multi_client(p_ip, p_port, num_threads):
    """
    Simulasi multi-client secara simultan menggunakan multi-threading.
    """
    print(f"\n=== SIMULASI MULTI-CLIENT ({num_threads} Threads Simultan) ===")
    threads = []
    for i in range(num_threads):
        t = threading.Thread(
            target=send_request,
            args=(p_ip, p_port, "/index.html", i+1)
        )
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
    print("=== SIMULASI MULTI-CLIENT SELESAI ===")

# =========================================
# MAIN INTERFACE
# =========================================
def main():
    global proxy_ip, proxy_port, server_ip, udp_port
    
    while True:
        print("\n========================================")
        print("      MENU TERMINAL SOCKET CLIENT       ")
        print("========================================")
        print(f"IP Proxy Server   : {proxy_ip}:{proxy_port}")
        print(f"IP Web/UDP Server : {server_ip} (UDP Port: {udp_port})")
        print("----------------------------------------")
        print("1. Request Halaman Web (Single Thread)")
        print("2. Test Kualitas Jaringan QoS (UDP)")
        print("3. Simulasi Multi-Client (Multi-Thread)")
        print("4. Ubah Konfigurasi IP & Port")
        print("5. Keluar")
        print("========================================")
        
        pilihan = input("Pilih menu (1-5): ").strip()
        
        if pilihan == "1":
            path = input("Masukkan path file (default: /index.html): ").strip() or "/index.html"
            send_request(proxy_ip, proxy_port, path)
        elif pilihan == "2":
            test_qos(server_ip, udp_port)
        elif pilihan == "3":
            try:
                num = int(input("Masukkan jumlah thread client (default: 5): ").strip() or "5")
                run_multi_client(proxy_ip, proxy_port, num)
            except ValueError:
                print("Input harus berupa angka!")
        elif pilihan == "4":
            proxy_ip = input(f"IP Proxy Server (current: {proxy_ip}): ").strip() or proxy_ip
            try:
                proxy_port = int(input(f"Port Proxy Server (current: {proxy_port}): ").strip() or proxy_port)
            except ValueError:
                print("Port harus berupa angka!")
            server_ip = input(f"IP Web/UDP Server (current: {server_ip}): ").strip() or server_ip
            try:
                udp_port = int(input(f"Port UDP Server (current: {udp_port}): ").strip() or udp_port)
            except ValueError:
                print("Port harus berupa angka!")
        elif pilihan == "5":
            print("Keluar dari program client. Terima kasih!")
            break
        else:
            print("Pilihan menu tidak valid!")
            
        input("\nTekan Enter untuk kembali ke menu...")

if __name__ == "__main__":
    main()
