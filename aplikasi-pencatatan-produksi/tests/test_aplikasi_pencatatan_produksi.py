"""Tes Aplikasi Pencatatan Produksi (#52) — Playwright Chromium, file lokal.
Hari ini 2026-11-20. Data seed (tanggal relatif, diuji silang Python):
  Produk 8 (harga/satuan): Padi 5500/kg, Jagung 4500/kg, Tomat 9000/kg,
    Telur Ayam 2200/butir, Susu Sapi 15000/liter, Lele 25000/kg,
    Cabai Merah 32000/kg, Kopi Robusta 45000/kg.
  Produksi 15 catatan, nilai total Rp70.110.000.
    Nov (11): Rp52.410.000. Okt (4): Rp17.700.000.
    7 hari terakhir, hari ini + 6 hari ke belakang (4): Rp17.770.000.
    Per produk: Susu 830 liter Rp12.450.000; Telur 5.500 butir Rp12.100.000;
      Padi 2.100 kg Rp11.550.000; Kopi 250 kg Rp11.250.000; Lele 350 kg Rp8.750.000;
      Jagung 1.400 kg Rp6.300.000; Tomat 430 kg Rp3.870.000; Cabai 120 kg Rp3.840.000.
    Petani (Tomat, Telur, Cabai — 5 catatan): Rp19.810.000; 7 hari 2 catatan Rp7.120.000.
  Biaya 14 catatan, total Rp16.750.000 (Bahan 11.450.000, Tenaga Kerja 4.800.000, Lain-lain 500.000).
    Nov (12): Rp15.250.000. Okt (2): Rp1.500.000. Petani (4): Rp4.650.000.
  Laba: Nov Rp37.160.000; Okt Rp16.200.000; total Rp53.360.000; petani Rp15.160.000.
  Perbandingan Nov vs Okt: nilai +196,1%; biaya +916,7%; laba +129,4%.
  Per produk (nilai/biaya/laba): Padi 11.550.000/4.800.000/6.750.000;
    Jagung 6.300.000/1.600.000/4.700.000; Tomat 3.870.000/600.000/3.270.000;
    Telur 12.100.000/3.300.000/8.800.000; Susu 12.450.000/3.300.000/9.150.000;
    Lele 8.750.000/1.100.000/7.650.000; Cabai 3.840.000/750.000/3.090.000;
    Kopi 11.250.000/1.300.000/9.950.000.
  CSV produksi: Nov 11 baris + header = 12; Okt 4 baris + header = 5.
"""
import sys
from datetime import date
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent  # folder aplikasi-pencatatan-produksi
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
        check("Judul halaman", page.title() == "Aplikasi Pencatatan Produksi", page.title())
        check("Overlay login terlihat", page.is_visible("#loginOverlay"))
        login_text = text(page, "#loginOverlay")
        check("Layar login menampilkan akun admin", "admin / admin123" in login_text)
        check("Layar login menampilkan akun manajer", "manajer / manajer123" in login_text)
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
        check("Masuk mendarat di dasbor", page.is_visible("#panel-dashboard"))

        # ---- 3. Dasbor (angka seed) ----
        check("Dasbor nilai bulan ini", text(page, "#dNilaiBulan") == "Rp52.410.000", text(page, "#dNilaiBulan"))
        check("Dasbor nilai bulan subtotal", "11 catatan" in text(page, "#dNilaiBulanSub"))
        check("Dasbor biaya bulan ini", text(page, "#dBiayaBulan") == "Rp15.250.000", text(page, "#dBiayaBulan"))
        check("Dasbor biaya bulan subtotal", "12 catatan" in text(page, "#dBiayaBulanSub"))
        check("Dasbor laba bulan ini", text(page, "#dLabaBulan") == "Rp37.160.000", text(page, "#dLabaBulan"))
        check("Dasbor 7 hari terakhir", text(page, "#dTujuhHari") == "4 catatan", text(page, "#dTujuhHari"))
        check("Dasbor 7 hari nilai", "Rp17.770.000" in text(page, "#dTujuhHariSub"), text(page, "#dTujuhHariSub"))
        check("Dasbor total nilai", text(page, "#dNilaiTotal") == "Rp70.110.000", text(page, "#dNilaiTotal"))
        check("Dasbor total biaya", text(page, "#dBiayaTotal") == "Rp16.750.000", text(page, "#dBiayaTotal"))
        check("Dasbor total laba", text(page, "#dLabaTotal") == "Rp53.360.000", text(page, "#dLabaTotal"))
        check("Dasbor produk nilai tertinggi", text(page, "#dProdukTop") == "Susu Sapi", text(page, "#dProdukTop"))
        check("Dasbor produk top subtotal", "Rp12.450.000" in text(page, "#dProdukTopSub"))
        check("Badge produksi", text(page, "#badgeProduksi") == "15")
        check("Badge biaya", text(page, "#badgeBiaya") == "14")
        check("Kartu kelola pengguna terlihat untuk admin", page.is_visible("#cardPengguna"))
        check("Kartu ganti sandi sendiri terlihat", page.is_visible("#cardSandiSaya"))
        users_text = text(page, "#daftarPengguna")
        check("Daftar pengguna memuat manajer", "Dedi Kurniawan" in users_text)
        check("Daftar pengguna memuat petani", "Budi Santoso" in users_text)
        check("Daftar pengguna memuat tombol reset", "Reset ke bk123" in users_text)

        # ---- 4. Tab Produksi ----
        tab(page, "produksi")
        check("Panel produksi aktif", page.is_visible("#panel-produksi"))
        prod_text = text(page, "#panel-produksi")
        check("Produksi: Padi", "Padi" in prod_text)
        check("Produksi: Telur Ayam", "Telur Ayam" in prod_text)
        check("Produksi: ringkasan 15 catatan", "15 catatan produksi" in text(page, "#ringkasanProduksi"))
        check("Produksi: ringkasan total nilai", "Rp70.110.000" in text(page, "#ringkasanProduksi"))
        check("Produksi: nilai Padi 1200 kg", "Rp6.600.000" in prod_text)
        # Tambah produksi: Tomat 100 kg x 9000 = Rp900.000
        page.select_option("#prProduk", "Tomat")
        page.fill("#prJumlah", "100")
        check("Pratinjau nilai produksi live", page.input_value("#prNilai") == "Rp900.000", page.input_value("#prNilai"))
        page.click("#btnTambahProduksi")
        page.wait_for_timeout(200)
        prod_setelah = text(page, "#panel-produksi")
        check("Produksi baru muncul", "Rp900.000" in prod_setelah)
        check("Ringkasan naik jadi 16 catatan", "16 catatan produksi" in text(page, "#ringkasanProduksi"))
        check("Ringkasan total naik", "Rp71.010.000" in text(page, "#ringkasanProduksi"))
        # Hapus produksi baru (tombol hapus pertama = catatan terbaru, Tomat hari ini)
        page.click("[data-hapus-produksi]")
        page.wait_for_timeout(200)
        check("Modal konfirmasi hapus produksi muncul", konfirmasi_modal(page))
        check("Ringkasan kembali 15 catatan", "15 catatan produksi" in text(page, "#ringkasanProduksi"))
        check("Ringkasan total kembali", "Rp70.110.000" in text(page, "#ringkasanProduksi"))
        # Ubah harga produk Tomat -> 9500, lalu kembalikan 9000
        page.fill('[data-harga-ubah="Tomat"]', "9500")
        page.click('[data-harga-simpan="Tomat"]')
        page.wait_for_timeout(200)
        check("Harga Tomat berubah", "Rp9.500" in text(page, "#panel-produksi"))
        page.fill('[data-harga-ubah="Tomat"]', "9000")
        page.click('[data-harga-simpan="Tomat"]')
        page.wait_for_timeout(200)
        check("Harga Tomat dikembalikan", "Rp9.000" in text(page, "#panel-produksi"))

        # ---- 5. Tab Biaya ----
        tab(page, "biaya")
        check("Panel biaya aktif", page.is_visible("#panel-biaya"))
        biaya_text = text(page, "#panel-biaya")
        check("Biaya: Padi Bahan", "Pupuk kandang" in biaya_text)
        check("Biaya: Pakan ayam", "Pakan ayam" in biaya_text)
        check("Biaya: ringkasan 14 catatan", "14 catatan biaya" in text(page, "#ringkasanBiaya"))
        check("Biaya: ringkasan total", "Rp16.750.000" in text(page, "#ringkasanBiaya"))
        page.select_option("#byProduk", "Padi")
        page.select_option("#byKategori", "Bahan")
        page.fill("#byJumlah", "250000")
        page.fill("#byKeterangan", "Biaya Uji")
        page.click("#btnTambahBiaya")
        page.wait_for_timeout(200)
        check("Biaya baru muncul", "Biaya Uji" in text(page, "#panel-biaya"))
        check("Ringkasan biaya naik", "Rp17.000.000" in text(page, "#ringkasanBiaya"))
        page.click("[data-hapus-biaya]")
        page.wait_for_timeout(200)
        check("Modal konfirmasi hapus biaya muncul", konfirmasi_modal(page))
        check("Ringkasan biaya kembali", "Rp16.750.000" in text(page, "#ringkasanBiaya"))

        # ---- 6. Tab Periode ----
        tab(page, "periode")
        check("Panel periode aktif", page.is_visible("#panel-periode"))
        check("Periode default mulai = 1 Nov 2026", page.input_value("#pdMulai") == "2026-11-01", page.input_value("#pdMulai"))
        check("Periode default akhir = hari ini", page.input_value("#pdAkhir") == date.today().isoformat(), page.input_value("#pdAkhir"))
        check("Periode Nov nilai", text(page, "#pdNilai") == "Rp52.410.000", text(page, "#pdNilai"))
        check("Periode Nov biaya", text(page, "#pdBiaya") == "Rp15.250.000", text(page, "#pdBiaya"))
        check("Periode Nov laba", text(page, "#pdLaba") == "Rp37.160.000", text(page, "#pdLaba"))
        check("Periode Nov catatan", text(page, "#pdCatatan") == "23 catatan", text(page, "#pdCatatan"))
        check("Periode Nov per produk Padi", "Rp11.550.000" in text(page, "#tabelPeriode"))
        # Periode Oktober
        page.fill("#pdMulai", "2026-10-01")
        page.fill("#pdAkhir", "2026-10-31")
        page.click("#btnTerapkanPeriode")
        page.wait_for_timeout(200)
        check("Periode Okt nilai", text(page, "#pdNilai") == "Rp17.700.000", text(page, "#pdNilai"))
        check("Periode Okt biaya", text(page, "#pdBiaya") == "Rp1.500.000", text(page, "#pdBiaya"))
        check("Periode Okt laba", text(page, "#pdLaba") == "Rp16.200.000", text(page, "#pdLaba"))
        check("Periode Okt catatan", text(page, "#pdCatatan") == "6 catatan", text(page, "#pdCatatan"))
        # Tombol cepat 7 hari terakhir
        page.click('[data-periode-cepat="tujuh"]')
        page.wait_for_timeout(200)
        check("Periode 7 hari nilai", text(page, "#pdNilai") == "Rp17.770.000", text(page, "#pdNilai"))
        check("Periode 7 hari biaya", text(page, "#pdBiaya") == "Rp5.650.000", text(page, "#pdBiaya"))
        check("Periode 7 hari laba", text(page, "#pdLaba") == "Rp12.120.000", text(page, "#pdLaba"))
        check("Periode 7 hari catatan", text(page, "#pdCatatan") == "8 catatan", text(page, "#pdCatatan"))
        # Tombol cepat Semua Data
        page.click('[data-periode-cepat="semua"]')
        page.wait_for_timeout(200)
        check("Periode semua nilai", text(page, "#pdNilai") == "Rp70.110.000", text(page, "#pdNilai"))
        check("Periode semua biaya", text(page, "#pdBiaya") == "Rp16.750.000", text(page, "#pdBiaya"))
        check("Periode semua laba", text(page, "#pdLaba") == "Rp53.360.000", text(page, "#pdLaba"))
        check("Periode semua catatan", text(page, "#pdCatatan") == "29 catatan", text(page, "#pdCatatan"))
        # Validasi tanggal mulai > akhir ditolak
        page.fill("#pdMulai", "2026-11-10")
        page.fill("#pdAkhir", "2026-11-01")
        page.click("#btnTerapkanPeriode")
        page.wait_for_timeout(200)
        check("Periode terbalik ditolak (nilai tetap semua)", text(page, "#pdNilai") == "Rp70.110.000", text(page, "#pdNilai"))

        # ---- 7. Tab Perbandingan ----
        tab(page, "perbandingan")
        check("Panel perbandingan aktif", page.is_visible("#panel-perbandingan"))
        check("Perbandingan A mulai = 1 Nov 2026", page.input_value("#pbAMulai") == "2026-11-01", page.input_value("#pbAMulai"))
        check("Perbandingan B mulai = 1 Okt 2026", page.input_value("#pbBMulai") == "2026-10-01", page.input_value("#pbBMulai"))
        check("Perbandingan B akhir = 31 Okt 2026", page.input_value("#pbBAkhir") == "2026-10-31", page.input_value("#pbBAkhir"))
        pb_text = text(page, "#tabelPerbandingan")
        check("Perbandingan nilai A 52.410.000", "Rp52.410.000" in pb_text)
        check("Perbandingan nilai B 17.700.000", "Rp17.700.000" in pb_text)
        check("Perbandingan nilai +196,1%", "+196,1%" in pb_text, pb_text[:400])
        check("Perbandingan biaya +916,7%", "+916,7%" in pb_text)
        check("Perbandingan laba +129,4%", "+129,4%" in pb_text)
        check("Perbandingan kesimpulan laba", "lebih besar" in text(page, "#kesimpulanPerbandingan"))
        check("Perbandingan ringkasan periode A", "01/11/2026" in text(page, "#ringkasanPerbandingan"))
        check("Perbandingan ringkasan periode B", "01/10/2026" in text(page, "#ringkasanPerbandingan"))

        # ---- 8. Tab Laporan ----
        tab(page, "laporan")
        check("Panel laporan aktif", page.is_visible("#panel-laporan"))
        lap_text = text(page, "#panel-laporan")
        check("Laporan: per produk Padi", "Padi" in lap_text)
        check("Laporan: Padi 2.100 kg", "2.100" in lap_text)
        check("Laporan: Padi nilai 11.550.000", "Rp11.550.000" in lap_text)
        check("Laporan: Padi laba 6.750.000", "Rp6.750.000" in lap_text)
        check("Laporan: Susu Sapi 12.450.000", "Rp12.450.000" in lap_text)
        check("Laporan: per bulan November 2026", "November 2026" in lap_text)
        check("Laporan: Nov 11 catatan", "11" in lap_text)
        check("Laporan: kategori Bahan 11.450.000", "Rp11.450.000" in lap_text)
        check("Laporan: ringkasan total nilai", "Rp70.110.000" in text(page, "#ringkasanLaporan"))
        bulan_val = page.input_value("#fBulanLaporan")
        bulan_berjalan = date.today().isoformat()[:7]
        check("Bulan laporan default = bulan berjalan", bulan_val == bulan_berjalan, f"dapat {bulan_val}")
        # CSV bulan berjalan: 11 baris produksi + header = 12 baris
        with page.expect_download() as dl:
            page.click("#btnCsvLaporan")
        csv_path = dl.value.path()
        csv_isi = Path(csv_path).read_text(encoding="utf-8")
        csv_baris = [b for b in csv_isi.strip().split("\n") if b.strip()]
        check("CSV bulan berjalan 12 baris", len(csv_baris) == 12, f"dapat {len(csv_baris)}")
        check("CSV memuat Padi", "Padi" in csv_isi)
        check("CSV memuat Telur Ayam", "Telur Ayam" in csv_isi)
        # CSV Oktober: 4 baris + header = 5 baris
        page.select_option("#fBulanLaporan", "2026-10")
        page.wait_for_timeout(200)
        with page.expect_download() as dl2:
            page.click("#btnCsvLaporan")
        csv2 = Path(dl2.value.path()).read_text(encoding="utf-8")
        csv2_baris = [b for b in csv2.strip().split("\n") if b.strip()]
        check("CSV Oktober 5 baris", len(csv2_baris) == 5, f"dapat {len(csv2_baris)}")
        check("CSV Oktober memuat Kopi Robusta", "Kopi Robusta" in csv2)

        # ---- 9. Panduan ----
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

        # ---- 10. Ganti kata sandi sendiri (admin) ----
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

        # ---- 11. Tambah pengguna baru lalu reset kata sandinya ----
        page.fill("#pgUser", "ujiuser")
        page.fill("#pgNama", "Uji Coba")
        page.select_option("#pgPeran", "manajer")
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
        check("Chip manajer uji", "Manajer" in text(page, "#userChip"))
        logout(page)
        login(page, "admin", "admin123")
        page.click('[data-hapus-user="ujiuser"]')
        page.wait_for_timeout(200)
        konfirmasi_modal(page)
        check("Pengguna uji terhapus", "Uji Coba" not in text(page, "#daftarPengguna"))

        # ---- 12. Peran Petani (data terlihat saja) ----
        logout(page)
        login(page, "petani", "petani123")
        check("Login petani berhasil", not page.is_visible("#loginOverlay"))
        check("Chip petani", "Budi Santoso (Petani)" in text(page, "#userChip"))
        check("Dasbor petani nilai bulan ini", text(page, "#dNilaiBulan") == "Rp19.810.000", text(page, "#dNilaiBulan"))
        check("Dasbor petani biaya bulan ini", text(page, "#dBiayaBulan") == "Rp4.650.000", text(page, "#dBiayaBulan"))
        check("Dasbor petani laba bulan ini", text(page, "#dLabaBulan") == "Rp15.160.000", text(page, "#dLabaBulan"))
        check("Dasbor petani 7 hari", text(page, "#dTujuhHari") == "2 catatan", text(page, "#dTujuhHari"))
        check("Dasbor petani 7 hari nilai", "Rp7.120.000" in text(page, "#dTujuhHariSub"), text(page, "#dTujuhHariSub"))
        check("Dasbor petani produk top Telur Ayam", text(page, "#dProdukTop") == "Telur Ayam", text(page, "#dProdukTop"))
        check("Kartu kelola pengguna tersembunyi untuk petani", not page.is_visible("#cardPengguna"))
        check("Kartu ganti sandi tetap terlihat untuk petani", page.is_visible("#cardSandiSaya"))
        tab(page, "produksi")
        prod_petani = text(page, "#daftarProduksi")
        check("Petani melihat Tomat", "Tomat" in prod_petani)
        check("Petani melihat Telur Ayam", "Telur Ayam" in prod_petani)
        check("Petani tidak melihat Padi", "Padi" not in prod_petani)
        check("Petani tidak melihat Susu Sapi", "Susu Sapi" not in prod_petani)
        check("Petani: ringkasan 5 catatan", "5 catatan produksi" in text(page, "#ringkasanProduksi"))
        check("Petani tidak melihat kartu harga produk", not page.is_visible("#cardHargaProduk"))
        tab(page, "biaya")
        check("Petani: ringkasan biaya 4 catatan", "4 catatan biaya" in text(page, "#ringkasanBiaya"))
        check("Petani: total biaya 4.650.000", "Rp4.650.000" in text(page, "#ringkasanBiaya"))
        tab(page, "periode")
        check("Petani periode Nov nilai", text(page, "#pdNilai") == "Rp19.810.000", text(page, "#pdNilai"))
        check("Petani periode Nov laba", text(page, "#pdLaba") == "Rp15.160.000", text(page, "#pdLaba"))
        tab(page, "perbandingan")
        pb_petani = text(page, "#tabelPerbandingan")
        check("Petani perbandingan nilai A 19.810.000", "Rp19.810.000" in pb_petani)
        check("Petani perbandingan nilai B 0", "Rp0" in pb_petani)

        # ---- 13. Peran Manajer ----
        logout(page)
        login(page, "manajer", "manajer123")
        check("Login manajer berhasil", not page.is_visible("#loginOverlay"))
        check("Chip manajer", "Dedi Kurniawan (Manajer)" in text(page, "#userChip"))
        check("Kartu kelola pengguna tersembunyi untuk manajer", not page.is_visible("#cardPengguna"))
        check("Kartu ganti sandi tetap terlihat untuk manajer", page.is_visible("#cardSandiSaya"))
        check("Dasbor manajer nilai bulan ini", text(page, "#dNilaiBulan") == "Rp52.410.000", text(page, "#dNilaiBulan"))
        tab(page, "produksi")
        check("Manajer melihat kartu harga produk", page.is_visible("#cardHargaProduk"))

        # ---- 14. Backup JSON + reset data demo ----
        logout(page)
        login(page, "admin", "admin123")
        tab(page, "laporan")
        with page.expect_download() as dl3:
            page.click("#btnBackup")
        backup_isi = Path(dl3.value.path()).read_text(encoding="utf-8")
        check("Backup JSON memuat nama aplikasi", "aplikasi-pencatatan-produksi" in backup_isi)
        check("Backup JSON memuat produksi", '"produksi"' in backup_isi)
        # Pulihkan JSON dengan penanda RESTORE-TEST (uji end-to-end restore + rebind currentUser)
        import json as _json
        _d = _json.loads(backup_isi)
        _d["state"]["produksi"].append({"id": 999, "produk": "Tomat", "jumlah": 77, "hargaPerSatuan": 9000, "tanggal": "2026-11-20", "pemilik": "admin", "keterangan": "RESTORE-TEST"})
        _tmp = Path("/tmp/restore-produksi-test.json")
        _tmp.write_text(_json.dumps(_d), encoding="utf-8")
        page.set_input_files("#inputRestore", str(_tmp))
        page.wait_for_timeout(400)
        tab(page, "produksi")
        check("Restore JSON menampilkan penanda", "RESTORE-TEST" in text(page, "#panel-produksi"))
        check("Setelah restore masih login admin", "Administrator (Admin)" in text(page, "#userChip"))
        tab(page, "laporan")
        page.click("#btnResetData")
        page.wait_for_timeout(200)
        check("Modal konfirmasi reset muncul", konfirmasi_modal(page))
        tab(page, "dashboard")
        check("Setelah reset nilai bulan kembali", text(page, "#dNilaiBulan") == "Rp52.410.000", text(page, "#dNilaiBulan"))
        check("Setelah reset laba bulan kembali", text(page, "#dLabaBulan") == "Rp37.160.000", text(page, "#dLabaBulan"))
        check("Setelah reset total nilai kembali", text(page, "#dNilaiTotal") == "Rp70.110.000", text(page, "#dNilaiTotal"))

        # ---- 15. Console errors ----
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
