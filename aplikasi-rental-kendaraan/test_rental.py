"""Tes Aplikasi Rental Kendaraan (file lokal, Playwright Chromium).
Nilai harapan dihitung independen (Python, dari harga seed):
RNT-001 Avanza 3 hari x 350rb = 1.050.000 (Aktif)
RNT-002 Beat 3 hari x 75rb = 225.000, terlambat 1 hari, denda 50.000 (Aktif)
RNT-003 Innova 3 hari x 550rb = 1.650.000 (Selesai, denda 0)
RNT-004 Brio 3 hari x 300rb = 900.000 + denda 100.000 = 1.000.000 (Selesai)
RNT-005 Xpander 4 hari x 450rb = 1.800.000 (Dipesan)
RNT-006 PCX 2 hari x 150rb = 300.000 (Selesai)
RNT-007 Calya 4 hari x 300rb = 1.200.000 (Selesai)
RNT-008 HR-V 4 hari x 500rb = 2.000.000 (Dipesan)
RNT-009 Vario 3 hari x 100rb = 300.000 + denda 50.000 = 350.000 (Selesai)
RNT-010 Aerox Batal (tidak dihitung)
Pendapatan 30 hari (Selesai): 1.650.000+1.000.000+300.000+1.200.000+350.000 = 4.500.000
Total denda 30 hari: 100.000+50.000 (Selesai) + 50.000 (RNT-002 berjalan) = 200.000
Aktif 2 | Terlambat 1 | Dipesan 2 | Selesai 5 | Batal 1 | Total 10
Kendaraan: 12 (Tersedia 9, Disewa 2, Perawatan 1)
"""
import json
import sys
from datetime import date, timedelta
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = "file://" + str(ROOT / "aplikasi-rental-kendaraan" / "index.html")
HARI_INI = date.today().isoformat()
DUA_HARI = (date.today() + timedelta(days=2)).isoformat()

failures = []
passed = 0


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


def klik_tab(page, tab):
    page.click(f'[data-tab="{tab}"]')
    page.wait_for_timeout(300)


