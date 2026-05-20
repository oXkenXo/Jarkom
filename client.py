import socket
import time
import argparse
import threading

PROXY_HOST = "192.168.1.11"
PROXY_PORT = 8080

BUFFER_SIZE = 4096

UDP_HOST = "192.168.1.10"
UDP_PORT = 9000

UDP_PACKET_COUNT = 10
UDP_TIMEOUT = 3

def mode_tcp(path = "/"):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try: 
        print("Mode TCP")
        print("Client mengirim permintaan ke proxy...",)

        start_time = time.time()

        client_socket.connect((PROXY_HOST, PROXY_PORT))

        request = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {PROXY_HOST}\r\n"
            f"Connection: close\r\n"
            f"\r\n"
        )

        client_socket.sendall(request.encode('utf-8'))

        response = b""

        while True:
            data = client_socket.recv(BUFFER_SIZE)
            if not data:
                break
            response += data
        
        end_time = time.time()
        response_time = end_time - start_time

        response_text = response.decode("utf-8", errors="ignore")
        status_line = response_text.split("\r\n")[0] 

        print("Response diterima dari proxy")
        print("Status:", status_line)
        print("Response time:", round(response_time, 4), "detik")
        print("Ukuran response:", len(response), "bytes")
        print("\nIsi response:")
        print(response_text)
    
    except ConnectionRefusedError:
        print("Gagal terhubung ke proxy.")
        print("Pastikan proxy server sudah berjalan di port", PROXY_PORT)

    except Exception as error:
        print("Error:", error)
    
    finally:
        client_socket.close()

def mode_udp():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.settimeout(UDP_TIMEOUT)

    rtt_list = []
    packet_sent = 0
    packet_received = 0

    print("Mode UDP QOS")
    print("Client mengirim packet UDP ke server...")

    for i in range(1, UDP_PACKET_COUNT + 1):
        message = f"Packet UDP ke-{i}"

        try:
            start_time = time.time()

            udp_socket.sendto(message.encode("utf-8"), (UDP_HOST, UDP_PORT))
            packet_sent += 1
            data, server_address = udp_socket.recvfrom(BUFFER_SIZE)

            end_time = time.time()
            rtt = end_time - start_time

            rtt_list.append(rtt)
            packet_received += 1

            print("Packet", i, "RTT", round(rtt, 4), "detik")

        except socket.timeout:
            print("Packet", i, "timeout")

        except Exception as error:
            print("Packet", i, "error", error)
        
    udp_socket.close()

    packet_lost = packet_sent - packet_received

    if packet_sent > 0:
        packet_loss = (packet_lost / packet_sent) * 100
    else:
        packet_loss = 0

    print("\nStatistik RTT:")

    if len(rtt_list) > 0:
        min_rtt = min(rtt_list)
        avg_rtt = sum(rtt_list) / len(rtt_list)
        max_rtt = max(rtt_list)

        print("Min RTT:", round(min_rtt, 4), "detik")
        print("Avg RTT:", round(avg_rtt, 4), "detik")
        print("Max RTT:", round(max_rtt, 4), "detik")
    
    else: 
        print("Min RTT: -")
        print("Avg RTT: -")
        print("Max RTT: -")

    print("Packet dikirim:", packet_sent)
    print("Packet diterima:", packet_received)
    print("Packet hilang:", packet_lost)
    print("Packet loss:", round(packet_loss, 2), "%")

def mode_multi():
    print("Simulasi multi-client")
    print("Menjalankan 5 instance client.py")

    threads = []

    for i in range(1,6):
        thread = threading.Thread(target=mode_tcp, args=("/",))
        threads.append(thread)
        thread.start()

        print("client instance", i, "dijalankan")

    for thread in threads:
        thread.join() 

    print("Semua instance menerima response tanpa blocking/crash")

def main():
    parser = argparse.ArgumentParser()  

    parser.add_argument(
        "--mode",
        choices=["tcp", "udp", "multi"],
        required=True,
        help="Pilih mode: tcp, udp, atau multi"
    )  


    args = parser.parse_args()  

    if args.mode == "tcp":
        mode_tcp()  

    elif args.mode == "udp":
        mode_udp() 

    elif args.mode == "multi":
        mode_multi()  


if __name__ == "__main__":
    main()  

