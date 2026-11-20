"""Tes Aplikasi Stok Spare Part (file lokal, Playwright Chromium)."""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = "file://" + str(ROOT / "aplikasi-stok-spare-part" / "index.html")

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

        # 3. Dashboard data contoh (nilai dihitung independen via Python sebelum ditulis)
        check("dasbor nilai persediaan Rp27.200.000", "27.200.000" in text(page, "#dNilai"), text(page, "#dNilai"))
        check("dasbor menipis 3 (1 habis)", text(page, "#dMenipis").strip() == "3 (1 habis)", text(page, "#dMenipis"))
        check("dasbor omzet 7 hari Rp4.680.000", "4.680.000" in text(page, "#dOmzet"), text(page, "#dOmzet"))
        check("dasbor laba 7 hari Rp1.450.000", "1.450.000" in text(page, "#dLaba"), text(page, "#dLaba"))
        check("dasbor masuk 7 hari 55 pcs", text(page, "#dMasuk").strip() == "55 pcs", text(page, "#dMasuk"))
        check("dasbor keluar 7 hari 30 pcs", text(page, "#dKeluar").strip() == "30 pcs", text(page, "#dKeluar"))
        check("dasbor total barang 17", text(page, "#dTotalBarang").strip() == "17", text(page, "#dTotalBarang"))
        check("dasbor penjualan hari ini 1", text(page, "#dJualHariIni").strip() == "1", text(page, "#dJualHariIni"))
        check("badge menipis 3", text(page, "#badgeMenipis").strip() == "3", text(page, "#badgeMenipis"))
        check("badge masuk hari ini 1", text(page, "#badgeMasuk").strip() == "1", text(page, "#badgeMasuk"))
        check("peringatan Filter Bensin", "Filter Bensin" in text(page, "#daftarPeringatan"))
        check("peringatan Ban 185/65 menipis", "Ban 185/65 R15" in text(page, "#daftarPeringatan"))
        check("peringatan V-Belt habis", "V-Belt Motor Matic" in text(page, "#daftarPeringatan"))
        check("gerakan hari ini BM-008", "BM-008" in text(page, "#daftarGerakanHariIni"))
        check("gerakan hari ini PJ-007", "PJ-007" in text(page, "#daftarGerakanHariIni"))
        check("gerakan hari ini PK-003", "PK-003" in text(page, "#daftarGerakanHariIni"))
        check("terlaris Busi Iridium 6 pcs", "Busi Iridium" in text(page, "#daftarTerlaris") and "6 pcs" in text(page, "#daftarTerlaris"), text(page, "#daftarTerlaris")[:300])

        # 4. Spare part: status + riwayat per barang + tambah + ubah + guard hapus
        klik_tab(page, "sparepart")
        t = text(page, "#daftarPart")
        check("part V-Belt Habis", "V-Belt Motor Matic" in t and "Habis" in t)
        check("part Filter Bensin Menipis", "Filter Bensin" in t and "Menipis" in t)
        check("part Filter Oli stok 30", "Filter Oli" in t and "Stok 30 pcs" in t, t[:500])
        page.click('[data-riwayat-part="3"]')
        page.wait_for_timeout(400)
        m = text(page, "#modalKonten")
        check("riwayat Filter Oli ada BM-004", "BM-004" in m, m[:500])
        check("riwayat Filter Oli ada PJ-001", "PJ-001" in m)
        check("riwayat Filter Oli ada PK-001", "PK-001" in m)
        page.click("#modalBatal")
        page.wait_for_timeout(300)
        check("tombol hapus Filter Oli tidak ada (dipakai transaksi)", page.query_selector('[data-hapus-part="3"]') is None)
        page.click("#btnTambahPart")
        page.wait_for_timeout(300)
        page.fill("#fpNama", "Kabel Busi")
        page.fill("#fpMerek", "NGK")
        page.fill("#fpStok", "5")
        page.fill("#fpBeli", "20000")
        page.fill("#fpJual", "35000")
        page.click("#formPart button[type=submit]")
        page.wait_for_timeout(400)
        check("part Kabel Busi ditambah", "Kabel Busi" in text(page, "#daftarPart"))
        check("tombol hapus Kabel Busi ada (belum dipakai)", page.query_selector('[data-hapus-part="18"]') is not None)
        page.click('[data-ubah-part="18"]')
        page.wait_for_timeout(300)
        page.fill("#fpJual", "40000")
        page.click("#formPart button[type=submit]")
        page.wait_for_timeout(400)
        check("ubah Kabel Busi harga jual 40.000", "40.000" in text(page, "#daftarPart"), text(page, "#daftarPart")[:600])

        # 5. Supplier: tambah + hapus
        klik_tab(page, "supplier")
        page.click("#btnTambahSupplier")
        page.wait_for_timeout(300)
        page.fill("#fsNama", "PT Test Supplier")
        page.fill("#fsTelp", "081200000000")
        page.click("#formSupplier button[type=submit]")
        page.wait_for_timeout(400)
        check("supplier PT Test Supplier ditambah", "PT Test Supplier" in text(page, "#daftarSupplier"))
        page.click('[data-hapus-supplier="7"]')
        page.wait_for_timeout(300)
        page.click("#modalYa")
        page.wait_for_timeout(400)
        check("supplier PT Test Supplier dihapus", "PT Test Supplier" not in text(page, "#daftarSupplier"))

        # 6. Pembelian BM-009: Busi Iridium +5 -> stok 45
        klik_tab(page, "pembelian")
        page.select_option("#pbSupplier", "1")
        page.select_option("#pbPart", "11")
        page.fill("#pbJumlah", "5")
        page.fill("#pbHarga", "35000")
        page.click("#btnSimpanPembelian")
        page.wait_for_timeout(400)
        check("pembelian BM-009 tersimpan", "BM-009" in text(page, "#daftarPembelian"))
        check("toast stok Busi jadi 45", "menjadi 45" in text(page, "#toast"), text(page, "#toast"))
        klik_tab(page, "sparepart")
        check("Busi Iridium stok jadi 45", "Busi Iridium" in text(page, "#daftarPart") and "Stok 45 pcs" in text(page, "#daftarPart"), text(page, "#daftarPart")[:600])

        # 7. Pemakaian: guard stok habis + sukses
        klik_tab(page, "pemakaian")
        page.select_option("#pkPart", "16")
        page.fill("#pkJumlah", "1")
        page.fill("#pkAlasan", "Test pemakaian V-Belt habis")
        page.click("#btnSimpanPemakaian")
        page.wait_for_timeout(400)
        check("pemakaian V-Belt habis ditolak", "tidak cukup" in text(page, "#toast"), text(page, "#toast"))
        page.select_option("#pkPart", "3")
        page.fill("#pkJumlah", "1")
        page.fill("#pkAlasan", "Servis berkala test")
        page.click("#btnSimpanPemakaian")
        page.wait_for_timeout(400)
        check("pemakaian PK-004 tersimpan", "PK-004" in text(page, "#daftarPemakaian"))
        check("toast stok Filter Oli jadi 29", "menjadi 29" in text(page, "#toast"), text(page, "#toast"))

        # 8. Opname: Filter Udara 15 -> 12, selisih -3
        klik_tab(page, "opname")
        page.select_option("#opPart", "4")
        page.wait_for_timeout(300)
        check("opname rincian stok tercatat 15", "15" in text(page, "#opRincian"), text(page, "#opRincian"))
        page.fill("#opHitung", "12")
        page.fill("#opAlasan", "3 pcs hilang di rak")
        page.click("#btnSimpanOpname")
        page.wait_for_timeout(400)
        check("opname OP-004 tersimpan", "OP-004" in text(page, "#daftarOpname"))
        check("opname selisih -3", "Selisih -3" in text(page, "#daftarOpname"), text(page, "#daftarOpname")[:400])
        check("toast opname 15 ke 12", "15" in text(page, "#toast") and "12" in text(page, "#toast"), text(page, "#toast"))

        # 9. Riwayat: filter per barang + per jenis
        klik_tab(page, "riwayat")
        page.select_option("#filterRiwayatPart", "3")
        page.wait_for_timeout(300)
        rt = text(page, "#tabelRiwayat")
        check("riwayat Filter Oli ada PJ-001", "PJ-001" in rt, rt[:500])
        check("riwayat Filter Oli ada PK-001", "PK-001" in rt)
        check("riwayat Filter Oli ada BM-004", "BM-004" in rt)
        page.select_option("#filterRiwayatPart", "semua")
        page.select_option("#filterRiwayatJenis", "Masuk")
        page.wait_for_timeout(300)
        check("riwayat jenis Masuk ada BM-008", "BM-008" in text(page, "#tabelRiwayat"))

        # 10. Kasir: guard stok habis + penjualan PJ-008
        klik_tab(page, "kasir")
        page.select_option("#ksPart", "16")
        page.fill("#ksJumlah", "1")
        page.click("#btnTambahKeranjang")
        page.wait_for_timeout(400)
        check("kasir V-Belt habis ditolak", "tidak cukup" in text(page, "#toast"), text(page, "#toast"))
        page.select_option("#ksPart", "3")
        page.fill("#ksJumlah", "1")
        page.click("#btnTambahKeranjang")
        page.wait_for_timeout(300)
        page.select_option("#ksPart", "1")
        page.fill("#ksJumlah", "2")
        page.click("#btnTambahKeranjang")
        page.wait_for_timeout(300)
        check("keranjang total 235.000", "235.000" in text(page, "#ksRincian"), text(page, "#ksRincian"))
        page.fill("#ksBayar", "250000")
        page.wait_for_timeout(200)
        check("kembalian 15.000", "15.000" in text(page, "#ksRincian"), text(page, "#ksRincian"))
        page.fill("#ksPelanggan", "Bapak Test")
        page.click("#btnSimpanPenjualan")
        page.wait_for_timeout(400)
        check("penjualan PJ-008 tersimpan", "PJ-008" in text(page, "#daftarPenjualan"))
        check("toast PJ-008 kembalian 15.000", "PJ-008" in text(page, "#toast") and "15.000" in text(page, "#toast"))
        klik_tab(page, "sparepart")
        check("Filter Oli stok jadi 28", "Filter Oli" in text(page, "#daftarPart") and "Stok 28 pcs" in text(page, "#daftarPart"), text(page, "#daftarPart")[:600])
        check("Oli 10W-40 stok jadi 22", "Oli Mesin 10W-40" in text(page, "#daftarPart") and "Stok 22" in text(page, "#daftarPart"))
        klik_tab(page, "dashboard")
        check("omzet 7 hari jadi 4.915.000", "4.915.000" in text(page, "#dOmzet"), text(page, "#dOmzet"))
        check("laba 7 hari jadi 1.530.000", "1.530.000" in text(page, "#dLaba"), text(page, "#dLaba"))
        check("nilai persediaan jadi 27.160.000", "27.160.000" in text(page, "#dNilai"), text(page, "#dNilai"))

        # 11. Laporan 7 hari setelah mutasi
        klik_tab(page, "laporan")
        check("laporan transaksi 8", text(page, "#lTransaksi").strip() == "8", text(page, "#lTransaksi"))
        check("laporan terjual 29 pcs", text(page, "#lTerjual").strip() == "29 pcs", text(page, "#lTerjual"))
        check("laporan omzet 4.915.000", "4.915.000" in text(page, "#lOmzet"), text(page, "#lOmzet"))
        check("laporan laba 1.530.000", "1.530.000" in text(page, "#lLaba"), text(page, "#lLaba"))
        check("laporan pembelian 9", text(page, "#lPembelian").strip() == "9", text(page, "#lPembelian"))
        check("laporan nilai beli 6.355.000", "6.355.000" in text(page, "#lNilaiBeli"), text(page, "#lNilaiBeli"))
        check("laporan masuk 60 pcs", text(page, "#lMasuk").strip() == "60 pcs", text(page, "#lMasuk"))
        check("laporan nilai persediaan 27.160.000", "27.160.000" in text(page, "#lNilai"), text(page, "#lNilai"))
        check("terlaris Oli 10W-40 6 pcs", "Oli Mesin 10W-40" in text(page, "#daftarTerlarisLap") and "6 pcs" in text(page, "#daftarTerlarisLap"), text(page, "#daftarTerlarisLap")[:300])

        # 12. Ekspor CSV
        with page.expect_download() as dl_info:
            page.click("#btnExportCSV")
        dl = dl_info.value
        check("CSV nama file", "csv" in dl.suggested_filename, dl.suggested_filename)
        csv_path = Path("/tmp/sparepart-test-laporan.csv")
        dl.save_as(csv_path)
        isi_csv = csv_path.read_text(encoding="utf-8")
        check("CSV berisi PJ-001", "PJ-001" in isi_csv)
        check("CSV berisi Busi Iridium", "Busi Iridium" in isi_csv)

        # 13. Backup JSON + pulihkan
        with page.expect_download() as dl_info2:
            page.click("#btnBackupJSON")
        dl2 = dl_info2.value
        check("JSON nama file", "json" in dl2.suggested_filename, dl2.suggested_filename)
        backup_path = Path("/tmp/sparepart-test-backup.json")
        dl2.save_as(backup_path)
        check("backup berisi PJ-008", "PJ-008" in backup_path.read_text(encoding="utf-8"))
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
        klik_tab(page, "kasir")
        check("restore PJ-008 tetap ada", "PJ-008" in text(page, "#daftarPenjualan"))

        # 14. Kelola pengguna: tambah Dewi, reset sandi bk123, nonaktifkan, login ditolak
        klik_tab(page, "dashboard")
        page.fill("#nuNama", "Dewi")
        page.fill("#nuUser", "dewi")
        page.fill("#nuPass", "dewi123")
        page.select_option("#nuPeran", "gudang")
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
        # 16. Gudang tidak melihat kelola pengguna, kasir, laporan
        page.click("#btnKeluar")
        page.wait_for_timeout(300)
        login(page, "gudang", "gudang123")
        page.wait_for_timeout(300)
        check("gudang tidak lihat kelola pengguna", not page.is_visible("#cardPengguna"))
        check("gudang tidak lihat tab kasir", not page.is_visible('[data-tab="kasir"]'))
        check("gudang tidak lihat tab laporan", not page.is_visible('[data-tab="laporan"]'))
        check("gudang lihat tab supplier", page.is_visible('[data-tab="supplier"]'))
        check("gudang lihat tab pembelian", page.is_visible('[data-tab="pembelian"]'))
        check("gudang lihat tab pemakaian", page.is_visible('[data-tab="pemakaian"]'))
        check("gudang lihat tab opname", page.is_visible('[data-tab="opname"]'))
        # 17. Kasir tidak melihat kelola pengguna, supplier, pembelian, pemakaian, opname; spare part read-only
        page.click("#btnKeluar")
        page.wait_for_timeout(300)
        login(page, "kasir", "kasir123")
        page.wait_for_timeout(300)
        check("kasir tidak lihat kelola pengguna", not page.is_visible("#cardPengguna"))
        check("kasir tidak lihat tab supplier", not page.is_visible('[data-tab="supplier"]'))
        check("kasir tidak lihat tab pembelian", not page.is_visible('[data-tab="pembelian"]'))
        check("kasir tidak lihat tab pemakaian", not page.is_visible('[data-tab="pemakaian"]'))
        check("kasir tidak lihat tab opname", not page.is_visible('[data-tab="opname"]'))
        check("kasir lihat tab kasir", page.is_visible('[data-tab="kasir"]'))
        check("kasir lihat tab laporan", page.is_visible('[data-tab="laporan"]'))
        klik_tab(page, "sparepart")
        check("kasir tidak ada tombol ubah part (read-only)", page.query_selector('[data-ubah-part]') is None)
        # 18. Panduan: akun demo, harga, APK, garansi
        klik_tab(page, "panduan")
        t = text(page, "#panel-panduan")
        check("panduan akun demo", "admin123" in t and "gudang123" in t and "kasir123" in t)
        check("panduan harga 499.000", "499.000" in t)
        check("panduan APK 400.000", "400.000" in t)
        check("panduan garansi 30/60/90", "30 hari" in t and "90 hari" in t)
        # 19. Reset data contoh (butuh admin)
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
        check("reset nilai kembali 27.200.000", "27.200.000" in text(page, "#dNilai"), text(page, "#dNilai"))
        klik_tab(page, "kasir")
        check("reset PJ-008 hilang", "PJ-008" not in text(page, "#daftarPenjualan"))
        klik_tab(page, "sparepart")
        check("reset Kabel Busi hilang", "Kabel Busi" not in text(page, "#daftarPart"))

        check("0 console error", len(errors) == 0, str(errors[:3]))
        browser.close()

    print(f"\n{passed} lolos, {len(failures)} gagal")
    if failures:
        print("Gagal:", failures)
        sys.exit(1)


if __name__ == "__main__":
    main()
