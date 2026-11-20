"""Tes Kasir Toko Level 3 (file lokal, Playwright Chromium)."""
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = "file://" + str(ROOT / "kasir-toko" / "index.html")

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
    page.click("#logoutBtn")
    page.wait_for_timeout(300)


def klik_tab(page, tab):
    page.click(f'[data-tab="{tab}"]')
    page.wait_for_timeout(300)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(accept_downloads=True)
        page = ctx.new_page()
        errors = []
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("dialog", lambda d: d.accept())
        page.goto(URL)
        page.wait_for_timeout(500)
        page.evaluate("localStorage.clear()")
        page.reload()
        page.wait_for_timeout(500)

        # 1. Layar login menampilkan akun demo
        # judul "Akun demo" dirender huruf besar oleh CSS (text-transform: uppercase)
        check("login menampilkan 'Akun demo'", "AKUN DEMO" in text(page, "#demoAccounts"))
        check("login menampilkan admin/admin123", "admin" in text(page, "#demoAccounts") and "admin123" in text(page, "#demoAccounts"))
        check("login menampilkan kasir/kasir123", "kasir123" in text(page, "#demoAccounts"))
        check("login menampilkan gudang/gudang123", "gudang123" in text(page, "#demoAccounts"))
        check("login menampilkan CONTOH DEMO", "CONTOH DEMO" in text(page, "#demoAccounts"))

        # 2. Login salah ditolak, login admin benar
        login(page, "admin", "salah")
        check("login salah ditolak", page.is_visible("#loginError"))
        login(page, "admin", "admin123")
        check("login admin berhasil", not page.is_visible("#loginOverlay"))
        check("chip pengguna admin (Admin)", "admin (Admin)" in text(page, "#userChip"))

        # 3. Dasbor data contoh (8 transaksi, omzet 7 hari 914.000)
        check("dasbor omzet 7 hari Rp914.000", "914.000" in text(page, "#dOmzet7"), text(page, "#dOmzet7"))
        check("dasbor 8 transaksi 7 hari", "8 transaksi" in text(page, "#dTrx7"), text(page, "#dTrx7"))
        check("dasbor omzet hari ini Rp152.000", "152.000" in text(page, "#dOmzetHari"), text(page, "#dOmzetHari"))
        check("dasbor 1 transaksi hari ini", "1 transaksi" in text(page, "#dTrxHari"))
        check("dasbor produk terlaris Mie Instan Goreng", "Mie Instan Goreng" in text(page, "#dTerlaris"), text(page, "#dTerlaris"))
        check("dasbor terlaris 13 terjual", "13 terjual" in text(page, "#dTerlarisQty"), text(page, "#dTerlarisQty"))
        check("dasbor stok menipis 2", text(page, "#dStokMenipis").strip() == "2", text(page, "#dStokMenipis"))
        check("dasbor 16 produk", "16 produk" in text(page, "#dProduk"))

        # 4. Notifikasi stok
        check("badge notifikasi 2", text(page, "#notifBadge").strip() == "2", text(page, "#notifBadge"))
        page.click("#notifBtn")
        page.wait_for_timeout(300)
        check("notif ada Susu UHT", "Susu UHT" in text(page, "#notifList"))
        check("notif ada Tisu Wajah", "Tisu Wajah" in text(page, "#notifList"))
        page.click("#notifReadBtn")
        page.wait_for_timeout(300)
        check("badge hilang setelah dibaca", not page.is_visible("#notifBadge"))

        # 5. Kasir: tambah 2x Beras, diskon 10%, bayar tunai 150.000
        klik_tab(page, "kasir")
        page.click('button.product-card[data-pid="1"]')
        page.click('button.product-card[data-pid="1"]')
        page.wait_for_timeout(300)
        check("keranjang subtotal Rp136.000", "136.000" in text(page, "#subTotalLabel"), text(page, "#subTotalLabel"))
        page.fill("#discountInput", "10")
        page.wait_for_timeout(300)
        check("diskon 10% = Rp13.600", "13.600" in text(page, "#discountLabel"), text(page, "#discountLabel"))
        check("total bayar Rp122.400", "122.400" in text(page, "#grandTotalLabel"), text(page, "#grandTotalLabel"))
        check("tombol bayar masih nonaktif (uang kurang)", page.is_disabled("#payBtn"))
        page.fill("#cashInput", "150000")
        page.wait_for_timeout(300)
        check("kembalian Rp27.600", "27.600" in text(page, "#changeLabel"), text(page, "#changeLabel"))
        check("tombol bayar aktif", not page.is_disabled("#payBtn"))
        page.click("#payBtn")
        page.wait_for_timeout(400)
        check("struk muncul TRX-009", "TRX-009" in text(page, "#receiptBox"), text(page, "#receiptBox")[:200])
        check("struk total Rp122.400", "122.400" in text(page, "#receiptBox"))
        check("struk kembalian Rp27.600", "27.600" in text(page, "#receiptBox"))
        check("keranjang kosong setelah bayar", "masih kosong" in text(page, "#cartItems"))

        # 6. Stok berkurang + laporan ter-update
        klik_tab(page, "barang")
        check("stok Beras jadi 22", "22" in text(page, "#stockTable"), text(page, "#stockTable")[:600])
        klik_tab(page, "laporan")
        check("laporan omzet 7 hari Rp1.036.400", "1.036.400" in text(page, "#lapOmzet7"), text(page, "#lapOmzet7"))
        check("laporan 9 transaksi 7 hari", "9 transaksi" in text(page, "#lapTrx7"))
        check("laporan riwayat ada TRX-009", "TRX-009" in text(page, "#lapTable"))
        check("laporan per metode ada Tunai", "Tunai" in text(page, "#lapPerMetode"))
        check("laporan per kasir ada admin", "admin" in text(page, "#lapPerKasir"))

        # 7. Audit log mencatat transaksi
        klik_tab(page, "audit")
        check("audit ada TRX-009", "TRX-009" in text(page, "#auditTable"), text(page, "#auditTable")[:400])
        check("audit ada catatan login", "Masuk ke aplikasi" in text(page, "#auditTable"))
        page.select_option("#auditFilter", "transaksi")
        page.wait_for_timeout(300)
        check("filter audit transaksi jalan", "TRX-009" in text(page, "#auditTable"))
        page.select_option("#auditFilter", "semua")
        page.wait_for_timeout(200)

        # 8. Tambah barang baru + ubah stok (Admin)
        klik_tab(page, "barang")
        page.click("#addProductBtn")
        page.fill("#pfName", "Sabun Mandi 250 ml")
        page.fill("#pfPrice", "8000")
        page.fill("#pfStock", "10")
        page.fill("#pfCat", "Rumah Tangga")
        page.fill("#pfUnit", "botol")
        page.click("#saveProductBtn")
        page.wait_for_timeout(300)
        check("barang baru Sabun Mandi muncul", "Sabun Mandi 250 ml" in text(page, "#stockTable"))
        check("total produk jadi 17", "17 produk" in text(page, "#stockTotal"), text(page, "#stockTotal"))
        page.fill('input[data-stock="7"]', "10")
        page.click('button[data-save-stock="7"]')
        page.wait_for_timeout(300)
        check("stok Susu diubah jadi 10", "10" in text(page, "#stockTable"))
        check("badge notifikasi tinggal 1 (Tisu saja)", text(page, "#notifBadge").strip() == "1", text(page, "#notifBadge"))

        # 9. Kelola pengguna: tambah budi (kasir)
        klik_tab(page, "pengguna")
        page.click("#addUserBtn")
        page.fill("#ufName", "budi")
        page.fill("#ufPass", "budi123")
        page.select_option("#ufRole", "kasir")
        page.click("#saveUserBtn")
        page.wait_for_timeout(300)
        check("pengguna budi muncul", "budi" in text(page, "#userTable"))

        # 10. Ekspor CSV + backup JSON (download)
        klik_tab(page, "ekspor")
        with page.expect_download() as dl:
            page.click("#exportTrxCsvBtn2")
        csv_path = dl.value.path()
        csv_text = Path(csv_path).read_text(encoding="utf-8")
        check("CSV transaksi ada TRX-001", "TRX-001" in csv_text)
        check("CSV transaksi ada TRX-009", "TRX-009" in csv_text)
        with page.expect_download() as dl2:
            page.click("#exportJsonBtn")
        json_path = dl2.value.path()
        json_text = Path(json_path).read_text(encoding="utf-8")
        check("backup JSON ada kasir-toko-l3", "kasir-toko-l3" in json_text)
        check("backup JSON ada budi", "budi" in json_text)

        # 11. Peran Kasir (budi): tab terbatas + laporan hanya milik sendiri
        logout(page)
        login(page, "budi", "budi123")
        check("login budi berhasil", "budi (Kasir)" in text(page, "#userChip"))
        check("kasir tidak melihat tab Pengguna", not page.is_visible('[data-tab="pengguna"]'))
        check("kasir tidak melihat tab Audit", not page.is_visible('[data-tab="audit"]'))
        check("kasir tidak melihat tab Barang", not page.is_visible('[data-tab="barang"]'))
        check("kasir melihat tab Kasir", page.is_visible('[data-tab="kasir"]'))
        klik_tab(page, "laporan")
        check("laporan kasir 0 transaksi (hanya milik sendiri)", "0 transaksi" in text(page, "#lapTrx7"), text(page, "#lapTrx7"))

        # 12. Peran Gudang: barang + ekspor, tanpa kasir/pengguna/audit
        logout(page)
        login(page, "gudang", "gudang123")
        check("login gudang berhasil", "gudang (Gudang)" in text(page, "#userChip"))
        check("gudang melihat tab Barang", page.is_visible('[data-tab="barang"]'))
        check("gudang melihat tab Ekspor", page.is_visible('[data-tab="ekspor"]'))
        check("gudang tidak melihat tab Kasir", not page.is_visible('[data-tab="kasir"]'))
        check("gudang tidak melihat tab Pengguna", not page.is_visible('[data-tab="pengguna"]'))
        check("gudang tidak melihat tab Audit", not page.is_visible('[data-tab="audit"]'))

        # 13. Panduan: CONTOH DEMO + batas jujur
        klik_tab(page, "panduan")
        check("panduan ada CONTOH DEMO", "CONTOH DEMO" in text(page, "#view-panduan"))
        check("panduan ada batas tanpa sinkron", "tidak ada sinkron antar-perangkat" in text(page, "#view-panduan"))
        check("panduan ada akun demo", "admin123" in text(page, "#view-panduan"))

        # 14. Reset data demo mengembalikan angka awal
        logout(page)
        login(page, "admin", "admin123")
        klik_tab(page, "ekspor")
        page.click("#resetBtn")
        page.wait_for_timeout(400)
        klik_tab(page, "dashboard")
        check("setelah reset omzet 7 hari Rp914.000", "914.000" in text(page, "#dOmzet7"), text(page, "#dOmzet7"))
        check("setelah reset 8 transaksi", "8 transaksi" in text(page, "#dTrx7"))

        # 15. Tanpa error console
        check("tanpa error console/pageerror", len(errors) == 0, "; ".join(errors[:3]))

        browser.close()

    print(f"\n{passed} lolos, {len(failures)} gagal")
    if failures:
        print("Gagal:", failures)
        sys.exit(1)


if __name__ == "__main__":
    main()
