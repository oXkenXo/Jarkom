import socket
import threading
import os

HOST = ""
TCP_PORT = 8000
UDP_PORT = 9000
BUFFER_SIZE = 4096

WEB_ROOT = "HTML"


def create_response(status, body, content_type="text/html"):
    body = body.encode()

    response = (
        "HTTP/1.1 " + status + "\r\n"
        "Content-Type: " + content_type + "\r\n"
        "Content-Length: " + str(len(body)) + "\r\n"
        "Connection: close\r\n"
        "\r\n"
    ).encode() + body

    return response


def read_file(path):
    file_path = WEB_ROOT + path

    if not os.path.exists(file_path):
        return None

    file = open(file_path, "rb")
    data = file.read()
    file.close()

    return data


def get_content_type(path):
    if path.endswith(".html"):
        return "text/html"
    elif path.endswith(".css"):
        return "text/css"
    elif path.endswith(".png"):
        return "image/png"
    elif path.endswith(".mp4"):
        return "video/mp4"
    else:
        return "text/plain"


def handle_client(client_socket, client_address):
    print("Client terhubung:", client_address)

    try:
        request = client_socket.recv(BUFFER_SIZE).decode()

        if request == "":
            client_socket.close()
            return

        print("Request:")
        print(request.split("\n")[0])

        baris_pertama = request.split("\n")[0]
        bagian = baris_pertama.split()

        if len(bagian) < 2:
            response = create_response(
                "400 Bad Request",
                "<h1>400 Bad Request</h1>"
            )
            client_socket.send(response)
            client_socket.close()
            return

        method = bagian[0]
        path = bagian[1]

        if path == "/":
            path = "/index.html"

        if method != "GET":
            response = create_response(
                "501 Not Implemented",
                "<h1>501 Not Implemented</h1>"
            )
            client_socket.send(response)
            client_socket.close()
            return

        data = read_file(path)

        if data is None:
            response = create_response(
                "404 Not Found",
                "<h1>404 File Not Found</h1>"
            )
            client_socket.send(response)
            print("Status: 404 Not Found")
        else:
            content_type = get_content_type(path)

            header = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: " + content_type + "\r\n"
                "Content-Length: " + str(len(data)) + "\r\n"
                "Connection: close\r\n"
                "\r\n"
            ).encode()

            response = header + data
            client_socket.send(response)
            print("Status: 200 OK")

    except Exception as error:
        print("Error:", error)

        response = create_response(
            "500 Internal Server Error",
            "<h1>500 Internal Server Error</h1>"
        )
        client_socket.send(response)

    client_socket.close()
    print("Koneksi ditutup:", client_address)


def start_tcp_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, TCP_PORT))
    server_socket.listen(5)

    print("TCP Web Server berjalan di port", TCP_PORT)
    print("Folder web:", WEB_ROOT)

    while True:
        client_socket, client_address = server_socket.accept()

        thread = threading.Thread(
            target=handle_client,
            args=(client_socket, client_address)
        )
        thread.start()


def start_udp_server():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind((HOST, UDP_PORT))

    print("UDP Echo Server berjalan di port", UDP_PORT)

    while True:
        data, address = udp_socket.recvfrom(BUFFER_SIZE)

        print("UDP dari", address, ":", data.decode())

        udp_socket.sendto(data, address)


def main():
    thread_tcp = threading.Thread(target=start_tcp_server)
    thread_udp = threading.Thread(target=start_udp_server)

    thread_tcp.start()
    thread_udp.start()


if __name__ == "__main__":
    main()