"""Tes Hotel Management System (#55) — Playwright Chromium, file lokal.
Hari ini 2026-11-20. Data seed (tanggal relatif, diuji silang Python /tmp/cek_hotel.py):
  Kamar 8: 101 Std 350rb Tersedia, 102 Std 350rb Tersedia, 103 Std 350rb Terisi,
    201 Dlx 550rb Tersedia, 202 Dlx 550rb Terisi, 203 Dlx 550rb Dibersihkan,
    301 Suite 950rb Tersedia, 302 Family 750rb Perawatan.
    Status: Tersedia 4, Terisi 2, Dibersihkan 1, Perawatan 1.
  Tamu 6: Andi, Sari, Budi, Dewi, Rudi, Maya.
  Pemesanan 8: B1 Andi/103 18-20 Nov 2 mlm 700rb Menginap;
    B2 Sari/202 19-22 Nov 3 mlm 1.650rb Menginap; B3 Budi/101 21-23 Nov 2 mlm 700rb Dipesan;
    B4 Dewi/201 22-25 Nov 3 mlm 1.650rb Dipesan; B5 Rudi/301 10-13 Nov 3 mlm 2.850rb Selesai;
    B6 Maya/102 14-16 Nov 2 mlm 700rb Selesai; B7 Andi/203 5-8 Nov 3 mlm 1.650rb Selesai;
    B8 Sari/101 25-27 Nov 2 mlm 700rb Dipesan.
    Menginap 2.350.000; Dipesan 3.050.000; Selesai 5.200.000; kamar Nov 10.600.000.
  Layanan 7, total Rp705.000 (Sarapan 350rb, Laundry 150rb, Antar-Jemput 120rb,
    Layanan Kamar 85rb): B1 175rb, B2 270rb, B5 100rb, B6 75rb, B7 85rb.
    Tagihan check-out B1 = 700rb + 175rb = 875rb; B2 = 1.650rb + 270rb = 1.920rb.
  Hunian Nov: 20 malam / (8 kamar x 30 hari = 240) = 8,3%.
  Pemasukan Nov = kamar 10.600.000 + layanan 705.000 = Rp11.305.000.
  Check-out hari ini 1 (B1); check-in hari ini 0; check-in besok 1 (B3).
  CSV pemesanan Nov: 8 baris + header = 9.
  CATATAN: tes menambah B9 (Maya/301, 23-25 Nov, 2 mlm, Rp1.900.000) dan
    B10 (Rudi/201, hari ini-+1, 1 mlm, Rp550.000), lalu check-out B1 dan B10,
    sehingga di seksi G: pemesanan Nov 10, malam terisi 23, hunian 9,6%,
    pemasukan kamar Nov Rp13.050.000, total Rp13.755.000;
    per tipe: Standard 8 mlm Rp2.800.000, Deluxe 10 mlm Rp5.500.000,
    Suite 5 mlm Rp4.750.000, Family 0 mlm Rp0.
"""
import json
from datetime import date, timedelta
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent  # folder hotel-management-system
URL = "file://" + str(ROOT / "index.html")

failures = []
passed = 0
console_errors = []
page_errors = []

T = date.today()


def dstr(n):
    return (T + timedelta(days=n)).isoformat()


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


def val(page, sel):
    el = page.query_selector(sel)
    return el.input_value() if el else ""


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
    page.wait_for_timeout(250)