def reset_data(page):
    klik_tab(page, "panduan")
    page.click("#btnResetData")
    page.wait_for_timeout(300)
    page.click("#modalYa")
    page.wait_for_timeout(500)
    klik_tab(page, "dashboard")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        errors = []
        ctx = browser.new_context(accept_downloads=True)
        page = ctx.new_page()
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.goto(URL)
        page.wait_for_timeout(500)

        print("== 1. Muat + login ==")
        check("judul halaman", "Rental Kendaraan" in page.title())
        check("overlay login tampil", page.is_visible("#loginOverlay"))
        check("akun demo admin tampil", "admin123" in text(page, ".login-note"))
        check("akun demo kasir tampil", "kasir123" in text(page, ".login-note"))
        check("akun demo mekanik tampil", "mekanik123" in text(page, ".login-note"))
        check("harga Basic Rp499.000 di Panduan", "Rp499.000" in text(page, "#panel-panduan"))
        check("harga APK +Rp400.000 di Panduan", "Rp400.000" in text(page, "#panel-panduan"))
        check("garansi 30/60/90 hari di Panduan", "30 hari" in text(page, "#panel-panduan") and "90 hari" in text(page, "#panel-panduan"))
        check("catatan jujur deposit jaminan", "jaminan" in text(page, "#panel-panduan"))
        check("catatan jujur hanya tersimpan di perangkat", "hanya tersimpan di perangkat ini" in text(page, "#panel-panduan"))
        check("catatan jujur bukan payment gateway", "bukan" in text(page, "#panel-panduan") and "payment gateway" in text(page, "#panel-panduan"))
        page.fill("#loginUser", "admin")
        page.fill("#loginPass", "salah")
        page.click("#formLogin button[type=submit]")
        page.wait_for_timeout(300)
        check("login salah -> error tampil", page.is_visible("#loginError"))
        login(page, "admin", "admin123")
        check("login admin berhasil", "Admin (Admin)" in text(page, "#userChip"))
        check("overlay login hilang", not page.is_visible("#loginOverlay"))
        check("kartu kelola pengguna tampil untuk admin", page.is_visible("#cardPengguna"))
        check("kartu ganti sandi tampil untuk admin", page.is_visible("#cardSandiSaya"))

        print("== 2. Dasbor admin (nilai seed) ==")
        check("sewa aktif 2", text(page, "#dAktif") == "2", text(page, "#dAktif"))
        check("pendapatan 30 hari Rp4.500.000", text(page, "#dPendapatan") == "Rp4.500.000", text(page, "#dPendapatan"))
        check("terlambat kembali 1", text(page, "#dTerlambat") == "1", text(page, "#dTerlambat"))
        check("dipesan 2", text(page, "#dDipesan") == "2", text(page, "#dDipesan"))
        check("badge kendaraan 12", text(page, "#badgeKend") == "12", text(page, "#badgeKend"))
        check("badge sewa 10", text(page, "#badgeSewa") == "10", text(page, "#badgeSewa"))
        perhatian = text(page, "#daftarPerhatian")
        check("perhatian ada RNT-002 terlambat", "RNT-002" in perhatian and "Terlambat 1 hari" in perhatian, perhatian)
        check("perhatian ada RNT-001 ambil hari ini", "RNT-001" in perhatian, perhatian)
        terbaru = text(page, "#daftarSewaTerbaru")
        check("terbaru ada RNT-008", "RNT-008" in terbaru, terbaru)
        check("terbaru ada RNT-005", "RNT-005" in terbaru, terbaru)
        check("terbaru RNT-001 Rp1.050.000", "RNT-001" in terbaru and "Rp1.050.000" in terbaru, terbaru)

        print("== 3. Kendaraan: ringkasan + filter + cari ==")
        klik_tab(page, "kendaraan")
        ring = text(page, "#ringkasanKendaraan")
        check("ringkasan 12 kendaraan", "12 kendaraan" in ring, ring)
        check("ringkasan Tersedia 9", "Tersedia 9" in ring, ring)
        check("ringkasan Disewa 2", "Disewa 2" in ring, ring)
        check("ringkasan Perawatan 1", "Perawatan 1" in ring, ring)
        page.select_option("#fKnStatus", "Disewa")
        page.wait_for_timeout(300)
        daftar = text(page, "#daftarKendaraan")
        check("filter Disewa -> Avanza + Beat", "B 1234 ABC" in daftar and "B 8901 VWX" in daftar and "B 5678 DEF" not in daftar, daftar)
        page.select_option("#fKnStatus", "Perawatan")
        page.wait_for_timeout(300)
        daftar = text(page, "#daftarKendaraan")
        check("filter Perawatan -> NMAX saja", "B 1122 BCD" in daftar and "B 1234 ABC" not in daftar, daftar)
        page.select_option("#fKnStatus", "semua")
        page.fill("#cariKn", "Innova")
        page.wait_for_timeout(300)
        daftar = text(page, "#daftarKendaraan")
        check("cari Innova -> B 5678 DEF Rp550.000/hari", "B 5678 DEF" in daftar and "Rp550.000/hari" in daftar, daftar)
        page.fill("#cariKn", "")
        page.wait_for_timeout(300)

        print("== 4. Sewa: filter + cari + denda ==")
        klik_tab(page, "sewa")
        page.select_option("#fSwStatus", "Selesai")
        page.wait_for_timeout(300)
        ring = text(page, "#ringkasanSewa")
        check("filter Selesai: 5 sewa", "5 sewa" in ring, ring)
        check("filter Selesai: total Rp4.500.000", "Rp4.500.000" in ring, ring)
        page.select_option("#fSwStatus", "semua")
        page.fill("#cariSw", "Innova")
        page.wait_for_timeout(300)
        daftar = text(page, "#daftarSewa")
        check("cari Innova -> RNT-003", "RNT-003" in daftar and "RNT-001" not in daftar, daftar)
        page.fill("#cariSw", "")
        page.wait_for_timeout(300)
        daftar = text(page, "#daftarSewa")
        check("daftar ada RNT-002 denda Rp50.000", "RNT-002" in daftar and "Rp50.000" in daftar, daftar)
        check("daftar ada RNT-004 total Rp1.000.000", "RNT-004" in daftar and "Rp1.000.000" in daftar, daftar)
        check("daftar ada RNT-010 Batal", "RNT-010" in daftar and "Batal" in daftar, daftar)

        print("== 5. Jadwal ==")
        klik_tab(page, "jadwal")
        telat = text(page, "#daftarTerlambat")
        check("terlambat ada RNT-002", "RNT-002" in telat, telat)
        hari = text(page, "#daftarHariIni")
        check("hari ini ada RNT-001 ambil", "RNT-001" in hari and "Ambil" in hari, hari)
        minggu = text(page, "#daftarMingguDepan")
        check("minggu depan ada RNT-005 ambil", "RNT-005" in minggu and "Ambil" in minggu, minggu)
        check("minggu depan ada RNT-008 ambil", "RNT-008" in minggu, minggu)
        check("minggu depan ada RNT-001 kembali", "RNT-001" in minggu and "Kembali" in minggu, minggu)
        check("minggu depan tidak ada RNT-003 selesai", "RNT-003" not in minggu, minggu)

        print("== 6. Laporan 30 hari + ekspor ==")
        klik_tab(page, "laporan")
        check("laporan jumlah 10", text(page, "#lJumlah") == "10", text(page, "#lJumlah"))
        check("laporan pendapatan Rp4.500.000", text(page, "#lNilai") == "Rp4.500.000", text(page, "#lNilai"))
        check("laporan total denda Rp200.000", text(page, "#lDenda") == "Rp200.000", text(page, "#lDenda"))
        check("laporan sewa aktif 2", text(page, "#lAktif") == "2", text(page, "#lAktif"))
        tabel = text(page, "#tabelLaporan")
        check("tabel ada Selesai 5 / Rp4.500.000", "Selesai" in tabel and "Rp4.500.000" in tabel, tabel)
        check("tabel ada Dipesan 2 / Rp3.800.000", "Dipesan" in tabel and "Rp3.800.000" in tabel, tabel)
        terlaris = text(page, "#daftarTerlaris")
        check("terlaris ada Innova Rp1.650.000", "B 5678 DEF" in terlaris and "Rp1.650.000" in terlaris, terlaris)
        page.select_option("#lapPeriode", "hari")
        page.wait_for_timeout(300)
        check("laporan hari ini jumlah 1", text(page, "#lJumlah") == "1", text(page, "#lJumlah"))
        page.select_option("#lapPeriode", "30hari")
        page.wait_for_timeout(300)
        with page.expect_download() as dl_info:
            page.click("#btnExportCSV")
        dl = dl_info.value
        csv_path = dl.path()
        csv_isi = Path(csv_path).read_text(encoding="utf-8")
        check("CSV berisi RNT-001", "RNT-001" in csv_isi, csv_isi[:200])
        check("CSV berisi RNT-004 + denda 100000", "RNT-004" in csv_isi and "100000" in csv_isi, csv_isi[:200])
        with page.expect_download() as dl_info:
            page.click("#btnBackupJSON")
        dl = dl_info.value
        json_isi = Path(dl.path()).read_text(encoding="utf-8")
        check("backup JSON berisi rental-kendaraan", "rental-kendaraan" in json_isi, json_isi[:200])
        check("backup JSON berisi RNT-003", "RNT-003" in json_isi, json_isi[:200])

        print("== 7. Buat sewa baru -> Aktif -> Pengembalian ==")
        klik_tab(page, "sewa")
        page.select_option("#swKendaraan", "3")
        page.select_option("#swPelanggan", "1")
        page.fill("#swAmbil", HARI_INI)
        page.fill("#swKembali", DUA_HARI)
        page.fill("#swDeposit", "500000")
        page.wait_for_timeout(300)
        check("total form Rp900.000 (3 hari x Rp300.000)", "Rp900.000" in text(page, "#swTotal"), text(page, "#swTotal"))
        page.click("#btnSimpanDipesan")
        page.wait_for_timeout(400)
        check("sewa baru tersimpan Dipesan", "RNT-011" in text(page, "#toast"), text(page, "#toast"))
        check("badge sewa jadi 11", text(page, "#badgeSewa") == "11", text(page, "#badgeSewa"))
        daftar = text(page, "#daftarSewa")
        check("daftar ada RNT-011 Dipesan Rp900.000", "RNT-011" in daftar and "Rp900.000" in daftar, daftar)
        page.click('[data-aksi-sewa="aktifkan"][data-id="11"]')
        page.wait_for_timeout(400)
        check("RNT-011 jadi Aktif", "Aktif" in text(page, "#toast"), text(page, "#toast"))
        klik_tab(page, "kendaraan")
        page.fill("#cariKn", "Brio")
        page.wait_for_timeout(300)
        check("Brio jadi Disewa", "Disewa" in text(page, "#daftarKendaraan"), text(page, "#daftarKendaraan"))
        page.fill("#cariKn", "")
        klik_tab(page, "sewa")
        page.click('[data-aksi-sewa="kembali"][data-id="11"]')
        page.wait_for_timeout(400)
        check("modal pengembalian tampil", page.is_visible("#kmTanggal"))
        check("modal denda Rp0 (tepat waktu)", "Rp0" in text(page, "#kmDendaInfo"), text(page, "#kmDendaInfo"))
        page.fill("#kmTanggal", DUA_HARI)
        page.fill("#kmKondisi", "Baik, bersih")
        page.click("#kmSimpan")
        page.wait_for_timeout(500)
        check("pengembalian selesai Rp900.000", "Rp900.000" in text(page, "#toast"), text(page, "#toast"))
        klik_tab(page, "dashboard")
        check("pendapatan jadi Rp5.400.000", text(page, "#dPendapatan") == "Rp5.400.000", text(page, "#dPendapatan"))
        check("sewa aktif kembali 2", text(page, "#dAktif") == "2", text(page, "#dAktif"))

        print("== 8. Teks WA sewa ==")
        klik_tab(page, "sewa")
        page.fill("#cariSw", "RNT-001")
        page.wait_for_timeout(300)
        page.click('[data-aksi-sewa="wa"][data-id="1"]')
        page.wait_for_timeout(400)
        check("salin teks WA berhasil", "Teks WA disalin" in text(page, "#toast"), text(page, "#toast"))
        page.fill("#cariSw", "")
        page.wait_for_timeout(300)

        print("== 9. RBAC kasir ==")
        logout(page)
        login(page, "kasir", "kasir123")
        check("login kasir berhasil", "Kasir (Kasir)" in text(page, "#userChip"))
        klik_tab(page, "dashboard")
        check("kasir tidak melihat kelola pengguna", not page.is_visible("#cardPengguna"))
        check("kasir melihat kartu ganti sandi", page.is_visible("#cardSandiSaya"))
        check("kasir melihat tab Sewa", page.is_visible('[data-tab="sewa"]'))
        check("kasir melihat tab Laporan", page.is_visible('[data-tab="laporan"]'))

        print("== 10. RBAC mekanik: kartu sandi selalu terlihat ==")
        logout(page)
        login(page, "mekanik", "mekanik123")
        check("login mekanik berhasil", "Mekanik (Agus)" in text(page, "#userChip"))
        check("mekanik TIDAK melihat tab Sewa", not page.is_visible('[data-tab="sewa"]'))
        check("mekanik TIDAK melihat tab Laporan", not page.is_visible('[data-tab="laporan"]'))
        check("mekanik melihat tab Kendaraan", page.is_visible('[data-tab="kendaraan"]'))
        check("mekanik melihat tab Jadwal", page.is_visible('[data-tab="jadwal"]'))
        check("mekanik TIDAK melihat kelola pengguna", not page.is_visible("#cardPengguna"))
        check("mekanik melihat kartu ganti sandi", page.is_visible("#cardSandiSaya"))
        klik_tab(page, "kendaraan")
        check("mekanik TIDAK melihat kartu tambah kendaraan", not page.is_visible("#cardTambahKendaraan"))
        klik_tab(page, "dashboard")
        page.fill("#sandiLama", "mekanik123")
        page.fill("#sandiBaru", "mekanik456")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(400)
        check("mekanik ganti sandi berhasil", "berhasil diganti" in text(page, "#toast"), text(page, "#toast"))
        logout(page)
        login(page, "mekanik", "mekanik123")
        check("sandi lama mekanik ditolak", page.is_visible("#loginError"))
        login(page, "mekanik", "mekanik456")
        check("sandi baru mekanik diterima", "Mekanik (Agus)" in text(page, "#userChip"))
        logout(page)
        login(page, "mekanik", "mekanik456")
        page.fill("#sandiLama", "mekanik456")
        page.fill("#sandiBaru", "mekanik123")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(400)
        check("mekanik kembalikan sandi", "berhasil diganti" in text(page, "#toast"), text(page, "#toast"))

        print("== 11. Admin reset sandi kasir -> bk123 ==")
        logout(page)
        login(page, "admin", "admin123")
        klik_tab(page, "dashboard")
        page.click('[data-aksi-pengguna="sandi"][data-user="kasir"]')
        page.wait_for_timeout(300)
        page.click("#modalYa")
        page.wait_for_timeout(400)
        check("reset sandi kasir ke bk123", "bk123" in text(page, "#toast"), text(page, "#toast"))
        logout(page)
        login(page, "kasir", "kasir123")
        check("sandi lama kasir ditolak", page.is_visible("#loginError"))
        login(page, "kasir", "bk123")
        check("kasir masuk dengan bk123", "Kasir (Kasir)" in text(page, "#userChip"))

        print("== 12. Reset data contoh ==")
        logout(page)
        login(page, "admin", "admin123")
        reset_data(page)
        check("reset: sewa aktif 2", text(page, "#dAktif") == "2", text(page, "#dAktif"))
        check("reset: pendapatan Rp4.500.000", text(page, "#dPendapatan") == "Rp4.500.000", text(page, "#dPendapatan"))
        check("reset: terlambat 1", text(page, "#dTerlambat") == "1", text(page, "#dTerlambat"))
        check("reset: badge sewa 10", text(page, "#badgeSewa") == "10", text(page, "#badgeSewa"))
        check("reset: badge kendaraan 12", text(page, "#badgeKend") == "12", text(page, "#badgeKend"))

        print(f"\n== HASIL: {passed} lolos, {len(failures)} gagal ==")
        if failures:
            print("GAGAL:", failures)
        check("tanpa console error / pageerror", len(errors) == 0, str(errors[:5]))
        browser.close()
        if failures:
            sys.exit(1)
        print("SEMUA TES LOLOS")


if __name__ == "__main__":
    main()
