"""Tes Dompet Digital (Simulasi Demo) (file lokal, Playwright Chromium).
Hari ini 2026-11-20. Data seed (tanggal relatif, semua dalam 30 hari):
  Admin (saldo awal contoh 1.000.000) — 6 transaksi:
    T-10 topup 500.000 (Transfer Bank) -> 1.500.000
    T-9  bayar 125.000 Warung Kopi Seduh -> 1.375.000
    T-7  transfer 200.000 ke Sari Dewi -> 1.175.000
    T-5  terima 300.000 dari Budi Santoso -> 1.475.000
    T-3  bayar 75.500 Minimarket Contoh -> 1.399.500
    T-1  topup 250.000 (Minimarket) -> 1.649.500
    Saldo akhir 1.649.500; masuk 1.050.000; keluar 400.500.
    7 hari (jendela = hari ini + 6 hari ke belakang, transfer T-7 di luar):
    masuk 550.000 (250.000+300.000), keluar 75.500, 3 trx.
    Notifikasi: 7 (6 transaksi + 1 promo contoh).
  Pengguna Budi Santoso (saldo awal contoh 500.000) — 6 transaksi:
    T-8 topup 200.000 -> 700.000
    T-6 bayar 85.000 Kantin Kampus -> 615.000
    T-5 transfer 300.000 ke Administrator -> 315.000
    T-4 bayar 150.000 SPBU Contoh -> 165.000
    T-2 terima 100.000 dari Andi Pratama -> 265.000
    T-0 bayar 45.000 Jajan Sore -> 220.000
    Saldo akhir 220.000; masuk 300.000; keluar 580.000.
    7 hari: masuk 100.000, keluar 580.000, 5 trx.
    Notifikasi: 7 (6 transaksi + 1 promo contoh).
  Saldo rendah: di bawah Rp100.000. Top up: min 10.000, maks 10.000.000.
Urutan tes: A pengguna (baseline + topup + bayar + saldo rendah),
  B admin (baseline + transfer ke pengguna + reset sandi pengguna),
  C pengguna (terima transfer + sandi baru), D admin (transfer lainnya +
  topup cepat + RESTORE-TEST + backup/reset/restore + CSV + hapus + notifikasi).
  CATATAN: Admin melihat SEMUA pengguna (transaksi + notifikasi). Jadi angka
  dasbor admin di fase B/D mencakup data pengguna yang dibuat di fase A.
"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = "file://" + str(ROOT / "dompet-digital" / "index.html")

failures = []
passed = 0
console_errors = []
page_errors = []


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


def visible(page, sel):
    el = page.query_selector(sel)
    return bool(el and el.is_visible())


def rupiah(n):
    return "Rp" + f"{round(n):,}".replace(",", ".")


def login(page, user, pw):
    page.fill("#loginUser", user)
    page.fill("#loginPass", pw)
    page.click("#formLogin button[type=submit]")
    page.wait_for_timeout(400)


def logout(page):
    page.click("#btnKeluar")
    page.wait_for_timeout(300)


def tab(page, nama):
    page.click(f"#tabbar button[data-tab='{nama}']")
    page.wait_for_timeout(300)


def saldo_dasbor(page):
    return text(page, "#dSaldo")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(accept_downloads=True)
        page = ctx.new_page()
        page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.goto(URL)
        page.wait_for_timeout(500)

        # ---------- Label simulasi ----------
        check("hero bertuliskan SIMULASI DEMO", "SIMULASI DEMO" in text(page, ".hero"))
        check("hero menegaskan bukan uang asli", "BUKAN UANG ASLI" in text(page, ".hero"))
        check("login menegaskan bukan uang asli", "BUKAN UANG ASLI" in text(page, "#loginOverlay"))
        check("QR toko berlabel bukan kode nyata", "bukan kode pembayaran nyata" in text(page, "#panel-qr"))

        # ---------- Login salah ----------
        page.fill("#loginUser", "admin")
        page.fill("#loginPass", "salah123")
        page.click("#formLogin button[type=submit]")
        page.wait_for_timeout(300)
        check("login salah menampilkan error", visible(page, "#loginError"))

        # ================= FASE A — pengguna =================
        login(page, "pengguna", "pengguna123")
        check("pengguna masuk, chip Budi Santoso", "Budi Santoso (Pengguna)" in text(page, "#userChip"))
        check("A: saldo pengguna 220.000", saldo_dasbor(page) == rupiah(220000), saldo_dasbor(page))
        check("A: total masuk 300.000", text(page, "#dMasuk") == rupiah(300000), text(page, "#dMasuk"))
        check("A: total keluar 580.000", text(page, "#dKeluar") == rupiah(580000), text(page, "#dKeluar"))
        check("A: 6 transaksi", text(page, "#dJumlah") == "6", text(page, "#dJumlah"))
        check("A: 7 notifikasi belum dibaca", text(page, "#badgeNotif") == "7", text(page, "#badgeNotif"))
        check("A: cardPengguna tersembunyi untuk pengguna", not visible(page, "#cardPengguna"))
        check("A: cardSandiSaya terlihat untuk pengguna", visible(page, "#cardSandiSaya"))
        check("A: tidak ada peringatan saldo rendah (220rb)", not visible(page, "#cardPeringatanSaldo"))

        # Saldo tab — periode 30 dan 7 hari
        tab(page, "saldo")
        check("A saldo: 220.000", text(page, "#sSaldo") == rupiah(220000), text(page, "#sSaldo"))
        check("A saldo awal 500.000", text(page, "#sSaldoAwal") == rupiah(500000), text(page, "#sSaldoAwal"))
        check("A nomor dompet 0812-0000-0002", "0812-0000-0002" in text(page, "#nomorDompet"))
        check("A saldo 30h masuk 300.000", text(page, "#sMasuk") == rupiah(300000), text(page, "#sMasuk"))
        check("A saldo 30h keluar 580.000", text(page, "#sKeluar") == rupiah(580000), text(page, "#sKeluar"))
        check("A saldo 30h selisih -280.000", text(page, "#sSelisih") == rupiah(-280000), text(page, "#sSelisih"))
        page.select_option("#fPeriodeSaldo", "7")
        page.wait_for_timeout(300)
        check("A saldo 7h masuk 100.000", text(page, "#sMasuk") == rupiah(100000), text(page, "#sMasuk"))
        check("A saldo 7h keluar 580.000", text(page, "#sKeluar") == rupiah(580000), text(page, "#sKeluar"))
        page.select_option("#fPeriodeSaldo", "30")
        page.wait_for_timeout(300)
        check("A tabel jenis 30h: topup 1 x 200.000", "Rp200.000" in text(page, "#tabelSaldoJenis"))

        # Top Up tab — validasi min/maks lalu sukses
        tab(page, "topup")
        page.fill("#tuJumlah", "5000")
        page.click("#btnTopup")
        page.wait_for_timeout(300)
        check("A topup 5.000 ditolak (min 10.000)", "minimal Rp10.000" in text(page, "#pesanTopup"))
        page.fill("#tuJumlah", "20000000")
        page.click("#btnTopup")
        page.wait_for_timeout(300)
        check("A topup 20jt ditolak (maks 10jt)", "maksimal Rp10.000.000" in text(page, "#pesanTopup"))
        page.select_option("#tuMetode", "Minimarket (contoh)")
        page.fill("#tuJumlah", "100000")
        page.click("#btnTopup")
        page.wait_for_timeout(300)
        check("A topup 100.000 berhasil", "berhasil (simulasi)" in text(page, "#pesanTopup"))
        tab(page, "dashboard")
        check("A saldo jadi 320.000 setelah topup", saldo_dasbor(page) == rupiah(320000), saldo_dasbor(page))

        # QR tab — bayar 150.000 lalu 100.000 (saldo rendah), lalu bayar ditolak
        tab(page, "qr")
        check("A canvas QR toko ada", page.query_selector("#qrToko") is not None)
        check("A canvas QR saya ada", page.query_selector("#qrSaya") is not None)
        page.fill("#qMerchant", "Toko Uji")
        page.fill("#qJumlahBayar", "150000")
        page.click("#btnBayarQR")
        page.wait_for_timeout(300)
        check("A bayar QR 150.000 berhasil", "berhasil (simulasi)" in text(page, "#pesanBayar"))
        tab(page, "dashboard")
        check("A saldo jadi 170.000", saldo_dasbor(page) == rupiah(170000), saldo_dasbor(page))
        tab(page, "qr")
        page.fill("#qMerchant", "Toko Uji")
        page.fill("#qJumlahBayar", "100000")
        page.click("#btnBayarQR")
        page.wait_for_timeout(300)
        tab(page, "dashboard")
        check("A saldo jadi 70.000", saldo_dasbor(page) == rupiah(70000), saldo_dasbor(page))
        check("A peringatan saldo rendah muncul", visible(page, "#cardPeringatanSaldo"))
        check("A peringatan menyebut Rp70.000", "Rp70.000" in text(page, "#dPeringatanSaldo"))
        tab(page, "notifikasi")
        check("A notifikasi saldo rendah ada", "Saldo rendah" in text(page, "#daftarNotifikasi"))
        tab(page, "qr")
        page.fill("#qMerchant", "Toko Uji")
        page.fill("#qJumlahBayar", "100000")
        page.click("#btnBayarQR")
        page.wait_for_timeout(300)
        check("A bayar melebihi saldo ditolak", "tidak cukup" in text(page, "#pesanBayar"))
        tab(page, "dashboard")
        check("A saldo tetap 70.000 setelah ditolak", saldo_dasbor(page) == rupiah(70000), saldo_dasbor(page))

        # Riwayat — pengguna tidak melihat transaksi admin; filter topup = 2
        tab(page, "riwayat")
        page.fill("#cariRiwayat", "Warung Kopi")
        page.wait_for_timeout(300)
        check("A pengguna tidak melihat transaksi admin", "Tidak ada transaksi yang cocok" in text(page, "#daftarRiwayat"))
        page.fill("#cariRiwayat", "")
        page.select_option("#fJenisRiwayat", "topup")
        page.wait_for_timeout(300)
        check("A filter topup pengguna = 2 transaksi", "2 transaksi" in text(page, "#ringkasanRiwayat"), text(page, "#ringkasanRiwayat"))
        page.select_option("#fJenisRiwayat", "")
        page.wait_for_timeout(200)
        logout(page)

        # ================= FASE B — admin =================
        login(page, "admin", "admin123")
        check("B admin masuk", "Administrator (Admin)" in text(page, "#userChip"))
        check("B saldo admin 1.649.500", saldo_dasbor(page) == rupiah(1649500), saldo_dasbor(page))
        # Admin melihat semua pengguna: masuk 1.050.000 + 400.000 (pengguna: topup 200rb+100rb, terima 100rb)
        check("B total masuk 1.450.000 (semua pengguna)", text(page, "#dMasuk") == rupiah(1450000), text(page, "#dMasuk"))
        # Keluar 400.500 + 830.000 (pengguna: 580.000 seed + 150.000 + 100.000 fase A)
        check("B total keluar 1.230.500 (semua pengguna)", text(page, "#dKeluar") == rupiah(1230500), text(page, "#dKeluar"))
        check("B 15 transaksi (6 admin + 9 pengguna)", text(page, "#dJumlah") == "15", text(page, "#dJumlah"))
        check("B 18 notifikasi (7 + 7 + 4 fase A)", text(page, "#badgeNotif") == "18", text(page, "#badgeNotif"))
        check("B cardPengguna terlihat untuk admin", visible(page, "#cardPengguna"))
        tab(page, "saldo")
        page.select_option("#fPeriodeSaldo", "7")
        page.wait_for_timeout(300)
        # 7h semua pengguna: masuk admin 550.000 + pengguna 200.000 (terima 100rb + topup 100rb)
        check("B saldo 7h masuk 750.000 (semua pengguna)", text(page, "#sMasuk") == rupiah(750000), text(page, "#sMasuk"))
        # 7h keluar: admin 75.500 (transfer T-7 di luar jendela) + pengguna 830.000
        check("B saldo 7h keluar 905.500 (semua pengguna)", text(page, "#sKeluar") == rupiah(905500), text(page, "#sKeluar"))
        page.select_option("#fPeriodeSaldo", "30")
        page.wait_for_timeout(200)

        # Transfer admin -> pengguna 50.000
        tab(page, "qr")
        page.select_option("#tPenerima", "pengguna")
        page.wait_for_timeout(200)
        page.fill("#tJumlahTransfer", "50000")
        page.click("#btnTransfer")
        page.wait_for_timeout(300)
        check("B transfer 50.000 ke Budi berhasil", "berhasil (simulasi)" in text(page, "#pesanTransfer") and "Budi Santoso" in text(page, "#pesanTransfer"))
        tab(page, "dashboard")
        check("B saldo admin jadi 1.599.500", saldo_dasbor(page) == rupiah(1599500), saldo_dasbor(page))

        # Reset sandi pengguna -> bk123
        page.click("[data-reset='pengguna']")
        page.wait_for_timeout(300)
        page.click("#modalYa")
        page.wait_for_timeout(300)
        check("B reset sandi pengguna ke bk123", "direset ke bk123" in text(page, "#toast"))
        logout(page)
        login(page, "pengguna", "bk123")
        check("B pengguna masuk dengan bk123", "Budi Santoso (Pengguna)" in text(page, "#userChip"))

        # Ganti sandi kembali ke pengguna123 (uji ikat ulang currentUser)
        page.fill("#sandiLama", "bk123")
        page.fill("#sandiBaru", "pengguna123")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        check("B ganti sandi kembali berhasil", "berhasil diubah" in text(page, "#pesanSandi"))
        logout(page)
        login(page, "pengguna", "pengguna123")
        check("B pengguna masuk lagi dengan pengguna123", "Budi Santoso (Pengguna)" in text(page, "#userChip"))

        # ================= FASE C — pengguna terima transfer =================
        check("C saldo pengguna 120.000 (70rb + 50rb)", saldo_dasbor(page) == rupiah(120000), saldo_dasbor(page))
        # Masuk: 300.000 seed + 100.000 topup fase A + 50.000 terima transfer
        check("C total masuk 450.000", text(page, "#dMasuk") == rupiah(450000), text(page, "#dMasuk"))
        # Keluar: 580.000 seed + 150.000 + 100.000 bayar fase A
        check("C total keluar 830.000", text(page, "#dKeluar") == rupiah(830000), text(page, "#dKeluar"))
        # 6 seed + topup + 2 bayar + 1 terima = 10
        check("C 10 transaksi", text(page, "#dJumlah") == "10", text(page, "#dJumlah"))
        tab(page, "riwayat")
        page.fill("#cariRiwayat", "Terima dari Administrator")
        page.wait_for_timeout(300)
        check("C riwayat terima transfer 50.000 ada", "Rp50.000" in text(page, "#daftarRiwayat"))
        page.fill("#cariRiwayat", "")
        page.wait_for_timeout(200)
        logout(page)

        # ================= FASE D — admin: transfer lainnya, topup cepat, backup/restore =================
        login(page, "admin", "admin123")
        tab(page, "qr")
        page.select_option("#tPenerima", "__lain__")
        page.wait_for_timeout(200)
        check("D kolom nama lain muncul", visible(page, "#fieldNamaLain"))
        page.fill("#tNamaLain", "Sari Dewi")
        page.fill("#tJumlahTransfer", "10000")
        page.click("#btnTransfer")
        page.wait_for_timeout(300)
        check("D transfer lainnya 10.000 berhasil", "berhasil (simulasi)" in text(page, "#pesanTransfer") and "Sari Dewi" in text(page, "#pesanTransfer"))
        tab(page, "dashboard")
        check("D saldo admin 1.589.500", saldo_dasbor(page) == rupiah(1589500), saldo_dasbor(page))
        page.fill("#qJumlahTopup", "25000")
        page.click("#btnTopupCepat")
        page.wait_for_timeout(300)
        check("D topup cepat 25.000 berhasil", "berhasil (simulasi)" in text(page, "#pesanTopupCepat"))
        check("D saldo admin 1.614.500", saldo_dasbor(page) == rupiah(1614500), saldo_dasbor(page))

        # Penanda RESTORE-TEST lalu backup
        tab(page, "qr")
        page.fill("#qMerchant", "RESTORE-TEST")
        page.fill("#qJumlahBayar", "10000")
        page.click("#btnBayarQR")
        page.wait_for_timeout(300)
        tab(page, "dashboard")
        check("D saldo admin 1.604.500 setelah RESTORE-TEST", saldo_dasbor(page) == rupiah(1604500), saldo_dasbor(page))
        tab(page, "riwayat")
        with page.expect_download() as dl:
            page.click("#btnBackup")
        backup_path = Path(dl.value.path())
        backup_data = json.loads(backup_path.read_text(encoding="utf-8"))
        check("D backup JSON berisi state+users", "state" in backup_data and "users" in backup_data)
        check("D backup berisi RESTORE-TEST", "RESTORE-TEST" in backup_path.read_text(encoding="utf-8"))

        # Reset -> seed kembali
        page.click("#btnResetData")
        page.wait_for_timeout(300)
        page.click("#modalYa")
        page.wait_for_timeout(400)
        tab(page, "dashboard")
        check("D reset kembalikan saldo seed 1.649.500", saldo_dasbor(page) == rupiah(1649500), saldo_dasbor(page))
        tab(page, "riwayat")
        page.fill("#cariRiwayat", "RESTORE-TEST")
        page.wait_for_timeout(300)
        check("D RESTORE-TEST hilang setelah reset", "Tidak ada transaksi yang cocok" in text(page, "#daftarRiwayat"))
        page.fill("#cariRiwayat", "")
        page.wait_for_timeout(200)

        # Restore dari backup
        page.set_input_files("#inputRestore", str(backup_path))
        page.wait_for_timeout(500)
        check("D restore berhasil (toast)", "berhasil dipulihkan" in text(page, "#toast"))
        tab(page, "dashboard")
        check("D saldo kembali 1.604.500 setelah restore", saldo_dasbor(page) == rupiah(1604500), saldo_dasbor(page))
        tab(page, "riwayat")
        page.fill("#cariRiwayat", "RESTORE-TEST")
        page.wait_for_timeout(300)
        check("D RESTORE-TEST kembali setelah restore", "RESTORE-TEST" in text(page, "#daftarRiwayat"))
        page.fill("#cariRiwayat", "")
        page.wait_for_timeout(200)

        # Restore file tidak valid ditolak
        bad = Path("/tmp/dompet_bad_restore.json")
        bad.write_text("{bukan json", encoding="utf-8")
        page.set_input_files("#inputRestore", str(bad))
        page.wait_for_timeout(500)
        check("D file cadangan tidak valid ditolak", "tidak valid" in text(page, "#toast"))
        tab(page, "dashboard")
        check("D saldo tetap 1.604.500 setelah restore gagal", saldo_dasbor(page) == rupiah(1604500), saldo_dasbor(page))

        # CSV riwayat (filter 30 hari, admin melihat semua):
        # 12 seed + 3 fase A pengguna (topup, 2 bayar) + transfer 50rb + terima 50rb
        # + transfer lainnya 10rb + topup cepat 25rb + RESTORE-TEST 10rb = 20 baris
        tab(page, "riwayat")
        with page.expect_download() as dl2:
            page.click("#btnCsvRiwayat")
        csv_path = Path(dl2.value.path())
        csv_text = csv_path.read_text(encoding="utf-8")
        lines = [l for l in csv_text.strip().split("\n") if l.strip()]
        check("D CSV punya header + 20 baris", len(lines) == 21, f"baris={len(lines)}")
        check("D CSV berisi RESTORE-TEST", "RESTORE-TEST" in csv_text)
        check("D CSV berisi Warung Kopi Seduh", "Warung Kopi Seduh" in csv_text)
        check("D CSV header berisi Saldo Setelah", "Saldo Setelah" in lines[0])

        # Hapus transaksi RESTORE-TEST -> saldo kembali 1.614.500
        page.fill("#cariRiwayat", "RESTORE-TEST")
        page.wait_for_timeout(300)
        page.click("[data-hapus-trx]")
        page.wait_for_timeout(300)
        page.click("#modalYa")
        page.wait_for_timeout(400)
        tab(page, "dashboard")
        check("D saldo 1.614.500 setelah hapus RESTORE-TEST", saldo_dasbor(page) == rupiah(1614500), saldo_dasbor(page))

        # Ganti sandi admin round-trip (setelah restore — uji ikat ulang currentUser)
        page.fill("#sandiLama", "admin123")
        page.fill("#sandiBaru", "admin456")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        check("D ganti sandi admin setelah restore berhasil", "berhasil diubah" in text(page, "#pesanSandi"))
        logout(page)
        login(page, "admin", "admin456")
        check("D admin masuk dengan sandi baru", "Administrator (Admin)" in text(page, "#userChip"))
        page.fill("#sandiLama", "admin456")
        page.fill("#sandiBaru", "admin123")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        logout(page)
        login(page, "admin", "admin123")
        check("D admin kembali ke admin123", "Administrator (Admin)" in text(page, "#userChip"))

        # Notifikasi — tandai semua dibaca
        tab(page, "panduan")
        check("D panduan menegaskan bukan dompet sungguhan", "bukan dompet digital sungguhan" in text(page, "#panel-panduan"))
        tab(page, "notifikasi")
        page.click("#btnBacaSemua")
        page.wait_for_timeout(400)
        check("D badge notifikasi 0 setelah baca semua", text(page, "#badgeNotif") == "0", text(page, "#badgeNotif"))

        browser.close()

    print(f"\nLOLOS: {passed}  GAGAL: {len(failures)}")
    if failures:
        print("Gagal:", failures)
    print("Console errors:", console_errors)
    print("Page errors:", page_errors)
    return 0 if not failures and not console_errors and not page_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
