"""Tes Aplikasi Riwayat Kendaraan (file lokal, Playwright Chromium)."""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = "file://" + str(ROOT / "aplikasi-riwayat-kendaraan" / "index.html")

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


def count(page, sel):
    return page.locator(sel).count()


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
        page = browser.new_page()
        errors = []
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(URL)
        page.wait_for_timeout(500)

        # 1. Login salah ditolak
        login(page, "admin", "salah")
        check("login salah ditolak", page.is_visible("#loginError"))
        # 2. Login admin benar
        login(page, "admin", "admin123")
        check("login admin berhasil", not page.is_visible("#loginOverlay"))
        check("chip pengguna Admin", "Admin (Admin)" in text(page, "#userChip"))
        check("judul Riwayat Kendaraan", "Riwayat Kendaraan" in page.title())
        check("localStorage terisi", page.evaluate("() => !!localStorage.getItem('aplikasiRiwayatKendaraan.v1')"))

        # 3. Dasbor data contoh
        check("dasbor kendaraan 12", text(page, "#dKendaraan").strip() == "12", text(page, "#dKendaraan"))
        check("dasbor riwayat 15", text(page, "#dRiwayat").strip() == "15", text(page, "#dRiwayat"))
        check("dasbor pengingat jatuh tempo 6", text(page, "#dPengingat").strip() == "6", text(page, "#dPengingat"))
        check("dasbor biaya 30 hari Rp1.335.000", text(page, "#dBiaya30").strip() == "Rp1.335.000", text(page, "#dBiaya30"))
        check("badge riwayat 21", text(page, "#badgeRiwayat").strip() == "21", text(page, "#badgeRiwayat"))
        check("badge pengingat 7", text(page, "#badgePengingat").strip() == "7", text(page, "#badgePengingat"))
        check("dasbor pengingat ada Brio jatuh tempo", "B 2345 GHI" in text(page, "#daftarPengingatDasbor"))
        check("dasbor riwayat terbaru ada RW-005", "RW-005" in text(page, "#daftarRiwayatDasbor"))
        check("dasbor riwayat terbaru ada RW-009", "RW-009" in text(page, "#daftarRiwayatDasbor"))
        check("dasbor riwayat terbaru 5 item", count(page, "#daftarRiwayatDasbor .item-bar") == 5, str(count(page, "#daftarRiwayatDasbor .item-bar")))

        # 4. Kendaraan: filter + cari + tombol Riwayat
        klik_tab(page, "kendaraan")
        page.select_option("#filterJenis", "Motor")
        page.wait_for_timeout(300)
        check("filter Motor 6 item", count(page, "#daftarKendaraan .item-bar") == 6, str(count(page, "#daftarKendaraan .item-bar")))
        page.select_option("#filterJenis", "Mobil")
        page.wait_for_timeout(300)
        check("filter Mobil 6 item", count(page, "#daftarKendaraan .item-bar") == 6, str(count(page, "#daftarKendaraan .item-bar")))
        page.select_option("#filterJenis", "semua")
        page.wait_for_timeout(300)
        page.fill("#cariKendaraan", "Brio")
        page.wait_for_timeout(300)
        check("cari Brio 1 item", count(page, "#daftarKendaraan .item-bar") == 1, str(count(page, "#daftarKendaraan .item-bar")))
        page.fill("#cariKendaraan", "")
        page.wait_for_timeout(300)
        page.click('[data-riwayat-kendaraan="3"]')
        page.wait_for_timeout(400)
        check("tombol Riwayat pindah ke tab riwayat", page.is_visible("#panel-riwayat"))
        check("riwayat Brio 3 entri", count(page, "#daftarRiwayat .item-bar") == 3, str(count(page, "#daftarRiwayat .item-bar")))
        check("riwayat Brio ada BK-001", "BK-001" in text(page, "#daftarRiwayat"))
        check("riwayat Brio ada RW-005", "RW-005" in text(page, "#daftarRiwayat"))
        check("riwayat Brio total Rp1.080.000", "Rp1.080.000" in text(page, "#ringkasanRiwayat"), text(page, "#ringkasanRiwayat"))

        # 5. Riwayat tab: semua, filter jenis, pilih kendaraan, cari, detail
        page.select_option("#rwKendaraan", "semua")
        page.wait_for_timeout(300)
        check("riwayat semua 21 entri", count(page, "#daftarRiwayat .item-bar") == 21, str(count(page, "#daftarRiwayat .item-bar")))
        page.select_option("#filterRiwayatJenis", "Servis")
        page.wait_for_timeout(300)
        check("filter Servis 15 entri", count(page, "#daftarRiwayat .item-bar") == 15, str(count(page, "#daftarRiwayat .item-bar")))
        page.select_option("#filterRiwayatJenis", "Booking")
        page.wait_for_timeout(300)
        check("filter Booking 6 entri", count(page, "#daftarRiwayat .item-bar") == 6, str(count(page, "#daftarRiwayat .item-bar")))
        page.select_option("#filterRiwayatJenis", "semua")
        page.wait_for_timeout(300)
        page.select_option("#rwKendaraan", "1")
        page.wait_for_timeout(300)
        check("riwayat Avanza 3 entri", count(page, "#daftarRiwayat .item-bar") == 3, str(count(page, "#daftarRiwayat .item-bar")))
        check("riwayat Avanza total Rp945.000", "Rp945.000" in text(page, "#ringkasanRiwayat"), text(page, "#ringkasanRiwayat"))
        page.select_option("#rwKendaraan", "semua")
        page.wait_for_timeout(300)
        page.fill("#cariRiwayat", "kampas")
        page.wait_for_timeout(300)
        check("cari kampas 5 entri", count(page, "#daftarRiwayat .item-bar") == 5, str(count(page, "#daftarRiwayat .item-bar")))
        check("cari kampas ada RW-015", "RW-015" in text(page, "#daftarRiwayat"))
        check("cari kampas ada BK-006", "BK-006" in text(page, "#daftarRiwayat"))
        check("cari kampas ada BK-003 (layanan Kampas Rem)", "BK-003" in text(page, "#daftarRiwayat"))
        page.fill("#cariRiwayat", "")
        page.wait_for_timeout(300)
        page.click('[data-detail-riwayat="1"]')
        page.wait_for_timeout(400)
        check("detail RW-001 total Rp455.000", "Rp455.000" in text(page, "#modalKonten"), text(page, "#modalKonten")[:300])
        check("detail RW-001 ada Oli Mesin", "Oli Mesin 10W-40" in text(page, "#modalKonten"))
        check("detail RW-001 ada Filter Oli", "Filter Oli Mobil" in text(page, "#modalKonten"))
        page.click("#modalBatal")
        page.wait_for_timeout(300)

        # 6. Catat servis baru
        hari_ini = page.evaluate("() => new Date().toISOString().slice(0, 10)")
        page.select_option("#rsKendaraan", "12")
        page.fill("#rsTanggal", hari_ini)
        page.fill("#rsDiagnosa", "Tes servis baru")
        page.click('[data-jasa-id="2"]')
        page.check('input[data-part-id="2"]')
        page.wait_for_timeout(300)
        check("total form Rp245.000", "Rp245.000" in text(page, "#rsTotal"), text(page, "#rsTotal"))
        page.click("#btnSimpanRiwayat")
        page.wait_for_timeout(500)
        check("toast RW-016 disimpan", "RW-016" in text(page, "#toast"), text(page, "#toast"))
        page.select_option("#rwKendaraan", "12")
        page.wait_for_timeout(300)
        check("riwayat Scoopy jadi 2 entri", count(page, "#daftarRiwayat .item-bar") == 2, str(count(page, "#daftarRiwayat .item-bar")))
        check("riwayat Scoopy ada RW-016", "RW-016" in text(page, "#daftarRiwayat"))
        klik_tab(page, "dashboard")
        check("dasbor riwayat jadi 16", text(page, "#dRiwayat").strip() == "16", text(page, "#dRiwayat"))
        check("dasbor biaya 30 hari jadi Rp1.580.000", text(page, "#dBiaya30").strip() == "Rp1.580.000", text(page, "#dBiaya30"))
        reset_data(page)
        check("reset riwayat kembali 15", text(page, "#dRiwayat").strip() == "15", text(page, "#dRiwayat"))

        # 7. Servis berkala: centang berkala perbarui jadwal + km
        klik_tab(page, "riwayat")
        page.select_option("#rsKendaraan", "12")
        page.fill("#rsTanggal", hari_ini)
        page.fill("#rsDiagnosa", "Servis berkala tes")
        page.fill("#rsKm", "6000")
        page.click('[data-jasa-id="2"]')
        page.check("#rsBerkala")
        page.click("#btnSimpanRiwayat")
        page.wait_for_timeout(500)
        klik_tab(page, "dashboard")
        check("pengingat jatuh tempo jadi 5 setelah berkala", text(page, "#dPengingat").strip() == "5", text(page, "#dPengingat"))
        klik_tab(page, "kendaraan")
        page.fill("#cariKendaraan", "Scoopy")
        page.wait_for_timeout(300)
        check("km Scoopy jadi 6.000", "6.000 km" in text(page, "#daftarKendaraan"))
        reset_data(page)
        check("reset pengingat kembali 6", text(page, "#dPengingat").strip() == "6", text(page, "#dPengingat"))

        # 8. Pengingat: teks, salin, tandai
        klik_tab(page, "pengingat")
        check("pengingat servis 6 item", count(page, "#daftarPengingatServis .item-bar") == 6, str(count(page, "#daftarPengingatServis .item-bar")))
        check("pengingat servis ada Scoopy", "B 3344 HIJ" in text(page, "#daftarPengingatServis"))
        check("teks pengingat berisi Bengkel Oyen", "Bengkel Oyen" in text(page, "#daftarPengingatServis"))
        check("pengingat booking besok 1 item", count(page, "#daftarPengingatBooking .item-bar") == 1, str(count(page, "#daftarPengingatBooking .item-bar")))
        check("pengingat booking ada BK-004", "BK-004" in text(page, "#daftarPengingatBooking"))
        page.click('[data-salin-pengingat-servis="12"]')
        page.wait_for_timeout(400)
        check("salin pesan toast muncul", page.is_visible("#toast") and "disalin" in text(page, "#toast"))
        page.click('[data-ingatkan-servis="12"]')
        page.wait_for_timeout(400)
        check("Scoopy ditandai sudah diingatkan", "Sudah diingatkan" in text(page, "#daftarPengingatServis"))
        reset_data(page)

        # 9. Laporan: periode + per kendaraan + terlaris
        klik_tab(page, "laporan")
        check("laporan 30hari total 4", text(page, "#lTotal").strip() == "4", text(page, "#lTotal"))
        check("laporan 30hari biaya Rp1.335.000", text(page, "#lBiaya").strip() == "Rp1.335.000", text(page, "#lBiaya"))
        check("laporan 30hari rata-rata Rp333.750", text(page, "#lRata").strip() == "Rp333.750", text(page, "#lRata"))
        check("laporan 30hari terbanyak PCX", "B 7890 STU" in text(page, "#lTerbanyak"), text(page, "#lTerbanyak"))
        check("terlaris Ganti Kampas Rem 2 kali", "Ganti Kampas Rem" in text(page, "#daftarTerlaris") and "2 kali" in text(page, "#daftarTerlaris"))
        page.select_option("#lapPeriode", "7hari")
        page.wait_for_timeout(300)
        check("laporan 7hari total 3", text(page, "#lTotal").strip() == "3", text(page, "#lTotal"))
        check("laporan 7hari biaya Rp1.005.000", text(page, "#lBiaya").strip() == "Rp1.005.000", text(page, "#lBiaya"))
        page.select_option("#lapPeriode", "semua")
        page.wait_for_timeout(300)
        check("laporan semua total 15", text(page, "#lTotal").strip() == "15", text(page, "#lTotal"))
        check("laporan semua biaya Rp6.425.000", text(page, "#lBiaya").strip() == "Rp6.425.000", text(page, "#lBiaya"))
        page.select_option("#lapPeriode", "hari")
        page.wait_for_timeout(300)
        check("laporan hari ini total 0", text(page, "#lTotal").strip() == "0", text(page, "#lTotal"))
        page.select_option("#lapPeriode", "semua")
        page.select_option("#lapKendaraan", "1")
        page.wait_for_timeout(300)
        check("laporan Avanza semua total 2", text(page, "#lTotal").strip() == "2", text(page, "#lTotal"))
        check("laporan Avanza semua biaya Rp945.000", text(page, "#lBiaya").strip() == "Rp945.000", text(page, "#lBiaya"))
        page.select_option("#lapKendaraan", "semua")
        page.select_option("#lapPeriode", "30hari")
        page.wait_for_timeout(300)

        # 10. Ekspor CSV + Backup JSON + Pulihkan
        with page.expect_download() as dl:
            page.click("#btnExportCSV")
        d = dl.value
        check("CSV terunduh", "laporan-riwayat-kendaraan" in d.suggested_filename, d.suggested_filename)
        with page.expect_download() as dl2:
            page.click("#btnBackupJSON")
        d2 = dl2.value
        check("backup JSON terunduh", "backup-riwayat-kendaraan" in d2.suggested_filename, d2.suggested_filename)
        page.evaluate("""() => {
          const raw = localStorage.getItem('aplikasiRiwayatKendaraan.v1');
          const s = JSON.parse(raw);
          s.riwayat.push({ id: 99, no: 'RW-999', kendaraanId: 1, tanggal: new Date().toISOString(),
            mekanik: 'Agus', diagnosa: 'Servis dari restore', km: 70000, status: 'Diambil', diskon: 0,
            jasa: [{ layananId: 1, harga: 75000 }], parts: [] });
          window.__restorePayload = JSON.stringify({ app: 'aplikasi-riwayat-kendaraan', version: 1, state: s });
        }""")
        Path("/tmp/restore-riwayat.json").write_text(page.evaluate("() => window.__restorePayload"), encoding="utf-8")
        page.set_input_files("#inputRestore", "/tmp/restore-riwayat.json")
        page.wait_for_timeout(600)
        klik_tab(page, "riwayat")
        page.select_option("#rwKendaraan", "semua")
        page.wait_for_timeout(300)
        check("restore: RW-999 muncul", "RW-999" in text(page, "#daftarRiwayat"))
        reset_data(page)
        klik_tab(page, "riwayat")
        check("reset: RW-999 hilang", "RW-999" not in text(page, "#daftarRiwayat"))

        # 11. Pengguna: tambah, ganti sandi sendiri, reset, nonaktifkan
        klik_tab(page, "dashboard")
        page.fill("#nuNama", "Dewi")
        page.fill("#nuUser", "dewi")
        page.fill("#nuPass", "dewi123")
        page.select_option("#nuPeran", "kasir")
        page.click("#btnTambahPengguna")
        page.wait_for_timeout(400)
        check("pengguna Dewi ditambahkan", "Dewi" in text(page, "#daftarPengguna"))
        logout(page)
        login(page, "dewi", "dewi123")
        check("login Dewi berhasil", not page.is_visible("#loginOverlay"))
        check("chip Dewi Kasir", "Dewi (Kasir)" in text(page, "#userChip"))
        klik_tab(page, "dashboard")
        page.fill("#sandiLama", "dewi123")
        page.fill("#sandiBaru", "dewi456")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(400)
        check("ganti sandi sendiri toast", "berhasil diganti" in text(page, "#toast"))
        logout(page)
        login(page, "dewi", "dewi456")
        check("login Dewi sandi baru berhasil", not page.is_visible("#loginOverlay"))
        logout(page)
        login(page, "admin", "admin123")
        klik_tab(page, "dashboard")
        page.click('[data-aksi-pengguna="sandi"][data-user="dewi"]')
        page.wait_for_timeout(300)
        page.click("#modalYa")
        page.wait_for_timeout(400)
        check("reset sandi Dewi toast bk123", "bk123" in text(page, "#toast"))
        logout(page)
        login(page, "dewi", "bk123")
        check("login Dewi bk123 berhasil", not page.is_visible("#loginOverlay"))
        logout(page)
        login(page, "admin", "admin123")
        klik_tab(page, "dashboard")
        page.click('[data-aksi-pengguna="aktif"][data-user="dewi"]')
        page.wait_for_timeout(400)
        logout(page)
        login(page, "dewi", "bk123")
        check("login pengguna nonaktif ditolak", page.is_visible("#loginError"))

        # 12. RBAC mekanik: pengingat + laporan tersembunyi, riwayat terlihat
        login(page, "mekanik", "mekanik123")
        check("login mekanik berhasil", not page.is_visible("#loginOverlay"))
        check("mekanik: tab pengingat tersembunyi", not page.is_visible('[data-tab="pengingat"]'))
        check("mekanik: tab laporan tersembunyi", not page.is_visible('[data-tab="laporan"]'))
        check("mekanik: tab riwayat terlihat", page.is_visible('[data-tab="riwayat"]'))
        check("mekanik: tab kendaraan terlihat", page.is_visible('[data-tab="kendaraan"]'))
        check("mekanik: kartu kelola pengguna tersembunyi", not page.is_visible("#cardPengguna"))
        logout(page)
        login(page, "admin", "admin123")

        # 13. RBAC kasir: pengingat + laporan terlihat, kelola pengguna tersembunyi
        logout(page)
        login(page, "kasir", "kasir123")
        check("login kasir berhasil", not page.is_visible("#loginOverlay"))
        check("kasir: tab pengingat terlihat", page.is_visible('[data-tab="pengingat"]'))
        check("kasir: tab laporan terlihat", page.is_visible('[data-tab="laporan"]'))
        check("kasir: kartu kelola pengguna tersembunyi", not page.is_visible("#cardPengguna"))
        logout(page)
        login(page, "admin", "admin123")

        # 14. Panduan: akun demo + harga + garansi + catatan jujur
        klik_tab(page, "panduan")
        t = text(page, "#panel-panduan")
        check("panduan akun demo", "admin123" in t and "kasir123" in t and "mekanik123" in t)
        check("panduan harga 499.000", "499.000" in t)
        check("panduan APK 400.000", "400.000" in t)
        check("panduan garansi 30/60/90", "30 hari" in t and "90 hari" in t)
        check("panduan jujur teks saja", "teks saja" in t)
        check("panduan jujur per perangkat", "hanya tersimpan di perangkat ini" in t)

        # 15. Reset data contoh
        page.click("#btnResetData")
        page.wait_for_timeout(300)
        page.click("#modalYa")
        page.wait_for_timeout(500)
        klik_tab(page, "dashboard")
        check("reset riwayat kembali 15", text(page, "#dRiwayat").strip() == "15", text(page, "#dRiwayat"))

        check("0 console error", len(errors) == 0, str(errors[:3]))
        browser.close()

    print(f"\n{passed} lolos, {len(failures)} gagal")
    if failures:
        print("Gagal:", failures)
        sys.exit(1)


if __name__ == "__main__":
    main()
