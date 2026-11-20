"""Tes Manajemen Franchise Makanan (file lokal, Playwright Chromium)."""
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = "file://" + str(ROOT / "manajemen-franchise-makanan" / "index.html")

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
    page.wait_for_timeout(300)


def tab(page, name):
    page.click(f'[data-tab="{name}"]')
    page.wait_for_timeout(250)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        errors = []
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(URL)
        page.wait_for_timeout(500)

        # 1. Layar login + akun demo terlihat
        check("layar login tampil", page.is_visible("#loginOverlay"))
        check("kotak akun demo di login", "Akun demo" in text(page, ".login-note"))
        check("admin123 tampil di login", "admin123" in text(page, ".login-note"))

        # 2. Login salah ditolak
        login(page, "admin", "salah")
        check("login salah ditolak", page.is_visible("#loginOverlay") and page.is_visible("#loginError"))

        # 3. Login admin benar
        login(page, "admin", "admin123")
        check("login admin berhasil", not page.is_visible("#loginOverlay"))
        check("chip pengguna Admin", "Admin" in text(page, "#userChip"))

        # 4. Dashboard: 4 cabang aktif, omzet hari ini Rp151.000, transaksi 4, bahan kritis 6
        d = text(page, "#dCabang")
        check("dasbor cabang aktif = 4", d.strip() == "4", d)
        omzet = text(page, "#dOmzet")
        check("omzet hari ini Rp151.000", "151.000" in omzet, omzet)
        check("transaksi hari ini = 4", text(page, "#dTransaksi").strip() == "4")
        check("bahan kritis = 6", text(page, "#dKritis").strip() == "6", text(page, "#dKritis"))
        check("peringkat cabang ada 4 baris", "Pejaten" in text(page, "#tabelPeringkat") and "Kemang" in text(page, "#tabelPeringkat"))
        peringkat = text(page, "#tabelPeringkat")
        check("peringkat 1 Pejaten omzet 237.000", "237.000" in peringkat, peringkat[:400])
        check("peringatan kritis tampil (Telur Habis)", "Telur" in text(page, "#daftarPeringatan") and "Habis" in text(page, "#daftarPeringatan"))

        # 5. Kelola pengguna terlihat untuk admin
        check("kartu kelola pengguna tampil (admin)", page.is_visible("#cardPengguna"))

        # 6. Cabang: 4 cabang, detail Pejaten omzet 237.000
        tab(page, "cabang")
        check("daftar cabang 4", text(page, "#daftarCabang").count("Warung Kopi Oyen") >= 4)
        page.click('[data-lihat-cabang="1"]')
        page.wait_for_timeout(300)
        check("detail cabang Pejaten omzet 237.000", "237.000" in text(page, "#detailCabangIsi"))

        # 7. Tambah cabang baru (admin)
        page.click("#btnTambahCabang")
        page.wait_for_timeout(300)
        page.fill("#fcNama", "Warung Kopi Oyen — Tebet")
        page.fill("#fcAlamat", "Jl. Tebet Raya No.1")
        page.fill("#fcPj", "Rudi")
        page.fill("#fcTelp", "081299988877")
        page.click("#formCabang button[type=submit]")
        page.wait_for_timeout(400)
        check("cabang baru Tebet muncul", "Tebet" in text(page, "#daftarCabang"))
        tab(page, "dashboard")
        check("dasbor cabang aktif jadi 5", text(page, "#dCabang").strip() == "5", text(page, "#dCabang"))

        # 8. Ubah harga standar menu (admin) — Nasi Goreng 18000 -> 19000
        tab(page, "menu")
        check("menu standar 12 item", "Nasi Goreng Oyen" in text(page, "#daftarMenu"))
        page.click('[data-ubah-menu="1"]')
        page.wait_for_timeout(300)
        page.fill("#fmHarga", "19000")
        page.click("#formMenu button[type=submit]")
        page.wait_for_timeout(400)
        check("harga Nasi Goreng jadi Rp19.000", "19.000" in text(page, "#daftarMenu"))
        # harga baru berlaku di form penjualan
        tab(page, "penjualan")
        check("form penjualan pakai harga baru 19.000", "19.000" in text(page, "#pjBaris"))

        # 9. Tambah penjualan: 2x Nasi Goreng (19000) + 1x Es Teh (5000) = 43000
        page.select_option("#pjCabang", "2")
        page.click("#pjTambahBaris")
        page.wait_for_timeout(200)
        rows = page.query_selector_all("[data-baris-jual]")
        rows[0].query_selector(".jual-menu").select_option("1")
        rows[0].query_selector(".jual-qty").fill("2")
        rows[1].query_selector(".jual-menu").select_option("5")
        rows[1].query_selector(".jual-qty").fill("1")
        page.wait_for_timeout(300)
        check("total form penjualan Rp43.000", "43.000" in text(page, "#pjTotal"), text(page, "#pjTotal"))
        page.click("#btnSimpanPenjualan")
        page.wait_for_timeout(400)
        check("penjualan baru JUAL-015 tersimpan", "JUAL-015" in text(page, "#daftarPenjualan"))
        check("riwayat penjualan tampilkan Rp43.000", "43.000" in text(page, "#daftarPenjualan"))

        # 10. Stok: pilih Cilandak — Telur Habis; +Stok 12 butir -> Aman
        tab(page, "stok")
        page.select_option("#stokCabang", "3")
        page.wait_for_timeout(300)
        check("stok Cilandak Telur Habis", "Habis" in text(page, "#tabelStok"))
        page.click('[data-stok-masuk="3:3"]')
        page.wait_for_timeout(300)
        page.fill("#fsJumlah", "12")
        page.fill("#fsKet", "Beli telur 1 krat")
        page.click("#formStok button[type=submit]")
        page.wait_for_timeout(400)
        check("Telur Cilandak jadi 12 (aman)", "12 butir" in text(page, "#tabelStok") or "12" in text(page, "#tabelStok"))
        check("mutasi stok tercatat", "Beli telur" in text(page, "#riwayatMutasiStok"))

        # 11. Laporan 7 hari: seed 665.000 + revaluasi harga Nasi Goreng 18.000->19.000 (+7.000: 7 porsi) + penjualan baru 43.000 = 715.000; Kebagusan (241.000) menyalip Pejaten (239.000)
        tab(page, "laporan")
        check("laporan total omzet Rp715.000", "715.000" in text(page, "#lOmzet"), text(page, "#lOmzet"))
        check("laporan total transaksi 15", text(page, "#lTransaksi").strip() == "15", text(page, "#lTransaksi"))
        check("cabang terbaik Kebagusan", "Kebagusan" in text(page, "#lTop"), text(page, "#lTop"))
        check("tabel laporan Pejaten 239.000", "239.000" in text(page, "#tabelLaporan"), text(page, "#tabelLaporan")[:500])
        check("tabel laporan Kebagusan 241.000", "241.000" in text(page, "#tabelLaporan"))
        check("terlaris per cabang tampil", "Terlaris" in text(page, "#daftarTerlaris"))

        # 12. Tambah pengguna Dewi -> ubah peran -> reset sandi (fm123) -> nonaktifkan -> login ditolak
        tab(page, "dashboard")
        page.fill("#nuNama", "Dewi Lestari")
        page.fill("#nuUser", "dewi")
        page.fill("#nuPass", "dewi123")
        page.click("#btnTambahPengguna")
        page.wait_for_timeout(300)
        check("pengguna Dewi ditambahkan", "Dewi Lestari" in text(page, "#daftarPengguna"))
        page.click('[data-aksi-pengguna="peran"][data-user="dewi"]')
        page.wait_for_timeout(300)
        check("peran Dewi diubah ke Admin", "Dewi Lestari" in text(page, "#daftarPengguna"))
        page.click('[data-aksi-pengguna="sandi"][data-user="dewi"]')
        page.wait_for_timeout(300)
        page.click("#modalYa")
        page.wait_for_timeout(300)
        check("reset sandi toast fm123", "fm123" in text(page, "#toast"))
        page.click('[data-aksi-pengguna="aktif"][data-user="dewi"]')
        page.wait_for_timeout(300)
        check("Dewi dinonaktifkan", "Nonaktif" in text(page, "#daftarPengguna"))
        page.click("#btnKeluar")
        page.wait_for_timeout(300)
        login(page, "dewi", "fm123")
        check("login Dewi nonaktif ditolak", page.is_visible("#loginOverlay"))

        # 13. Ganti sandi sendiri (admin): salah ditolak, benar berhasil
        login(page, "admin", "admin123")
        page.wait_for_timeout(300)
        tab(page, "dashboard")
        page.fill("#sandiLama", "salah123")
        page.fill("#sandiBaru", "baru12345")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        check("ganti sandi lama salah ditolak", "lama salah" in text(page, "#toast"))
        page.fill("#sandiLama", "admin123")
        page.fill("#sandiBaru", "baru12345")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        check("ganti sandi berhasil", "berhasil diganti" in text(page, "#toast"))
        page.click("#btnKeluar")
        page.wait_for_timeout(300)
        login(page, "admin", "baru12345")
        check("login admin sandi baru berhasil", not page.is_visible("#loginOverlay"))
        # kembalikan sandi admin agar demo tetap admin123
        tab(page, "dashboard")
        page.fill("#sandiLama", "baru12345")
        page.fill("#sandiBaru", "admin123")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)

        # 14. Kasir: tidak melihat kelola pengguna + tidak bisa ubah menu standar
        page.click("#btnKeluar")
        page.wait_for_timeout(300)
        login(page, "kasir", "kasir123")
        check("login kasir berhasil", not page.is_visible("#loginOverlay"))
        check("kasir tidak melihat kelola pengguna", not page.is_visible("#cardPengguna"))
        tab(page, "menu")
        check("kasir tidak melihat tombol ubah menu", page.query_selector('[data-ubah-menu="1"]') is None)
        check("kasir tidak melihat tombol tambah menu", not page.is_visible("#btnTambahMenu"))
        tab(page, "cabang")
        check("kasir bisa lihat daftar cabang", "Pejaten" in text(page, "#daftarCabang"))

        # 15. Panduan: akun demo, harga, APK, garansi
        tab(page, "panduan")
        panduan = text(page, "#panel-panduan")
        check("panduan akun demo", "Akun demo" in panduan and "admin123" in panduan)
        check("panduan harga Rp499.000", "Rp499.000" in panduan)
        check("panduan APK +Rp400.000", "Rp400.000" in panduan)
        check("panduan garansi 30/60/90", "30 hari" in panduan and "90 hari" in panduan)
        check("panduan batas satu perangkat", "satu perangkat" in panduan)

        # 16. Reset data contoh -> kembali 4 cabang, omzet hari ini 151.000
        page.click("#btnResetData")
        page.wait_for_timeout(300)
        page.click("#modalYa")
        page.wait_for_timeout(400)
        tab(page, "dashboard")
        check("reset: cabang aktif kembali 4", text(page, "#dCabang").strip() == "4", text(page, "#dCabang"))
        check("reset: omzet hari ini kembali 151.000", "151.000" in text(page, "#dOmzet"), text(page, "#dOmzet"))
        check("reset: bahan kritis kembali 6", text(page, "#dKritis").strip() == "6")

        # 17. Tidak ada console/page error
        check("0 console error", len(errors) == 0, str(errors[:3]))

        browser.close()

    print(f"\n{passed} lolos, {len(failures)} gagal")
    if failures:
        print("GAGAL:", failures)
        sys.exit(1)


if __name__ == "__main__":
    main()
