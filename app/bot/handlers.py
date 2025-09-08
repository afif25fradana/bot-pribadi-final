# app/bot/handlers.py
"""
Handler perintah untuk bot Telegram.

Modul ini berisi semua handler perintah yang digunakan oleh bot Telegram.
"""

import logging
import datetime
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.bot.utils import restricted, parse_message, format_currency, get_month_name
from app.database.sheets import get_worksheet, append_row

@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Pesan selamat datang dengan tombol interaktif."""
    user_name = update.effective_user.first_name
    
    keyboard = [
        [
            InlineKeyboardButton("📊 Laporan Bulan Ini", callback_data="laporan"),
            InlineKeyboardButton("📈 Perbandingan", callback_data="compare")
        ],
        [
            InlineKeyboardButton("💡 Tips Penggunaan", callback_data="tips"),
            InlineKeyboardButton("ℹ️ Info Bot", callback_data="info")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    pesan = (
        f"👋 *Halo {user_name}!*\n\n"
        "🎯 *Bot Keuangan Pribadi* siap membantu!\n\n"
        "📝 *Perintah Utama:*\n"
        "• `/masuk [jumlah] #[kategori] [keterangan]`\n"
        "  _Contoh: /masuk 500000 #gaji Gaji bulan ini_\n\n"
        "• `/keluar [jumlah] #[kategori] [keterangan]`\n"
        "  _Contoh: /keluar 50000 #makanan Makan siang_\n\n"
        "📊 *Laporan & Analisis:*\n"
        "• `/laporan` - Ringkasan keuangan bulan ini\n"
        "• `/compare` - Perbandingan dengan bulan lalu\n\n"
        "💡 *Kategori Populer:*\n"
        "`#makanan #transportasi #belanja #tagihan #hiburan #kesehatan #gaji #bonus`\n\n"
        "Pilih menu di bawah untuk aksi cepat! 👇"
    )
    
    await update.message.reply_text(pesan, parse_mode='Markdown', reply_markup=reply_markup)

@restricted
async def catat_transaksi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mencatat transaksi pemasukan atau pengeluaran dengan umpan balik yang lebih baik dan penanganan error yang optimal."""
    try:
        command = update.message.text.split()[0].lower()
        tipe = "Pemasukan" if command == "/masuk" else "Pengeluaran"
        emoji = "💰" if tipe == "Pemasukan" else "💸"
        
        jumlah, kategori, deskripsi = parse_message(update.message.text)
        if jumlah is None:
            keyboard = [[
                InlineKeyboardButton("📝 Contoh Format", callback_data="format_help")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "❌ *Format Salah*\n\n"
                "📝 *Format yang benar:*\n"
                f"`{command} [jumlah] #[kategori] [keterangan]`\n\n"
                "💡 *Contoh:*\n"
                f"`{command} 50000 #makanan Makan siang di restoran`\n\n"
                "⚠️ *Pastikan:*\n"
                "• Jumlah berupa angka tanpa titik/koma\n"
                "• Kategori diawali dengan #\n"
                "• Keterangan bersifat opsional",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            return
            
        # Optimalkan format timestamp untuk pengurutan yang lebih baik di spreadsheet
        tanggal = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_row = [tanggal, tipe, jumlah, kategori, deskripsi]
        
        try:
            # Gunakan connection pooling untuk kinerja yang lebih baik
            target_sheet = get_worksheet("Transaksi")
            if not target_sheet:
                await update.message.reply_text(
                    "❌ *Worksheet Tidak Ditemukan*\n\n"
                    "Worksheet 'Transaksi' tidak ditemukan.\n"
                    "Pastikan spreadsheet memiliki sheet dengan nama 'Transaksi'.",
                    parse_mode='Markdown'
                )
                return
                
            append_row(target_sheet, new_row)
            
            # Pesan sukses yang ditingkatkan dengan tombol interaktif
            keyboard = [[
                InlineKeyboardButton("📊 Lihat Laporan", callback_data="laporan"),
                InlineKeyboardButton("➕ Tambah Lagi", callback_data="add_more")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Format timestamp sekali untuk menghindari pemformatan yang berlebihan
            formatted_time = datetime.datetime.now().strftime('%d/%m/%Y %H:%M')
            
            await update.message.reply_text(
                f"{emoji} *Transaksi Berhasil Dicatat!*\n\n"
                f"📋 *Detail:*\n"
                f"• *Tipe:* {tipe}\n"
                f"• *Jumlah:* `{format_currency(jumlah)}`\n"
                f"• *Kategori:* `#{kategori}`\n"
                f"• *Keterangan:* _{deskripsi}_\n"
                f"• *Waktu:* {formatted_time}\n\n"
                "✅ Data telah tersimpan di spreadsheet!",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
            logging.info(f"✅ Transaksi dicatat: {tipe} {format_currency(jumlah)} untuk #{kategori}")
            
        except Exception as e:
            logging.error(f"❌ Kesalahan akses worksheet: {e}")
            await update.message.reply_text(
                "⚠️ *Error Akses Spreadsheet*\n\n"
                "Terjadi kesalahan saat mengakses Google Sheets.\n"
                "Silakan coba lagi dalam beberapa saat.",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logging.error(f"❌ Kesalahan di catat_transaksi: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ *Terjadi Kesalahan*\n\n"
            "Maaf, ada error saat mencatat transaksi.\n"
            "Silakan coba lagi atau hubungi administrator.",
            parse_mode='Markdown'
        )

@restricted
async def laporan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menghasilkan laporan keuangan bulanan yang komprehensif dan teroptimasi."""
    try:
        # Tampilkan pesan memuat
        loading_msg = await update.message.reply_text("⏳ *Menyusun laporan keuangan...*", parse_mode='Markdown')
        
        # Dapatkan informasi tanggal saat ini sekali
        sekarang = datetime.datetime.now()
        bulan_target, tahun_target = sekarang.month, sekarang.year

        # Ambil dan validasi data
        try:
            sheet = get_worksheet("Transaksi")
            if not sheet:
                await loading_msg.edit_text(
                    "❌ *Worksheet Tidak Ditemukan*\n\n"
                    "Worksheet 'Transaksi' tidak ditemukan.\n"
                    "Pastikan spreadsheet memiliki sheet dengan nama 'Transaksi'.",
                    parse_mode='Markdown'
                )
                return
                
            data = sheet.get_all_records()

            if not data:
                await loading_msg.edit_text(
                    "📭 *Belum Ada Data*\n\n"
                    "Belum ada transaksi yang tercatat.\n"
                    "Mulai catat transaksi dengan `/masuk` atau `/keluar`!",
                    parse_mode='Markdown'
                )
                return
                
        except Exception as e:
            logging.error(f"❌ Kesalahan mengakses worksheet di laporan: {e}")
            await loading_msg.edit_text(
                "⚠️ *Error Mengakses Data*\n\n"
                "Terjadi kesalahan saat mengakses data.\n"
                "Silakan coba lagi dalam beberapa saat.",
                parse_mode='Markdown'
            )
            return

        # Proses data lebih efisien
        df = pd.DataFrame(data)
        
        # Konversi tipe data dalam satu kali jalan
        df['Jumlah'] = pd.to_numeric(df['Jumlah'], errors='coerce').fillna(0)
        df['Tanggal'] = pd.to_datetime(df['Tanggal'], errors='coerce')
        df = df.dropna(subset=['Tanggal'])  # Lebih efisien daripada inplace=True

        # Hitung saldo
        tanggal_awal_bulan_ini = datetime.date(tahun_target, bulan_target, 1)
        
        # Buat dataframe yang difilter
        mask_sebelumnya = df['Tanggal'].dt.date < tanggal_awal_bulan_ini
        mask_bulan_ini = ((df['Tanggal'].dt.month == bulan_target) & 
                          (df['Tanggal'].dt.year == tahun_target))
        
        df_sebelumnya = df[mask_sebelumnya]
        df_bulan_ini = df[mask_bulan_ini]
        
        # Hitung total dengan operasi vektor
        mask_pemasukan_sebelumnya = df_sebelumnya['Tipe'] == 'Pemasukan'
        mask_pengeluaran_sebelumnya = df_sebelumnya['Tipe'] == 'Pengeluaran'
        
        pemasukan_sebelumnya = df_sebelumnya.loc[mask_pemasukan_sebelumnya, 'Jumlah'].sum()
        pengeluaran_sebelumnya = df_sebelumnya.loc[mask_pengeluaran_sebelumnya, 'Jumlah'].sum()
        
        mask_pemasukan_bulan_ini = df_bulan_ini['Tipe'] == 'Pemasukan'
        mask_pengeluaran_bulan_ini = df_bulan_ini['Tipe'] == 'Pengeluaran'
        
        pemasukan_bulan_ini = df_bulan_ini.loc[mask_pemasukan_bulan_ini, 'Jumlah'].sum()
        pengeluaran_bulan_ini = df_bulan_ini.loc[mask_pengeluaran_bulan_ini, 'Jumlah'].sum()
        
        # Hitung saldo akhir
        saldo_awal = pemasukan_sebelumnya - pengeluaran_sebelumnya
        saldo_akhir = saldo_awal + pemasukan_bulan_ini - pengeluaran_bulan_ini

        # Hasilkan rincian kategori
        pengeluaran_per_kategori = df_bulan_ini[mask_pengeluaran_bulan_ini].groupby('Kategori')['Jumlah'].sum().sort_values(ascending=False)
        pemasukan_per_kategori = df_bulan_ini[mask_pemasukan_bulan_ini].groupby('Kategori')['Jumlah'].sum().sort_values(ascending=False)
        
        # Bangun teks rincian kategori
        rincian_pengeluaran = ""
        if not pengeluaran_per_kategori.empty:
            rincian_pengeluaran = "\n\n💸 *Rincian Pengeluaran:*\n"
            for kategori, total in pengeluaran_per_kategori.head(5).items():
                percentage = (total / pengeluaran_bulan_ini * 100) if pengeluaran_bulan_ini > 0 else 0
                rincian_pengeluaran += f"`#{kategori:<12} {format_currency(total)} ({percentage:.1f}%)`\n"
            
            if len(pengeluaran_per_kategori) > 5:
                rincian_pengeluaran += f"_...dan {len(pengeluaran_per_kategori) - 5} kategori lainnya_\n"

        rincian_pemasukan = ""
        if not pemasukan_per_kategori.empty:
            rincian_pemasukan = "\n\n💰 *Rincian Pemasukan:*\n"
            for kategori, total in pemasukan_per_kategori.head(3).items():
                rincian_pemasukan += f"`#{kategori:<12} {format_currency(total)}`\n"

        # Tentukan kesehatan finansial
        if saldo_akhir > saldo_awal:
            health_emoji = "📈"
            health_text = "Keuangan membaik!"
        elif saldo_akhir < saldo_awal:
            health_emoji = "📉"
            health_text = "Perlu lebih hemat."
        else:
            health_emoji = "➖"
            health_text = "Keuangan stabil."

        nama_bulan_laporan = get_month_name(bulan_target)
        
        # Buat tombol interaktif
        keyboard = [
            [
                InlineKeyboardButton("📈 Perbandingan", callback_data="compare"),
                InlineKeyboardButton("🔄 Segarkan", callback_data="laporan")
            ],
            [InlineKeyboardButton("➕ Tambah Transaksi", callback_data="add_transaction")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        pesan = (
            f"📊 *Laporan Keuangan {nama_bulan_laporan} {tahun_target}*\n\n"
            f"💼 *Saldo Awal:* `{format_currency(saldo_awal)}`\n\n"
            f"💰 *Pemasukan:* `{format_currency(pemasukan_bulan_ini)}`\n"
            f"💸 *Pengeluaran:* `{format_currency(pengeluaran_bulan_ini)}`\n"
            f"{'─' * 30}\n"
            f"🏦 *SALDO AKHIR:* `{format_currency(saldo_akhir)}`\n\n"
            f"{health_emoji} _{health_text}_"
            f"{rincian_pemasukan}"
            f"{rincian_pengeluaran}"
        )
        
        await loading_msg.edit_text(pesan, parse_mode='Markdown', reply_markup=reply_markup)
        
    except Exception as e:
        logging.error(f"❌ Kesalahan di laporan: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ *Error Membuat Laporan*\n\n"
            "Terjadi kesalahan saat membuat laporan.\n"
            "Silakan coba lagi dalam beberapa saat.",
            parse_mode='Markdown'
        )

@restricted
async def compare_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menghasilkan laporan perbandingan terperinci antara bulan ini dan sebelumnya dengan performa optimal."""
    try:
        loading_msg = await update.message.reply_text("⏳ *Menyusun analisis perbandingan...*", parse_mode='Markdown')
        
        # Ambil dan validasi data
        try:
            sheet = get_worksheet("Transaksi")
            if not sheet:
                await loading_msg.edit_text(
                    "❌ *Worksheet Tidak Ditemukan*\n\n"
                    "Worksheet 'Transaksi' tidak ditemukan.\n"
                    "Pastikan spreadsheet memiliki sheet dengan nama 'Transaksi'.",
                    parse_mode='Markdown'
                )
                return
                
            data = sheet.get_all_records()
            if not data:
                await loading_msg.edit_text(
                    "📭 *Belum Ada Data*\n\n"
                    "Belum ada data untuk dibandingkan.\n"
                    "Mulai catat transaksi terlebih dahulu!",
                    parse_mode='Markdown'
                )
                return
        except Exception as e:
            logging.error(f"❌ Kesalahan mengakses worksheet di compare_report: {e}")
            await loading_msg.edit_text(
                "⚠️ *Error Mengakses Data*\n\n"
                "Terjadi kesalahan saat mengakses data.\n"
                "Silakan coba lagi dalam beberapa saat.",
                parse_mode='Markdown'
            )
            return

        # Proses data secara efisien
        df = pd.DataFrame(data)
        df['Jumlah'] = pd.to_numeric(df['Jumlah'], errors='coerce').fillna(0)
        df['Tanggal'] = pd.to_datetime(df['Tanggal'], errors='coerce')
        df = df.dropna(subset=['Tanggal'])  # Lebih efisien daripada inplace=True

        # Dapatkan tanggal saat ini dan hitung bulan sebelumnya
        sekarang = datetime.datetime.now()
        bulan_ini, tahun_ini = sekarang.month, sekarang.year
        
        # Hitung bulan sebelumnya lebih efisien
        if bulan_ini == 1:
            bulan_lalu, tahun_lalu = 12, tahun_ini - 1
        else:
            bulan_lalu, tahun_lalu = bulan_ini - 1, tahun_ini

        # Buat mask filter untuk kinerja yang lebih baik
        mask_bulan_ini = ((df['Tanggal'].dt.month == bulan_ini) & 
                          (df['Tanggal'].dt.year == tahun_ini))
        mask_bulan_lalu = ((df['Tanggal'].dt.month == bulan_lalu) & 
                           (df['Tanggal'].dt.year == tahun_lalu))
        
        df_bulan_ini = df[mask_bulan_ini]
        df_bulan_lalu = df[mask_bulan_lalu]

        # Hitung total dengan operasi vektor
        mask_pemasukan_ini = df_bulan_ini['Tipe'] == 'Pemasukan'
        mask_pengeluaran_ini = df_bulan_ini['Tipe'] == 'Pengeluaran'
        mask_pemasukan_lalu = df_bulan_lalu['Tipe'] == 'Pemasukan'
        mask_pengeluaran_lalu = df_bulan_lalu['Tipe'] == 'Pengeluaran'
        
        pemasukan_ini = df_bulan_ini.loc[mask_pemasukan_ini, 'Jumlah'].sum()
        pengeluaran_ini = df_bulan_ini.loc[mask_pengeluaran_ini, 'Jumlah'].sum()
        pemasukan_lalu = df_bulan_lalu.loc[mask_pemasukan_lalu, 'Jumlah'].sum()
        pengeluaran_lalu = df_bulan_lalu.loc[mask_pengeluaran_lalu, 'Jumlah'].sum()

        # Hasilkan perbandingan kategori
        kat_pengeluaran_ini = df_bulan_ini[mask_pengeluaran_ini].groupby('Kategori')['Jumlah'].sum()
        kat_pengeluaran_lalu = df_bulan_lalu[mask_pengeluaran_lalu].groupby('Kategori')['Jumlah'].sum()
        
        # Buat dataframe perbandingan
        df_compare = pd.concat([kat_pengeluaran_ini.rename('Bulan Ini'), 
                               kat_pengeluaran_lalu.rename('Bulan Lalu')], 
                              axis=1).fillna(0)
        df_compare = df_compare.sort_values(by='Bulan Ini', ascending=False)
        
        # Bangun teks perbandingan
        rincian_teks = "\n\n📊 *Perbandingan per Kategori:*\n"
        for kategori, row in df_compare.head(8).iterrows():
            total_ini, total_lalu = row['Bulan Ini'], row['Bulan Lalu']
            selisih = total_ini - total_lalu
            
            # Tentukan indikator tren
            if selisih > 0:
                emoji = "🔺"
            elif selisih < 0:
                emoji = "🔻"
            else:
                emoji = "➖"
            
            rincian_teks += f"`#{kategori:<10}` {format_currency(total_ini)} vs {format_currency(total_lalu)} {emoji}\n"
        
        # Hitung perubahan persentase dengan aman
        pemasukan_change = ((pemasukan_ini - pemasukan_lalu) / pemasukan_lalu * 100) if pemasukan_lalu > 0 else 0
        pengeluaran_change = ((pengeluaran_ini - pengeluaran_lalu) / pengeluaran_lalu * 100) if pengeluaran_lalu > 0 else 0
        
        # Tentukan tren keseluruhan
        if pengeluaran_change > 10:
            trend_emoji = "⚠️"
            trend_text = "Pengeluaran meningkat signifikan!"
        elif pengeluaran_change < -10:
            trend_emoji = "✅"
            trend_text = "Pengeluaran berkurang signifikan!"
        else:
            trend_emoji = "📊"
            trend_text = "Pengeluaran relatif stabil."

        nama_bulan_ini = get_month_name(bulan_ini)
        nama_bulan_lalu = get_month_name(bulan_lalu)

        # Buat tombol interaktif
        keyboard = [
            [
                InlineKeyboardButton("📊 Laporan Detail", callback_data="laporan"),
                InlineKeyboardButton("🔄 Segarkan", callback_data="compare")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        pesan = (
            f"📈 *Analisis Perbandingan Keuangan*\n"
            f"_{nama_bulan_ini} vs {nama_bulan_lalu}_\n\n"
            f"💰 *Pemasukan:*\n"
            f"• {nama_bulan_ini}: `{format_currency(pemasukan_ini)}`\n"
            f"• {nama_bulan_lalu}: `{format_currency(pemasukan_lalu)}`\n"
            f"• Perubahan: `{pemasukan_change:+.1f}%`\n\n"
            f"💸 *Pengeluaran:*\n"
            f"• {nama_bulan_ini}: `{format_currency(pengeluaran_ini)}`\n"
            f"• {nama_bulan_lalu}: `{format_currency(pengeluaran_lalu)}`\n"
            f"• Perubahan: `{pengeluaran_change:+.1f}%`\n\n"
            f"{trend_emoji} _{trend_text}_"
            f"{rincian_teks}"
        )
        
        await loading_msg.edit_text(pesan, parse_mode='Markdown', reply_markup=reply_markup)
        
    except Exception as e:
        logging.error(f"❌ Kesalahan di compare_report: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ *Error Membuat Perbandingan*\n\n"
            "Terjadi kesalahan saat membuat analisis.\n"
            "Silakan coba lagi dalam beberapa saat.",
            parse_mode='Markdown'
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menangani penekanan tombol keyboard inline dengan penanganan error yang lebih baik."""
    query = update.callback_query
    
    try:
        await query.answer()
        
        # Buat objek update baru dengan pesan dari callback query
        # Ini diperlukan karena fungsi laporan dan compare_report mengharapkan update dengan pesan
        if query.data in ["laporan", "compare"]:
            # Buat objek update sementara yang memiliki atribut pesan
            class TempUpdate:
                def __init__(self, message):
                    self.message = message
                    self.effective_user = update.effective_user
            
            temp_update = TempUpdate(query.message)
            
            if query.data == "laporan":
                await laporan(temp_update, context)
            elif query.data == "compare":
                await compare_report(temp_update, context)
            return
        
        # Tangani tindakan tombol lain dengan pengeditan pesan langsung
        if query.data == "tips":
            tips_text = (
                "💡 *Tips Penggunaan Bot*\n\n"
                "📝 *Format Pesan:*\n"
                "• Gunakan angka tanpa titik/koma\n"
                "• Kategori harus diawali #\n"
                "• Keterangan bersifat opsional\n\n"
                "🏷️ *Kategori yang Disarankan:*\n"
                "`#makanan #transportasi #belanja #tagihan`\n"
                "`#hiburan #kesehatan #pendidikan #gaji`\n\n"
                "⚡ *Tips Cepat:*\n"
                "• Catat transaksi segera setelah terjadi\n"
                "• Gunakan kategori yang konsisten\n"
                "• Periksa laporan secara berkala\n"
                "• Bandingkan pengeluaran antar bulan"
            )
            await query.edit_message_text(tips_text, parse_mode='Markdown')
        elif query.data == "info":
            info_text = (
                "ℹ️ *Informasi Bot Keuangan Pribadi*\n\n"
                "🤖 *Versi:* 2.0.0\n"
                "👨‍💻 *Pengembang:* Asisten Keuangan Pribadi\n"
                "📊 *Database:* Google Sheets\n"
                "🔒 *Keamanan:* Akses Pribadi Saja\n\n"
                "✨ *Fitur Utama:*\n"
                "• Pencatatan transaksi otomatis\n"
                "• Laporan keuangan bulanan\n"
                "• Analisis perbandingan\n"
                "• Kategorisasi pengeluaran\n"
                "• Antarmuka interaktif\n\n"
                "📞 *Dukungan:* Hubungi administrator jika ada masalah"
            )
            await query.edit_message_text(info_text, parse_mode='Markdown')
        elif query.data == "format_help":
            format_text = (
                "📝 *Panduan Format Pesan*\n\n"
                "✅ *Format Benar:*\n"
                "`/masuk 500000 #gaji Gaji bulan ini`\n"
                "`/keluar 75000 #makanan Makan di restoran`\n"
                "`/keluar 20000 #transportasi Ongkos ojek`\n\n"
                "❌ *Format Salah:*\n"
                "`/masuk lima ratus ribu` _(bukan angka)_\n"
                "`/keluar 50.000` _(pakai titik)_\n"
                "`/masuk 100000 makanan` _(tanpa #)_\n\n"
                "💡 *Tips:*\n"
                "• Jumlah harus berupa angka bulat\n"
                "• Kategori wajib diawali dengan #\n"
                "• Keterangan boleh kosong"
            )
            await query.edit_message_text(format_text, parse_mode='Markdown')
        elif query.data == "add_more":
            add_text = (
                "➕ *Tambah Transaksi Baru*\n\n"
                "Gunakan perintah berikut:\n\n"
                "💰 *Untuk Pemasukan:*\n"
                "`/masuk [jumlah] #[kategori] [keterangan]`\n\n"
                "💸 *Untuk Pengeluaran:*\n"
                "`/keluar [jumlah] #[kategori] [keterangan]`\n\n"
                "📝 *Contoh Cepat:*\n"
                "• `/masuk 1000000 #gaji`\n"
                "• `/keluar 50000 #makanan`\n"
                "• `/keluar 100000 #belanja Kebutuhan bulanan`"
            )
            await query.edit_message_text(add_text, parse_mode='Markdown')
        elif query.data == "add_transaction":
            transaction_text = (
                "➕ *Menu Tambah Transaksi*\n\n"
                "Pilih jenis transaksi yang ingin dicatat:\n\n"
                "💰 *Pemasukan:* `/masuk [jumlah] #[kategori] [keterangan]`\n"
                "💸 *Pengeluaran:* `/keluar [jumlah] #[kategori] [keterangan]`\n\n"
                "🏷️ *Kategori Populer:*\n"
                "• Pemasukan: `#gaji #bonus #freelance #investasi`\n"
                "• Pengeluaran: `#makanan #transportasi #belanja #tagihan #hiburan`\n\n"
                "Ketik perintah langsung di chat untuk mencatat transaksi!"
            )
            await query.edit_message_text(transaction_text, parse_mode='Markdown')
        elif query.data == "start":
            # Kembali ke menu utama
            user_name = update.effective_user.first_name
            keyboard = [
                [
                    InlineKeyboardButton("📊 Laporan Bulan Ini", callback_data="laporan"),
                    InlineKeyboardButton("📈 Perbandingan", callback_data="compare")
                ],
                [
                    InlineKeyboardButton("💡 Tips Penggunaan", callback_data="tips"),
                    InlineKeyboardButton("ℹ️ Info Bot", callback_data="info")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            pesan = (
                f"👋 *Halo {user_name}!*\n\n"
                "🎯 *Bot Keuangan Pribadi* siap membantu!\n\n"
                "📝 *Perintah Utama:*\n"
                "• `/masuk [jumlah] #[kategori] [keterangan]`\n"
                "  _Contoh: /masuk 500000 #gaji Gaji bulan ini_\n\n"
                "• `/keluar [jumlah] #[kategori] [keterangan]`\n"
                "  _Contoh: /keluar 50000 #makanan Makan siang_\n\n"
                "📊 *Laporan & Analisis:*\n"
                "• `/laporan` - Ringkasan keuangan bulan ini\n"
                "• `/compare` - Perbandingan dengan bulan lalu\n\n"
                "💡 *Kategori Populer:*\n"
                "`#makanan #transportasi #belanja #tagihan #hiburan #kesehatan #gaji #bonus`\n\n"
                "Pilih menu di bawah untuk aksi cepat! 👇"
            )
            
            await query.edit_message_text(pesan, parse_mode='Markdown', reply_markup=reply_markup)
        else:
            # Tangani data callback yang tidak dikenal
            logging.warning(f"Callback data tidak dikenal: {query.data}")
            await query.edit_message_text(
                "⚠️ Terjadi kesalahan. Silakan coba lagi.",
                parse_mode='Markdown'
            )
    except Exception as e:
        logging.error(f"❌ Error saat menangani button callback: {e}", exc_info=True)
        try:
            await query.edit_message_text(
                "⚠️ Terjadi kesalahan saat memproses permintaan Anda. Silakan coba lagi.",
                parse_mode='Markdown'
            )
        except Exception:
            # Jika edit message gagal, coba kirim pesan baru
            try:
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text="⚠️ Terjadi kesalahan saat memproses permintaan Anda. Silakan coba lagi.",
                    parse_mode='Markdown'
                )
            except Exception as e2:
                logging.error(f"❌ Gagal mengirim pesan error: {e2}")