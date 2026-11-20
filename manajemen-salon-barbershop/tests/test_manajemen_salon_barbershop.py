"""Tes Manajemen Salon & Barbershop (#57) — Playwright Chromium, file lokal.
Hari ini 2026-11-20. Data seed (tanggal relatif, diuji silang Python /tmp/cek_salon.py):
  Pelanggan 8: Andi, Sari, Budi, Dewi, Rudi, Maya, Joko, Lina.
  Kapster 5: Agus (Potong, 20%), Sinta (Pewarnaan & Creambath, 25%),
    Budi (Cukur & Pijat, 15%), Rina (Facial & Smoothing, 25%),
    Dedi (Potong, 20%).
  Layanan 8: Potong 35rb, Creambath 60rb, Pewarnaan 150rb, Cukur 25rb,
    Facial 80rb, Smoothing 200rb, Pijat 50rb, Manicure & Pedicure 70rb.
  Jadwal 13: hari ini 3 (Terjadwal 2, Selesai 1), segera 4, lewat 1,
    selesai 5, dibatalkan 1.
  Transaksi 11: Nov 9 (Rp680.000), Okt 2 (Rp95.000), total Rp775.000.
    Hari ini Rp35.000 (1 trx). Tunai Rp400.000 (7), QRIS Rp375.000 (4).
    Kembalian: T1 15rb, T5 50rb, T7 65rb.
  Komisi total Rp180.000: sudah Rp28.500, belum Rp151.500.
    Agus 28rb (sudah 14rb, belum 14rb), Sinta 67.500 (belum semua),
    Budi 7.500 (sudah semua), Rina 70rb (belum semua), Dedi 7rb (sudah semua).
  Per layanan: Potong 5x Rp175.000, Smoothing 1x Rp200.000,
    Creambath 2x Rp120.000, Pewarnaan 1x Rp150.000, Pijat 1x Rp50.000,
    Facial 1x Rp80.000.
  CSV transaksi Nov: 9 baris + header = 10; semua: 11 + header = 12.
  CATATAN: tes menambah J14 (Lina/Agus/Potong, +5, 12:00) lalu menyelesaikannya
    (transaksi T12 Rp35.000, komisi 7rb belum), membatalkan lalu menghapus J4,
    membayar komisi T12, menambah transaksi walk-in T13 (Joko/Dedi/Potong,
    Tunai 100rb, kembalian 65rb) dan T14 (Maya/Rina/Facial, QRIS 80rb) lalu
    menghapus T14. Sehingga di seksi G: transaksi 13, Nov 11 trx Rp750.000,
    Okt 2 trx Rp95.000; komisi total Rp194.000, sudah Rp35.500, belum Rp158.500;
    per layanan Potong 7x Rp245.000; per kapster Agus Rp175.000, Rina Rp280.000,
    Dedi Rp70.000; Tunai Rp470.000 (9), QRIS Rp375.000 (4);
    CSV Nov 11 + header = 12, semua 13 + header = 14.
"""
import json
from datetime import date, timedelta
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent  # folder manajemen-salon-barbershop
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
        check("A6 jadwal hari ini 3", "3 jadwal" in text(page, "#dJadwalHariIni"))
        check("A7 sub hari ini: terjadwal 2, selesai 1",
              "terjadwal 2" in text(page, "#dJadwalHariIniSub") and "selesai 1" in text(page, "#dJadwalHariIniSub"))
        check("A8 segera 4 jadwal", "4 jadwal" in text(page, "#dSegera"))
        check("A9 lewat 1 jadwal", "1 jadwal" in text(page, "#dLewat"))
        check("A10 pemasukan hari ini Rp35.000", "Rp35.000" in text(page, "#dMasukHariIni"))
        check("A11 sub hari ini 1 transaksi", "1 transaksi hari ini" in text(page, "#dMasukHariIniSub"))
        check("A12 pemasukan bulan Rp680.000", "Rp680.000" in text(page, "#dMasukBulan"))
        check("A13 sub bulan 9 transaksi, November 2026",
              "9 transaksi" in text(page, "#dMasukBulanSub") and "November 2026" in text(page, "#dMasukBulanSub"))
        check("A14 komisi belum Rp151.500", "Rp151.500" in text(page, "#dKomisiBelum"))
        check("A15 sub komisi total 180.000, sudah 28.500",
              "Rp180.000" in text(page, "#dKomisiBelumSub") and "Rp28.500" in text(page, "#dKomisiBelumSub"))
        check("A16 pelanggan 8 orang", "8 orang" in text(page, "#dPelanggan"))
        check("A17 sub pelanggan 11 transaksi", "11 transaksi tercatat" in text(page, "#dPelangganSub"))
        check("A18 kapster aktif 5", "5 kapster" in text(page, "#dKapster"))
        check("A19 badge pelanggan 8", text(page, "#badgePelanggan") == "8")
        check("A20 badge jadwal 7 (terjadwal)", text(page, "#badgeJadwal") == "7")
        check("A21 badge kapster 5", text(page, "#badgeKapster") == "5")
        check("A22 badge komisi 7 (belum dibayar)", text(page, "#badgeKomisi") == "7")
        check("A23 cardSandiSaya terlihat untuk admin", page.is_visible("#cardSandiSaya"))
        check("A24 cardPengguna terlihat untuk admin", page.is_visible("#cardPengguna"))
        check("A25 jadwal hari ini memuat Andi & Rudi",
              "Andi Pratama" in text(page, "#daftarJadwalHariIni") and "Rudi Hartono" in text(page, "#daftarJadwalHariIni"))
        check("A26 transaksi terbaru memuat Andi & Smoothing",
              "Andi Pratama" in text(page, "#daftarTransaksiRingkas") and "Smoothing" in text(page, "#daftarTransaksiRingkas"))

        print("A*. Sesi bertahan setelah reload")
        page.reload()
        page.wait_for_timeout(500)
        check("A27 setelah reload tetap masuk sebagai admin", "Administrator (Admin)" in text(page, "#userChip") and not page.is_visible("#loginOverlay"))

        print("B. Pelanggan")
        tab(page, "pelanggan")
        check("B1 ringkasan 8 pelanggan", "8 pelanggan" in text(page, "#ringkasanPelanggan"))
        check("B2 Andi: 3 transaksi, total belanja Rp165.000, kunjungan hari ini",
              "3 transaksi" in text(page, "#daftarPelanggan") and "Rp165.000" in text(page, "#daftarPelanggan") and "20/11/2026" in text(page, "#daftarPelanggan"))
        page.fill("#plNama", "Udin Saefudin")
        page.fill("#plTelepon", "0812-9999-0009")
        page.click("#btnTambahPelanggan")
        page.wait_for_timeout(300)
        check("B3 tambah Udin -> 9 pelanggan", "9 pelanggan" in text(page, "#ringkasanPelanggan"))
        check("B4 Udin kunjungan terakhir —", "Udin Saefudin" in text(page, "#daftarPelanggan") and "kunjungan terakhir —" in text(page, "#daftarPelanggan"))
        page.click('[data-hapus-pelanggan="9"]')
        page.wait_for_timeout(200)
        konfirmasi_modal(page)
        check("B5 hapus Udin -> 8 pelanggan", "8 pelanggan" in text(page, "#ringkasanPelanggan"))
        check("B6 pelanggan Andi (ada transaksi) tidak punya tombol hapus", page.query_selector('[data-hapus-pelanggan="1"]') is None)

        print("C. Jadwal: pratinjau, bentrok, selesai, batal, hapus")
        tab(page, "jadwal")
        page.select_option("#jdLayanan", "Pewarnaan")
        page.wait_for_timeout(200)
        check("C1 pratinjau harga Pewarnaan Rp150.000", "Rp150.000" in val(page, "#jdHarga"))
        # bentrok: Agus hari ini 09:00 (J1)
        page.select_option("#jdPelanggan", "2")  # Sari Wijaya
        page.select_option("#jdKapster", "1")  # Agus Santoso
        page.select_option("#jdLayanan", "Potong Rambut")
        page.fill("#jdTanggal", dstr(0))
        page.select_option("#jdJam", "09:00")
        page.click("#btnTambahJadwal")
        page.wait_for_timeout(300)
        check("C2 jadwal bentrok Agus 09:00 ditolak", page.is_visible("#toast.show") and "sudah ada jadwal" in text(page, "#toast"))
        check("C3 jadwal tetap 13 setelah bentrok ditolak", "13 jadwal" in text(page, "#ringkasanJadwal"))
        # jadwal valid J14: Lina/Agus/Potong, +5, 12:00
        page.select_option("#jdPelanggan", "8")  # Lina Marlina
        page.select_option("#jdKapster", "1")
        page.select_option("#jdLayanan", "Potong Rambut")
        page.fill("#jdTanggal", dstr(5))
        page.select_option("#jdJam", "12:00")
        page.click("#btnTambahJadwal")
        page.wait_for_timeout(300)
        check("C4 tambah J14 -> 14 jadwal", "14 jadwal" in text(page, "#ringkasanJadwal"))
        check("C5 J14 Lina muncul di daftar", "Lina Marlina" in text(page, "#daftarJadwal"))
        page.click('[data-selesai-jadwal="14"]')
        page.wait_for_timeout(300)
        check("C6 selesaikan J14 -> transaksi Rp35.000 tercatat", "Rp35.000 tercatat" in text(page, "#toast"))
        check("C7 J14 tidak lagi punya tombol Selesai", page.query_selector('[data-selesai-jadwal="14"]') is None)
        tab(page, "kasir")
        check("C8 kasir: transaksi jadi 12 setelah J14 selesai", "12 transaksi" in text(page, "#ringkasanKasir"))
        tab(page, "jadwal")
        page.click('[data-batal-jadwal="4"]')
        page.wait_for_timeout(200)
        konfirmasi_modal(page)
        check("C9 J4 dibatalkan (tombol hapus muncul)", page.query_selector('[data-hapus-jadwal="4"]') is not None)
        page.click('[data-hapus-jadwal="4"]')
        page.wait_for_timeout(200)
        konfirmasi_modal(page)
        check("C10 hapus J4 -> 13 jadwal", "13 jadwal" in text(page, "#ringkasanJadwal"))

        print("D. Kapster & harga layanan")
        tab(page, "kapster")
        check("D1 ringkasan 5 kapster, aktif 5", "5 kapster" in text(page, "#ringkasanKapster") and "aktif 5" in text(page, "#ringkasanKapster"))
        page.fill("#kpNama", "Eko Wijaya")
        page.fill("#kpSpesialisasi", "Cukur & Pijat")
        page.fill("#kpKomisi", "15")
        page.click("#btnTambahKapster")
        page.wait_for_timeout(300)
        check("D2 tambah Eko -> 6 kapster", "6 kapster" in text(page, "#ringkasanKapster"))
        page.fill('[data-komisi-kapster="6"]', "18")
        page.click('[data-simpan-komisi="6"]')
        page.wait_for_timeout(300)
        check("D3 ubah komisi Eko jadi 18%", "Komisi 18%" in text(page, "#daftarKapster"))
        page.click('[data-hapus-kapster="6"]')
        page.wait_for_timeout(200)
        konfirmasi_modal(page)
        check("D4 hapus Eko -> 5 kapster", "5 kapster" in text(page, "#ringkasanKapster"))
        check("D5 kapster Agus (ada data) tidak punya tombol hapus", page.query_selector('[data-hapus-kapster="1"]') is None)
        check("D6 Agus: 5 transaksi, nilai Rp175.000, komisi Rp35.000",
              "Agus Santoso" in text(page, "#daftarKapster") and "5 transaksi" in text(page, "#daftarKapster") and "Rp175.000" in text(page, "#daftarKapster") and "Rp35.000" in text(page, "#daftarKapster"))
        page.fill('[data-harga-layanan="4"]', "30000")
        page.click('[data-simpan-harga="4"]')
        page.wait_for_timeout(300)
        check("D7 ubah harga Cukur Jenggot jadi Rp30.000", "Rp30.000" in text(page, "#daftarLayanan"))
        page.fill('[data-harga-layanan="4"]', "25000")
        page.click('[data-simpan-harga="4"]')
        page.wait_for_timeout(300)
        check("D8 kembalikan harga Cukur Jenggot Rp25.000", "Rp25.000" in text(page, "#daftarLayanan"))

        print("E. Komisi")
        tab(page, "komisi")
        check("E1 ringkasan komisi total 187.000, sudah 28.500, belum 158.500",
              "Rp187.000" in text(page, "#ringkasanKomisi") and "Rp28.500" in text(page, "#ringkasanKomisi") and "Rp158.500" in text(page, "#ringkasanKomisi"))
        t_kap = text(page, "#tabelKomisiKapster")
        check("E2 rekap Agus total 35.000, sudah 14.000, belum 21.000",
              "Agus Santoso" in t_kap and "Rp35.000" in t_kap and "Rp14.000" in t_kap and "Rp21.000" in t_kap)
        check("E3 rekap Sinta total 67.500", "Sinta Wijaya" in t_kap and "Rp67.500" in t_kap)
        check("E4 rekap Rina total 70.000", "Rina Lestari" in t_kap and "Rp70.000" in t_kap)
        page.select_option("#fKomisiStatus", "Belum")
        page.wait_for_timeout(250)
        check("E5 filter Belum -> 8 tombol bayar komisi", len(page.query_selector_all("[data-bayar-komisi]")) == 8)
        page.click('[data-bayar-komisi="12"]')
        page.wait_for_timeout(300)
        check("E6 bayar komisi T12 -> belum tinggal 7", len(page.query_selector_all("[data-bayar-komisi]")) == 7)
        check("E7 ringkasan sudah dibayar Rp35.500", "Rp35.500" in text(page, "#ringkasanKomisi"))
        page.select_option("#fKomisiStatus", "semua")
        page.wait_for_timeout(250)

        print("F. Kasir")
        tab(page, "kasir")
        check("F1 ringkasan 12 transaksi, total Rp810.000", "12 transaksi" in text(page, "#ringkasanKasir") and "Rp810.000" in text(page, "#ringkasanKasir"))
        page.select_option("#ksPelanggan", "7")  # Joko Santoso
        page.select_option("#ksKapster", "5")  # Dedi Prasetyo
        page.select_option("#ksLayanan", "Potong Rambut")
        page.fill("#ksTanggal", dstr(0))
        page.select_option("#ksMetode", "Tunai")
        page.fill("#ksBayar", "100000")
        page.wait_for_timeout(200)
        check("F2 pratinjau harga Rp35.000", "Rp35.000" in val(page, "#ksHarga"))
        check("F3 pratinjau kembalian Rp65.000", "Rp65.000" in val(page, "#ksKembalian"))
        page.click("#btnTambahTransaksi")
        page.wait_for_timeout(300)
        check("F4 tambah T13 -> 13 transaksi, total Rp845.000", "13 transaksi" in text(page, "#ringkasanKasir") and "Rp845.000" in text(page, "#ringkasanKasir"))
        check("F5 toast menyebut kembalian Rp65.000", "Rp65.000" in text(page, "#toast"))
        # bayar kurang ditolak, input kembali ke harga
        page.select_option("#ksPelanggan", "8")  # Lina Marlina
        page.select_option("#ksKapster", "2")  # Sinta Wijaya
        page.select_option("#ksLayanan", "Creambath")
        page.fill("#ksTanggal", dstr(0))
        page.select_option("#ksMetode", "Tunai")
        page.fill("#ksBayar", "50000")
        page.click("#btnTambahTransaksi")
        page.wait_for_timeout(300)
        check("F6 bayar kurang (50rb < 60rb) ditolak", "kurang dari harga" in text(page, "#toast"))
        check("F7 input bayar dikembalikan ke harga Rp60.000", val(page, "#ksBayar") == "60000")
        check("F8 transaksi tetap 13 setelah bayar kurang ditolak", "13 transaksi" in text(page, "#ringkasanKasir"))
        # QRIS: bayar otomatis pas
        page.select_option("#ksPelanggan", "6")  # Maya Putri
        page.select_option("#ksKapster", "4")  # Rina Lestari
        page.select_option("#ksLayanan", "Facial")
        page.fill("#ksTanggal", dstr(0))
        page.select_option("#ksMetode", "QRIS")
        page.wait_for_timeout(200)
        check("F9 QRIS bayar otomatis Rp80.000", val(page, "#ksBayar") == "80000")
        check("F10 QRIS kembalian Rp0", "Rp0" in val(page, "#ksKembalian"))
        page.click("#btnTambahTransaksi")
        page.wait_for_timeout(300)
        check("F11 tambah T14 QRIS -> 14 transaksi, total Rp925.000", "14 transaksi" in text(page, "#ringkasanKasir") and "Rp925.000" in text(page, "#ringkasanKasir"))
        page.click('[data-hapus-transaksi="14"]')
        page.wait_for_timeout(200)
        konfirmasi_modal(page)
        check("F12 hapus T14 -> 13 transaksi, total Rp845.000", "13 transaksi" in text(page, "#ringkasanKasir") and "Rp845.000" in text(page, "#ringkasanKasir"))

        print("G. Laporan & CSV")
        tab(page, "laporan")
        check("G1 bulan laporan default bulan berjalan", "2026-11" in val(page, "#fBulanLaporan"))
        check("G2 ringkasan pemasukan bulan Rp750.000 (11 trx), komisi belum Rp158.500",
              "Rp750.000" in text(page, "#ringkasanLaporan") and "11 transaksi" in text(page, "#ringkasanLaporan") and "Rp158.500" in text(page, "#ringkasanLaporan"))
        t_lay = text(page, "#tabelPerLayanan")
        check("G3 per layanan Potong Rambut 7 trx Rp245.000", "Potong Rambut" in t_lay and "Rp245.000" in t_lay)
        check("G4 per layanan Smoothing Rp200.000", "Smoothing" in t_lay and "Rp200.000" in t_lay)
        check("G5 per layanan Creambath Rp120.000", "Creambath" in t_lay and "Rp120.000" in t_lay)
        t_kap = text(page, "#tabelPerKapster")
        check("G6 per kapster Agus Rp175.000", "Agus Santoso" in t_kap and "Rp175.000" in t_kap)
        check("G7 per kapster Rina Rp280.000", "Rina Lestari" in t_kap and "Rp280.000" in t_kap)
        check("G8 per kapster Dedi Rp70.000", "Dedi Prasetyo" in t_kap and "Rp70.000" in t_kap)
        t_bulan = text(page, "#tabelPerBulan")
        check("G9 per bulan Nov 11 trx Rp750.000", "November 2026" in t_bulan and "Rp750.000" in t_bulan)
        check("G10 per bulan Okt 2 trx Rp95.000", "Oktober 2026" in t_bulan and "Rp95.000" in t_bulan)
        t_met = text(page, "#tabelPerMetode")
        check("G11 per metode Tunai Rp470.000 (9 trx)", "Tunai" in t_met and "Rp470.000" in t_met)
        check("G12 per metode QRIS Rp375.000 (4 trx)", "QRIS" in t_met and "Rp375.000" in t_met)
        with page.expect_download() as dl:
            page.click("#btnCsvLaporan")
        lines = Path(dl.value.path()).read_text(encoding="utf-8").strip().split("\n")
        check("G13 CSV Nov 11 baris + header = 12", len(lines) == 12, f"dapat {len(lines)}")
        check("G14 CSV header memuat Pelanggan", "Pelanggan" in lines[0])
        check("G15 CSV memuat Andi Pratama", any("Andi Pratama" in ln for ln in lines))
        page.select_option("#fBulanLaporan", "semua")
        page.wait_for_timeout(200)
        with page.expect_download() as dl2:
            page.click("#btnCsvLaporan")
        lines2 = Path(dl2.value.path()).read_text(encoding="utf-8").strip().split("\n")
        check("G16 CSV semua bulan 13 + header = 14", len(lines2) == 14, f"dapat {len(lines2)}")

        print("H. Backup / restore / reset")
        with page.expect_download() as dl3:
            page.click("#btnBackup")
        backup_path = Path(dl3.value.path())
        data = json.loads(backup_path.read_text(encoding="utf-8"))
        check("H1 backup JSON memuat 13 transaksi", len(data["state"]["transaksi"]) == 13)
        data["state"]["pelanggan"].append({"id": 99, "nama": "RESTORE-TEST", "telepon": "000", "email": ""})
        restore_path = Path("/tmp/salon-restore-test.json")
        restore_path.write_text(json.dumps(data), encoding="utf-8")
        page.set_input_files("#inputRestore", str(restore_path))
        page.wait_for_timeout(400)
        check("H2 restore berhasil (toast)", page.is_visible("#toast.show") and "berhasil dipulihkan" in text(page, "#toast"))
        tab(page, "pelanggan")
        check("H3 pelanggan RESTORE-TEST muncul setelah restore", "RESTORE-TEST" in text(page, "#daftarPelanggan"))
        invalid = Path("/tmp/salon-invalid.json")
        invalid.write_text("bukan json", encoding="utf-8")
        page.set_input_files("#inputRestore", str(invalid))
        page.wait_for_timeout(400)
        check("H4 file cadangan tidak valid ditolak", "tidak valid" in text(page, "#toast"))
        tab(page, "laporan")
        page.click("#btnResetData")
        page.wait_for_timeout(200)
        konfirmasi_modal(page)
        tab(page, "dashboard")
        check("H5 reset -> dasbor seed kembali (jadwal 3, pemasukan Rp680.000)",
              "3 jadwal" in text(page, "#dJadwalHariIni") and "Rp680.000" in text(page, "#dMasukBulan"))
        check("H6 reset -> komisi belum kembali Rp151.500", "Rp151.500" in text(page, "#dKomisiBelum"))

        print("I. Peran manajer & kasir")
        logout(page)
        login(page, "manajer", "manajer123")
        check("I1 manajer masuk", "Dedi Kurniawan (Manajer)" in text(page, "#userChip"))
        check("I2 cardPengguna tersembunyi untuk manajer", not page.is_visible("#cardPengguna"))
        check("I3 cardSandiSaya terlihat untuk manajer", page.is_visible("#cardSandiSaya"))
        check("I4 manajer melihat dasbor seed penuh (pemasukan Rp680.000)", "Rp680.000" in text(page, "#dMasukBulan"))
        tab(page, "kapster")
        check("I5 cardTambahKapster terlihat untuk manajer", page.is_visible("#cardTambahKapster"))
        check("I6 input komisi terlihat untuk manajer", page.query_selector('[data-komisi-kapster="1"]') is not None)
        tab(page, "komisi")
        check("I7 tombol bayar komisi ada untuk manajer", page.query_selector("[data-bayar-komisi]") is not None)
        logout(page)
        login(page, "kasir", "kasir123")
        check("I8 kasir masuk", "Rina Kusuma (Kasir)" in text(page, "#userChip"))
        check("I9 cardPengguna tersembunyi untuk kasir", not page.is_visible("#cardPengguna"))
        check("I10 cardSandiSaya terlihat untuk kasir", page.is_visible("#cardSandiSaya"))
        tab(page, "jadwal")
        check("I11 cardTambahJadwal tersembunyi untuk kasir", not page.is_visible("#cardTambahJadwal"))
        check("I12 kasir tetap bisa Selesaikan jadwal (tombol ada)", page.query_selector('[data-selesai-jadwal="1"]') is not None)
        tab(page, "kapster")
        check("I13 cardTambahKapster tersembunyi untuk kasir", not page.is_visible("#cardTambahKapster"))
        check("I14 tidak ada input komisi untuk kasir", page.query_selector('[data-komisi-kapster="1"]') is None)
        tab(page, "komisi")
        check("I15 tidak ada tombol bayar komisi untuk kasir", page.query_selector("[data-bayar-komisi]") is None)
        tab(page, "jadwal")
        page.click('[data-selesai-jadwal="1"]')
        page.wait_for_timeout(300)
        check("I16 kasir berhasil selesaikan J1 (transaksi tercatat)", "tercatat" in text(page, "#toast"))
        tab(page, "kasir")
        check("I17 kasir: transaksi jadi 12 setelah J1 selesai", "12 transaksi" in text(page, "#ringkasanKasir"))
        logout(page)
        login(page, "admin", "admin123")
        tab(page, "laporan")
        page.click("#btnResetData")
        page.wait_for_timeout(200)
        konfirmasi_modal(page)

        print("J. Ganti kata sandi & reset admin")
        logout(page)
        login(page, "kasir", "kasir123")
        page.fill("#sandiLama", "kasir123")
        page.fill("#sandiBaru", "baru123456")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        check("J1 ganti sandi kasir berhasil", "Kata sandi berhasil diubah" in text(page, "#pesanSandi"))
        logout(page)
        login(page, "kasir", "baru123456")
        check("J2 login kasir dengan sandi baru berhasil", "Rina Kusuma (Kasir)" in text(page, "#userChip"))
        logout(page)
        login(page, "admin", "admin123")
        page.click('[data-reset="kasir"]')
        page.wait_for_timeout(200)
        konfirmasi_modal(page)
        logout(page)
        login(page, "kasir", "bk123")
        check("J3 login kasir dengan bk123 setelah reset admin", "Rina Kusuma (Kasir)" in text(page, "#userChip"))
        logout(page)
        login(page, "admin", "admin123")
        tab(page, "laporan")
        page.click("#btnResetData")
        page.wait_for_timeout(200)
        konfirmasi_modal(page)
        logout(page)
        login(page, "kasir", "kasir123")
        check("J4 setelah reset data demo, sandi kasir kembali kasir123", "Rina Kusuma (Kasir)" in text(page, "#userChip"))

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
