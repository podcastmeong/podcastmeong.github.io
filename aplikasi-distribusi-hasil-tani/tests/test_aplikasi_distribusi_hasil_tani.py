"""Tes Aplikasi Distribusi Hasil Tani (#51) — Playwright Chromium, file lokal.
Hari ini 2026-11-20. Data seed (tanggal relatif, diuji silang Python):
  Harga 8 komoditas: Padi 5500, Jagung 4500, Tomat 9000, Udang 65000, Sawi 6000,
    Lele 25000, Cabai 32000, Kopi 45000 (per kg).
  Hasil tani 8: stok awal 8.080 kg (Padi 4200, Jagung 1750, Tomat 580, Udang 380,
    Sawi 140, Lele 480, Cabai 250, Kopi 300).
  Pesanan 11 (1 Batal): aktif 10, 4.530 kg / Rp44.660.000.
    Dipesan 4 (2.050 kg / Rp22.050.000), Dikirim 2 (1.700 kg / Rp13.250.000),
    Selesai 4 (780 kg / Rp9.360.000), Batal 1 (500 kg / Rp2.750.000).
    Nov: 4.010 kg / Rp37.460.000; Okt: 520 kg / Rp7.200.000.
  Stok tersisa: Padi 1700, Jagung 550, Tomat 380, Udang 230, Sawi 80, Lele 280,
    Cabai 150, Kopi 180 — total 3.550 kg.
  Pengiriman 8: Dijadwalkan 2 (segera 2: PG6 T+1, PG7 T+2; lewat 0), Dikirim 2,
    Sampai 4; ongkir total Rp3.225.000 (Nov Rp2.425.000, Okt Rp800.000).
  Petani (Tomat, Sawi, Cabai): stok awal 970 kg, pesanan aktif 360 kg / Rp5.360.000,
    tersisa 610 kg, selesai Rp2.160.000, pengiriman 2 (Sampai), ongkir Rp225.000.
  CSV: bulan berjalan (Nov) 10 baris pesanan + header = 11 baris;
    Okt 2 baris + header = 3 baris.
Catatan: langkah 5 menambah 100 kg Padi milik petani ("Sawah Baru"), jadi angka
petani/distributor setelah itu bergeser +100 kg (tersisa petani 710 kg dari 1.070 kg;
stok tersisa distributor/admin 3.650 kg).
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent  # folder aplikasi-distribusi-hasil-tani
URL = "file://" + str(ROOT / "index.html")

failures = []
passed = 0
console_errors = []
page_errors = []


def check(name, cond, extra=""):
    global passed
    if cond:
        passed += 1
        print(f"  OK  {name}")
    else:
        failures.append(name)
        print(f"  GAGAL  {name} {extra}")


def text(page, sel):
    el = page.query_selector(sel)
    return el.inner_text() if el else ""


def login(page, user, pw):
    page.fill("#loginUser", user)
    page.fill("#loginPass", pw)
    page.click("#formLogin button[type=submit]")
    page.wait_for_timeout(400)


def logout(page):
    page.click("#btnKeluar")
    page.wait_for_timeout(300)


def tab(page, nama):
    page.click(f'[data-tab="{nama}"]')
    page.wait_for_timeout(200)


def konfirmasi_modal(page):
    if page.is_visible("#modalBack.open"):
        page.click("#modalYa")
        page.wait_for_timeout(300)
        return True
    return False


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.goto(URL, wait_until="load")
        page.wait_for_timeout(300)

        # ---- 1. Struktur + login overlay ----
        check("Judul halaman", page.title() == "Aplikasi Distribusi Hasil Tani", page.title())
        check("Overlay login terlihat", page.is_visible("#loginOverlay"))
        login_text = text(page, "#loginOverlay")
        check("Layar login menampilkan akun admin", "admin / admin123" in login_text)
        check("Layar login menampilkan akun distributor", "distributor / distributor123" in login_text)
        check("Layar login menampilkan akun petani", "petani / petani123" in login_text)
        body = text(page, "body")
        check("TIDAK ada kartu toko/kamar", page.query_selector(".card-toko") is None and page.query_selector(".card-kamar") is None)
        check("TIDAK ada tautan toko", "toko.html" not in body)
        page.fill("#loginUser", "admin")
        page.fill("#loginPass", "salah")
        page.click("#formLogin button[type=submit]")
        page.wait_for_timeout(200)
        check("Login gagal menampilkan pesan", page.is_visible("#loginError"))

        # ---- 2. Login admin ----
        page.fill("#loginPass", "admin123")
        page.click("#formLogin button[type=submit]")
        page.wait_for_timeout(400)
        check("Setelah login overlay hilang", not page.is_visible("#loginOverlay"))
        check("Chip pengguna admin", "Administrator (Admin)" in text(page, "#userChip"))

        # ---- 3. Dasbor (angka seed) ----
        check("Dasbor stok tersisa", text(page, "#dStok") == "3.550 kg", text(page, "#dStok"))
        check("Dasbor stok subtotal", "8.080 kg" in text(page, "#dStokSub"))
        check("Dasbor nilai pesanan aktif", text(page, "#dNilaiPesanan") == "Rp44.660.000", text(page, "#dNilaiPesanan"))
        check("Dasbor nilai pesanan subtotal", "4.530 kg" in text(page, "#dNilaiPesananSub"))
        check("Dasbor nilai selesai", text(page, "#dSelesai") == "Rp9.360.000", text(page, "#dSelesai"))
        check("Dasbor ongkir", text(page, "#dOngkir") == "Rp3.225.000", text(page, "#dOngkir"))
        check("Dasbor kirim hari ini", text(page, "#dKirimHariIni") == "0")
        check("Dasbor kirim segera", text(page, "#dKirimSegera") == "2")
        check("Dasbor kirim lewat", text(page, "#dKirimLewat") == "0")
        check("Dasbor dipesan", text(page, "#dDipesan") == "4")
        check("Badge hasil", text(page, "#badgeHasil") == "8")
        check("Badge pesanan", text(page, "#badgePesanan") == "4")
        check("Badge pengiriman", text(page, "#badgePengiriman") == "2")
        check("Kartu kelola pengguna terlihat untuk admin", page.is_visible("#cardPengguna"))
        check("Kartu ganti sandi sendiri terlihat", page.is_visible("#cardSandiSaya"))
        users_text = text(page, "#daftarPengguna")
        check("Daftar pengguna memuat distributor", "Dedi Kurniawan" in users_text)
        check("Daftar pengguna memuat petani", "Budi Santoso" in users_text)
        check("Daftar pengguna memuat tombol reset", "Reset ke bk123" in users_text)

        # ---- 4. Tab Hasil Tani ----
        tab(page, "hasil")
        check("Panel hasil aktif", page.is_visible("#panel-hasil"))
        hasil_text = text(page, "#panel-hasil")
        check("Hasil: Padi Ciherang", "Padi Ciherang" in hasil_text)
        check("Hasil: stok Padi tersisa 1.700", "1.700 / 4.200 kg" in hasil_text)
        check("Hasil: Udang Vaname", "Udang Vaname" in hasil_text)
        check("Hasil: stok Udang tersisa 230", "230 / 380 kg" in hasil_text)
        check("Hasil: Kopi Robusta", "Kopi Robusta" in hasil_text)
        check("Hasil: ringkasan 8 hasil tani", "8 hasil tani" in text(page, "#ringkasanHasil"))
        check("Hasil: ringkasan stok tersisa", "3.550 kg" in text(page, "#ringkasanHasil"))
        check("Hasil: ringkasan stok awal", "8.080 kg" in text(page, "#ringkasanHasil"))

        # ---- 5. Tambah hasil tani baru (Padi 100 kg, pemilik petani) ----
        page.select_option("#htKomoditas", "Padi Ciherang")
        page.fill("#htKg", "100")
        page.fill("#htLokasi", "Sawah Baru")
        page.select_option("#htPemilik", "petani")
        page.click("#btnTambahHasil")
        page.wait_for_timeout(200)
        hasil_setelah = text(page, "#panel-hasil")
        check("Hasil baru muncul", "Sawah Baru" in hasil_setelah)
        check("Ringkasan naik jadi 9 hasil", "9 hasil tani" in text(page, "#ringkasanHasil"))
        check("Ringkasan stok awal naik", "8.180 kg" in text(page, "#ringkasanHasil"))
        check("Ringkasan stok tersisa naik", "3.650 kg" in text(page, "#ringkasanHasil"))

        # ---- 6. Tab Pesanan ----
        tab(page, "pesanan")
        check("Panel pesanan aktif", page.is_visible("#panel-pesanan"))
        pesanan_text = text(page, "#panel-pesanan")
        check("Pesanan: Toko Beras Jaya", "Toko Beras Jaya" in pesanan_text)
        check("Pesanan: Pasar Induk Kramat Jati", "Pasar Induk Kramat Jati" in pesanan_text)
        check("Pesanan: nilai Toko Beras Jaya 1000 kg", "Rp5.500.000" in pesanan_text)
        check("Pesanan: ringkasan nilai aktif", "Rp44.660.000" in text(page, "#ringkasanPesanan"))
        check("Pesanan: ringkasan nilai selesai", "Rp9.360.000" in text(page, "#ringkasanPesanan"))
        # Pesanan baru: Jagung 100 kg x 4500 = Rp450.000 (stok Jagung tersisa 550)
        page.select_option("#psHasil", label="Jagung Manis · tersisa 550 kg · Rp4.500/kg")
        page.fill("#psPembeli", "Toko Uji")
        page.fill("#psKg", "100")
        page.click("#btnTambahPesanan")
        page.wait_for_timeout(200)
        pesanan_setelah = text(page, "#panel-pesanan")
        check("Pesanan baru muncul", "Toko Uji" in pesanan_setelah)
        check("Pesanan baru nilai", "Rp450.000" in pesanan_setelah)
        check("Ringkasan nilai aktif naik", "Rp45.110.000" in text(page, "#ringkasanPesanan"))
        tab(page, "hasil")
        check("Stok Jagung berkurang jadi 450", "450 / 1.750 kg" in text(page, "#panel-hasil"))
        # Pesanan melebihi stok ditolak (Jagung tersisa 450, pesan 500)
        tab(page, "pesanan")
        page.select_option("#psHasil", label="Jagung Manis · tersisa 450 kg · Rp4.500/kg")
        page.fill("#psPembeli", "Toko Serakah")
        page.fill("#psKg", "500")
        page.click("#btnTambahPesanan")
        page.wait_for_timeout(200)
        check("Pesanan melebihi stok ditolak", "Toko Serakah" not in text(page, "#panel-pesanan"))
        check("Ringkasan nilai aktif tetap", "Rp45.110.000" in text(page, "#ringkasanPesanan"))
        # Batalkan pesanan "Toko Uji" (tombol batal pertama = pesanan terbaru, Toko Uji)
        page.click("[data-pesanan-batal]")
        page.wait_for_timeout(200)
        check("Modal konfirmasi batal muncul", konfirmasi_modal(page))
        check("Ringkasan kembali 44.660.000 setelah batal", "Rp44.660.000" in text(page, "#ringkasanPesanan"))
        check("Pesanan Toko Uji berstatus Batal", "Batal" in text(page, "#panel-pesanan"))

        # ---- 7. Tab Pengiriman ----
        tab(page, "pengiriman")
        check("Panel pengiriman aktif", page.is_visible("#panel-pengiriman"))
        kirim_text = text(page, "#panel-pengiriman")
        check("Pengiriman: Toko Beras Jaya", "Toko Beras Jaya" in kirim_text)
        check("Pengiriman: Koperasi Tani Makmur", "Koperasi Tani Makmur" in kirim_text)
        check("Pengiriman: ringkasan hari ini 0", "hari ini 0" in text(page, "#ringkasanPengiriman"))
        check("Pengiriman: ringkasan segera 2", "segera 2" in text(page, "#ringkasanPengiriman"))
        check("Pengiriman: ringkasan lewat 0", "lewat 0" in text(page, "#ringkasanPengiriman"))
        check("Pengiriman: ringkasan ongkir", "Rp3.225.000" in text(page, "#ringkasanPengiriman"))
        check("Pengiriman: label segera PG6", "Dalam 1 hari" in kirim_text)
        check("Pengiriman: label segera PG7", "Dalam 2 hari" in kirim_text)
        # Buat pengiriman dari pesanan Dipesan pertama (Toko Beras Jaya, id 1)
        from datetime import date, timedelta
        t3 = (date.today() + timedelta(days=3)).isoformat()
        page.select_option("#pgPesanan", index=0)
        page.fill("#pgTanggal", t3)
        page.fill("#pgOngkir", "100000")
        page.click("#btnTambahPengiriman")
        page.wait_for_timeout(300)
        kirim_setelah = text(page, "#panel-pengiriman")
        check("Pengiriman baru muncul", "Rp100.000" in kirim_setelah)
        check("Ringkasan ongkir naik", "Rp3.325.000" in text(page, "#ringkasanPengiriman"))
        check("Ringkasan segera naik jadi 3", "segera 3" in text(page, "#ringkasanPengiriman"))
        check("Ada tombol Tandai Dikirim", page.query_selector("[data-kirim-dikirim]") is not None)
        # Tandai PG6 (Toko Beras Jaya, T+1) dikirim
        btn_pg6 = page.query_selector('[data-kirim-dikirim="6"]')
        check("Tombol Tandai Dikirim PG6 ada", btn_pg6 is not None)
        if btn_pg6:
            btn_pg6.click()
            page.wait_for_timeout(300)
            check("PG6 berubah jadi Dikirim", "Dikirim" in text(page, "#panel-pengiriman"))
            tab(page, "pesanan")
            ps_lagi = text(page, "#panel-pesanan")
            check("Pesanan id 1 ikut Dikirim", "Dikirim" in ps_lagi and "Rp5.500.000" in ps_lagi)
        # Tandai PG1 sampai -> pesanan id 2 selesai
        tab(page, "pengiriman")
        btn_pg1 = page.query_selector('[data-kirim-sampai="1"]')
        check("Tombol Tandai Sampai PG1 ada", btn_pg1 is not None)
        if btn_pg1:
            btn_pg1.click()
            page.wait_for_timeout(300)
            check("PG1 berubah jadi Sampai", "Sampai" in text(page, "#panel-pengiriman"))
            tab(page, "pesanan")
            check("Pesanan id 2 ikut Selesai", "Selesai" in text(page, "#panel-pesanan"))

        # ---- 8. Tab Harga ----
        tab(page, "harga")
        check("Panel harga aktif", page.is_visible("#panel-harga"))
        harga_text = text(page, "#panel-harga")
        check("Harga: Padi Ciherang Rp5.500", "Rp5.500" in harga_text)
        check("Harga: Udang Vaname Rp65.000", "Rp65.000" in harga_text)
        check("Harga: Kopi Robusta Rp45.000", "Rp45.000" in harga_text)
        check("Harga: 8 komoditas", "8 komoditas" in text(page, "#ringkasanHarga"))
        page.fill('[data-harga-ubah="Tomat"]', "9500")
        page.click('[data-harga-simpan="Tomat"]')
        page.wait_for_timeout(200)
        check("Harga Tomat berubah", "Rp9.500" in text(page, "#panel-harga"))
        page.fill("#hgKomoditas", "Bawang Merah")
        page.fill("#hgHarga", "20000")
        page.click("#btnSimpanHarga")
        page.wait_for_timeout(200)
        harga_baru = text(page, "#panel-harga")
        check("Harga baru muncul", "Bawang Merah" in harga_baru)
        check("Ringkasan naik jadi 9 komoditas", "9 komoditas" in text(page, "#ringkasanHarga"))

        # ---- 9. Tab Laporan ----
        tab(page, "laporan")
        check("Panel laporan aktif", page.is_visible("#panel-laporan"))
        lap_text = text(page, "#panel-laporan")
        check("Laporan: per komoditas Padi", "Padi Ciherang" in lap_text)
        check("Laporan: Padi total 2.500 kg", "2.500" in lap_text)
        check("Laporan: per pembeli Toko Beras Jaya", "Toko Beras Jaya" in lap_text)
        check("Laporan: per bulan November 2026", "November 2026" in lap_text)
        check("Laporan: stok tersisa Padi 1.700", "1.700" in lap_text)
        check("Laporan: ringkasan", "44.660.000" in text(page, "#ringkasanLaporan"))
        bulan_val = page.input_value("#fBulanLaporan")
        bulan_berjalan = date.today().isoformat()[:7]
        check("Bulan laporan default = bulan berjalan", bulan_val == bulan_berjalan, f"dapat {bulan_val}")
        # CSV bulan berjalan: 10 baris pesanan + header = 11 baris
        with page.expect_download() as dl:
            page.click("#btnCsvLaporan")
        csv_path = dl.value.path()
        csv_isi = Path(csv_path).read_text(encoding="utf-8")
        csv_baris = [b for b in csv_isi.strip().split("\n") if b.strip()]
        check("CSV bulan berjalan 11 baris", len(csv_baris) == 11, f"dapat {len(csv_baris)}")
        check("CSV memuat Toko Beras Jaya", "Toko Beras Jaya" in csv_isi)
        # CSV Oktober: 2 baris + header = 3 baris
        page.select_option("#fBulanLaporan", "2026-10")
        page.wait_for_timeout(200)
        with page.expect_download() as dl2:
            page.click("#btnCsvLaporan")
        csv2 = Path(dl2.value.path()).read_text(encoding="utf-8")
        csv2_baris = [b for b in csv2.strip().split("\n") if b.strip()]
        check("CSV Oktober 3 baris", len(csv2_baris) == 3, f"dapat {len(csv2_baris)}")
        check("CSV Oktober memuat Pasar Tradisional Cikini", "Pasar Tradisional Cikini" in csv2)

        # ---- 10. Panduan ----
        tab(page, "panduan")
        check("Panel panduan aktif", page.is_visible("#panel-panduan"))
        panduan_text = text(page, "#panel-panduan")
        check("Panduan: harga Basic", "Rp499.000" in panduan_text)
        check("Panduan: harga Professional", "Rp999.000" in panduan_text)
        check("Panduan: harga Business", "Rp1.999.000" in panduan_text)
        check("Panduan: langganan 49.000", "Rp49.000" in panduan_text)
        check("Panduan: APK +400.000", "Rp400.000" in panduan_text)
        check("Panduan: batasan jujur localStorage", "localStorage" in panduan_text)
        check("Panduan: bukan payment gateway", "payment gateway" in panduan_text)
        check("Panduan: akun demo admin", "admin / admin123" in panduan_text)

        # ---- 11. Ganti kata sandi sendiri (admin) ----
        tab(page, "dashboard")
        page.fill("#sandiLama", "admin123")
        page.fill("#sandiBaru", "adminBaru1")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(200)
        check("Ganti sandi berhasil", "berhasil" in text(page, "#pesanSandi"))
        logout(page)
        check("Overlay login muncul lagi setelah keluar", page.is_visible("#loginOverlay"))
        login(page, "admin", "adminBaru1")
        check("Login dengan sandi baru berhasil", not page.is_visible("#loginOverlay"))
        page.fill("#sandiLama", "adminBaru1")
        page.fill("#sandiBaru", "admin123")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(200)
        check("Sandi admin dikembalikan", "berhasil" in text(page, "#pesanSandi"))

        # ---- 12. Tambah pengguna baru lalu reset kata sandinya ----
        page.fill("#pgUser", "ujiuser")
        page.fill("#pgNama", "Uji Coba")
        page.select_option("#pgPeran", "distributor")
        page.fill("#pgPass", "uji12345")
        page.click("#btnTambahPengguna")
        page.wait_for_timeout(200)
        check("Pengguna baru muncul", "Uji Coba" in text(page, "#daftarPengguna"))
        page.click('[data-reset="ujiuser"]')
        page.wait_for_timeout(200)
        check("Modal konfirmasi reset muncul", konfirmasi_modal(page))
        logout(page)
        login(page, "ujiuser", "bk123")
        check("Login pengguna direset (bk123) berhasil", not page.is_visible("#loginOverlay"))
        check("Chip distributor uji", "Distributor" in text(page, "#userChip"))
        logout(page)
        login(page, "admin", "admin123")
        page.click('[data-hapus-user="ujiuser"]')
        page.wait_for_timeout(200)
        konfirmasi_modal(page)
        check("Pengguna uji terhapus", "Uji Coba" not in text(page, "#daftarPengguna"))

        # ---- 13. Peran Petani (data terlihat saja) ----
        logout(page)
        login(page, "petani", "petani123")
        check("Login petani berhasil", not page.is_visible("#loginOverlay"))
        check("Chip petani", "Budi Santoso (Petani)" in text(page, "#userChip"))
        check("Dasbor petani stok tersisa", text(page, "#dStok") == "710 kg", text(page, "#dStok"))
        check("Dasbor petani stok subtotal", "1.070 kg" in text(page, "#dStokSub"))
        check("Dasbor petani nilai aktif", text(page, "#dNilaiPesanan") == "Rp5.360.000", text(page, "#dNilaiPesanan"))
        check("Dasbor petani nilai selesai", text(page, "#dSelesai") == "Rp2.160.000", text(page, "#dSelesai"))
        check("Dasbor petani ongkir", text(page, "#dOngkir") == "Rp225.000", text(page, "#dOngkir"))
        check("Dasbor petani kirim segera", text(page, "#dKirimSegera") == "0")
        check("Kartu kelola pengguna tersembunyi untuk petani", not page.is_visible("#cardPengguna"))
        check("Kartu ganti sandi tetap terlihat untuk petani", page.is_visible("#cardSandiSaya"))
        tab(page, "hasil")
        hasil_petani = text(page, "#daftarHasil")
        check("Petani melihat Tomat", "Tomat" in hasil_petani)
        check("Petani melihat Cabai Merah", "Cabai Merah" in hasil_petani)
        check("Petani melihat hasil tambahannya (Sawah Baru)", "Sawah Baru" in hasil_petani)
        check("Petani tidak melihat Udang", "Udang Vaname" not in hasil_petani)
        check("Petani tidak melihat Jagung", "Jagung Manis" not in hasil_petani)
        check("Petani: ringkasan 4 hasil", "4 hasil tani" in text(page, "#ringkasanHasil"))
        tab(page, "harga")
        check("Petani tidak melihat tombol simpan harga", page.query_selector("[data-harga-simpan]") is None)
        check("Petani tidak melihat tombol tambah harga", not page.is_visible("#btnSimpanHarga"))
        tab(page, "pesanan")
        ps_petani = text(page, "#daftarPesanan")
        check("Petani melihat Restoran Sederhana", "Restoran Sederhana" in ps_petani)
        check("Petani tidak melihat Toko Beras Jaya", "Toko Beras Jaya" not in ps_petani)
        check("Petani tidak melihat tombol tambah pesanan", not page.is_visible("#btnTambahPesanan"))
        tab(page, "pengiriman")
        pg_petani = text(page, "#daftarPengiriman")
        check("Petani melihat Warung Sayur Bu Ani", "Warung Sayur Bu Ani" in pg_petani)
        check("Petani tidak melihat Pasar Induk", "Pasar Induk Kramat Jati" not in pg_petani)
        check("Petani tidak melihat tombol tambah pengiriman", not page.is_visible("#btnTambahPengiriman"))

        # ---- 14. Peran Distributor ----
        logout(page)
        login(page, "distributor", "distributor123")
        check("Login distributor berhasil", not page.is_visible("#loginOverlay"))
        check("Chip distributor", "Dedi Kurniawan (Distributor)" in text(page, "#userChip"))
        check("Kartu kelola pengguna tersembunyi untuk distributor", not page.is_visible("#cardPengguna"))
        check("Kartu ganti sandi tetap terlihat untuk distributor", page.is_visible("#cardSandiSaya"))
        check("Dasbor distributor stok tersisa", text(page, "#dStok") == "3.650 kg", text(page, "#dStok"))

        # ---- 15. Backup JSON + reset data demo ----
        logout(page)
        login(page, "admin", "admin123")
        tab(page, "laporan")
        with page.expect_download() as dl3:
            page.click("#btnBackup")
        backup_isi = Path(dl3.value.path()).read_text(encoding="utf-8")
        check("Backup JSON memuat nama aplikasi", "aplikasi-distribusi-hasil-tani" in backup_isi)
        check("Backup JSON memuat hasil tani", '"hasil"' in backup_isi)
        page.click("#btnResetData")
        page.wait_for_timeout(200)
        check("Modal konfirmasi reset muncul", konfirmasi_modal(page))
        tab(page, "dashboard")
        check("Setelah reset stok kembali 3.550", text(page, "#dStok") == "3.550 kg", text(page, "#dStok"))
        check("Setelah reset nilai aktif kembali", text(page, "#dNilaiPesanan") == "Rp44.660.000", text(page, "#dNilaiPesanan"))
        check("Setelah reset ongkir kembali", text(page, "#dOngkir") == "Rp3.225.000", text(page, "#dOngkir"))

        # ---- 16. Console errors ----
        check("0 console error", len(console_errors) == 0, " | ".join(console_errors[:5]))
        check("0 page error", len(page_errors) == 0, " | ".join(page_errors[:5]))
        browser.close()

    print(f"\n=== HASIL: {passed}/{passed + len(failures)} lolos ===")
    if failures:
        print("GAGAL:")
        for f in failures:
            print(" - " + f)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
