# 🔒 Kebijakan Keamanan Pribadi Saya

Sebagai satu-satunya pengembang dan pemelihara proyek hobi ini, saya telah banyak memikirkan untuk memastikan data keuangan Anda tetap aman dan pribadi. Dokumen ini menguraikan fitur keamanan dan praktik terbaik yang telah saya terapkan untuk Bot Keuangan Pribadi saya.

## 🔑 Fitur Keamanan Utama yang Telah Saya Bangun

1.  **Kontrol Akses Pribadi**:
    *   Bot ini dirancang untuk penggunaan pribadi saya (dan Anda, jika Anda memilih untuk menerapkannya sendiri!). Akses sangat terbatas pada satu ID pengguna Telegram yang sah, yang Anda konfigurasikan melalui variabel lingkungan `ALLOWED_USER_ID`.
    *   Setiap pesan dari pengguna yang tidak sah akan diabaikan, dan saya telah menyiapkan pencatatan untuk menangkap dan memperingatkan tentang upaya tersebut.

2.  **Manajemen Kredensial Aman**:
    *   Semua informasi sensitif, termasuk token bot Telegram, kredensial Google Sheets, dan ID pengguna Anda, dikelola melalui variabel lingkungan. Ini adalah praktik penting untuk mencegah pengkodean data sensitif secara langsung ke dalam kode sumber, yang merupakan risiko keamanan utama.
    *   File `.gitignore` dikonfigurasi dengan hati-hati untuk mencegah file `.env` (tempat variabel-variabel ini biasanya disimpan secara lokal) agar tidak pernah secara tidak sengaja di-commit ke repositori publik.

3.  **Tidak Ada Penyimpanan Data di Server**:
    *   Saya merancang bot ini agar tidak memiliki status (stateless). Ini berarti bot tidak menyimpan data keuangan Anda di server tempat bot di-hosting.
    *   Semua data transaksi ditransmisikan dengan aman ke dan disimpan di Google Sheet pribadi Anda, memberi Anda kendali penuh atas data Anda.

4.  **Komunikasi Aman**:
    *   Bot ini memanfaatkan API Telegram resmi, yang mengenkripsi semua komunikasi antara aplikasi Telegram Anda dan bot.
    *   Koneksi ke Google Sheets juga dienkripsi, memastikan data Anda terlindungi selama transit.

## 🚀 Praktik Terbaik untuk Penerapan Aman Anda

Untuk memastikan keamanan bot Anda, harap ikuti praktik terbaik ini:

1.  **JANGAN PERNAH Bagikan Kredensial Anda**:
    *   Serius, jangan pernah meng-commit file `.env` Anda atau file apa pun yang berisi kredensial Anda ke repositori publik seperti GitHub.
    *   Selalu gunakan metode yang direkomendasikan penyedia hosting Anda untuk mengelola variabel lingkungan (misalnya, Heroku Config Vars, Vercel Environment Variables).

2.  **Gunakan Token Bot yang Kuat dan Unik**:
    *   Perlakukan token bot Telegram Anda seperti kata sandi. Jika token tersebut pernah terekspos, segera buat ulang dari BotFather di Telegram.

3.  **Amankan Google Sheet Anda**:
    *   Pastikan Google Sheet Anda tidak dapat diakses secara publik.
    *   Hanya bagikan dengan alamat email akun layanan yang Anda buat untuk bot.

4.  **Pantau Aktivitas Bot**:
    *   Saya telah menyertakan pencatatan untuk membantu Anda memantau aktivitas bot. Periksa log secara teratur untuk setiap perilaku mencurigakan atau upaya akses tidak sah.

## 🚨 Melaporkan Kerentanan

Jika Anda menemukan kerentanan keamanan, harap laporkan secara bertanggung jawab. Jangan mengungkapkannya secara publik. Sebagai gantinya, buat masalah baru di repositori GitHub dengan label "security" untuk memberitahukannya kepada saya.

Saya menganggap serius keamanan, bahkan dalam proyek hobi, dan akan mengatasi setiap kerentanan secepat mungkin.

---

Dengan mengikuti panduan ini, Anda dapat dengan percaya diri menggunakan Bot Keuangan Pribadi Anda untuk mengelola keuangan Anda dengan aman.
