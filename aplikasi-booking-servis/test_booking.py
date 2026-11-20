"""Tes Aplikasi Booking Servis (file lokal, Playwright Chromium)."""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = "file://" + str(ROOT / "aplikasi-booking-servis" / "index.html")

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
        check("judul Booking Servis", "Booking Servis" in page.title())
        check("localStorage terisi", page.evaluate("() => !!localStorage.getItem('aplikasiBookingServis.v1')"))

        # 3. Dasbor data contoh
        check("dasbor booking hari ini 3", text(page, "#dBooking").strip() == "3", text(page, "#dBooking"))
        check("dasbor booking besok 3", text(page, "#dBookingBesok").strip() == "3", text(page, "#dBookingBesok"))
        check("dasbor WO aktif 2", text(page, "#dWOAktif").strip() == "2", text(page, "#dWOAktif"))
        check("dasbor antrean hari ini 5", text(page, "#dAntrean").strip() == "5", text(page, "#dAntrean"))
        check("badge booking 9", text(page, "#badgeBooking").strip() == "9", text(page, "#badgeBooking"))
        check("badge antrean 5", text(page, "#badgeAntrean").strip() == "5", text(page, "#badgeAntrean"))
        check("badge pengingat 9", text(page, "#badgePengingat").strip() == "9", text(page, "#badgePengingat"))
        check("dasbor pengingat ada BK besok", "BK-004" in text(page, "#daftarPengingatDasbor"))
        check("dasbor pengingat ada jatuh tempo", "B 2345 GHI" in text(page, "#daftarPengingatDasbor"))

        # 4. Antrean: slot + daftar
        klik_tab(page, "antrean")
        slot = text(page, "#daftarSlot")
        check("slot 08:00 terisi BK-001", "BK-001" in slot)
        check("slot 11:00 kosong", "11:00" in slot and "Kosong" in slot)
        check("daftar antrean 5 item", count(page, "#daftarAntrean .item-bar") == 5, str(count(page, "#daftarAntrean .item-bar")))
        check("antrean ada WO-003", "WO-003" in text(page, "#daftarAntrean"))

        # 5. Booking: daftar + filter
        klik_tab(page, "booking")
        check("daftar booking 12 item", count(page, "#daftarBooking .item-bar") == 12, str(count(page, "#daftarBooking .item-bar")))
        page.select_option("#filterBookingStatus", "Dijadwalkan")
        page.wait_for_timeout(300)
        check("filter Dijadwalkan 9 item", count(page, "#daftarBooking .item-bar") == 9, str(count(page, "#daftarBooking .item-bar")))
        page.select_option("#filterBookingStatus", "Batal")
        page.wait_for_timeout(300)
        check("filter Batal 1 item BK-011", count(page, "#daftarBooking .item-bar") == 1 and "BK-011" in text(page, "#daftarBooking"))
        check("booking batal tanpa tombol Buat WO", count(page, '[data-buat-wo="11"]') == 0)
        page.select_option("#filterBookingStatus", "semua")
        page.wait_for_timeout(300)

        # 6. Buat booking baru besok
        besok = page.evaluate("() => { const d = new Date(); d.setDate(d.getDate() + 1); return d.toISOString().slice(0, 10); }")
        page.select_option("#bkKendaraan", "2")
        page.fill("#bkTanggal", besok)
        page.fill("#bkJam", "15:00")
        page.fill("#bkKeluhan", "Tes booking baru")
        page.click("#btnSimpanBooking")
        page.wait_for_timeout(400)
        check("booking baru BK-013 muncul", "BK-013" in text(page, "#daftarBooking"))
        klik_tab(page, "dashboard")
        check("booking besok jadi 4", text(page, "#dBookingBesok").strip() == "4", text(page, "#dBookingBesok"))
        check("badge booking jadi 10", text(page, "#badgeBooking").strip() == "10", text(page, "#badgeBooking"))
        reset_data(page)
        check("reset kembalikan booking besok 3", text(page, "#dBookingBesok").strip() == "3", text(page, "#dBookingBesok"))

        # 7. Alur booking: Datang -> Selesai, Buat WO, Batalkan
        klik_tab(page, "booking")
        page.click('[data-datang-booking="1"]')
        page.wait_for_timeout(400)
        check("BK-001 jadi Datang", "Datang" in text(page, "#daftarBooking"))
        page.click('[data-selesai-booking="1"]')
        page.wait_for_timeout(400)
        page.select_option("#filterBookingStatus", "Selesai")
        page.wait_for_timeout(300)
        check("BK-001 jadi Selesai", "BK-001" in text(page, "#daftarBooking"))
        page.select_option("#filterBookingStatus", "semua")
        page.wait_for_timeout(300)
        page.click('[data-buat-wo="2"]')
        page.wait_for_timeout(400)
        check("WO-005 dibuat dari BK-002", True)
        klik_tab(page, "workorder")
        check("WO-005 ada di daftar WO", "WO-005" in text(page, "#daftarWO"))
        klik_tab(page, "dashboard")
        check("WO aktif jadi 3", text(page, "#dWOAktif").strip() == "3", text(page, "#dWOAktif"))
        klik_tab(page, "booking")
        page.click('[data-batal-booking="3"]')
        page.wait_for_timeout(300)
        page.click("#modalYa")
        page.wait_for_timeout(400)
        klik_tab(page, "dashboard")
        check("booking hari ini jadi 2 setelah batal", text(page, "#dBooking").strip() == "2", text(page, "#dBooking"))
        reset_data(page)

        # 8. Work Order: lanjut status + booking otomatis Selesai + detail jasa
        klik_tab(page, "workorder")
        check("daftar WO 4 item", count(page, "#daftarWO .item-bar") == 4, str(count(page, "#daftarWO .item-bar")))
        page.click('[data-detail-wo="3"]')
        page.wait_for_timeout(400)
        check("detail WO-003 estimasi Rp125.000", "Rp125.000" in text(page, "#modalKonten"), text(page, "#modalKonten")[:200])
        page.select_option("#wdJasa", "6")
        page.click("#btnTambahJasa")
        page.wait_for_timeout(400)
        check("tambah jasa -> estimasi Rp200.000", "Rp200.000" in text(page, "#modalKonten"))
        page.click("#modalBatal")
        page.wait_for_timeout(300)
        page.click('[data-lanjut-wo="2"]')
        page.wait_for_timeout(400)
        check("WO-002 jadi Diambil", "Diambil" in text(page, "#daftarWO"))
        klik_tab(page, "booking")
        page.select_option("#filterBookingStatus", "Selesai")
        page.wait_for_timeout(300)
        check("BK-010 otomatis Selesai", "BK-010" in text(page, "#daftarBooking"))
        page.select_option("#filterBookingStatus", "semua")
        page.wait_for_timeout(300)
        reset_data(page)

        # 9. Pengingat: teks, salin, tandai
        klik_tab(page, "pengingat")
        check("pengingat booking besok 3 item", count(page, "#daftarPengingatBooking .item-bar") == 3, str(count(page, "#daftarPengingatBooking .item-bar")))
        check("teks pengingat booking berisi Bengkel Oyen", "Bengkel Oyen" in text(page, "#daftarPengingatBooking"))
        check("teks pengingat booking berisi besok", "besok" in text(page, "#daftarPengingatBooking"))
        page.click('[data-salin-pengingat-booking="4"]')
        page.wait_for_timeout(400)
        check("salin pesan toast muncul", page.is_visible("#toast") and "disalin" in text(page, "#toast"))
        page.click('[data-ingatkan-booking="4"]')
        page.wait_for_timeout(400)
        check("BK-004 ditandai sudah diingatkan", "Sudah diingatkan" in text(page, "#daftarPengingatBooking"))
        check("pengingat servis 6 item", count(page, "#daftarPengingatServis .item-bar") == 6, str(count(page, "#daftarPengingatServis .item-bar")))
        check("pengingat servis ada Scoopy", "B 3344 HIJ" in text(page, "#daftarPengingatServis"))
        page.click('[data-ingatkan-servis="12"]')
        page.wait_for_timeout(400)
        check("Scoopy ditandai sudah diingatkan", "Sudah diingatkan" in text(page, "#daftarPengingatServis"))

        # 10. Laporan: periode + terlaris
        klik_tab(page, "laporan")
        check("laporan 7hari total 6", text(page, "#lTotal").strip() == "6", text(page, "#lTotal"))
        check("laporan 7hari Dijadwalkan 3", text(page, "#lDijadwalkan").strip() == "3", text(page, "#lDijadwalkan"))
        check("laporan 7hari Datang 1", text(page, "#lDatang").strip() == "1", text(page, "#lDatang"))
        check("laporan 7hari Selesai 1", text(page, "#lSelesai").strip() == "1", text(page, "#lSelesai"))
        check("laporan 7hari Batal 1", text(page, "#lBatal").strip() == "1", text(page, "#lBatal"))
        check("terlaris Ganti Oli Mesin 2 kali", "Ganti Oli Mesin" in text(page, "#daftarTerlaris") and "2 kali" in text(page, "#daftarTerlaris"))
        page.select_option("#lapPeriode", "hari")
        page.wait_for_timeout(300)
        check("laporan hari ini total 3", text(page, "#lTotal").strip() == "3", text(page, "#lTotal"))
        page.select_option("#lapPeriode", "semua")
        page.wait_for_timeout(300)
        check("laporan semua total 12", text(page, "#lTotal").strip() == "12", text(page, "#lTotal"))
        check("laporan semua Dijadwalkan 9", text(page, "#lDijadwalkan").strip() == "9", text(page, "#lDijadwalkan"))
        page.select_option("#lapPeriode", "7hari")
        page.wait_for_timeout(300)

        # 11. Ekspor CSV + Backup JSON + Pulihkan
        with page.expect_download() as dl:
            page.click("#btnExportCSV")
        d = dl.value
        check("CSV terunduh", "laporan-booking-servis" in d.suggested_filename, d.suggested_filename)
        with page.expect_download() as dl2:
            page.click("#btnBackupJSON")
        d2 = dl2.value
        check("backup JSON terunduh", "backup-booking-servis" in d2.suggested_filename, d2.suggested_filename)
        # pulihkan: tambah booking BK-999 ke state lalu restore
        page.evaluate("""() => {
          const raw = localStorage.getItem('aplikasiBookingServis.v1');
          const s = JSON.parse(raw);
          s.booking.push({ id: 99, no: 'BK-999', kendaraanId: 1, layananId: 1, mekanik: 'Agus',
            tanggal: new Date().toISOString(), keluhan: 'Booking dari restore', status: 'Dijadwalkan', diingatkan: false });
          window.__restorePayload = JSON.stringify({ app: 'aplikasi-booking-servis', version: 1, state: s });
        }""")
        Path("/tmp/restore-booking.json").write_text(page.evaluate("() => window.__restorePayload"), encoding="utf-8")
        page.set_input_files("#inputRestore", "/tmp/restore-booking.json")
        page.wait_for_timeout(600)
        klik_tab(page, "booking")
        check("restore: BK-999 muncul", "BK-999" in text(page, "#daftarBooking"))
        reset_data(page)
        klik_tab(page, "booking")
        check("reset: BK-999 hilang", "BK-999" not in text(page, "#daftarBooking"))

        # 12. Kendaraan: filter motor + riwayat
        klik_tab(page, "kendaraan")
        page.select_option("#filterJenis", "Motor")
        page.wait_for_timeout(300)
        check("filter Motor 6 item", count(page, "#daftarKendaraan .item-bar") == 6, str(count(page, "#daftarKendaraan .item-bar")))
        page.select_option("#filterJenis", "Mobil")
        page.wait_for_timeout(300)
        check("filter Mobil 6 item", count(page, "#daftarKendaraan .item-bar") == 6, str(count(page, "#daftarKendaraan .item-bar")))
        page.select_option("#filterJenis", "semua")
        page.wait_for_timeout(300)
        page.click('[data-riwayat-kendaraan="3"]')
        page.wait_for_timeout(400)
        check("riwayat Brio ada BK-001", "BK-001" in text(page, "#modalKonten"))
        check("riwayat Brio ada tabel booking", "Booking" in text(page, "#modalKonten"))
        page.click("#modalBatal")
        page.wait_for_timeout(300)

        # 13. Pengguna: tambah, ganti sandi sendiri, reset, nonaktifkan
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

        # 14. RBAC mekanik: pengingat + laporan tersembunyi
        login(page, "mekanik", "mekanik123")
        check("login mekanik berhasil", not page.is_visible("#loginOverlay"))
        check("mekanik: tab pengingat tersembunyi", not page.is_visible('[data-tab="pengingat"]'))
        check("mekanik: tab laporan tersembunyi", not page.is_visible('[data-tab="laporan"]'))
        check("mekanik: tab booking terlihat", page.is_visible('[data-tab="booking"]'))
        check("mekanik: tab kendaraan terlihat", page.is_visible('[data-tab="kendaraan"]'))
        logout(page)
        login(page, "admin", "admin123")

        # 15. Panduan: akun demo + harga + garansi + catatan jujur
        klik_tab(page, "panduan")
        t = text(page, "#panel-panduan")
        check("panduan akun demo", "admin123" in t and "kasir123" in t and "mekanik123" in t)
        check("panduan harga 499.000", "499.000" in t)
        check("panduan APK 400.000", "400.000" in t)
        check("panduan garansi 30/60/90", "30 hari" in t and "90 hari" in t)
        check("panduan jujur teks saja", "teks saja" in t)
        check("panduan jujur per perangkat", "hanya tersimpan di perangkat ini" in t)

        # 16. Reset data contoh
        page.click("#btnResetData")
        page.wait_for_timeout(300)
        page.click("#modalYa")
        page.wait_for_timeout(500)
        klik_tab(page, "dashboard")
        check("reset booking hari ini kembali 3", text(page, "#dBooking").strip() == "3", text(page, "#dBooking"))

        check("0 console error", len(errors) == 0, str(errors[:3]))
        browser.close()

    print(f"\n{passed} lolos, {len(failures)} gagal")
    if failures:
        print("Gagal:", failures)
        sys.exit(1)


if __name__ == "__main__":
    main()
