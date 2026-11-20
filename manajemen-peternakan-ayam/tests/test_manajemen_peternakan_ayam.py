"""Tes Manajemen Peternakan Ayam (#53) — Playwright Chromium, file lokal.
Hari ini 2026-11-20. Data seed (tanggal relatif, diuji silang Python /tmp/cek_ayam.py):
  Kandang 5: A Petelur 1000 (peternak), B Petelur 800 (manajer), C Pedaging 1500 (manajer),
    D Pedaging 1200 (peternak), E Petelur 500 (manajer).
  Populasi: A 865, B 732, C 1320, D 1060, E 468. Total 4.445; petelur 2.065; pedaging 2.380;
    peternak (A+D) 1.925.
  Telur 14 catatan, 8.448 butir (retak 40), nilai Rp18.585.600 @ Rp2.200/butir.
    Nov (12): 7.218 butir, Rp15.879.600. Okt (2): 1.230 butir, Rp2.706.000.
    Tingkat produksi Nov: A 79,6%, B 80,1%, E 79,1%; rata-rata tertimbang 79,7%.
    Peternak telur Nov (A): 4.133 butir, Rp9.092.600.
  Jadwal 12: hari ini belum 4, segera 4, lewat 2, selesai 2; belum 10.
  Biaya 11 catatan, total Rp14.250.000 (Pakan 12.000.000, Obat 1.100.000, Lain-lain 1.150.000).
    Nov Rp13.800.000; Okt Rp450.000. Peternak (A+D) Rp5.900.000.
  Nilai telur - biaya: total Rp4.335.600; Nov Rp2.079.600.
  Nilai daging pedaging: 2.380 x Rp40.000 = Rp95.200.000.
  CSV telur: Nov 12 baris + header = 13; Okt 2 baris + header = 3.
"""
import json
import sys
from datetime import date
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent  # folder manajemen-peternakan-ayam
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
        page = browser.new_page()
        page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.goto(URL)
        page.wait_for_timeout(500)

        print("A. Login & dasbor admin")
        check("A1 overlay login terlihat", page.is_visible("#loginOverlay"))
        login(page, "admin", "salah")
        check("A2 login salah ditolak", page.is_visible("#loginError"))
        login(page, "admin", "admin123")
        check("A3 login admin berhasil, overlay hilang", not page.is_visible("#loginOverlay"))
        check("A4 masuk mendarat di dasbor", "active" in (page.get_attribute("#panel-dashboard", "class") or ""))
        check("A5 chip pengguna admin", "Administrator (Admin)" in text(page, "#userChip"))
        check("A6 populasi total 4.445 ekor", "4.445 ekor" in text(page, "#dPopulasi"))
        check("A7 sub populasi petelur/pedaging", "petelur 2.065" in text(page, "#dPopulasiSub") and "pedaging 2.380" in text(page, "#dPopulasiSub"))
        check("A8 telur bulan ini 7.218 butir", "7.218 butir" in text(page, "#dTelurBulan"))
        check("A9 tingkat produksi 79,7%", "79,7%" in text(page, "#dTingkat"))
        check("A10 biaya bulan ini Rp13.800.000", "Rp13.800.000" in text(page, "#dBiayaBulan"))
        check("A11 jadwal hari ini 4 belum", "4 belum" in text(page, "#dJadwalHariIni"))
        check("A12 sub jadwal segera 4 lewat 2", "segera 4" in text(page, "#dJadwalHariIniSub") and "lewat 2" in text(page, "#dJadwalHariIniSub"))
        check("A13 nilai telur bulan Rp15.879.600", "Rp15.879.600" in text(page, "#dNilaiTelur"))
        check("A14 nilai daging Rp95.200.000", "Rp95.200.000" in text(page, "#dNilaiDaging"))
        check("A15 kandang 5", "5 kandang" in text(page, "#dKandang"))
        check("A16 sub kandang penuh 2", "2 kandang isi" in text(page, "#dKandangSub"))
        check("A17 badge kandang 5", text(page, "#badgeKandang") == "5")
        check("A18 badge pakan 10 belum", text(page, "#badgePakan") == "10")
        check("A19 badge telur 14", text(page, "#badgeTelur") == "14")
        check("A20 badge biaya 11", text(page, "#badgeBiaya") == "11")
        check("A21 cardSandiSaya terlihat untuk admin", page.is_visible("#cardSandiSaya"))
        check("A22 cardPengguna terlihat untuk admin", page.is_visible("#cardPengguna"))
        check("A23 isi kandang B 91,5% tampil", "91,5%" in text(page, "#daftarIsiKandang") or "732 / 800" in text(page, "#daftarIsiKandang"))
        check("A24 telur terbaru tampil", "690 butir" in text(page, "#daftarTelurRingkas"))

        print("B. Kandang")
        tab(page, "kandang")
        check("B1 ringkasan 5 kandang", "5 kandang" in text(page, "#ringkasanKandang"))
        check("B2 daftar memuat Kandang A", "Kandang A" in text(page, "#daftarKandang"))
        check("B3 daftar memuat Kandang C pedaging", "Kandang C" in text(page, "#daftarKandang"))
        page.fill("#kdNama", "Kandang F")
        page.select_option("#kdJenis", "Pedaging")
        page.fill("#kdKapasitas", "900")
        page.select_option("#kdPemilik", "manajer")
        page.click("#btnTambahKandang")
        page.wait_for_timeout(300)
        check("B4 tambah Kandang F -> 6 kandang", "6 kandang" in text(page, "#ringkasanKandang"))
        page.fill("#kdNama", "Kandang F")
        page.fill("#kdKapasitas", "500")
        page.click("#btnTambahKandang")
        page.wait_for_timeout(300)
        check("B5 nama kandang duplikat ditolak", "6 kandang" in text(page, "#ringkasanKandang"))
        page.click('[data-hapus-kandang="1"]')
        page.wait_for_timeout(300)
        check("B6 hapus Kandang A diblokir (masih ada data)", "6 kandang" in text(page, "#ringkasanKandang") and page.is_visible("#toast.show"))
        page.click('[data-hapus-kandang="6"]')
        page.wait_for_timeout(200)
        check("B7 modal konfirmasi hapus muncul", page.is_visible("#modalBack.open"))
        konfirmasi_modal(page)
        check("B8 Kandang F terhapus -> 5 kandang", "5 kandang" in text(page, "#ringkasanKandang"))

        print("C. Populasi")
        tab(page, "kandang")
        page.fill("#kdNama", "Kandang F")
        page.select_option("#kdJenis", "Pedaging")
        page.fill("#kdKapasitas", "900")
        page.select_option("#kdPemilik", "manajer")
        page.click("#btnTambahKandang")
        page.wait_for_timeout(300)
        tab(page, "populasi")
        check("C1 populasi kini Kandang F tampil 0", True)  # dicek lewat tambah di bawah
        page.select_option("#ppKandang", "7")
        page.select_option("#ppJenis", "Masuk")
        page.fill("#ppJumlah", "200")
        page.fill("#ppTanggal", "2026-11-20")
        page.click("#btnTambahPopulasi")
        page.wait_for_timeout(300)
        check("C2 masuk 200 ekor -> populasi kini 200", "200 ekor" in val(page, "#ppPopulasiKini"))
        page.select_option("#ppJenis", "Mati")
        page.fill("#ppJumlah", "250")
        page.click("#btnTambahPopulasi")
        page.wait_for_timeout(300)
        check("C3 mati 250 ditolak (melebihi populasi 200)", "200 ekor" in val(page, "#ppPopulasiKini"))
        page.fill("#ppJumlah", "50")
        page.click("#btnTambahPopulasi")
        page.wait_for_timeout(300)
        check("C4 mati 50 diterima -> populasi 150", "150 ekor" in val(page, "#ppPopulasiKini"))
        check("C5 ringkasan masuk 200", "masuk" in text(page, "#ringkasanPopulasi"))
        page.click('[data-hapus-populasi="13"]')
        page.wait_for_timeout(200)
        check("C6 hapus catatan Masuk diblokir (populasi jadi negatif)", page.is_visible("#toast.show"))
        page.click('[data-hapus-populasi="14"]')
        page.wait_for_timeout(200)
        konfirmasi_modal(page)
        check("C7 hapus catatan Mati -> populasi kembali 200", "200 ekor" in val(page, "#ppPopulasiKini"))
        page.click('[data-hapus-populasi="13"]')
        page.wait_for_timeout(200)
        konfirmasi_modal(page)
        check("C8 hapus catatan Masuk -> populasi 0", "0 ekor" in val(page, "#ppPopulasiKini"))
        tab(page, "kandang")
        page.click('[data-hapus-kandang="7"]')
        page.wait_for_timeout(200)
        konfirmasi_modal(page)
        check("C9 Kandang F terhapus setelah data dibersihkan", "5 kandang" in text(page, "#ringkasanKandang"))

        print("D. Pakan & vaksin")
        tab(page, "pakan")
        check("D1 ringkasan hari ini 4 segera 4 lewat 2 selesai 2",
              "hari ini 4" in text(page, "#ringkasanPakan") and "segera 4" in text(page, "#ringkasanPakan")
              and "lewat 2" in text(page, "#ringkasanPakan") and "selesai 2" in text(page, "#ringkasanPakan"))
        page.click('[data-selesai-jadwal="1"]')
        page.wait_for_timeout(300)
        check("D2 tandai selesai jadwal 1 -> hari ini 3", "hari ini 3" in text(page, "#ringkasanPakan"))
        page.click('[data-batal-jadwal="1"]')
        page.wait_for_timeout(300)
        check("D3 batalkan selesai -> hari ini 4 lagi", "hari ini 4" in text(page, "#ringkasanPakan"))
        page.select_option("#fPakan", "lewat")
        page.wait_for_timeout(200)
        check("D4 filter lewat menampilkan 2 jadwal", "2 jadwal" in text(page, "#ringkasanPakan"))
        page.select_option("#fPakan", "semua")
        page.wait_for_timeout(200)
        page.select_option("#pkKandang", "5")
        page.select_option("#pkJenis", "Vaksin")
        page.fill("#pkNama", "Vaksin Uji")
        page.fill("#pkTanggal", "2026-11-21")
        page.click("#btnTambahPakan")
        page.wait_for_timeout(300)
        check("D5 tambah jadwal vaksin -> segera 5", "segera 5" in text(page, "#ringkasanPakan"))
        page.click('[data-hapus-jadwal="13"]')
        page.wait_for_timeout(200)
        konfirmasi_modal(page)
        check("D6 hapus jadwal uji -> segera 4 lagi", "segera 4" in text(page, "#ringkasanPakan"))

        print("E. Telur")
        tab(page, "telur")
        check("E1 ringkasan total 8.448 butir", "8.448 butir" in text(page, "#ringkasanTelur"))
        check("E2 nilai telur total Rp18.585.600", "Rp18.585.600" in text(page, "#ringkasanTelur"))
        page.select_option("#tlKandang", "1")
        page.fill("#tlButir", "700")
        check("E3 pratinjau tingkat 80,9% (700/865)", "80,9%" in val(page, "#tlTingkat"))
        page.fill("#tlTanggal", "2026-11-20")
        page.fill("#tlRetak", "2")
        page.click("#btnTambahTelur")
        page.wait_for_timeout(300)
        check("E4 tambah telur 700 -> total 9.148 butir", "9.148 butir" in text(page, "#ringkasanTelur"))
        page.select_option("#tlKandang", "1")
        page.fill("#tlButir", "100")
        page.fill("#tlRetak", "101")
        page.click("#btnTambahTelur")
        page.wait_for_timeout(300)
        check("E5 retak melebihi butir ditolak", "9.148 butir" in text(page, "#ringkasanTelur"))
        page.click('[data-hapus-telur="15"]')
        page.wait_for_timeout(200)
        konfirmasi_modal(page)
        check("E6 hapus telur uji -> kembali 8.448 butir", "8.448 butir" in text(page, "#ringkasanTelur"))
        page.select_option("#fTelurBulan", "2026-10")
        page.wait_for_timeout(200)
        check("E7 filter bulan Okt menampilkan 2 catatan", "2 catatan" in text(page, "#ringkasanTelur") or "1.230" in text(page, "#ringkasanTelur"))
        page.select_option("#fTelurBulan", "semua")
        page.wait_for_timeout(200)

        print("F. Biaya")
        tab(page, "biaya")
        check("F1 ringkasan total Rp14.250.000", "Rp14.250.000" in text(page, "#ringkasanBiaya"))
        page.select_option("#byKandang", "1")
        page.select_option("#byKategori", "Pakan")
        page.fill("#byJumlah", "1000000")
        page.fill("#byTanggal", "2026-11-20")
        page.fill("#byKeterangan", "Biaya Uji")
        page.click("#btnTambahBiaya")
        page.wait_for_timeout(300)
        check("F2 tambah biaya 1jt -> total Rp15.250.000", "Rp15.250.000" in text(page, "#ringkasanBiaya"))
        page.click('[data-hapus-biaya="12"]')
        page.wait_for_timeout(200)
        konfirmasi_modal(page)
        check("F3 hapus biaya uji -> kembali Rp14.250.000", "Rp14.250.000" in text(page, "#ringkasanBiaya"))
        page.select_option("#fBiaya", "Obat")
        page.wait_for_timeout(200)
        check("F4 filter Obat menampilkan 3 catatan", "3 catatan" in text(page, "#ringkasanBiaya"))
        page.select_option("#fBiaya", "semua")
        page.wait_for_timeout(200)

        print("G. Harga acuan")
        tab(page, "telur")
        page.fill("#hgTelur", "2500")
        page.click("#btnSimpanHarga")
        page.wait_for_timeout(300)
        check("G1 harga telur 2500 -> nilai total Rp21.120.000", "Rp21.120.000" in text(page, "#ringkasanTelur"))
        page.fill("#hgTelur", "2200")
        page.click("#btnSimpanHarga")
        page.wait_for_timeout(300)
        check("G2 harga dikembalikan 2200 -> Rp18.585.600", "Rp18.585.600" in text(page, "#ringkasanTelur"))
        page.fill("#hgTelur", "0")
        page.click("#btnSimpanHarga")
        page.wait_for_timeout(300)
        check("G3 harga 0 ditolak, nilai tetap Rp18.585.600", "Rp18.585.600" in text(page, "#ringkasanTelur"))

        print("H. Laporan & CSV")
        tab(page, "laporan")
        check("H1 bulan laporan default November 2026", "2026-11" in val(page, "#fBulanLaporan"))
        check("H2 ringkasan selisih Rp4.335.600", "Rp4.335.600" in text(page, "#ringkasanLaporan"))
        check("H3 tabel per kandang: Kandang A 4.793 butir (semua bulan)", "4.793" in text(page, "#tabelPerKandang"))
        check("H4 tabel per bulan Nov: 12 catatan, 7.218 butir", "7.218" in text(page, "#tabelPerBulan"))
        check("H5 tabel per bulan Nov selisih Rp2.079.600", "Rp2.079.600" in text(page, "#tabelPerBulan"))
        check("H6 tabel per bulan Okt: 1.230 butir, selisih Rp2.256.000",
              "1.230" in text(page, "#tabelPerBulan") and "Rp2.256.000" in text(page, "#tabelPerBulan"))
        check("H7 tabel kategori Pakan Rp12.000.000", "Rp12.000.000" in text(page, "#tabelPerKategori"))
        with page.expect_download() as dl:
            page.click("#btnCsvLaporan")
        p_csv = Path(dl.value.path())
        lines = p_csv.read_text(encoding="utf-8").strip().split("\n")
        check("H8 CSV Nov 12 baris + header = 13", len(lines) == 13, f"dapat {len(lines)}")
        page.select_option("#fBulanLaporan", "2026-10")
        page.wait_for_timeout(200)
        with page.expect_download() as dl2:
            page.click("#btnCsvLaporan")
        lines2 = Path(dl2.value.path()).read_text(encoding="utf-8").strip().split("\n")
        check("H9 CSV Okt 2 baris + header = 3", len(lines2) == 3, f"dapat {len(lines2)}")

        print("I. Peran manajer & peternak")
        logout(page)
        login(page, "manajer", "manajer123")
        check("I1 manajer masuk", "Dedi Kurniawan (Manajer)" in text(page, "#userChip"))
        check("I2 cardPengguna tersembunyi untuk manajer", not page.is_visible("#cardPengguna"))
        check("I3 cardSandiSaya terlihat untuk manajer", page.is_visible("#cardSandiSaya"))
        check("I4 manajer melihat populasi penuh 4.445", "4.445 ekor" in text(page, "#dPopulasi"))
        logout(page)
        login(page, "peternak", "peternak123")
        check("I5 peternak masuk", "Budi Santoso (Peternak)" in text(page, "#userChip"))
        check("I6 peternak populasi 1.925 ekor", "1.925 ekor" in text(page, "#dPopulasi"))
        check("I7 peternak telur bulan 4.133 butir", "4.133 butir" in text(page, "#dTelurBulan"))
        check("I8 peternak biaya bulan Rp5.900.000", "Rp5.900.000" in text(page, "#dBiayaBulan"))
        check("I9 peternak nilai telur Rp9.092.600", "Rp9.092.600" in text(page, "#dNilaiTelur"))
        check("I10 peternak kandang 2", "2 kandang" in text(page, "#dKandang"))
        check("I11 cardPengguna tersembunyi untuk peternak", not page.is_visible("#cardPengguna"))
        check("I12 cardSandiSaya terlihat untuk peternak", page.is_visible("#cardSandiSaya"))
        tab(page, "kandang")
        check("I13 peternak hanya melihat Kandang A & D", "Kandang A" in text(page, "#daftarKandang") and "Kandang D" in text(page, "#daftarKandang") and "Kandang B" not in text(page, "#daftarKandang"))
        check("I14 cardTambahKandang tersembunyi untuk peternak", not page.is_visible("#cardTambahKandang"))
        tab(page, "telur")
        opts_tl = page.query_selector_all("#tlKandang option")
        check("I15 pilihan kandang telur peternak hanya 1 (Kandang A)", len(opts_tl) == 1)
        check("I16 cardHargaTelur tersembunyi untuk peternak", not page.is_visible("#cardHargaTelur"))
        tab(page, "biaya")
        check("I17 cardTambahBiaya tersembunyi untuk peternak", not page.is_visible("#cardTambahBiaya"))
        check("I18 peternak melihat biaya miliknya Rp5.900.000", "Rp5.900.000" in text(page, "#ringkasanBiaya"))
        tab(page, "pakan")
        check("I19 peternak melihat jadwal miliknya (hari ini 2)", "hari ini 2" in text(page, "#ringkasanPakan"))
        tab(page, "dashboard")
        page.click("#btnKeTelur")
        page.wait_for_timeout(200)
        check("I20 tombol cepat Catat Telur pindah ke tab telur", "active" in (page.get_attribute("#panel-telur", "class") or ""))

        print("J. Ganti kata sandi & reset")
        tab(page, "dashboard")
        page.fill("#sandiLama", "salah123")
        page.fill("#sandiBaru", "baru12345")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        check("J1 kata sandi lama salah ditolak", "Kata sandi lama salah" in text(page, "#pesanSandi"))
        page.fill("#sandiLama", "peternak123")
        page.fill("#sandiBaru", "peternak456")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        check("J2 ganti sandi peternak berhasil", "berhasil diubah" in text(page, "#pesanSandi"))
        logout(page)
        login(page, "peternak", "peternak123")
        check("J3 sandi lama sudah tidak berlaku", page.is_visible("#loginError"))
        login(page, "peternak", "peternak456")
        check("J4 login dengan sandi baru berhasil", not page.is_visible("#loginOverlay"))
        logout(page)
        login(page, "admin", "admin123")
        tab(page, "dashboard")
        page.click('[data-reset="peternak"]')
        page.wait_for_timeout(200)
        konfirmasi_modal(page)
        check("J5 admin reset sandi peternak ke bk123", True)
        logout(page)
        login(page, "peternak", "bk123")
        check("J6 login peternak dengan bk123 berhasil", not page.is_visible("#loginOverlay"))
        tab(page, "dashboard")
        page.fill("#sandiLama", "bk123")
        page.fill("#sandiBaru", "peternak123")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        check("J7 sandi peternak dikembalikan ke peternak123", "berhasil diubah" in text(page, "#pesanSandi"))
        logout(page)

        print("K. Backup & restore")
        login(page, "admin", "admin123")
        tab(page, "laporan")
        with page.expect_download() as dl3:
            page.click("#btnBackup")
        backup_path = Path(dl3.value.path())
        data_backup = json.loads(backup_path.read_text(encoding="utf-8"))
        check("K1 backup JSON berisi state telur 14", len(data_backup["state"]["telur"]) == 14)
        check("K2 backup JSON berisi users 3", len(data_backup["users"]) == 3)
        tab(page, "kandang")
        page.fill("#kdNama", "RESTORE-TEST")
        page.select_option("#kdJenis", "Petelur")
        page.fill("#kdKapasitas", "100")
        page.select_option("#kdPemilik", "manajer")
        page.click("#btnTambahKandang")
        page.wait_for_timeout(300)
        check("K3 kandang RESTORE-TEST ditambahkan", "RESTORE-TEST" in text(page, "#daftarKandang"))
        tab(page, "laporan")
        page.set_input_files("#inputRestore", str(backup_path))
        page.wait_for_timeout(500)
        tab(page, "kandang")
        check("K4 restore menghapus RESTORE-TEST", "RESTORE-TEST" not in text(page, "#daftarKandang"))
        check("K5 restore kembali ke 5 kandang", "5 kandang" in text(page, "#ringkasanKandang"))
        invalid = ROOT / "tests" / "invalid.json"
        invalid.write_text("bukan json", encoding="utf-8")
        tab(page, "laporan")
        page.set_input_files("#inputRestore", str(invalid))
        page.wait_for_timeout(500)
        check("K6 file cadangan tidak valid ditolak", page.is_visible("#toast.show"))
        invalid.unlink()

        print("L. Reset data demo")
        tab(page, "laporan")
        page.click("#btnResetData")
        page.wait_for_timeout(200)
        konfirmasi_modal(page)
        tab(page, "dashboard")
        check("L1 reset -> populasi kembali 4.445", "4.445 ekor" in text(page, "#dPopulasi"))
        check("L2 reset -> telur bulan kembali 7.218", "7.218 butir" in text(page, "#dTelurBulan"))

        print("M. Panduan & batasan jujur")
        tab(page, "panduan")
        isi = text(page, "#panel-panduan")
        check("M1 panduan menyebut localStorage perangkat ini", "localStorage" in isi)
        check("M2 panduan menyebut bukan payment gateway", "payment gateway" in isi)
        check("M3 harga Basic Rp499.000", "Rp499.000" in isi)
        check("M4 harga Business Rp1.999.000", "Rp1.999.000" in isi)
        check("M5 APK +Rp400.000", "Rp400.000" in isi)
        check("M6 akun demo admin/manajer/peternak tampil", "admin123" in isi and "manajer123" in isi and "peternak123" in isi)

        print(f"\nHASIL: {passed} lolos, {len(failures)} gagal")
        if failures:
            print("GAGAL:", failures)
        check("Z1 tanpa console error", len(console_errors) == 0, str(console_errors[:3]))
        check("Z2 tanpa page error", len(page_errors) == 0, str(page_errors[:3]))
        browser.close()
        print(f"TOTAL: {passed} lolos, {len(failures)} gagal")
        sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
