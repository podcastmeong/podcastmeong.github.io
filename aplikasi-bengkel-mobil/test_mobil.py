"""Tes Aplikasi Bengkel Mobil (file lokal, Playwright Chromium)."""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = "file://" + str(ROOT / "aplikasi-bengkel-mobil" / "index.html")

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


def klik_tab(page, tab):
    page.click(f'[data-tab="{tab}"]')
    page.wait_for_timeout(300)


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
        # 3. Dashboard data contoh
        check("dasbor WO aktif 2", text(page, "#dWOAktif").strip() == "2", text(page, "#dWOAktif"))
        check("dasbor booking hari ini 2", text(page, "#dBooking").strip() == "2", text(page, "#dBooking"))
        check("dasbor omzet 7 hari Rp2.175.000", "2.175.000" in text(page, "#dOmzet"), text(page, "#dOmzet"))
        check("dasbor laba 7 hari Rp1.275.000", "1.275.000" in text(page, "#dLaba"), text(page, "#dLaba"))
        check("badge booking 4", text(page, "#badgeBooking").strip() == "4", text(page, "#badgeBooking"))
        check("badge WO 2", text(page, "#badgeWO").strip() == "2", text(page, "#badgeWO"))
        check("peringatan Ban 185/65 R15 menipis", "Ban 185/65 R15" in text(page, "#daftarPeringatan"))
        check("peringatan Ban 195/55 R16 menipis", "Ban 195/55 R16" in text(page, "#daftarPeringatan"))
        check("peringatan servis jatuh tempo 6", "Servis jatuh tempo (4)" in text(page, "#daftarPeringatan"), text(page, "#daftarPeringatan")[:400])
        check("peringatan Brio terlambat 20 hari", "Terlambat 20 hari" in text(page, "#daftarPeringatan"))
        check("WO hari ini ada WO-005", "WO-005" in text(page, "#daftarWOHariIni"))
        check("WO hari ini ada WO-006", "WO-006" in text(page, "#daftarWOHariIni"))
        check("booking hari ini ada BK-001", "BK-001" in text(page, "#daftarBookingHariIni"))
        check("booking hari ini ada BK-002", "BK-002" in text(page, "#daftarBookingHariIni"))

        # 4. Kendaraan: data + riwayat servis
        klik_tab(page, "kendaraan")
        t = text(page, "#daftarKendaraan")
        check("mobil Avanza 68.400 km", "B 1234 ABC" in t and "68.400 km" in t, t[:400])
        check("mobil Brio terlambat 20 hari", "Terlambat 20 hari" in t)
        page.click('[data-riwayat-kendaraan="5"]')
        page.wait_for_timeout(400)
        m = text(page, "#modalKonten")
        check("riwayat Calya ada WO-001", "WO-001" in m, m[:400])
        check("riwayat Calya total 1.130.000", "1.130.000" in m)
        page.click("#modalBatal")
        page.wait_for_timeout(300)

        # 5. Booking: tambah booking baru
        klik_tab(page, "booking")
        check("booking BK-001 ada", "BK-001" in text(page, "#daftarBooking"))
        page.select_option("#bkKendaraan", "1")
        page.fill("#bkTanggal", "2026-11-21")
        page.fill("#bkJam", "09:00")
        page.fill("#bkKeluhan", "Servis berkala Avanza")
        page.click("#btnSimpanBooking")
        page.wait_for_timeout(400)
        check("booking baru BK-007 tersimpan", "BK-007" in text(page, "#daftarBooking"))

        # 6. Booking BK-001 -> Work Order WO-009
        page.click('[data-buat-wo="1"]')
        page.wait_for_timeout(400)
        check("toast WO-009 dibuat", "WO-009" in text(page, "#toast"), text(page, "#toast"))
        klik_tab(page, "workorder")
        check("WO-009 ada di daftar", "WO-009" in text(page, "#daftarWO"))
        check("WO-009 status Antre", "Antre" in text(page, "#daftarWO"))

        # 7. Detail WO-009: tambah jasa + part, stok berkurang, lanjut status sampai Selesai
        page.click('[data-detail-wo="9"]')
        page.wait_for_timeout(400)
        page.select_option("#wdJasa", "2")
        page.click("#btnTambahJasa")
        page.wait_for_timeout(400)
        check("WO-009 estimasi 150.000 setelah jasa", "150.000" in text(page, "#modalKonten"), text(page, "#modalKonten")[:600])
        page.select_option("#wdPart", "9")
        page.fill("#wdJumlahPart", "1")
        page.click("#btnTambahPartWO")
        page.wait_for_timeout(400)
        check("WO-009 estimasi 225.000 setelah part", "225.000" in text(page, "#modalKonten"), text(page, "#modalKonten")[:600])
        # Guard: part melebihi stok ditolak
        page.select_option("#wdPart", "8")
        page.fill("#wdJumlahPart", "10")
        page.click("#btnTambahPartWO")
        page.wait_for_timeout(400)
        check("part melebihi stok ditolak", "tidak cukup" in text(page, "#toast"), text(page, "#toast"))
        page.click("#modalBatal")
        page.wait_for_timeout(300)
        klik_tab(page, "sparepart")
        check("Busi Iridium stok jadi 23", "Busi Iridium" in text(page, "#daftarPart") and "Stok 23 pcs" in text(page, "#daftarPart"), text(page, "#daftarPart")[:500])
        klik_tab(page, "workorder")
        page.click('[data-lanjut-wo="9"]')
        page.wait_for_timeout(400)
        page.click('[data-lanjut-wo="9"]')
        page.wait_for_timeout(400)
        check("WO-009 status Selesai", "Selesai" in text(page, "#daftarWO"))

        # 8. Spare part: ubah stok Ban 185/65 R15 3 -> 6, peringatan hilang
        klik_tab(page, "sparepart")
        page.click('[data-stok-part="6"]')
        page.wait_for_timeout(300)
        page.fill("#fsStok", "6")
        page.click("#formStok button[type=submit]")
        page.wait_for_timeout(400)
        klik_tab(page, "dashboard")
        check("Ban 185/65 R15 tidak lagi di peringatan", "Ban 185/65 R15" not in text(page, "#daftarPeringatan"), text(page, "#daftarPeringatan")[:400])
        check("Ban 195/55 R16 masih di peringatan", "Ban 195/55 R16" in text(page, "#daftarPeringatan"))
        # Guard: part yang dipakai tidak punya tombol hapus; part yang tidak dipakai bisa dihapus
        klik_tab(page, "sparepart")
        check("tombol hapus Busi tidak ada (dipakai WO)", page.query_selector('[data-hapus-part="9"]') is None)
        check("tombol hapus Lampu H4 ada (tidak dipakai)", page.query_selector('[data-hapus-part="13"]') is not None)
        page.click('[data-hapus-part="13"]')
        page.wait_for_timeout(300)
        page.click("#modalYa")
        page.wait_for_timeout(400)
        check("Lampu H4 terhapus", "Lampu Depan H4" not in text(page, "#daftarPart"))

        # 9. Kasir: bayar WO-004 Rp755.000, bayar 800.000, kembalian 45.000
        klik_tab(page, "kasir")
        page.select_option("#ksWO", "4")
        page.wait_for_timeout(300)
        check("rincian kasir total 755.000", "755.000" in text(page, "#ksRincian"), text(page, "#ksRincian"))
        page.fill("#ksBayar", "800000")
        page.wait_for_timeout(200)
        check("kembalian 45.000", "45.000" in text(page, "#ksRincian"), text(page, "#ksRincian"))
        page.click("#btnSimpanPembayaran")
        page.wait_for_timeout(400)
        check("pembayaran BYR-005 tersimpan", "BYR-005" in text(page, "#daftarPembayaran"))
        check("toast BYR-005 kembalian 45.000", "BYR-005" in text(page, "#toast") and "45.000" in text(page, "#toast"))
        klik_tab(page, "dashboard")
        check("omzet 7 hari jadi 2.930.000", "2.930.000" in text(page, "#dOmzet"), text(page, "#dOmzet"))
        check("laba 7 hari jadi 1.640.000", "1.640.000" in text(page, "#dLaba"), text(page, "#dLaba"))
        klik_tab(page, "workorder")
        check("WO-004 status Diambil", "WO-004" in text(page, "#daftarWO") and "Diambil" in text(page, "#daftarWO"))

        # 10. Laporan 7 hari setelah mutasi
        klik_tab(page, "laporan")
        check("laporan transaksi 4", text(page, "#lTransaksi").strip() == "4", text(page, "#lTransaksi"))
        check("laporan kendaraan dilayani 4", text(page, "#lKendaraan").strip() == "4", text(page, "#lKendaraan"))
        check("laporan omzet 2.930.000", "2.930.000" in text(page, "#lOmzet"), text(page, "#lOmzet"))
        check("laporan laba 1.640.000", "1.640.000" in text(page, "#lLaba"), text(page, "#lLaba"))
        check("terlaris Ganti Oli Mesin 3 kali", "Ganti Oli Mesin" in text(page, "#daftarTerlaris") and "3 kali" in text(page, "#daftarTerlaris"), text(page, "#daftarTerlaris")[:300])

        # 11. Ekspor CSV
        with page.expect_download() as dl_info:
            page.click("#btnExportCSV")
        dl = dl_info.value
        check("CSV nama file", "csv" in dl.suggested_filename, dl.suggested_filename)
        csv_path = Path("/tmp/mobil-test-laporan.csv")
        dl.save_as(csv_path)
        isi_csv = csv_path.read_text(encoding="utf-8")
        check("CSV berisi BYR-001", "BYR-001" in isi_csv)
        check("CSV berisi Calya", "Calya" in isi_csv)

        # 12. Backup JSON + pulihkan
        with page.expect_download() as dl_info2:
            page.click("#btnBackupJSON")
        dl2 = dl_info2.value
        check("JSON nama file", "json" in dl2.suggested_filename, dl2.suggested_filename)
        backup_path = Path("/tmp/mobil-test-backup.json")
        dl2.save_as(backup_path)
        check("backup berisi WO-009", "WO-009" in backup_path.read_text(encoding="utf-8"))
        klik_tab(page, "sparepart")
        page.click("#btnTambahPart")
        page.wait_for_timeout(300)
        page.fill("#fpNama", "Part Test Restore")
        page.fill("#fpStok", "1")
        page.fill("#fpBeli", "1000")
        page.fill("#fpJual", "2000")
        page.click("#formPart button[type=submit]")
        page.wait_for_timeout(400)
        check("part test restore ditambah", "Part Test Restore" in text(page, "#daftarPart"))
        klik_tab(page, "laporan")
        page.click("#btnPulihkan")
        page.wait_for_timeout(300)
        page.set_input_files("#inputRestore", str(backup_path))
        page.wait_for_timeout(600)
        klik_tab(page, "sparepart")
        check("restore hapus part test", "Part Test Restore" not in text(page, "#daftarPart"))
        klik_tab(page, "workorder")
        check("restore WO-009 tetap ada", "WO-009" in text(page, "#daftarWO"))

        # 13. Kelola pengguna: tambah Dewi, reset sandi bk123, nonaktifkan, login ditolak
        klik_tab(page, "dashboard")
        page.fill("#nuNama", "Dewi")
        page.fill("#nuUser", "dewi")
        page.fill("#nuPass", "dewi123")
        page.select_option("#nuPeran", "mekanik")
        page.click("#btnTambahPengguna")
        page.wait_for_timeout(400)
        check("pengguna Dewi ditambah", "Dewi" in text(page, "#daftarPengguna"))
        page.click('[data-aksi-pengguna="sandi"][data-user="dewi"]')
        page.wait_for_timeout(300)
        page.click("#modalYa")
        page.wait_for_timeout(400)
        check("reset sandi toast bk123", "bk123" in text(page, "#toast"))
        page.click('[data-aksi-pengguna="aktif"][data-user="dewi"]')
        page.wait_for_timeout(400)
        page.click("#btnKeluar")
        page.wait_for_timeout(400)
        login(page, "dewi", "bk123")
        check("login pengguna nonaktif ditolak", page.is_visible("#loginError"))
        # 14. Ganti sandi sendiri: salah ditolak, benar berhasil, kembalikan
        login(page, "admin", "admin123")
        page.wait_for_timeout(300)
        page.fill("#sandiLama", "salah")
        page.fill("#sandiBaru", "baru12345")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        check("ganti sandi lama salah ditolak", "salah" in text(page, "#toast").lower())
        page.fill("#sandiLama", "admin123")
        page.fill("#sandiBaru", "baru12345")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        page.click("#btnKeluar")
        page.wait_for_timeout(300)
        login(page, "admin", "baru12345")
        check("login sandi baru berhasil", not page.is_visible("#loginOverlay"))
        page.fill("#sandiLama", "baru12345")
        page.fill("#sandiBaru", "admin123")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        # 15. Kasir tidak melihat kelola pengguna dan tab spare part
        page.click("#btnKeluar")
        page.wait_for_timeout(300)
        login(page, "kasir", "kasir123")
        page.wait_for_timeout(300)
        check("kasir tidak lihat kelola pengguna", not page.is_visible("#cardPengguna"))
        check("kasir tidak lihat tab sparepart", not page.is_visible('[data-tab="sparepart"]'))
        check("kasir lihat tab kasir", page.is_visible('[data-tab="kasir"]'))
        check("kasir lihat tab laporan", page.is_visible('[data-tab="laporan"]'))
        # 16. Mekanik tidak melihat tab kasir/laporan
        page.click("#btnKeluar")
        page.wait_for_timeout(300)
        login(page, "mekanik", "mekanik123")
        page.wait_for_timeout(300)
        check("mekanik tidak lihat tab kasir", not page.is_visible('[data-tab="kasir"]'))
        check("mekanik tidak lihat tab laporan", not page.is_visible('[data-tab="laporan"]'))
        check("mekanik lihat tab sparepart", page.is_visible('[data-tab="sparepart"]'))
        check("mekanik lihat tab workorder", page.is_visible('[data-tab="workorder"]'))
        # 17. Panduan: akun demo, harga, APK, garansi
        klik_tab(page, "panduan")
        t = text(page, "#panel-panduan")
        check("panduan akun demo", "admin123" in t and "kasir123" in t and "mekanik123" in t)
        check("panduan harga 499.000", "499.000" in t)
        check("panduan APK 400.000", "400.000" in t)
        check("panduan garansi 30/60/90", "30 hari" in t and "90 hari" in t)
        # 18. Reset data contoh (butuh admin)
        page.click("#btnKeluar")
        page.wait_for_timeout(300)
        login(page, "admin", "admin123")
        page.wait_for_timeout(300)
        klik_tab(page, "panduan")
        page.click("#btnResetData")
        page.wait_for_timeout(300)
        page.click("#modalYa")
        page.wait_for_timeout(500)
        klik_tab(page, "dashboard")
        check("reset omzet kembali 2.175.000", "2.175.000" in text(page, "#dOmzet"), text(page, "#dOmzet"))
        klik_tab(page, "workorder")
        check("reset WO-009 hilang", "WO-009" not in text(page, "#daftarWO"))

        check("0 console error", len(errors) == 0, str(errors[:3]))
        browser.close()

    print(f"\n{passed} lolos, {len(failures)} gagal")
    if failures:
        print("Gagal:", failures)
        sys.exit(1)


if __name__ == "__main__":
    main()
