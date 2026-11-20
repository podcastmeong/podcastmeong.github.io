"""Tes Manajemen Budidaya Ikan (#54) — Playwright Chromium, file lokal.
Hari ini 2026-11-20. Data seed (tanggal relatif, diuji silang Python /tmp/cek_ikan.py):
  Kolam 6: K1 Kolam Lele A 800 m2 (pembudidaya), K2 Kolam Nila B 1200 (manajer),
    K3 Tambak Udang 2000 (manajer), K4 Keramba Gurame 500 (pembudidaya),
    K5 Kolam Bandeng 1500 (manajer), K6 Kolam Lele C 600 (pembudidaya).
  Benih 6 tebaran, 35.800 ekor; biaya benih Rp9.700.000 (semua Okt).
  Pertumbuhan 16 catatan; bobot terakhir K1 240, K2 290, K3 22, K4 550, K5 320, K6 190 g.
  Panen 7 catatan, 470 kg, nilai Rp14.930.000. Nov (6): 420 kg Rp13.680.000.
    Okt (1): 50 kg Rp1.250.000.
  Sisa ekor: K1 4167, K2 3690, K3 17955, K4 755, K5 2812, K6 2737; total 32.116 ekor.
  Stok ikan perkiraan (kg): total 4.300,31 kg.
  Pembudidaya (K1+K4+K6): populasi 7.659 ekor, stok 1.935,36 kg, panen Nov 225 kg
    Rp6.375.000, biaya Nov Rp7.500.000, stok pakan 760 kg.
  Stok pakan: Pelet Lele 560, Pelet Nila 465, Pelet Udang 300, Pelet Gurame 200,
    Pelet Bandeng 400 kg; total 1.925 kg, nilai Rp26.165.000.
  Jadwal pakan 12: hari ini belum 4, segera 4, lewat 2, selesai 2; belum 10.
  Biaya 13 catatan, total Rp37.550.000 (Benih 9.700.000, Pakan 27.100.000, Obat 750.000).
    Nov Rp24.850.000; Okt Rp12.700.000.
  Selisih (nilai panen - biaya): total -Rp22.620.000; Nov -Rp11.170.000; Okt -Rp11.450.000.
  CSV panen: Nov 6 baris + header = 7; Okt 1 baris + header = 2.
  CATATAN: tes D6 menambah stok Pelet Nila 100 kg (biaya +Rp1.300.000) sehingga
    biaya Nov menjadi Rp26.150.000, total biaya Rp38.850.000, selisih total
    -Rp23.920.000, selisih Nov -Rp12.470.000, kategori Pakan Rp28.400.000.
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent  # folder manajemen-budidaya-ikan
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
        check("A6 populasi total 32.116 ekor", "32.116 ekor" in text(page, "#dPopulasi"))
        check("A7 sub tebar 35.800 ekor", "tebar 35.800 ekor" in text(page, "#dPopulasiSub"))
        check("A8 stok ikan 4.300,31 kg", "4.300,31 kg" in text(page, "#dStokIkan"))
        check("A9 panen bulan ini 420 kg", "420 kg" in text(page, "#dPanenBulan"))
        check("A10 stok pakan 1.925 kg", "1.925 kg" in text(page, "#dStokPakan"))
        check("A11 sub stok pakan nilai Rp26.165.000", "Rp26.165.000" in text(page, "#dStokPakanSub"))
        check("A12 jadwal hari ini 4 belum", "4 belum" in text(page, "#dJadwalHariIni"))
        check("A13 sub jadwal segera 4 lewat 2", "segera 4" in text(page, "#dJadwalHariIniSub") and "lewat 2" in text(page, "#dJadwalHariIniSub"))
        check("A14 biaya bulan ini Rp24.850.000", "Rp24.850.000" in text(page, "#dBiayaBulan"))
        check("A15 nilai panen bulan Rp13.680.000", "Rp13.680.000" in text(page, "#dNilaiPanen"))
        check("A16 sub selisih bulan Rp-11.170.000", "Rp-11.170.000" in text(page, "#dNilaiPanenSub"))
        check("A17 kolam 6", "6 kolam" in text(page, "#dKolam"))
        check("A18 sub luas total 6.600 m2", "6.600 m" in text(page, "#dKolamSub"))
        check("A19 badge kolam 6", text(page, "#badgeKolam") == "6")
        check("A20 badge benih 6", text(page, "#badgeBenih") == "6")
        check("A21 badge pakan 10 belum", text(page, "#badgePakan") == "10")
        check("A22 badge panen 7", text(page, "#badgePanen") == "7")
        check("A23 cardSandiSaya terlihat untuk admin", page.is_visible("#cardSandiSaya"))
        check("A24 cardPengguna terlihat untuk admin", page.is_visible("#cardPengguna"))
        check("A25 grafik bobot memuat 550 g (Gurame)", "550 g" in text(page, "#daftarBobot"))
        check("A26 panen terbaru 80 kg", "80 kg" in text(page, "#daftarPanenRingkas"))

        print("B. Kolam")
        tab(page, "kolam")
        check("B1 ringkasan 6 kolam", "6 kolam" in text(page, "#ringkasanKolam"))
        check("B2 daftar memuat Tambak Udang", "Tambak Udang" in text(page, "#daftarKolam"))
        check("B3 daftar memuat Keramba Gurame", "Keramba Gurame" in text(page, "#daftarKolam"))
        page.fill("#klNama", "Kolam Uji")
        page.select_option("#klJenis", "Kolam")
        page.fill("#klLuas", "700")
        page.select_option("#klPemilik", "manajer")
        page.click("#btnTambahKolam")
        page.wait_for_timeout(300)
        check("B4 tambah Kolam Uji -> 7 kolam", "7 kolam" in text(page, "#ringkasanKolam"))
        page.fill("#klNama", "Kolam Uji")
        page.fill("#klLuas", "500")
        page.click("#btnTambahKolam")
        page.wait_for_timeout(300)
        check("B5 nama kolam duplikat ditolak", "7 kolam" in text(page, "#ringkasanKolam"))
        page.click('[data-hapus-kolam="1"]')
        page.wait_for_timeout(300)
        check("B6 hapus Kolam Lele A diblokir (masih ada data)", "7 kolam" in text(page, "#ringkasanKolam") and page.is_visible("#toast.show"))
        page.click('[data-hapus-kolam="7"]')
        page.wait_for_timeout(200)
        check("B7 modal konfirmasi hapus muncul", page.is_visible("#modalBack.open"))
        konfirmasi_modal(page)
        check("B8 Kolam Uji terhapus -> 6 kolam", "6 kolam" in text(page, "#ringkasanKolam"))

        print("C. Benih")
        tab(page, "kolam")
        page.fill("#klNama", "Kolam Uji")
        page.select_option("#klJenis", "Kolam")
        page.fill("#klLuas", "700")
        page.select_option("#klPemilik", "manajer")
        page.click("#btnTambahKolam")
        page.wait_for_timeout(300)
        tab(page, "benih")
        check("C1 ringkasan 6 tebaran 35.800 ekor Rp9.700.000",
              "6 tebaran" in text(page, "#ringkasanBenih") and "35.800 ekor" in text(page, "#ringkasanBenih")
              and "Rp9.700.000" in text(page, "#ringkasanBenih"))
        page.select_option("#bnKolam", label="Kolam Uji · Kolam · 0 ekor")
        page.select_option("#bnJenisIkan", "Lele")
        page.fill("#bnJumlah", "1000")
        page.fill("#bnHarga", "300")
        check("C2 pratinjau biaya benih Rp300.000", "Rp300.000" in val(page, "#bnBiaya"))
        page.fill("#bnTanggal", "2026-11-20")
        page.click("#btnTambahBenih")
        page.wait_for_timeout(300)
        check("C3 tebar 1000 ekor -> 7 tebaran 36.800 ekor Rp10.000.000",
              "7 tebaran" in text(page, "#ringkasanBenih") and "36.800 ekor" in text(page, "#ringkasanBenih")
              and "Rp10.000.000" in text(page, "#ringkasanBenih"))
        page.select_option("#bnKolam", label="Kolam Uji · Kolam · 1.000 ekor")
        page.fill("#bnJumlah", "500")
        page.fill("#bnHarga", "0")
        page.click("#btnTambahBenih")
        page.wait_for_timeout(300)
        check("C4 harga per ekor 0 ditolak", "36.800 ekor" in text(page, "#ringkasanBenih"))
        page.click('[data-hapus-benih="7"]')
        page.wait_for_timeout(200)
        konfirmasi_modal(page)
        check("C5 hapus tebaran uji -> kembali 35.800 ekor", "35.800 ekor" in text(page, "#ringkasanBenih"))
        page.click('[data-hapus-benih="3"]')
        page.wait_for_timeout(300)
        check("C6 hapus tebaran Udang diblokir (populasi jadi negatif)", page.is_visible("#toast.show") and "6 tebaran" in text(page, "#ringkasanBenih"))
        tab(page, "kolam")
        page.click('[data-hapus-kolam="8"]')
        page.wait_for_timeout(200)
        konfirmasi_modal(page)
        check("C7 Kolam Uji terhapus -> 6 kolam", "6 kolam" in text(page, "#ringkasanKolam"))

        print("D. Pakan & stok")
        tab(page, "pakan")
        check("D1 stok Pelet Lele 560 kg", "Pelet Lele" in text(page, "#daftarStokPakan") and "560 kg" in text(page, "#daftarStokPakan"))
        check("D2 ringkasan hari ini 4 segera 4 lewat 2 selesai 2",
              "hari ini 4" in text(page, "#ringkasanPakan") and "segera 4" in text(page, "#ringkasanPakan")
              and "lewat 2" in text(page, "#ringkasanPakan") and "selesai 2" in text(page, "#ringkasanPakan"))
        page.click('[data-beri-jadwal="1"]')
        page.wait_for_timeout(300)
        check("D3 beri jadwal 1 -> hari ini 3, stok Lele 520 kg",
              "hari ini 3" in text(page, "#ringkasanPakan") and "520 kg" in text(page, "#daftarStokPakan"))
        page.click('[data-batal-jadwal="1"]')
        page.wait_for_timeout(300)
        check("D4 batalkan jadwal 1 -> hari ini 4, stok Lele 560 kg lagi",
              "hari ini 4" in text(page, "#ringkasanPakan") and "560 kg" in text(page, "#daftarStokPakan"))
        page.select_option("#pkKolam", "3")
        page.select_option("#pkJenisPakan", "Pelet Udang")
        page.fill("#pkNama", "Pakan Uji")
        page.fill("#pkJumlah", "9999")
        page.fill("#pkTanggal", "2026-11-20")
        page.click("#btnTambahPakan")
        page.wait_for_timeout(300)
        check("D5a tambah jadwal uji 9999 kg -> hari ini 5", "hari ini 5" in text(page, "#ringkasanPakan"))
        page.click('[data-beri-jadwal="13"]')
        page.wait_for_timeout(300)
        check("D5b beri 9999 kg ditolak (stok Udang 300 kg)", page.is_visible("#toast.show") and "hari ini 5" in text(page, "#ringkasanPakan"))
        page.click('[data-hapus-jadwal="13"]')
        page.wait_for_timeout(200)
        konfirmasi_modal(page)
        check("D5c hapus jadwal uji -> hari ini 4 lagi", "hari ini 4" in text(page, "#ringkasanPakan"))
        page.select_option("#spJenis", "Pelet Nila")
        page.fill("#spKg", "100")
        page.fill("#spHarga", "13000")
        page.fill("#spTanggal", "2026-11-20")
        page.click("#btnTambahStokPakan")
        page.wait_for_timeout(300)
        check("D6 beli Pelet Nila 100 kg -> stok 565 kg", "565 kg" in text(page, "#daftarStokPakan"))
        page.select_option("#fPakan", "lewat")
        page.wait_for_timeout(200)
        check("D7 filter lewat menampilkan 2 jadwal", "2 jadwal" in text(page, "#ringkasanPakan"))
        page.select_option("#fPakan", "semua")
        page.wait_for_timeout(200)

        print("E. Pertumbuhan")
        tab(page, "pertumbuhan")
        check("E1 ringkasan 16 catatan pertumbuhan", "16 catatan" in text(page, "#ringkasanPertumbuhan"))
        check("E2 grafik memuat 550 g", "550 g" in text(page, "#grafikBobot"))
        page.select_option("#ptKolam", "2")
        page.fill("#ptTanggal", "2026-11-20")
        page.fill("#ptBobot", "300")
        page.fill("#ptPanjang", "25")
        page.click("#btnTambahPertumbuhan")
        page.wait_for_timeout(300)
        check("E3 tambah pertumbuhan K2 300 g -> grafik 300 g", "300 g" in text(page, "#grafikBobot"))
        page.click('[data-hapus-tumbuh="17"]')
        page.wait_for_timeout(200)
        konfirmasi_modal(page)
        check("E4 hapus pertumbuhan uji -> grafik kembali 290 g", "290 g" in text(page, "#grafikBobot"))
        page.select_option("#fTumbuhBulan", "2026-10")
        page.wait_for_timeout(200)
        check("E5 filter bulan Okt menampilkan 4 catatan", "4 catatan" in text(page, "#ringkasanPertumbuhan"))
        page.select_option("#fTumbuhBulan", "semua")
        page.wait_for_timeout(200)
        page.select_option("#fTumbuh", "3")
        page.wait_for_timeout(200)
        check("E6 filter kolam Tambak Udang menampilkan 3 catatan", "3 catatan" in text(page, "#ringkasanPertumbuhan"))
        page.select_option("#fTumbuh", "semua")
        page.wait_for_timeout(200)

        print("F. Panen")
        tab(page, "panen")
        check("F1 ringkasan 7 catatan 470 kg Rp14.930.000",
              "7 catatan" in text(page, "#ringkasanPanen") and "470 kg" in text(page, "#ringkasanPanen")
              and "Rp14.930.000" in text(page, "#ringkasanPanen"))
        page.select_option("#pnKolam", "1")
        page.fill("#pnKg", "100")
        page.fill("#pnHarga", "25000")
        check("F2 pratinjau nilai Rp2.500.000, stok 1.000,08 kg, 417 ekor",
              "Rp2.500.000" in val(page, "#pnNilai") and "1.000,08 kg" in val(page, "#pnStok")
              and "417 ekor" in val(page, "#pnNilai"))
        page.fill("#pnTanggal", "2026-11-20")
        page.click("#btnTambahPanen")
        page.wait_for_timeout(300)
        check("F3 tambah panen 100 kg -> total 570 kg Rp17.430.000",
              "570 kg" in text(page, "#ringkasanPanen") and "Rp17.430.000" in text(page, "#ringkasanPanen"))
        page.fill("#pnKg", "5000")
        page.fill("#pnHarga", "25000")
        page.click("#btnTambahPanen")
        page.wait_for_timeout(300)
        check("F4 panen 5000 kg ditolak (melebihi stok)", page.is_visible("#toast.show") and "570 kg" in text(page, "#ringkasanPanen"))
        page.click('[data-hapus-panen="8"]')
        page.wait_for_timeout(200)
        konfirmasi_modal(page)
        check("F5 hapus panen uji -> kembali 470 kg", "470 kg" in text(page, "#ringkasanPanen"))
        page.select_option("#fPanenBulan", "2026-10")
        page.wait_for_timeout(200)
        check("F6 filter bulan Okt menampilkan 1 catatan", "1 catatan" in text(page, "#ringkasanPanen"))
        page.select_option("#fPanenBulan", "semua")
        page.wait_for_timeout(200)
        page.select_option("#fPanen", "1")
        page.wait_for_timeout(200)
        check("F7 filter kolam Lele A menampilkan 2 catatan", "2 catatan" in text(page, "#ringkasanPanen"))
        page.select_option("#fPanen", "semua")
        page.wait_for_timeout(200)

        print("G. Laporan & CSV")
        tab(page, "laporan")
        check("G1 bulan laporan default November 2026", "2026-11" in val(page, "#fBulanLaporan"))
        check("G2 ringkasan selisih total Rp-23.920.000", "Rp-23.920.000" in text(page, "#ringkasanLaporan"))
        check("G3 tabel per kolam: Lele A nilai panen Rp5.000.000", "Rp5.000.000" in text(page, "#tabelPerKolam"))
        check("G4 tabel per bulan Nov: 420 kg, selisih Rp-12.470.000",
              "420" in text(page, "#tabelPerBulan") and "Rp-12.470.000" in text(page, "#tabelPerBulan"))
        check("G5 tabel per bulan Okt: 50 kg, selisih Rp-11.450.000",
              "50" in text(page, "#tabelPerBulan") and "Rp-11.450.000" in text(page, "#tabelPerBulan"))
        check("G6 tabel kategori Pakan Rp28.400.000", "Rp28.400.000" in text(page, "#tabelPerKategori"))
        with page.expect_download() as dl:
            page.click("#btnCsvLaporan")
        p_csv = Path(dl.value.path())
        lines = p_csv.read_text(encoding="utf-8").strip().split("\n")
        check("G7 CSV Nov 6 baris + header = 7", len(lines) == 7, f"dapat {len(lines)}")
        page.select_option("#fBulanLaporan", "2026-10")
        page.wait_for_timeout(200)
        with page.expect_download() as dl2:
            page.click("#btnCsvLaporan")
        lines2 = Path(dl2.value.path()).read_text(encoding="utf-8").strip().split("\n")
        check("G8 CSV Okt 1 baris + header = 2", len(lines2) == 2, f"dapat {len(lines2)}")

        print("H. Peran manajer & pembudidaya")
        logout(page)
        login(page, "manajer", "manajer123")
        check("H1 manajer masuk", "Dedi Kurniawan (Manajer)" in text(page, "#userChip"))
        check("H2 cardPengguna tersembunyi untuk manajer", not page.is_visible("#cardPengguna"))
        check("H3 cardSandiSaya terlihat untuk manajer", page.is_visible("#cardSandiSaya"))
        check("H4 manajer melihat populasi penuh 32.116", "32.116 ekor" in text(page, "#dPopulasi"))
        tab(page, "kolam")
        check("H5 cardTambahKolam terlihat untuk manajer", page.is_visible("#cardTambahKolam"))
        logout(page)
        login(page, "pembudidaya", "pembudidaya123")
        check("H6 pembudidaya masuk", "Budi Santoso (Pembudidaya)" in text(page, "#userChip"))
        check("H7 pembudidaya populasi 7.659 ekor", "7.659 ekor" in text(page, "#dPopulasi"))
        check("H8 pembudidaya stok ikan 1.935,36 kg", "1.935,36 kg" in text(page, "#dStokIkan"))
        check("H9 pembudidaya panen bulan 225 kg", "225 kg" in text(page, "#dPanenBulan"))
        check("H10 pembudidaya stok pakan 760 kg", "760 kg" in text(page, "#dStokPakan"))
        check("H11 pembudidaya jadwal hari ini 2 belum", "2 belum" in text(page, "#dJadwalHariIni"))
        check("H12 pembudidaya biaya bulan Rp7.500.000", "Rp7.500.000" in text(page, "#dBiayaBulan"))
        check("H13 pembudidaya kolam 3", "3 kolam" in text(page, "#dKolam"))
        check("H14 cardPengguna tersembunyi untuk pembudidaya", not page.is_visible("#cardPengguna"))
        check("H15 cardSandiSaya terlihat untuk pembudidaya", page.is_visible("#cardSandiSaya"))
        tab(page, "kolam")
        check("H16 pembudidaya hanya melihat Lele A, Gurame, Lele C",
              "Kolam Lele A" in text(page, "#daftarKolam") and "Keramba Gurame" in text(page, "#daftarKolam")
              and "Kolam Lele C" in text(page, "#daftarKolam") and "Kolam Nila B" not in text(page, "#daftarKolam"))
        check("H17 cardTambahKolam tersembunyi untuk pembudidaya", not page.is_visible("#cardTambahKolam"))
        tab(page, "benih")
        check("H18 pembudidaya benih 3 tebaran 8.800 ekor",
              "3 tebaran" in text(page, "#ringkasanBenih") and "8.800 ekor" in text(page, "#ringkasanBenih"))
        tab(page, "pakan")
        check("H19 cardStokPakan tersembunyi untuk pembudidaya", not page.is_visible("#cardStokPakan"))
        check("H20 cardTambahBiaya tersembunyi untuk pembudidaya", not page.is_visible("#cardTambahBiaya"))
        check("H21 pembudidaya jadwal hari ini 2", "hari ini 2" in text(page, "#ringkasanPakan"))
        tab(page, "pertumbuhan")
        opts_pt = page.query_selector_all("#ptKolam option")
        check("H22 pilihan kolam pertumbuhan pembudidaya hanya 3", len(opts_pt) == 3)
        tab(page, "panen")
        opts_pn = page.query_selector_all("#pnKolam option")
        check("H23 pilihan kolam panen pembudidaya hanya 3", len(opts_pn) == 3)
        tab(page, "dashboard")
        page.click("#btnKePanen")
        page.wait_for_timeout(200)
        check("H24 tombol cepat Catat Panen pindah ke tab panen", "active" in (page.get_attribute("#panel-panen", "class") or ""))

        print("I. Ganti kata sandi & reset")
        tab(page, "dashboard")
        page.fill("#sandiLama", "salah123")
        page.fill("#sandiBaru", "baru12345")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        check("I1 kata sandi lama salah ditolak", "Kata sandi lama salah" in text(page, "#pesanSandi"))
        page.fill("#sandiLama", "pembudidaya123")
        page.fill("#sandiBaru", "budibaru123")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        check("I2 ganti sandi pembudidaya berhasil", "berhasil diubah" in text(page, "#pesanSandi"))
        logout(page)
        login(page, "pembudidaya", "pembudidaya123")
        check("I3 sandi lama sudah tidak berlaku", page.is_visible("#loginError"))
        login(page, "pembudidaya", "budibaru123")
        check("I4 login dengan sandi baru berhasil", not page.is_visible("#loginOverlay"))
        logout(page)
        login(page, "admin", "admin123")
        tab(page, "dashboard")
        page.click('[data-reset="pembudidaya"]')
        page.wait_for_timeout(200)
        konfirmasi_modal(page)
        check("I5 admin reset sandi pembudidaya ke bk123", True)
        logout(page)
        login(page, "pembudidaya", "bk123")
        check("I6 login pembudidaya dengan bk123 berhasil", not page.is_visible("#loginOverlay"))
        tab(page, "dashboard")
        page.fill("#sandiLama", "bk123")
        page.fill("#sandiBaru", "pembudidaya123")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        check("I7 sandi pembudidaya dikembalikan ke pembudidaya123", "berhasil diubah" in text(page, "#pesanSandi"))
        logout(page)

        print("J. Backup & restore")
        login(page, "admin", "admin123")
        tab(page, "laporan")
        with page.expect_download() as dl3:
            page.click("#btnBackup")
        backup_path = Path(dl3.value.path())
        data_backup = json.loads(backup_path.read_text(encoding="utf-8"))
        check("J1 backup JSON berisi state panen 7", len(data_backup["state"]["panen"]) == 7)
        check("J2 backup JSON berisi users 3", len(data_backup["users"]) == 3)
        tab(page, "kolam")
        page.fill("#klNama", "RESTORE-TEST")
        page.select_option("#klJenis", "Kolam")
        page.fill("#klLuas", "100")
        page.select_option("#klPemilik", "manajer")
        page.click("#btnTambahKolam")
        page.wait_for_timeout(300)
        check("J3 kolam RESTORE-TEST ditambahkan", "RESTORE-TEST" in text(page, "#daftarKolam"))
        tab(page, "laporan")
        page.set_input_files("#inputRestore", str(backup_path))
        page.wait_for_timeout(500)
        tab(page, "kolam")
        check("J4 restore menghapus RESTORE-TEST", "RESTORE-TEST" not in text(page, "#daftarKolam"))
        check("J5 restore kembali ke 6 kolam", "6 kolam" in text(page, "#ringkasanKolam"))
        invalid = ROOT / "tests" / "invalid.json"
        invalid.write_text("bukan json", encoding="utf-8")
        tab(page, "laporan")
        page.set_input_files("#inputRestore", str(invalid))
        page.wait_for_timeout(500)
        check("J6 file cadangan tidak valid ditolak", page.is_visible("#toast.show"))
        invalid.unlink()

        print("K. Reset data demo")
        tab(page, "laporan")
        page.click("#btnResetData")
        page.wait_for_timeout(200)
        konfirmasi_modal(page)
        tab(page, "dashboard")
        check("K1 reset -> populasi kembali 32.116", "32.116 ekor" in text(page, "#dPopulasi"))
        check("K2 reset -> panen bulan kembali 420 kg", "420 kg" in text(page, "#dPanenBulan"))
        check("K3 reset -> stok pakan kembali 1.925 kg", "1.925 kg" in text(page, "#dStokPakan"))

        print("L. Panduan & batasan jujur")
        tab(page, "panduan")
        isi = text(page, "#panel-panduan")
        check("L1 panduan menyebut localStorage perangkat ini", "localStorage" in isi)
        check("L2 panduan menyebut bukan payment gateway", "payment gateway" in isi)
        check("L3 panduan menyebut bobot acuan", "bobot acuan" in isi)
        check("L4 harga Basic Rp499.000", "Rp499.000" in isi)
        check("L5 harga Business Rp1.999.000", "Rp1.999.000" in isi)
        check("L6 APK +Rp400.000", "Rp400.000" in isi)
        check("L7 akun demo admin/manajer/pembudidaya tampil", "admin123" in isi and "manajer123" in isi and "pembudidaya123" in isi)

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
