"""Tes Aplikasi Project Management (file lokal, Playwright Chromium).
Nilai harapan dihitung dari data seed (tenggat relatif terhadap hari ini):
Proyek: 5 (Berjalan 3, Selesai 1, Perencanaan 1)
Tugas: 14 (Selesai 5, Berjalan 4, Belum Dimulai 5, Tertunda 0)
Terlambat: TGS-007 (tenggat -1) + TGS-012 (tenggat -2) = 2
Progres keseluruhan: 5/14 = 36%
Progres proyek: PRJ-001 25%, PRJ-002 25%, PRJ-003 100%, PRJ-004 33%, PRJ-005 0%
Progres anggota: Siti 100% (3/3), Andi 33% (1/3), Dewi 0% (0/3), Rizky 0% (0/3), Maya 50% (1/2), Budi 0% (0/0)
Tenggat hari ini: TGS-006 (tenggat 0). 7 hari ke depan: TGS-002 (+3), TGS-008 (+5), TGS-013 (+7)
Laporan 30 hari (tenggat -29..0): 7 tugas, Selesai 4, Terlambat 2, Progres 57%
Laporan hari ini: 1 tugas, Selesai 0, Terlambat 0, 0%
Laporan 7 hari (tenggat -6..0): 3 tugas, Selesai 0, Terlambat 2, 0%
Laporan semua: 14 tugas, Selesai 5, Terlambat 2, 36%
Anggota demo (Andi, id 3): TGS-002, TGS-006, TGS-011 = 3 tugas
"""
import sys
from datetime import date, timedelta
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = "file://" + str(ROOT / "project-management" / "index.html")
HARI_INI = date.today().isoformat()
LIMA_HARI = (date.today() + timedelta(days=5)).isoformat()
DUAPULUH_HARI = (date.today() + timedelta(days=20)).isoformat()

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
        check("judul halaman", "Project Management" in page.title())
        check("overlay login tampil", page.is_visible("#loginOverlay"))
        check("akun demo admin tampil", "admin123" in text(page, ".login-note"))
        check("akun demo manajer tampil", "manajer123" in text(page, ".login-note"))
        check("akun demo anggota tampil", "anggota123" in text(page, ".login-note"))
        check("harga Basic Rp499.000 di Panduan", "Rp499.000" in text(page, "#panel-panduan"))
        check("harga APK +Rp400.000 di Panduan", "Rp400.000" in text(page, "#panel-panduan"))
        check("garansi 30/60/90 hari di Panduan", "30 hari" in text(page, "#panel-panduan") and "90 hari" in text(page, "#panel-panduan"))
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
        check("total proyek 5", text(page, "#dProyek") == "5", text(page, "#dProyek"))
        check("sub proyek Berjalan 3 Selesai 1", "Berjalan 3" in text(page, "#dProyekSub") and "Selesai 1" in text(page, "#dProyekSub"), text(page, "#dProyekSub"))
        check("total tugas 14", text(page, "#dTugas") == "14", text(page, "#dTugas"))
        check("sub tugas Selesai 5 Berjalan 4", "Selesai 5" in text(page, "#dTugasSub") and "Berjalan 4" in text(page, "#dTugasSub"), text(page, "#dTugasSub"))
        check("terlambat 2", text(page, "#dTerlambat") == "2", text(page, "#dTerlambat"))
        check("progres keseluruhan 36%", text(page, "#dProgres") == "36%", text(page, "#dProgres"))
        check("badge proyek 5", text(page, "#badgeProyek") == "5", text(page, "#badgeProyek"))
        check("badge tugas 14", text(page, "#badgeTugas") == "14", text(page, "#badgeTugas"))
        check("badge tim 6", text(page, "#badgeTim") == "6", text(page, "#badgeTim"))
        perhatian = text(page, "#daftarPerhatian")
        check("perhatian ada PRJ-004 tenggat lewat", "PRJ-004" in perhatian and "Tenggat proyek lewat" in perhatian, perhatian)
        check("perhatian ada TGS-007 terlambat", "TGS-007" in perhatian and "Terlambat" in perhatian, perhatian)
        check("perhatian ada TGS-012 terlambat", "TGS-012" in perhatian, perhatian)
        hari = text(page, "#daftarHariIni")
        check("hari ini ada TGS-006", "TGS-006" in hari, hari)
        terbaru = text(page, "#daftarTugasTerbaru")
        check("terbaru ada TGS-014", "TGS-014" in terbaru, terbaru)
        check("terbaru ada TGS-010", "TGS-010" in terbaru, terbaru)

        print("== 3. Proyek: progres per proyek ==")
        klik_tab(page, "proyek")
        check("ringkasan 5 proyek", "5 proyek" in text(page, "#ringkasanProyek"), text(page, "#ringkasanProyek"))
        daftar = text(page, "#daftarProyek")
        check("PRJ-001 progres 25%", "PRJ-001" in daftar and "25%" in daftar, daftar)
        check("PRJ-003 progres 100%", "PRJ-003" in daftar and "100%" in daftar, daftar)
        check("PRJ-004 progres 33%", "PRJ-004" in daftar and "33%" in daftar, daftar)
        check("PRJ-005 progres 0%", "PRJ-005" in daftar and "0%" in daftar, daftar)
        check("PRJ-004 ada label Tenggat lewat", "PRJ-004" in daftar and "Tenggat lewat" in daftar, daftar)

        print("== 4. Tugas: filter + cari ==")
        klik_tab(page, "tugas")
        page.select_option("#fTgStatus", "Selesai")
        page.wait_for_timeout(300)
        check("filter Selesai -> 5 tugas", "5 tugas" in text(page, "#ringkasanTugas"), text(page, "#ringkasanTugas"))
        check("filter Selesai ada TGS-001, tidak ada TGS-002", "TGS-001" in text(page, "#daftarTugas") and "TGS-002" not in text(page, "#daftarTugas"), text(page, "#daftarTugas"))
        page.select_option("#fTgStatus", "semua")
        page.select_option("#fTgProyek", "2")
        page.wait_for_timeout(300)
        check("filter PRJ-002 -> 4 tugas", "4 tugas" in text(page, "#ringkasanTugas"), text(page, "#ringkasanTugas"))
        page.select_option("#fTgProyek", "semua")
        page.select_option("#fTgAnggota", "4")
        page.wait_for_timeout(300)
        check("filter Dewi -> 3 tugas", "3 tugas" in text(page, "#ringkasanTugas"), text(page, "#ringkasanTugas"))
        check("filter Dewi ada TGS-007 + TGS-012", "TGS-007" in text(page, "#daftarTugas") and "TGS-012" in text(page, "#daftarTugas"), text(page, "#daftarTugas"))
        page.select_option("#fTgAnggota", "semua")
        page.fill("#cariTg", "barcode")
        page.wait_for_timeout(300)
        check("cari barcode -> TGS-006 saja", "TGS-006" in text(page, "#daftarTugas") and "TGS-007" not in text(page, "#daftarTugas"), text(page, "#daftarTugas"))
        page.fill("#cariTg", "")
        page.wait_for_timeout(300)

        print("== 5. Tim ==")
        klik_tab(page, "tim")
        check("ringkasan 6 anggota", "6 anggota" in text(page, "#ringkasanTim"), text(page, "#ringkasanTim"))
        tim = text(page, "#daftarTim")
        check("Siti 3 tugas 3 selesai", "Siti Rahma" in tim and "3 tugas (0 aktif, 3 selesai)" in tim, tim)
        check("Andi 3 tugas 1 selesai", "Andi Pratama" in tim and "3 tugas (2 aktif, 1 selesai)" in tim, tim)
        check("Dewi ada 2 terlambat", "Dewi Lestari" in tim and "2 terlambat" in tim, tim)
        check("Budi 0 tugas", "Budi Santoso" in tim and "0 tugas" in tim, tim)

        print("== 6. Tenggat ==")
        klik_tab(page, "tenggat")
        check("terlambat ada TGS-007 + TGS-012", "TGS-007" in text(page, "#daftarTerlambat") and "TGS-012" in text(page, "#daftarTerlambat"), text(page, "#daftarTerlambat"))
        check("hari ini ada TGS-006", "TGS-006" in text(page, "#daftarTenggatHariIni"), text(page, "#daftarTenggatHariIni"))
        minggu = text(page, "#daftarMingguDepan")
        check("minggu depan ada TGS-002", "TGS-002" in minggu, minggu)
        check("minggu depan ada TGS-008", "TGS-008" in minggu, minggu)
        check("minggu depan ada TGS-013", "TGS-013" in minggu, minggu)
        check("minggu depan tidak ada TGS-006 (hari ini)", "TGS-006" not in minggu, minggu)

        print("== 7. Progres ==")
        klik_tab(page, "progres")
        prog = text(page, "#daftarProgresProyek")
        check("progres PRJ-002 25%", "PRJ-002" in prog and "25%" in prog, prog)
        check("progres PRJ-003 100%", "PRJ-003" in prog and "100%" in prog, prog)
        ang = text(page, "#daftarProgresAnggota")
        check("progres Siti 100%", "Siti Rahma" in ang and "100%" in ang, ang)
        check("progres Andi 33%", "Andi Pratama" in ang and "33%" in ang, ang)
        check("progres Maya 50%", "Maya Kusuma" in ang and "50%" in ang, ang)
        check("progres Dewi 0%", "Dewi Lestari" in ang and "0%" in ang, ang)

        print("== 8. Laporan + ekspor ==")
        klik_tab(page, "laporan")
        check("laporan 30 hari jumlah 7", text(page, "#lJumlah") == "7", text(page, "#lJumlah"))
        check("laporan 30 hari selesai 4", text(page, "#lSelesai") == "4", text(page, "#lSelesai"))
        check("laporan 30 hari terlambat 2", text(page, "#lTerlambat") == "2", text(page, "#lTerlambat"))
        check("laporan 30 hari progres 57%", text(page, "#lProgres") == "57%", text(page, "#lProgres"))
        tabel = text(page, "#tabelLaporan")
        check("tabel ada Selesai 4", "Selesai" in tabel and "4" in tabel, tabel)
        check("tabel ada Berjalan 3", "Berjalan" in tabel and "3" in tabel, tabel)
        lap_pr = text(page, "#daftarLaporanProyek")
        check("laporan proyek PRJ-002 ada", "PRJ-002" in lap_pr, lap_pr)
        page.select_option("#lapPeriode", "hari")
        page.wait_for_timeout(300)
        check("laporan hari ini jumlah 1", text(page, "#lJumlah") == "1", text(page, "#lJumlah"))
        check("laporan hari ini selesai 0", text(page, "#lSelesai") == "0", text(page, "#lSelesai"))
        page.select_option("#lapPeriode", "7hari")
        page.wait_for_timeout(300)
        check("laporan 7 hari jumlah 3", text(page, "#lJumlah") == "3", text(page, "#lJumlah"))
        check("laporan 7 hari terlambat 2", text(page, "#lTerlambat") == "2", text(page, "#lTerlambat"))
        page.select_option("#lapPeriode", "semua")
        page.wait_for_timeout(300)
        check("laporan semua jumlah 14", text(page, "#lJumlah") == "14", text(page, "#lJumlah"))
        check("laporan semua selesai 5", text(page, "#lSelesai") == "5", text(page, "#lSelesai"))
        check("laporan semua progres 36%", text(page, "#lProgres") == "36%", text(page, "#lProgres"))
        page.select_option("#lapPeriode", "30hari")
        page.wait_for_timeout(300)
        with page.expect_download() as dl_info:
            page.click("#btnExportCSV")
        csv_isi = Path(dl_info.value.path()).read_text(encoding="utf-8")
        check("CSV berisi TGS-001", "TGS-001" in csv_isi, csv_isi[:200])
        check("CSV berisi TGS-007 + Berjalan", "TGS-007" in csv_isi and "Berjalan" in csv_isi, csv_isi[:200])
        check("CSV tidak berisi TGS-009 (di luar 30 hari)", "TGS-009" not in csv_isi, csv_isi[:200])
        with page.expect_download() as dl_info:
            page.click("#btnBackupJSON")
        json_isi = Path(dl_info.value.path()).read_text(encoding="utf-8")
        check("backup JSON berisi project-management", "project-management" in json_isi, json_isi[:200])
        check("backup JSON berisi TGS-001", "TGS-001" in json_isi, json_isi[:200])

        print("== 9. Detail tugas + komentar + ubah status ==")
        klik_tab(page, "tugas")
        page.click('[data-aksi-tugas="detail"][data-id="2"]')
        page.wait_for_timeout(400)
        check("modal detail tampil", page.is_visible("#mdStatus"))
        check("modal ada komentar Budi", "Budi Santoso" in text(page, "#mdDaftarKomentar"), text(page, "#mdDaftarKomentar"))
        check("modal ada komentar Andi", "Andi Pratama" in text(page, "#mdDaftarKomentar"), text(page, "#mdDaftarKomentar"))
        page.select_option("#mdStatus", "Selesai")
        page.fill("#mdKomentarBaru", "Katalog selesai, lanjut ke pencarian.")
        page.click("#mdSimpan")
        page.wait_for_timeout(400)
        check("simpan detail -> toast diperbarui", "diperbarui" in text(page, "#toast"), text(page, "#toast"))
        page.click('[data-aksi-tugas="detail"][data-id="2"]')
        page.wait_for_timeout(400)
        check("komentar baru tersimpan (3 komentar)", "Katalog selesai" in text(page, "#mdDaftarKomentar"), text(page, "#mdDaftarKomentar"))
        check("status TGS-002 jadi Selesai di modal", page.input_value("#mdStatus") == "Selesai", page.input_value("#mdStatus"))
        page.keyboard.press("Escape")
        page.click("#modalBatal")
        page.wait_for_timeout(300)
        klik_tab(page, "dashboard")
        check("dasbor selesai jadi 6 setelah TGS-002 selesai", "Selesai 6" in text(page, "#dTugasSub"), text(page, "#dTugasSub"))

        print("== 10. Buat tugas + proyek baru ==")
        klik_tab(page, "tugas")
        page.select_option("#tgProyek", "1")
        page.fill("#tgNama", "Buat halaman tentang kami")
        page.select_option("#tgAnggota", "2")
        page.fill("#tgTenggat", LIMA_HARI)
        page.select_option("#tgPrioritas", "Sedang")
        page.click("#btnSimpanTugas")
        page.wait_for_timeout(400)
        check("tugas baru tersimpan TGS-015", "TGS-015" in text(page, "#toast"), text(page, "#toast"))
        check("badge tugas jadi 15", text(page, "#badgeTugas") == "15", text(page, "#badgeTugas"))
        page.fill("#cariTg", "tentang kami")
        page.wait_for_timeout(300)
        check("daftar ada TGS-015", "TGS-015" in text(page, "#daftarTugas"), text(page, "#daftarTugas"))
        page.fill("#cariTg", "")
        klik_tab(page, "proyek")
        page.fill("#prNama", "Website Company Profile")
        page.fill("#prTenggat", DUAPULUH_HARI)
        page.click("#btnSimpanProyek")
        page.wait_for_timeout(400)
        check("proyek baru tersimpan PRJ-006", "PRJ-006" in text(page, "#toast"), text(page, "#toast"))
        check("badge proyek jadi 6", text(page, "#badgeProyek") == "6", text(page, "#badgeProyek"))
        page.click('[data-aksi-proyek="mulai"][data-id="5"]')
        page.wait_for_timeout(400)
        check("PRJ-005 dimulai", "dimulai" in text(page, "#toast"), text(page, "#toast"))

        print("== 11. RBAC manajer ==")
        logout(page)
        login(page, "manajer", "manajer123")
        check("login manajer berhasil", "Manajer (Manajer)" in text(page, "#userChip"))
        klik_tab(page, "dashboard")
        check("manajer tidak melihat kelola pengguna", not page.is_visible("#cardPengguna"))
        check("manajer melihat kartu ganti sandi", page.is_visible("#cardSandiSaya"))
        check("manajer melihat tab Proyek", page.is_visible('[data-tab="proyek"]'))
        check("manajer melihat tab Tim", page.is_visible('[data-tab="tim"]'))
        check("manajer melihat tab Laporan", page.is_visible('[data-tab="laporan"]'))
        klik_tab(page, "proyek")
        check("manajer melihat kartu tambah proyek", page.is_visible("#cardTambahProyek"))

        print("== 12. RBAC anggota: hanya tugas sendiri ==")
        logout(page)
        login(page, "anggota", "anggota123")
        check("login anggota berhasil", "Anggota (Andi) (Anggota)" in text(page, "#userChip"))
        check("anggota TIDAK melihat tab Proyek", not page.is_visible('[data-tab="proyek"]'))
        check("anggota TIDAK melihat tab Tim", not page.is_visible('[data-tab="tim"]'))
        check("anggota TIDAK melihat tab Laporan", not page.is_visible('[data-tab="laporan"]'))
        check("anggota melihat tab Tugas", page.is_visible('[data-tab="tugas"]'))
        check("anggota TIDAK melihat kelola pengguna", not page.is_visible("#cardPengguna"))
        check("anggota melihat kartu ganti sandi", page.is_visible("#cardSandiSaya"))
        klik_tab(page, "tugas")
        check("anggota TIDAK melihat kartu tambah tugas", not page.is_visible("#cardTambahTugas"))
        check("anggota hanya 3 tugas", "3 tugas" in text(page, "#ringkasanTugas"), text(page, "#ringkasanTugas"))
        check("anggota melihat TGS-006 (miliknya)", "TGS-006" in text(page, "#daftarTugas"), text(page, "#daftarTugas"))
        check("anggota TIDAK melihat TGS-007 (bukan miliknya)", "TGS-007" not in text(page, "#daftarTugas"), text(page, "#daftarTugas"))
        klik_tab(page, "dashboard")
        page.fill("#sandiLama", "anggota123")
        page.fill("#sandiBaru", "anggota456")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(400)
        check("anggota ganti sandi berhasil", "berhasil diganti" in text(page, "#toast"), text(page, "#toast"))
        logout(page)
        login(page, "anggota", "anggota123")
        check("sandi lama anggota ditolak", page.is_visible("#loginError"))
        login(page, "anggota", "anggota456")
        check("sandi baru anggota diterima", "Anggota (Andi)" in text(page, "#userChip"))
        logout(page)
        login(page, "anggota", "anggota456")
        page.fill("#sandiLama", "anggota456")
        page.fill("#sandiBaru", "anggota123")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(400)
        check("anggota kembalikan sandi", "berhasil diganti" in text(page, "#toast"), text(page, "#toast"))

        print("== 13. Admin reset sandi manajer -> bk123 ==")
        logout(page)
        login(page, "admin", "admin123")
        klik_tab(page, "dashboard")
        page.click('[data-aksi-pengguna="sandi"][data-user="manajer"]')
        page.wait_for_timeout(300)
        page.click("#modalYa")
        page.wait_for_timeout(400)
        check("reset sandi manajer ke bk123", "bk123" in text(page, "#toast"), text(page, "#toast"))
        logout(page)
        login(page, "manajer", "manajer123")
        check("sandi lama manajer ditolak", page.is_visible("#loginError"))
        login(page, "manajer", "bk123")
        check("manajer masuk dengan bk123", "Manajer (Manajer)" in text(page, "#userChip"))

        print("== 14. Reset data contoh ==")
        logout(page)
        login(page, "admin", "admin123")
        reset_data(page)
        check("reset: total proyek 5", text(page, "#dProyek") == "5", text(page, "#dProyek"))
        check("reset: total tugas 14", text(page, "#dTugas") == "14", text(page, "#dTugas"))
        check("reset: terlambat 2", text(page, "#dTerlambat") == "2", text(page, "#dTerlambat"))
        check("reset: progres 36%", text(page, "#dProgres") == "36%", text(page, "#dProgres"))
        check("reset: badge proyek 5", text(page, "#badgeProyek") == "5", text(page, "#badgeProyek"))
        check("reset: badge tugas 14", text(page, "#badgeTugas") == "14", text(page, "#badgeTugas"))

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
