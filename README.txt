========================================================================
             TUGAS BESAR JARINGAN KOMPUTER - README GUIDE
========================================================================

Panduan langkah demi langkah untuk menjalankan dan mempresentasikan proyek
socket programming: Client -> Proxy Server -> Web Server.

------------------------------------------------------------------------
A. CARA MENJALANKAN (DI SATU LAPTOP / LOCALHOST)
------------------------------------------------------------------------

Buka 3 jendela Command Prompt (CMD) atau Terminal terpisah di direktori 
proyek Anda, kemudian jalankan program dengan urutan berikut:

1. JALANKAN WEB SERVER (Terminal 1):
   Perintah: python webserver.py
   - Web Server akan berjalan di port TCP 8000 dan port UDP 9000.

2. JALANKAN PROXY SERVER (Terminal 2):
   Perintah: python proxy.py
   - Ketik IP Web Server tujuan: Tekan ENTER (default: 127.0.0.1)
   - Ketik Port Web Server tujuan: Tekan ENTER (default: 8000)
   - Proxy Server akan berjalan di port TCP 8080.

3. JALANKAN CLIENT (Terminal 3):
   Perintah: python client.py
   - Menu terminal interaktif akan muncul.
   - Anda langsung dapat mencoba fitur Request Halaman Web, QoS UDP,
     atau Simulasi Multi-Client.

------------------------------------------------------------------------
B. CARA MENJALANKAN DI 3 DEVICE BERBEDA (SATU JARINGAN WIFI/HOTSPOT)
------------------------------------------------------------------------

Untuk mendemonstrasikan komunikasi jaringan antar device sesungguhnya:

1. HUBUNGKAN 3 DEVICE:
   Hubungkan Laptop 1 (Web Server), Laptop 2 (Proxy Server), dan Laptop 3 
   (Client) ke dalam satu jaringan WiFi atau Hotspot yang sama.

2. TEMUKAN ALAMAT IP LOKAL MASING-MASING:
   - Di Windows: Buka CMD, ketik `ipconfig`. Cari baris `IPv4 Address`
     pada adapter WiFi Anda (contoh: 192.168.1.10).
   - Di macOS/Linux: Buka Terminal, ketik `ifconfig` atau `ip route`.

3. MENJALANKAN DI LAPTOP 1 (WEB SERVER):
   - Jalankan `python webserver.py`.
   - Catat IPv4 Laptop 1 ini (misal: 192.168.1.10).

4. MENJALANKAN DI LAPTOP 2 (PROXY SERVER):
   - Jalankan `python proxy.py`.
   - Masukkan IP Web Server: ketik IP Laptop 1 (192.168.1.10).
   - Masukkan Port Web Server: Tekan ENTER (default: 8000).
   - Catat IPv4 Laptop 2 ini (misal: 192.168.1.15).

5. MENJALANKAN DI LAPTOP 3 (CLIENT):
   - Jalankan `python client.py`.
   - Pilih Menu 4 (Ubah Konfigurasi IP & Port).
   - Masukkan IP Proxy Server: ketik IP Laptop 2 (192.168.1.15).
   - Masukkan IP Web Server: ketik IP Laptop 1 (192.168.1.10).
   - Pilih Menu 1 untuk request halaman web, atau Menu 2 untuk QoS test.

------------------------------------------------------------------------
C. PENJELASAN KONSEP & FITUR JARINGAN (UNTUK PRESENTASI SIDANG)
------------------------------------------------------------------------

1. TCP HTTP (Transmission Control Protocol):
   - Digunakan untuk mentransmisikan data web/HTML melalui TCP Socket (SOCK_STREAM).
   - Mengapa TCP? Karena TCP menjamin reliabilitas data melalui mekanisme 
     handshaking (3-way handshake) dan retransmisi data jika ada paket yang rusak
     atau hilang, sehingga file HTML diterima secara utuh tanpa korup.

2. UDP QoS (User Datagram Protocol - Quality of Service):
   - Digunakan untuk pengujian kualitas performa link jaringan melalui UDP Socket 
     (SOCK_DGRAM) pada Port 9000.
   - Parameter yang diukur:
     a. RTT / Delay: Waktu bolak-balik pengiriman paket (Min, Max, Avg) dalam ms.
     b. Jitter: Variasi selisih waktu kedatangan antar paket berturut-turut.
     c. Packet Loss: Persentase paket yang hilang (RTO) diukur dari timeout.
     d. Throughput: Kecepatan transfer bit data riil per detik (Kbps).

3. PROXY CACHE:
   - Proxy menyimpan data response yang diperoleh dari Web Server ke dalam 
     dictionary (RAM RAM Cache) dengan kunci berupa path URL.
   - [CACHE MISS]: Terjadi saat halaman belum pernah diakses sebelumnya. Proxy
     harus mengambilnya dari Web Server terlebih dahulu.
   - [CACHE HIT]: Terjadi saat halaman diminta kembali. Proxy langsung mengirim
     halaman tersebut dari RAM miliknya ke Client tanpa menghubungi Web Server.
     Menghemat bandwidth dan mempercepat response time.

4. MULTI-THREADING:
   - Diimplementasikan menggunakan library bawaan Python `threading.Thread()`.
   - Di Server & Proxy: Setiap koneksi masuk ditangani oleh thread baru secara
     asinkron agar server dapat melayani banyak client secara konkuren tanpa 
     terjadi blocking/antrean panjang.
   - Di Client: Digunakan untuk mensimulasikan beberapa request client dikirim
     secara simultan untuk menguji performa concurrency server.
========================================================================
