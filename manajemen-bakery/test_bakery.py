"""Tes Manajemen Bakery (file lokal, Playwright Chromium)."""
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = "file://" + str(ROOT / "manajemen-bakery" / "index.html")

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
        check("dasbor produksi hari ini 3", text(page, "#dProduksi").strip() == "3", text(page, "#dProduksi"))
        check("dasbor pesanan aktif 3", text(page, "#dPesanan").strip() == "3", text(page, "#dPesanan"))
        check("dasbor omzet 7 hari Rp1.530.000", "1.530.000" in text(page, "#dOmzet"), text(page, "#dOmzet"))
        check("dasbor laba 7 hari Rp785.260", "785.260" in text(page, "#dLaba"), text(page, "#dLaba"))
        check("peringatan meses menipis", "Meses Cokelat" in text(page, "#daftarPeringatan"))
        check("peringatan kadaluarsa dekat 6", "Mendekati kadaluarsa (6)" in text(page, "#daftarPeringatan"), text(page, "#daftarPeringatan")[:400])
        check("peringatan susu cair", "Susu Cair" in text(page, "#daftarPeringatan"))
        check("produksi hari ini ada PRD-001", "PRD-001" in text(page, "#daftarProduksiHariIni"))
        check("produksi hari ini ada PRD-003", "PRD-003" in text(page, "#daftarProduksiHariIni"))
        check("pesanan baru ada BKY-001", "BKY-001" in text(page, "#daftarBaru"))
        check("pesanan baru ada BKY-003", "BKY-003" in text(page, "#daftarBaru"))

        # 4. Produk: biaya & margin terverifikasi
        klik_tab(page, "produk")
        t = text(page, "#daftarProduk")
        check("Roti Sobek biaya 16.120", "16.120" in t, t[:500])
        check("Roti Sobek laba 8.880", "8.880" in t)
        check("Croissant stok 18 pcs", "Stok 18 pcs" in t)
        check("Donat Cokelat biaya 3.755", "3.755" in t)

        # 5. Bahan: stok & status
        klik_tab(page, "bahan")
        t = text(page, "#daftarBahan")
        check("Meses stok 0,8 kg menipis", "0,8 kg" in t and "Menipis" in t, t[:400])
        check("Tepung stok 25 kg", "25 kg" in t)

        # 6. Tambah bahan baru: Cokelat Putih
        page.click("#btnTambahBahan")
        page.wait_for_timeout(300)
        page.fill("#fbNama", "Cokelat Putih")
        page.fill("#fbStok", "2")
        page.fill("#fbHarga", "95000")
        page.fill("#fbMin", "1")
        page.fill("#fbExp", "2027-06-01")
        page.click("#formBahan button[type=submit]")
        page.wait_for_timeout(400)
        check("bahan Cokelat Putih tersimpan", "Cokelat Putih" in text(page, "#daftarBahan"))

        # 7. Ubah stok Meses 0,8 -> 5: peringatan menipis hilang
        page.click('[data-stok-bahan="8"]')
        page.wait_for_timeout(300)
        page.fill("#fsStok", "5")
        page.click("#formStok button[type=submit]")
        page.wait_for_timeout(400)
        klik_tab(page, "dashboard")
        check("Meses tidak lagi di peringatan", "Meses" not in text(page, "#daftarPeringatan"), text(page, "#daftarPeringatan")[:400])

        # 8. Guard: hapus bahan yang dipakai resep ditolak
        klik_tab(page, "bahan")
        page.click('[data-hapus-bahan="1"]')
        page.wait_for_timeout(400)
        check("hapus bahan dipakai ditolak", "Tepung Terigu" in text(page, "#daftarBahan"))
        check("toast hapus bahan dipakai", "masih dipakai" in text(page, "#toast"))

        # 9. Tambah produk baru: Roti Keju Rp11.000
        klik_tab(page, "produk")
        page.click("#btnTambahProduk")
        page.wait_for_timeout(300)
        page.fill("#fprNama", "Roti Keju")
        page.fill("#fprHarga", "11000")
        page.fill("#fprStok", "10")
        for bid, jml in [("1", "0.07"), ("9", "0.02"), ("3", "0.01"), ("2", "0.01"), ("4", "0.2"), ("6", "1")]:
            page.check(f'.fpBahan[value="{bid}"]')
            page.fill(f'.fpJumlah[data-bahan="{bid}"]', jml)
        page.wait_for_timeout(300)
        fr = text(page, "#fprRincian")
        check("rincian produk baru biaya 4.210", "4.210" in fr, fr)
        check("rincian produk baru margin 6.790", "6.790" in fr)
        page.click("#formProduk button[type=submit]")
        page.wait_for_timeout(400)
        check("produk Roti Keju tersimpan", "Roti Keju" in text(page, "#daftarProduk"))

        # 10. Guard: hapus produk yang dipakai ditolak
        page.click('[data-hapus-produk="1"]')
        page.wait_for_timeout(400)
        check("hapus produk dipakai ditolak", "Roti Sobek Cokelat" in text(page, "#daftarProduk"))

        # 11. Produksi: tambah batch Croissant x10, rincian bahan 0,8 kg tepung
        klik_tab(page, "produksi")
        page.select_option("#pdProduk", "6")
        page.fill("#pdJumlah", "10")
        page.wait_for_timeout(300)
        r = text(page, "#pdRincian")
        check("rincian produksi tepung 0,8 kg", "0,8 kg" in r, r)
        page.click("#btnSimpanProduksi")
        page.wait_for_timeout(400)
        check("batch baru PRD-007 tersimpan", "PRD-007" in text(page, "#daftarProduksi"))

        # 12. Selesaikan PRD-003 (Roti Unyil x60): bahan berkurang, stok produk naik
        page.click('#daftarProduksi [data-lanjut-produksi="3"]')
        page.wait_for_timeout(400)
        klik_tab(page, "bahan")
        t = text(page, "#daftarBahan")
        check("tepung jadi 21,4 kg", "21,4 kg" in t, t[:500])
        klik_tab(page, "produk")
        check("Roti Unyil stok jadi 100", "Stok 100 pcs" in text(page, "#daftarProduk"))

        # 13. Pesanan: tambah pesanan Roti Tawar x2 untuk Ibu Ratna
        klik_tab(page, "pesanan")
        page.select_option("#psPelanggan", "1")
        page.select_option("#psProduk", "7")
        page.fill("#psJumlah", "2")
        page.wait_for_timeout(300)
        r = text(page, "#psRincian")
        check("rincian pesanan harga 40.000", "40.000" in r, r)
        check("rincian pesanan laba 19.840", "19.840" in r)
        page.fill("#psAlamat", "Jl. Test No. 1, Jakarta")
        page.click("#btnSimpanPesanan")
        page.wait_for_timeout(400)
        check("pesanan baru BKY-007 tersimpan", "BKY-007" in text(page, "#daftarPesanan"))

        # 14. Selesaikan BKY-002 (Bolu Pandan x2): stok turun, omzet naik
        page.click('#daftarPesanan [data-lanjut-pesanan="2"]')
        page.wait_for_timeout(400)
        klik_tab(page, "dashboard")
        check("omzet 7 hari jadi 1.620.000", "1.620.000" in text(page, "#dOmzet"), text(page, "#dOmzet"))
        check("laba 7 hari jadi 823.360", "823.360" in text(page, "#dLaba"), text(page, "#dLaba"))
        klik_tab(page, "produk")
        check("Bolu Pandan stok jadi 3", "Bolu Pandan" in text(page, "#daftarProduk") and "Stok 3 pcs" in text(page, "#daftarProduk"))

        # 15. Kasir: jual Roti Sobek x2, bayar 100.000, kembalian 50.000
        klik_tab(page, "kasir")
        page.select_option("#ksProduk", "1")
        page.fill("#ksJumlah", "2")
        page.click("#btnTambahKeranjang")
        page.wait_for_timeout(300)
        check("keranjang total 50.000", "50.000" in text(page, "#ksRincian"), text(page, "#ksRincian"))
        page.fill("#ksBayar", "100000")
        page.wait_for_timeout(200)
        check("kembalian 50.000", text(page, "#ksRincian").count("50.000") >= 2, text(page, "#ksRincian"))
        page.click("#btnSimpanPenjualan")
        page.wait_for_timeout(400)
        check("penjualan JUAL-009 tersimpan", "JUAL-009" in text(page, "#daftarPenjualan"))
        check("toast JUAL-009 kembalian 50.000", "JUAL-009" in text(page, "#toast") and "50.000" in text(page, "#toast"))
        klik_tab(page, "produk")
        check("Roti Sobek stok jadi 10", "Stok 10 pcs" in text(page, "#daftarProduk"))

        # 16. Laporan 7 hari setelah mutasi
        klik_tab(page, "laporan")
        check("laporan transaksi 13", text(page, "#lTransaksi").strip() == "13", text(page, "#lTransaksi"))
        check("laporan unit 140", text(page, "#lUnit").strip() == "140", text(page, "#lUnit"))
        check("laporan omzet 1.670.000", "1.670.000" in text(page, "#lOmzet"), text(page, "#lOmzet"))
        check("laporan laba 841.120", "841.120" in text(page, "#lLaba"), text(page, "#lLaba"))
        tl = text(page, "#tabelLaporan")
        check("laporan Croissant omzet 408.000", "408.000" in tl, tl[:400])
        check("terlaris Croissant 34 pcs", "Croissant Mentega" in text(page, "#daftarTerlaris") and "34 pcs" in text(page, "#daftarTerlaris"))

        # 17. Ekspor CSV
        with page.expect_download() as dl_info:
            page.click("#btnExportCSV")
        dl = dl_info.value
        check("CSV nama file", "csv" in dl.suggested_filename, dl.suggested_filename)
        csv_path = Path("/tmp/bakery-test-laporan.csv")
        dl.save_as(csv_path)
        isi_csv = csv_path.read_text(encoding="utf-8")
        check("CSV berisi JUAL-001", "JUAL-001" in isi_csv)
        check("CSV berisi Croissant", "Croissant" in isi_csv)

        # 18. Backup JSON + pulihkan
        with page.expect_download() as dl_info2:
            page.click("#btnBackupJSON")
        dl2 = dl_info2.value
        check("JSON nama file", "json" in dl2.suggested_filename, dl2.suggested_filename)
        backup_path = Path("/tmp/bakery-test-backup.json")
        dl2.save_as(backup_path)
        check("backup berisi Roti Keju", "Roti Keju" in backup_path.read_text(encoding="utf-8"))
        klik_tab(page, "bahan")
        page.click("#btnTambahBahan")
        page.wait_for_timeout(300)
        page.fill("#fbNama", "Bahan Test Restore")
        page.fill("#fbStok", "1")
        page.fill("#fbHarga", "1000")
        page.fill("#fbMin", "1")
        page.fill("#fbExp", "2027-01-01")
        page.click("#formBahan button[type=submit]")
        page.wait_for_timeout(400)
        check("bahan test restore ditambah", "Bahan Test Restore" in text(page, "#daftarBahan"))
        klik_tab(page, "laporan")
        page.click("#btnPulihkan")
        page.wait_for_timeout(300)
        page.set_input_files("#inputRestore", str(backup_path))
        page.wait_for_timeout(600)
        klik_tab(page, "bahan")
        check("restore hapus bahan test", "Bahan Test Restore" not in text(page, "#daftarBahan"))
        klik_tab(page, "produk")
        check("restore Roti Keju tetap ada", "Roti Keju" in text(page, "#daftarProduk"))

        # 19. Kelola pengguna: tambah Dewi, reset sandi bk123, nonaktifkan, login ditolak
        klik_tab(page, "dashboard")
        page.fill("#nuNama", "Dewi")
        page.fill("#nuUser", "dewi")
        page.fill("#nuPass", "dewi123")
        page.select_option("#nuPeran", "produksi")
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
        # 20. Ganti sandi sendiri: salah ditolak, benar berhasil, kembalikan
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
        # 21. Kasir tidak melihat kelola pengguna
        page.click("#btnKeluar")
        page.wait_for_timeout(300)
        login(page, "kasir", "kasir123")
        page.wait_for_timeout(300)
        check("kasir tidak lihat kelola pengguna", not page.is_visible("#cardPengguna"))
        # 22. Produksi tidak melihat tab pesanan/kasir/laporan
        page.click("#btnKeluar")
        page.wait_for_timeout(300)
        login(page, "produksi", "produksi123")
        page.wait_for_timeout(300)
        check("produksi tidak lihat tab pesanan", not page.is_visible('[data-tab="pesanan"]'))
        check("produksi tidak lihat tab kasir", not page.is_visible('[data-tab="kasir"]'))
        check("produksi tidak lihat tab laporan", not page.is_visible('[data-tab="laporan"]'))
        check("produksi lihat tab produksi", page.is_visible('[data-tab="produksi"]'))
        # 23. Panduan: akun demo, harga, APK, garansi
        klik_tab(page, "panduan")
        t = text(page, "#panel-panduan")
        check("panduan akun demo", "admin123" in t and "kasir123" in t and "produksi123" in t)
        check("panduan harga 499.000", "499.000" in t)
        check("panduan APK 400.000", "400.000" in t)
        check("panduan garansi 30/60/90", "30 hari" in t and "90 hari" in t)
        # 24. Reset data contoh (butuh admin)
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
        check("reset produksi hari ini 3", text(page, "#dProduksi").strip() == "3", text(page, "#dProduksi"))
        check("reset omzet kembali 1.530.000", "1.530.000" in text(page, "#dOmzet"), text(page, "#dOmzet"))
        klik_tab(page, "pesanan")
        check("reset BKY-007 hilang", "BKY-007" not in text(page, "#daftarPesanan"))

        check("0 console error", len(errors) == 0, str(errors[:3]))
        browser.close()

    print(f"\n{passed} lolos, {len(failures)} gagal")
    if failures:
        print("Gagal:", failures)
        sys.exit(1)


if __name__ == "__main__":
    main()
