import socket
import threading
import os
import time
from datetime import datetime

HOST = ""
PROXY_PORT = 8080

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000

BUFFER_SIZE = 4096
TIMEOUT = 10

CACHE_DIR = "cache"

cache_lock = threading.Lock()


def log(message):

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    print(
        "[" + timestamp + "] "
        + message
    )


def get_cache_path(path):

    safe_name = path.replace(
        "/",
        "_"
    )

    if safe_name == "_" or safe_name == "":
        safe_name = "_index.html"

    return os.path.join(
        CACHE_DIR,
        safe_name
    )


def cache_exists(path):

    return os.path.exists(
        get_cache_path(path)
    )


def cache_read(path):

    try:

        with open(
            get_cache_path(path),
            "rb"
        ) as file:

            return file.read()

    except:

        return None


def cache_write(path,data):

    try:

        with open(
            get_cache_path(path),
            "wb"
        ) as file:

            file.write(data)

    except Exception as error:

        log(
            "Cache write error: "
            + str(error)
        )


def parse_request(raw_request):

    try:

        header = raw_request.split(
            "\r\n\r\n"
        )[0]

        first_line = header.split(
            "\r\n"
        )[0]

        bagian = first_line.split()

        if len(bagian) < 2:

            return None,None

        method = bagian[0]
        path = bagian[1]

        if path == "/":
            path="/index.html"

        return method,path

    except:

        return None,None


def get_status_code(response):

    try:

        first_line = response\
            .split(
            b"\r\n"
        )[0].decode()

        return first_line.split()[1]

    except:

        return "???"


def forward_to_server(request):

    server_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    server_socket.settimeout(
        TIMEOUT
    )

    try:

        server_socket.connect(
            (
                SERVER_HOST,
                SERVER_PORT
            )
        )

        server_socket.sendall(
            request
        )

        response = b""

        while True:

            data = server_socket.recv(
                BUFFER_SIZE
            )

            if not data:
                break

            response += data

        return response

    finally:

        server_socket.close()


def build_error_response(
        status,
        description
):

    body=(

        "<h1>"
        +status+
        "</h1>"

        "<p>"
        +description+
        "</p>"
    )

    body=body.encode()

    response=(

        "HTTP/1.1 "
        +status+
        "\r\n"

        "Content-Type:text/html\r\n"

        "Content-Length:"
        +str(
            len(body)
        )
        +"\r\n"

        "Connection:close\r\n"

        "\r\n"

    ).encode()

    response+=body

    return response


def handle_client(
        client_socket,
        client_address
):

    client_socket.settimeout(5.0)

    client_ip = client_address[0]

    start_time=time.time()

    log(
        "Client terhubung: "
        +str(client_address)
    )

    try:

        request=b""

        while b"\r\n\r\n" \
            not in request:

            data=client_socket.recv(
                BUFFER_SIZE
            )

            if not data:
                break

            request+=data


        if not request:

            client_socket.close()

            return


        request_text=request.decode(
            "utf-8",
            errors="ignore"
        )

        log(
            "Request: "
            +request_text.split(
                "\n"
            )[0]
        )


        method,path=\
            parse_request(
                request_text
            )


        if method is None:

            response=\
            build_error_response(

                "400 Bad Request",

                "Request invalid"

            )

            client_socket.sendall(
                response
            )

            client_socket.close()

            return


        if method!="GET":

            response=\
            build_error_response(

                "501 Not Implemented",

                "Only GET supported"

            )

            client_socket.sendall(
                response
            )

            client_socket.close()

            return


        response = None
        with cache_lock:
            if cache_exists(path):
                response = cache_read(path)

        if response:

                client_socket.sendall(
                    response
                )

                response_time=round(
                    (
                     time.time()
                     -start_time
                    )*1000,
                    2
                )

                log(

                    "IP: "
                    +client_ip+

                    " | URL: "
                    +path+

                    " | Cache: HIT"

                    +" | Response Time: "

                    +str(
                        response_time
                    )

                    +" ms"

                    +" | Size: "

                    +str(
                        len(response)
                    )

                    +" bytes"

                )

                client_socket.close()

                return


        try:

            response=\
            forward_to_server(
                request
            )


        except socket.timeout:

            response=\
            build_error_response(

                "504 Gateway Timeout",

                "Server timeout"

            )

            client_socket.sendall(
                response
            )

            client_socket.close()

            return


        except ConnectionRefusedError:

            response=\
            build_error_response(

                "502 Bad Gateway",

                "Server unreachable"

            )

            client_socket.sendall(
                response
            )

            client_socket.close()

            return


        except Exception as error:

            log(
                "Forward Error: "
                +str(error)
            )

            response=\
            build_error_response(

                "502 Bad Gateway",

                "Proxy Error"

            )

            client_socket.sendall(
                response
            )

            client_socket.close()

            return


        status=\
        get_status_code(
            response
        )


        if status=="200":

            with cache_lock:

                cache_write(
                    path,
                    response
                )

            cache_status=\
            "MISS->SAVE"

        else:

            cache_status=\
            "MISS"


        client_socket.sendall(
            response
        )


        response_time=round(

            (
                time.time()
                -start_time
            )*1000,

            2

        )


        log(

            "IP: "
            +client_ip+

            " | URL: "
            +path+

            " | Cache: "
            +cache_status+

            " | Status: "
            +status+

            " | Response Time: "
            +str(
                response_time
            )

            +" ms"

            +" | Size: "

            +str(
                len(response)
            )

            +" bytes"

        )


    except Exception as error:

        log(
            "Error: "
            +str(error)
        )

        try:

            response=\
            build_error_response(

                "500 Internal Server Error",

                "Proxy Internal Error"

            )

            client_socket.sendall(
                response
            )

        except:
            pass


    client_socket.close()

    log(
        "Koneksi ditutup"
    )

    log(
        "-------------------"
    )


def main():

    if not os.path.exists(
        CACHE_DIR
    ):

        os.makedirs(
            CACHE_DIR
        )

        log(
            "Folder cache dibuat"
        )


    proxy_socket=socket.socket(

        socket.AF_INET,

        socket.SOCK_STREAM

    )

    proxy_socket.setsockopt(

        socket.SOL_SOCKET,

        socket.SO_REUSEADDR,

        1

    )

    proxy_socket.bind(
        (
            HOST,
            PROXY_PORT
        )
    )

    proxy_socket.listen(5)


    log(
        "Proxy Server berjalan"
    )

    log(
        "Port: "
        +str(PROXY_PORT)
    )

    log(
        "Forward ke: "
        +SERVER_HOST+
        ":"+
        str(SERVER_PORT)
    )

    log(
        "Folder cache: "
        +CACHE_DIR
    )

    log(
        "-------------------"
    )


    while True:

        client_socket,\
        client_address=\
        proxy_socket.accept()


        thread=\
        threading.Thread(

            target=
            handle_client,

            args=(
                client_socket,
                client_address
            )

        )

        thread.start()


        log(
            "Thread dibuat: "
            +thread.name
        )


if __name__=="__main__":

    main()