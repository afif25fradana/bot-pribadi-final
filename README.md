# 🤖 Bot Keuangan Pribadi Saya 🤖

👋 Selamat datang di bot keuangan pribadi saya! Ini adalah proyek hobi yang saya curahkan dengan penuh semangat, menciptakan bot Telegram yang sederhana namun kuat untuk membantu saya (dan semoga Anda juga!) mengelola keuangan dengan mudah. Bot ini dirancang agar intuitif, menarik secara visual, dan dilengkapi dengan fitur-fitur untuk memberikan gambaran yang jelas tentang kesehatan finansial.

Anggap saja bot ini sebagai asisten keuangan pribadi saya, selalu siap membantu saya mengelola anggaran dan membuat keputusan finansial yang tepat.

---

✨ **Apa yang Baru di v2.0.0?** ✨

*   **🚀 Antarmuka Pengguna yang Ditingkatkan**: Antarmuka yang sepenuhnya didesain ulang, menarik secara visual dengan tombol interaktif untuk pengalaman pengguna yang mulus.
*   **📊 Pelaporan Lanjutan**: Laporan yang lebih rinci dan mendalam, termasuk rincian kategori, status kesehatan finansial, dan perbandingan kinerja.
*   **⚡ Kinerja yang Ditingkatkan**: Kode yang dioptimalkan untuk waktu respons yang lebih cepat dan pemrosesan data yang lebih efisien.
*   **🛡️ Penanganan Kesalahan yang Kuat**: Penanganan kesalahan yang lebih baik dan koneksi ulang otomatis untuk memastikan bot selalu tersedia saat Anda membutuhkannya.
*   **⚙️ Pemeriksaan Kesehatan Komprehensif**: Skrip pemeriksaan kesehatan baru untuk dengan mudah mendiagnosis dan memecahkan masalah apa pun.
*   **📁 Struktur Proyek yang Direfaktor**: Kode diorganisir ulang ke dalam struktur modular untuk pemeliharaan yang lebih mudah dan pengembangan yang lebih cepat. File main.py telah dihapus dan fungsinya diintegrasikan ke dalam app.py.
```
---

✨ **Fitur Utama** ✨

*   **✍️ Pencatatan Transaksi Mudah**: Catat pemasukan dan pengeluaran dengan cepat menggunakan perintah sederhana.
    *   `/masuk [jumlah] #[kategori] [keterangan]`
    *   `/keluar [jumlah] #[kategori] [keterangan]`
*   **📊 Laporan Arus Kas Bulanan**: Dapatkan ringkasan jelas tentang pemasukan, pengeluaran, dan saldo Anda saat ini untuk bulan tersebut.
    *   `/laporan`
*   **📈 Perbandingan Pengeluaran**: Bandingkan pengeluaran bulan ini dengan bulan lalu untuk mengidentifikasi tren dan tetap sesuai anggaran.
    *   `/compare`
*   **🔒 Pribadi & Aman**: Akses terbatas untuk memastikan data keuangan Anda tetap rahasia.
*   **💡 Interaktif & Ramah Pengguna**: Antarmuka yang kaya dengan tombol, tips, dan panduan bermanfaat untuk membuat pelacakan keuangan menjadi mudah dan menyenangkan.

---

📁 **Struktur Proyek** 📁

```
.
├── app/                    # Direktori utama aplikasi
│   ├── bot/                # Modul bot Telegram
│   │   ├── __init__.py     # Inisialisasi bot
│   │   ├── handlers.py     # Handler perintah bot
│   │   └── utils.py        # Fungsi utilitas bot
│   ├── database/           # Modul database
│   │   ├── __init__.py     # Inisialisasi database
│   │   └── sheets.py       # Interaksi dengan Google Sheets
│   ├── web/                # Modul web
│   │   ├── __init__.py     # Inisialisasi web
│   │   └── routes.py       # Endpoint web dan webhook
│   ├── __init__.py         # Inisialisasi aplikasi
│   └── config.py           # Konfigurasi aplikasi
├── logs/                   # Direktori log
│   └── .gitkeep            # File untuk memastikan direktori log disertakan dalam Git
├── tests/                  # Direktori tes
│   ├── __init__.py         # Inisialisasi tes
│   └── health_check.py     # Skrip pemeriksaan kesehatan
├── .env.example            # Contoh file konfigurasi lingkungan
├── .gitignore              # File yang diabaikan Git
├── app.py                  # File utama aplikasi
├── Procfile                # Konfigurasi untuk deployment
├── README.md               # Dokumentasi proyek
├── requirements.txt        # Dependensi Python
├── run.py                  # Skrip untuk menjalankan aplikasi secara lokal
└── SECURITY.md             # Kebijakan keamanan
```