def konfirmasi_modal(page):
    if page.is_visible("#modalBack.open"):
        page.click("#modalYa")
        page.wait_for_timeout(300)
        return True
    return False


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.goto(URL)
        page.wait_for_timeout(500)

        print("A. Login & dasbor admin (seed)")
        check("A1 overlay login terlihat", page.is_visible("#loginOverlay"))
        login(page, "admin", "salah")
        check("A2 login salah ditolak", page.is_visible("#loginError"))
        login(page, "admin", "admin123")
        check("A3 login admin berhasil, overlay hilang", not page.is_visible("#loginOverlay"))
        check("A4 masuk mendarat di dasbor", "active" in (page.get_attribute("#panel-dashboard", "class") or ""))
        check("A5 chip pengguna admin", "Administrator (Admin)" in text(page, "#userChip"))
        check("A6 kamar tersedia 4", "4 kamar" in text(page, "#dTersedia"))
        check("A7 sub tersedia: dari 8, dibersihkan 1, perawatan 1",
              "dari 8 kamar" in text(page, "#dTersediaSub") and "dibersihkan 1" in text(page, "#dTersediaSub") and "perawatan 1" in text(page, "#dTersediaSub"))
        check("A8 kamar terisi 2", "2 kamar" in text(page, "#dTerisi"))
        check("A9 sub terisi 2 tamu menginap", "2 tamu sedang menginap" in text(page, "#dTerisiSub"))
        check("A10 check-out hari ini 1 tamu", "1 tamu" in text(page, "#dCoHariIni"))
        check("A11 sub co: check-in besok 1", "check-in besok 1 tamu" in text(page, "#dCoHariIniSub"))
        check("A12 check-in hari ini 0 tamu", "0 tamu" in text(page, "#dCiHariIni"))
        check("A13 sub ci: dipesan 3, selesai 3",
              "dipesan 3" in text(page, "#dCiHariIniSub") and "selesai 3" in text(page, "#dCiHariIniSub"))
        check("A14 menginap 2 tamu", "2 tamu" in text(page, "#dMenginap"))
        check("A15 sub menginap nilai tagihan Rp2.795.000", "Rp2.795.000" in text(page, "#dMenginapSub"))
        check("A16 dipesan 3 pemesanan", "3 pemesanan" in text(page, "#dDipesan"))
        check("A17 sub dipesan nilai kamar Rp3.050.000", "Rp3.050.000" in text(page, "#dDipesanSub"))
        check("A18 pemasukan bulan Rp11.305.000", "Rp11.305.000" in text(page, "#dPemasukanBulan"))
        check("A19 sub pemasukan kamar 10.600.000 + layanan 705.000",
              "Rp10.600.000" in text(page, "#dPemasukanBulanSub") and "Rp705.000" in text(page, "#dPemasukanBulanSub"))
        check("A20 hunian 8,3%", "8,3%" in text(page, "#dHunian"))
        check("A21 sub hunian 20 dari 240 malam", "20 malam terisi dari 240 malam kapasitas" in text(page, "#dHunianSub"))
        check("A22 badge kamar 8", text(page, "#badgeKamar") == "8")
        check("A23 badge pemesanan 5 (dipesan+menginap)", text(page, "#badgePemesanan") == "5")
        check("A24 badge tamu 6", text(page, "#badgeTamu") == "6")
        check("A25 cardSandiSaya terlihat untuk admin", page.is_visible("#cardSandiSaya"))
        check("A26 cardPengguna terlihat untuk admin", page.is_visible("#cardPengguna"))
        check("A27 status kamar 103 Terisi + Andi", "103" in text(page, "#daftarStatusKamar") and "Andi Pratama" in text(page, "#daftarStatusKamar"))
        check("A28 pemesanan terbaru memuat Sari/202", "Sari Wijaya" in text(page, "#daftarPemesananRingkas"))

        print("A*. Sesi bertahan setelah reload")
        page.reload()
        page.wait_for_timeout(500)
        check("A29 setelah reload tetap masuk sebagai admin", "Administrator (Admin)" in text(page, "#userChip") and not page.is_visible("#loginOverlay"))

        print("B. Kamar")
        tab(page, "kamar")
        check("B1 ringkasan 8 kamar, tersedia 4, terisi 2", "8 kamar" in text(page, "#ringkasanKamar") and "tersedia 4" in text(page, "#ringkasanKamar"))
        page.fill("#kmNomor", "104")
        page.select_option("#kmTipe", "Standard")
        page.fill("#kmTarif", "400000")
        page.click("#btnTambahKamar")
        page.wait_for_timeout(300)
        check("B2 tambah kamar 104 -> 9 kamar", "9 kamar" in text(page, "#ringkasanKamar"))
        check("B3 kamar 104 tarif Rp400.000 terlihat", "Rp400.000/malam" in text(page, "#daftarKamar"))
        page.fill('[data-tarif-kamar="9"]', "450000")
        page.click('[data-simpan-tarif="9"]')
        page.wait_for_timeout(300)
        check("B4 ubah tarif kamar 104 jadi Rp450.000", "Rp450.000/malam" in text(page, "#daftarKamar"))
        page.click('[data-rawat-kamar="9"]')
        page.wait_for_timeout(300)
        check("B5 kamar 104 masuk Perawatan", "Perawatan" in text(page, "#daftarKamar"))
        page.click('[data-selesai-rawat="9"]')
        page.wait_for_timeout(300)
        check("B6 kamar 104 selesai perawatan -> Tersedia", page.query_selector('[data-selesai-rawat="9"]') is None)
        page.click('[data-hapus-kamar="1"]')
        page.wait_for_timeout(200)
        check("B7 hapus kamar 101 ditolak (ada pemesanan)", page.is_visible("#toast.show") and "tidak bisa dihapus" in text(page, "#toast"))
        check("B8 kamar tetap 9 setelah hapus ditolak", "9 kamar" in text(page, "#ringkasanKamar"))
        page.click('[data-hapus-kamar="9"]')
        page.wait_for_timeout(200)
        konfirmasi_modal(page)
        check("B9 hapus kamar 104 (tanpa pemesanan) -> 8 kamar", "8 kamar" in text(page, "#ringkasanKamar"))

        print("C. Pemesanan: pratinjau & validasi")
        tab(page, "pemesanan")
        page.select_option("#psTamu", "3")  # Budi Santoso
        page.select_option("#psKamar", "4")  # 201 Deluxe 550rb
        page.fill("#psCheckin", dstr(0))
        page.fill("#psCheckout", dstr(2))
        page.wait_for_timeout(200)
        check("C1 pratinjau 2 malam", "2 malam" in val(page, "#psMalam"))
        check("C2 pratinjau total Rp1.100.000", "Rp1.100.000" in val(page, "#psTotal"))
        # bentrok: kamar 101 (B3: 21-23 Nov)
        page.select_option("#psKamar", "1")
        page.fill("#psCheckin", dstr(1))
        page.fill("#psCheckout", dstr(3))
        page.click("#btnTambahPemesanan")
        page.wait_for_timeout(300)
        check("C3 pemesanan bentrok kamar 101 ditolak", page.is_visible("#toast.show") and "sudah dipesan" in text(page, "#toast"))
        check("C4 pemesanan tetap 8 setelah bentrok ditolak", "8 pemesanan" in text(page, "#ringkasanPemesanan"))
        # perawatan: kamar 302
        page.select_option("#psKamar", "8")
        page.fill("#psCheckin", dstr(10))
        page.fill("#psCheckout", dstr(12))
        page.click("#btnTambahPemesanan")
        page.wait_for_timeout(300)
        check("C5 pemesanan kamar Perawatan (302) ditolak", "Perawatan" in text(page, "#toast"))
        # checkout <= checkin -> ditolak & input kembali ke nilai valid (besok)
        page.select_option("#psKamar", "7")  # 301
        page.fill("#psCheckin", dstr(3))
        page.fill("#psCheckout", dstr(3))
        page.click("#btnTambahPemesanan")
        page.wait_for_timeout(300)
        check("C6 check-out = check-in ditolak", "harus setelah tanggal check-in" in text(page, "#toast"))
        check("C7 input check-out dikembalikan ke besok (nilai valid)", val(page, "#psCheckout") == dstr(1))
        # pemesanan valid B9: Maya/301, +3..+5, 2 mlm x 950rb = 1.900.000
        page.select_option("#psTamu", "6")  # Maya Putri
        page.select_option("#psKamar", "7")  # 301 Suite
        page.fill("#psCheckin", dstr(3))
        page.fill("#psCheckout", dstr(5))
        page.wait_for_timeout(200)
        check("C8 pratinjau B9 total Rp1.900.000", "Rp1.900.000" in val(page, "#psTotal"))
        page.click("#btnTambahPemesanan")
        page.wait_for_timeout(300)
        check("C9 tambah B9 -> 9 pemesanan", "9 pemesanan" in text(page, "#ringkasanPemesanan"))
        check("C10 B9 Maya/301 muncul di daftar", "Maya Putri" in text(page, "#daftarPemesanan") and "Rp1.900.000" in text(page, "#daftarPemesanan"))

        print("D. Check-in / Check-out")
        tab(page, "checkin")
        check("D1 siap check-in kosong (B3 baru besok)", "Tidak ada pemesanan yang siap check-in" in text(page, "#daftarSiapCheckin"))
        check("D2 siap check-out memuat B1 tagihan Rp875.000",
              "Andi Pratama" in text(page, "#daftarSiapCheckout") and "Rp875.000" in text(page, "#daftarSiapCheckout"))
        check("D3 siap check-out memuat B2 tagihan Rp1.920.000",
              "Sari Wijaya" in text(page, "#daftarSiapCheckout") and "Rp1.920.000" in text(page, "#daftarSiapCheckout"))
        page.click('#panel-checkin [data-checkout="1"]')
        page.wait_for_timeout(300)
        check("D4 modal check-out B1 menampilkan Rp875.000", "Rp875.000" in text(page, "#modalIsi"))
        konfirmasi_modal(page)
        check("D5 B1 selesai -> tinggal 1 menginap (B2)", "Sari Wijaya" in text(page, "#daftarSiapCheckout") and "Andi Pratama" not in text(page, "#daftarSiapCheckout"))
        check("D6 kamar 103 masuk daftar Dibersihkan", "Kamar 103" in text(page, "#daftarDibersihkan"))
        page.click('#panel-checkin [data-bersih-kamar="3"]')
        page.wait_for_timeout(300)
        check("D7 kamar 103 selesai dibersihkan", "Kamar 103" not in text(page, "#daftarDibersihkan"))
        # B10: Rudi/201 hari ini-+1, 1 mlm x 550rb
        tab(page, "pemesanan")
        page.select_option("#psTamu", "5")  # Rudi Hartono
        page.select_option("#psKamar", "4")  # 201 Deluxe
        page.fill("#psCheckin", dstr(0))
        page.fill("#psCheckout", dstr(1))
        page.wait_for_timeout(200)
        check("D8 pratinjau B10 total Rp550.000", "Rp550.000" in val(page, "#psTotal"))
        page.click("#btnTambahPemesanan")
        page.wait_for_timeout(300)
        check("D9 tambah B10 -> 10 pemesanan", "10 pemesanan" in text(page, "#ringkasanPemesanan"))
        tab(page, "checkin")
        check("D10 siap check-in memuat B10 Rudi", "Rudi Hartono" in text(page, "#daftarSiapCheckin"))
        check("D11 siap check-in TIDAK memuat B3 (besok)", "Budi Santoso" not in text(page, "#daftarSiapCheckin"))
        page.click('#panel-checkin [data-checkin="10"]')
        page.wait_for_timeout(300)
        check("D12 B10 check-in -> menginap (B2 + B10)", "Rudi Hartono" in text(page, "#daftarSiapCheckout"))
        page.click('#panel-checkin [data-checkout="10"]')
        page.wait_for_timeout(300)
        check("D13 modal check-out B10 menampilkan Rp550.000", "Rp550.000" in text(page, "#modalIsi"))
        konfirmasi_modal(page)
        check("D14 B10 selesai, kamar 201 Dibersihkan", "Kamar 201" in text(page, "#daftarDibersihkan"))
        page.click('#panel-checkin [data-bersih-kamar="4"]')
        page.wait_for_timeout(300)
        check("D15 kamar 201 kembali Tersedia", "Kamar 201" not in text(page, "#daftarDibersihkan"))
        tab(page, "dashboard")
        check("D16 dasbor: menginap 1 tamu (B2)", "1 tamu" in text(page, "#dMenginap"))
        check("D17 dasbor: sub menginap Rp1.920.000", "Rp1.920.000" in text(page, "#dMenginapSub"))
        check("D18 dasbor: dipesan 4 pemesanan", "4 pemesanan" in text(page, "#dDipesan"))
        check("D19 dasbor: sub dipesan Rp4.950.000", "Rp4.950.000" in text(page, "#dDipesanSub"))

        print("E. Tamu")
        tab(page, "tamu")
        check("E1 ringkasan 6 tamu", "6 tamu" in text(page, "#ringkasanTamu"))
        page.fill("#tmNama", "Joko Santoso")
        page.fill("#tmTelepon", "0812-7777-0007")
        page.fill("#tmEmail", "joko@mail.com")
        page.click("#btnTambahTamu")
        page.wait_for_timeout(300)
        check("E2 tambah Joko -> 7 tamu", "7 tamu" in text(page, "#ringkasanTamu"))
        check("E3 Joko muncul dengan 0 pemesanan", "Joko Santoso" in text(page, "#daftarTamu") and "0 pemesanan" in text(page, "#daftarTamu"))
        page.click('[data-hapus-tamu="7"]')
        page.wait_for_timeout(200)
        konfirmasi_modal(page)
        check("E4 hapus Joko -> 6 tamu", "6 tamu" in text(page, "#ringkasanTamu"))
        check("E5 tamu Andi (ada pemesanan) tidak punya tombol hapus", page.query_selector('[data-hapus-tamu="1"]') is None)

        print("F. Layanan")
        tab(page, "layanan")
        opts = page.query_selector_all("#lyPemesanan option")
        check("F1 hanya 1 pemesanan Menginap (B2) di pilihan layanan", len(opts) == 1)
        page.select_option("#lyJenis", "Sarapan")
        page.fill("#lyJumlah", "2")
        page.wait_for_timeout(200)
        check("F2 pratinjau subtotal Sarapan 2x = Rp100.000", "Rp100.000" in val(page, "#lySubtotal"))
        page.click("#btnTambahLayanan")
        page.wait_for_timeout(300)
        check("F3 tambah layanan -> 8 layanan, total Rp805.000", "8 layanan" in text(page, "#ringkasanLayanan") and "Rp805.000" in text(page, "#ringkasanLayanan"))
        page.click('[data-hapus-layanan="8"]')
        page.wait_for_timeout(200)
        konfirmasi_modal(page)
        check("F4 hapus layanan uji -> 7 layanan, total Rp705.000", "7 layanan" in text(page, "#ringkasanLayanan") and "Rp705.000" in text(page, "#ringkasanLayanan"))

        print("G. Laporan & CSV")
        tab(page, "laporan")
        check("G1 bulan laporan default bulan berjalan", "2026-11" in val(page, "#fBulanLaporan"))
        check("G2 ringkasan pemasukan bulan berjalan Rp13.755.000", "Rp13.755.000" in text(page, "#ringkasanLaporan"))
        check("G3 ringkasan hunian 9,6% (23 dari 240)", "9,6%" in text(page, "#ringkasanLaporan"))
        t_tipe = text(page, "#tabelPerTipe")
        check("G4 per tipe Standard 8 mlm Rp2.800.000", "Standard" in t_tipe and "Rp2.800.000" in t_tipe)
        check("G5 per tipe Deluxe 10 mlm Rp5.500.000", "Deluxe" in t_tipe and "Rp5.500.000" in t_tipe)
        check("G6 per tipe Suite 5 mlm Rp4.750.000", "Suite" in t_tipe and "Rp4.750.000" in t_tipe)
        check("G7 per tipe Family 0 mlm Rp0", "Family" in t_tipe and "Rp0" in t_tipe)
        t_bulan = text(page, "#tabelPerBulan")
        check("G8 per bulan Nov: 10 pemesanan, 23 malam, 9,6%",
              "November 2026" in t_bulan and "9,6%" in t_bulan)
        check("G9 per bulan Nov: kamar Rp13.050.000, layanan Rp705.000, total Rp13.755.000",
              "Rp13.050.000" in t_bulan and "Rp705.000" in t_bulan and "Rp13.755.000" in t_bulan)
        t_lay = text(page, "#tabelPerLayanan")
        check("G10 per layanan Sarapan Rp350.000", "Sarapan" in t_lay and "Rp350.000" in t_lay)
        check("G11 per layanan Laundry Rp150.000", "Laundry" in t_lay and "Rp150.000" in t_lay)
        check("G12 per layanan Antar-Jemput Rp120.000", "Antar-Jemput" in t_lay and "Rp120.000" in t_lay)
        check("G13 per layanan Layanan Kamar Rp85.000", "Layanan Kamar" in t_lay and "Rp85.000" in t_lay)
        with page.expect_download() as dl:
            page.click("#btnCsvLaporan")
        lines = Path(dl.value.path()).read_text(encoding="utf-8").strip().split("\n")
        check("G14 CSV Nov 10 baris + header = 11", len(lines) == 11, f"dapat {len(lines)}")
        check("G15 CSV header memuat Tanggal Check-in", "Tanggal Check-in" in lines[0])
        check("G16 CSV memuat Sari Wijaya", any("Sari Wijaya" in ln for ln in lines))
        page.select_option("#fBulanLaporan", "semua")
        page.wait_for_timeout(200)
        with page.expect_download() as dl2:
            page.click("#btnCsvLaporan")
        lines2 = Path(dl2.value.path()).read_text(encoding="utf-8").strip().split("\n")
        check("G17 CSV semua bulan juga 11 baris", len(lines2) == 11, f"dapat {len(lines2)}")

        print("H. Backup / restore / reset")
        with page.expect_download() as dl3:
            page.click("#btnBackup")
        backup_path = Path(dl3.value.path())
        data = json.loads(backup_path.read_text(encoding="utf-8"))
        check("H1 backup JSON memuat 10 pemesanan", len(data["state"]["pemesanan"]) == 10)
        data["state"]["tamu"].append({"id": 99, "nama": "RESTORE-TEST", "telepon": "000", "email": ""})
        restore_path = Path("/tmp/hotel-restore-test.json")
        restore_path.write_text(json.dumps(data), encoding="utf-8")
        page.set_input_files("#inputRestore", str(restore_path))
        page.wait_for_timeout(400)
        check("H2 restore berhasil (toast)", page.is_visible("#toast.show") and "berhasil dipulihkan" in text(page, "#toast"))
        tab(page, "tamu")
        check("H3 tamu RESTORE-TEST muncul setelah restore", "RESTORE-TEST" in text(page, "#daftarTamu"))
        invalid = Path("/tmp/hotel-invalid.json")
        invalid.write_text("bukan json", encoding="utf-8")
        page.set_input_files("#inputRestore", str(invalid))
        page.wait_for_timeout(400)
        check("H4 file cadangan tidak valid ditolak", "tidak valid" in text(page, "#toast"))
        tab(page, "laporan")
        page.click("#btnResetData")
        page.wait_for_timeout(200)
        konfirmasi_modal(page)
        tab(page, "dashboard")
        check("H5 reset -> dasbor seed kembali (tersedia 4, hunian 8,3%)",
              "4 kamar" in text(page, "#dTersedia") and "8,3%" in text(page, "#dHunian"))
        check("H6 reset -> pemasukan kembali Rp11.305.000", "Rp11.305.000" in text(page, "#dPemasukanBulan"))

        print("I. Peran manajer & resepsionis")
        logout(page)
        login(page, "manajer", "manajer123")
        check("I1 manajer masuk", "Dedi Kurniawan (Manajer)" in text(page, "#userChip"))
        check("I2 cardPengguna tersembunyi untuk manajer", not page.is_visible("#cardPengguna"))
        check("I3 cardSandiSaya terlihat untuk manajer", page.is_visible("#cardSandiSaya"))
        check("I4 manajer melihat dasbor seed penuh (tersedia 4)", "4 kamar" in text(page, "#dTersedia"))
        tab(page, "kamar")
        check("I5 cardTambahKamar terlihat untuk manajer", page.is_visible("#cardTambahKamar"))
        check("I6 input tarif terlihat untuk manajer", page.query_selector('[data-tarif-kamar="1"]') is not None)
        logout(page)
        login(page, "resepsionis", "resepsionis123")
        check("I7 resepsionis masuk", "Rina Kusuma (Resepsionis)" in text(page, "#userChip"))
        check("I8 cardPengguna tersembunyi untuk resepsionis", not page.is_visible("#cardPengguna"))
        check("I9 cardSandiSaya terlihat untuk resepsionis", page.is_visible("#cardSandiSaya"))
        check("I10 resepsionis melihat dasbor seed penuh (hunian 8,3%)", "8,3%" in text(page, "#dHunian"))
        tab(page, "kamar")
        check("I11 cardTambahKamar tersembunyi untuk resepsionis", not page.is_visible("#cardTambahKamar"))
        check("I12 tidak ada input tarif untuk resepsionis", page.query_selector('[data-tarif-kamar="1"]') is None)
        tab(page, "checkin")
        check("I13 resepsionis bisa check-out B1 (tombol ada)", page.query_selector('#panel-checkin [data-checkout="1"]') is not None)
        page.click('#panel-checkin [data-checkout="1"]')
        page.wait_for_timeout(300)
        check("I14 modal check-out B1 Rp875.000 untuk resepsionis", "Rp875.000" in text(page, "#modalIsi"))
        konfirmasi_modal(page)
        check("I15 resepsionis berhasil check-out B1", "Andi Pratama" not in text(page, "#daftarSiapCheckout"))
        logout(page)
        login(page, "admin", "admin123")
        tab(page, "laporan")
        page.click("#btnResetData")
        page.wait_for_timeout(200)
        konfirmasi_modal(page)

        print("J. Ganti kata sandi & reset admin")
        logout(page)
        login(page, "resepsionis", "resepsionis123")
        page.fill("#sandiLama", "resepsionis123")
        page.fill("#sandiBaru", "baru123456")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        check("J1 ganti sandi resepsionis berhasil", "Kata sandi berhasil diubah" in text(page, "#pesanSandi"))
        logout(page)
        login(page, "resepsionis", "baru123456")
        check("J2 login resepsionis dengan sandi baru berhasil", "Rina Kusuma (Resepsionis)" in text(page, "#userChip"))
        logout(page)
        login(page, "admin", "admin123")
        page.click('[data-reset="resepsionis"]')
        page.wait_for_timeout(200)
        konfirmasi_modal(page)
        logout(page)
        login(page, "resepsionis", "bk123")
        check("J3 login resepsionis dengan bk123 setelah reset admin", "Rina Kusuma (Resepsionis)" in text(page, "#userChip"))
        logout(page)
        login(page, "admin", "admin123")
        tab(page, "laporan")
        page.click("#btnResetData")
        page.wait_for_timeout(200)
        konfirmasi_modal(page)
        logout(page)
        login(page, "resepsionis", "resepsionis123")
        check("J4 setelah reset data demo, sandi resepsionis kembali resepsionis123", "Rina Kusuma (Resepsionis)" in text(page, "#userChip"))

        print(f"\nLOLOS: {passed} | GAGAL: {len(failures)}")
        if failures:
            print("Yang gagal:", failures)
        check("K1 tidak ada console error", len(console_errors) == 0, str(console_errors[:3]))
        check("K2 tidak ada page error", len(page_errors) == 0, str(page_errors[:3]))
        browser.close()
        if failures or console_errors or page_errors:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
