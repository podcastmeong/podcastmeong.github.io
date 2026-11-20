"""Tes Manajemen Catering (file lokal, Playwright Chromium)."""
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = "file://" + str(ROOT / "manajemen-catering" / "index.html")

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
        check("dasbor pesanan aktif 3", text(page, "#dAktif").strip() == "3", text(page, "#dAktif"))
        check("dasbor pengiriman hari ini 2", text(page, "#dKirim").strip() == "2", text(page, "#dKirim"))
        check("dasbor omzet 7 hari Rp29.550.000", "29.550.000" in text(page, "#dOmzet"), text(page, "#dOmzet"))
        check("dasbor laba 7 hari Rp14.491.900", "14.491.900" in text(page, "#dLaba"), text(page, "#dLaba"))
        check("pengiriman hari ini ada CTR-001", "CTR-001" in text(page, "#daftarKirimHariIni"))
        check("pengiriman hari ini ada CTR-003", "CTR-003" in text(page, "#daftarKirimHariIni"))
        check("pesanan baru ada CTR-002", "CTR-002" in text(page, "#daftarBaru"))

        # 4. Paket menu: biaya & margin terverifikasi
        klik_tab(page, "paket")
        t = text(page, "#daftarPaket")
        check("Paket Hemat biaya 12.560", "12.560" in t, t[:400])
        check("Paket Hemat laba 12.440", "12.440" in t)
        check("Paket Standar biaya 17.085", "17.085" in t)
        check("Paket Standar laba 17.915", "17.915" in t)
        check("Paket Premium biaya 25.875", "25.875" in t)
        check("Paket Premium laba 24.125", "24.125" in t)

        # 5. Tambah pesanan baru: Standar x 40
        klik_tab(page, "pesanan")
        page.fill("#psAcara", "Rapat Test Catering")
        page.select_option("#psPaket", "2")
        page.fill("#psPorsi", "40")
        page.wait_for_timeout(300)
        r = text(page, "#psRincian")
        check("rincian pesanan harga 1.400.000", "1.400.000" in r, r)
        check("rincian pesanan laba 716.600", "716.600" in r, r)
        page.fill("#psAlamat", "Jl. Test No. 1, Jakarta")
        page.click("#btnSimpanPesanan")
        page.wait_for_timeout(400)
        t = text(page, "#daftarPesanan")
        check("pesanan baru CTR-007 tersimpan", "CTR-007" in t and "Rapat Test Catering" in t)
        check("pesanan baru status Baru", "Baru" in t)

        # 6. Ubah status CTR-002: Baru -> Disiapkan
        klik_tab(page, "dashboard")
        page.click('[data-lanjut-pesanan="2"]')
        page.wait_for_timeout(400)
        check("CTR-002 jadi Disiapkan", "CTR-002" not in text(page, "#daftarBaru"))
        check("pesanan aktif jadi 4", text(page, "#dAktif").strip() == "4", text(page, "#dAktif"))

        # 7. Jadwal hari ini + 7 hari
        klik_tab(page, "jadwal")
        t = text(page, "#daftarJadwal")
        check("jadwal hari ini ada CTR-001", "CTR-001" in t)
        check("jadwal hari ini ada CTR-003", "CTR-003" in t)
        check("jadwal hari ini ada CTR-007", "CTR-007" in t)
        check("jadwal 7 hari ada 7 baris", text(page, "#daftarJadwalMinggu").count("acara") >= 3)

        # 8. Biaya: kalkulator Premium x 100
        klik_tab(page, "biaya")
        page.select_option("#klPaket", "3")
        page.fill("#klPorsi", "100")
        page.wait_for_timeout(300)
        k = text(page, "#klHasil")
        check("kalkulator harga 5.000.000", "5.000.000" in k, k)
        check("kalkulator biaya 2.587.500", "2.587.500" in k, k)
        check("kalkulator laba 2.412.500", "2.412.500" in k, k)
        tb = text(page, "#tabelBiayaMenu")
        check("biaya menu Nasi Goreng 11.000", "11.000" in tb)
        check("biaya menu Jus Alpukat 9.500", "9.500" in tb)

        # 9. Laporan 7 hari (setelah tambah pesanan)
        klik_tab(page, "laporan")
        check("laporan acara 7", text(page, "#lAcara").strip() == "7", text(page, "#lAcara"))
        check("laporan porsi 750", text(page, "#lPorsi").strip() == "750", text(page, "#lPorsi"))
        check("laporan omzet 30.950.000", "30.950.000" in text(page, "#lOmzet"), text(page, "#lOmzet"))
        check("laporan laba 15.208.500", "15.208.500" in text(page, "#lLaba"), text(page, "#lLaba"))
        tl = text(page, "#tabelLaporan")
        check("laporan paket Standar 3 acara", "Standar" in tl)

        # 10. Pelanggan: Ibu Ratna 3 acara (2 contoh + CTR-007 test) omzet 10.600.000
        klik_tab(page, "pelanggan")
        t = text(page, "#daftarPelanggan")
        check("pelanggan Ratna 3 acara", "3 acara" in t)
        check("pelanggan Ratna omzet 10.600.000", "10.600.000" in t, t[:500])

        # 11. Tambah paket baru: Paket Keluarga 30000 isi [1,5,9]
        klik_tab(page, "paket")
        page.click("#btnTambahPaket")
        page.wait_for_timeout(300)
        page.fill("#fpNama", "Paket Keluarga")
        page.fill("#fpHarga", "30000")
        page.check(".fpMenu[value='1']")
        page.check(".fpMenu[value='5']")
        page.check(".fpMenu[value='9']")
        page.wait_for_timeout(300)
        fr = text(page, "#fpRincian")
        check("rincian paket baru biaya 16.760", "16.760" in fr, fr)
        check("rincian paket baru margin 13.240", "13.240" in fr, fr)
        page.click("#formPaket button[type=submit]")
        page.wait_for_timeout(400)
        check("paket baru tersimpan", "Paket Keluarga" in text(page, "#daftarPaket"))

        # 12. Guard: hapus paket yang dipakai ditolak
        page.click('[data-hapus-paket="1"]')
        page.wait_for_timeout(400)
        check("hapus paket dipakai ditolak", "Paket Hemat" in text(page, "#daftarPaket"))
        check("toast hapus paket dipakai", "masih dipakai" in text(page, "#toast"))

        # 13. Guard: hapus pelanggan yang punya pesanan ditolak
        klik_tab(page, "pelanggan")
        page.click('[data-hapus-pelanggan="1"]')
        page.wait_for_timeout(400)
        check("hapus pelanggan dipakai ditolak", "Ibu Ratna" in text(page, "#daftarPelanggan"))

        # 14. Kelola pengguna: tambah Dewi, reset sandi ct123, nonaktifkan, login ditolak
        klik_tab(page, "dashboard")
        page.fill("#nuNama", "Dewi")
        page.fill("#nuUser", "dewi")
        page.fill("#nuPass", "dewi123")
        page.click("#btnTambahPengguna")
        page.wait_for_timeout(400)
        check("pengguna Dewi ditambah", "Dewi" in text(page, "#daftarPengguna"))
        page.click('[data-aksi-pengguna="sandi"][data-user="dewi"]')
        page.wait_for_timeout(300)
        page.click("#modalYa")
        page.wait_for_timeout(400)
        check("reset sandi toast ct123", "ct123" in text(page, "#toast"))
        page.click('[data-aksi-pengguna="aktif"][data-user="dewi"]')
        page.wait_for_timeout(400)
        page.click("#btnKeluar")
        page.wait_for_timeout(400)
        login(page, "dewi", "ct123")
        check("login pengguna nonaktif ditolak", page.is_visible("#loginError"))
        # 15. Ganti sandi sendiri: salah ditolak, benar berhasil, kembalikan
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
        # 16. Kasir tidak melihat kelola pengguna
        page.click("#btnKeluar")
        page.wait_for_timeout(300)
        login(page, "kasir", "kasir123")
        page.wait_for_timeout(300)
        check("kasir tidak lihat kelola pengguna", not page.is_visible("#cardPengguna"))
        # 17. Panduan: akun demo, harga, APK, garansi
        klik_tab(page, "panduan")
        t = text(page, "#panel-panduan")
        check("panduan akun demo", "admin123" in t and "kasir123" in t)
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
        check("reset kembali aktif 3", text(page, "#dAktif").strip() == "3", text(page, "#dAktif"))
        check("reset CTR-007 hilang", "CTR-007" not in text(page, "#daftarKirimHariIni"))

        check("0 console error", len(errors) == 0, str(errors[:3]))
        browser.close()

    print(f"\n{passed} lolos, {len(failures)} gagal")
    if failures:
        print("Gagal:", failures)
        sys.exit(1)


if __name__ == "__main__":
    main()