---

🚀 **Panduan Memulai Cepat** 🚀

1.  **Berbicara dengan Bot**: Buka Telegram dan mulai obrolan dengan bot.
2.  **Mulai Mengobrol**: Kirim `/start` untuk mendapatkan pesan selamat datang dan melihat perintah yang tersedia.
3.  **Catat Transaksi**:
    *   Untuk menambahkan pemasukan: `/masuk 1000000 #gaji Bonus`
    *   Untuk menambahkan pengeluaran: `/keluar 50000 #makanan Makan siang`
4.  **Periksa Laporan**:
    *   Untuk ringkasan bulanan: `/laporan`
    *   Untuk membandingkan pengeluaran: `/compare`

---

🛠️ **Tumpukan Teknologi** 🛠️

*   **Python**: Bahasa inti untuk logika bot.
*   **`python-telegram-bot`**: Untuk integrasi yang mulus dengan Telegram API.
*   **`gspread`**: Untuk terhubung ke Google Sheets sebagai penyimpanan data.
*   **`pandas`**: Untuk analisis data yang kuat dan pembuatan laporan.
*   **Flask**: Untuk menangani webhook dan menjaga bot tetap berjalan lancar.
*   **Logging**: Pencatatan kesalahan yang komprehensif untuk pemecahan masalah yang mudah.
*   **Variabel Lingkungan**: Manajemen konfigurasi yang aman dengan dukungan `.env`.

---

⚙️ **Instruksi Penyiapan** ⚙️

Untuk menyiapkan bot keuangan pribadi Anda sendiri, Anda akan membutuhkan:

1.  **Token Bot Telegram**: Dapatkan dari BotFather di Telegram.
2.  **Proyek Google Cloud & Akun Layanan**:
    *   Aktifkan Google Sheets API.
    *   Buat akun layanan dan unduh kredensial JSON-nya.
    *   Bagikan Google Sheet Anda dengan alamat email akun layanan.
3.  **Variabel Lingkungan**: Siapkan ini di lingkungan deployment Anda:

---

🔄 **Mode Pengembangan vs Deployment** 🔄

Bot ini dapat dijalankan dalam dua mode berbeda:

1. **Mode Pengembangan (Polling)**:
   * Gunakan `python run.py` untuk menjalankan bot secara lokal
   * Menggunakan metode polling untuk menerima update dari Telegram
   * Tidak memerlukan WEBHOOK_URL
   * Ideal untuk pengembangan dan pengujian lokal

2. **Mode Deployment (Webhook)**:
   * Gunakan `gunicorn app:app` (seperti yang dikonfigurasi dalam Procfile)
   * Memerlukan WEBHOOK_URL yang valid (misalnya URL Render.com Anda)
   * Lebih efisien untuk deployment produksi
   * Dapat di-deploy di platform seperti Render.com
    *   `TELEGRAM_TOKEN`: Token bot Anda.
    *   `GSPREAD_CREDENTIALS`: Konten file JSON akun layanan Anda.
    *   `WEBHOOK_URL`: URL webhook Anda (hanya diperlukan untuk mode deployment).
    *   `HOST`: Host untuk server web (default: 0.0.0.0).
    *   `PORT`: Port untuk server web (default: 5000).
    *   `SPREADSHEET_ID`: ID Google Sheet Anda.
    *   `ALLOWED_USER_IDS`: ID pengguna Telegram Anda untuk membatasi akses.
    *   `WEBHOOK_URL`: URL webhook untuk bot Anda.

---

💖 **Mengapa Saya Membangun Ini** 💖

Saya membuat proyek ini untuk menyediakan alat yang sederhana, mudah diakses, dan kuat untuk mengelola keuangan pribadi. Ini adalah perjalanan yang memuaskan, dan saya harap ini menginspirasi Anda untuk mengambil kendali atas masa depan finansial Anda.

Selamat melacak! 💸

---

## 🔒 Keamanan

Bot ini dirancang dengan mempertimbangkan keamanan. Untuk gambaran rinci tentang fitur keamanan dan praktik terbaik, silakan lihat [Kebijakan Keamanan](SECURITY.md).
