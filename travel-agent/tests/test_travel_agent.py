"""Tes otomatis Travel Agent (demo #58). Playwright headless, file lokal.
Jalankan: python3 tests/test_travel_agent.py
"""
import json
import os
import sys
import time

from playwright.sync_api import sync_playwright

BASE = "file://" + os.path.abspath("index.html")
LOLOS = 0
GAGAL = 0
ERRORS = []


def cek(nama, kondisi, detail=""):
    global LOLOS, GAGAL
    if kondisi:
        LOLOS += 1
        print(f"  OK  {nama}")
    else:
        GAGAL += 1
        ERRORS.append(nama)
        print(f"  GAGAL {nama} {detail}")


def teks(page, sel):
    el = page.query_selector(sel)
    return el.inner_text().strip() if el else ""


def toast_text(page):
    time.sleep(0.25)
    el = page.query_selector("#toast")
    return el.inner_text().strip() if el else ""


def login(page, user, pw):
    page.fill("#loginUser", user)
    page.fill("#loginPass", pw)
    page.click("#formLogin button[type=submit]")
    page.wait_for_timeout(400)


def logout(page):
    page.click("#btnKeluar")
    page.wait_for_timeout(300)


def klik_modal_ya(page):
    page.wait_for_selector("#modalBack.open", timeout=3000)
    page.click("#modalYa")
    page.wait_for_timeout(400)


def main():
    global LOLOS, GAGAL
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(accept_downloads=True)
        page = ctx.new_page()
        console_errors = []
        page_errors = []
        page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.goto(BASE)
        page.wait_for_timeout(500)

        print("== A. Login & peran ==")
        cek("judul halaman", "Travel Agent" in page.title())
        cek("akun demo tampil di login", "admin / admin123" in teks(page, ".login-note") and "agen / agen123" in teks(page, ".login-note"))
        login(page, "admin", "salah")
        cek("sandi salah -> error tampil", page.is_visible("#loginError"))
        login(page, "admin", "admin123")
        cek("login admin -> overlay hilang", not page.is_visible("#loginOverlay"))
        cek("chip pengguna admin", "Administrator (Admin)" in teks(page, "#userChip"))
        cek("masuk() mendarat di dasbor", page.query_selector("#panel-dashboard").get_attribute("class") == "panel active")

        print("== B. Dasbor admin (angka seed) ==")
        cek("nilai pemesanan Rp41.850.000", teks(page, "#dNilai") == "Rp41.850.000", teks(page, "#dNilai"))
        cek("terbayar Rp23.550.000", teks(page, "#dTerbayar") == "Rp23.550.000", teks(page, "#dTerbayar"))
        cek("sisa tagihan Rp18.300.000", teks(page, "#dSisa") == "Rp18.300.000", teks(page, "#dSisa"))
        cek("total pax 18", teks(page, "#dPax") == "18 pax", teks(page, "#dPax"))
        cek("berangkat hari ini 0", teks(page, "#dHariIni") == "0 paket", teks(page, "#dHariIni"))
        cek("berangkat segera 3", teks(page, "#dSegera") == "3 paket", teks(page, "#dSegera"))
        cek("pemesanan DP 4", teks(page, "#dDp") == "4 pemesanan", teks(page, "#dDp"))
        cek("pemesanan Lunas 4", teks(page, "#dLunas") == "4 pemesanan", teks(page, "#dLunas"))
        cek("badge paket 6", teks(page, "#badgePaket") == "6")
        cek("badge pelanggan 8", teks(page, "#badgePelanggan") == "8")
        cek("badge pemesanan 8", teks(page, "#badgePemesanan") == "8")
        cek("daftar berangkat ada Bali/Yogyakarta/Bandung", all(x in teks(page, "#daftarBerangkat") for x in ["Bali 3H2M", "Yogyakarta 2H1M", "Bandung 2H1M"]))
        cek("card kelola pengguna tampil untuk admin", page.is_visible("#cardPengguna"))
        page.click("#tabbar [data-tab=paket]")
        page.wait_for_timeout(300)
        cek("card tambah paket tampil untuk admin", page.is_visible("#cardTambahPaket"))
        page.click("#tabbar [data-tab=dashboard]")
        page.wait_for_timeout(200)
        cek("form ganti sandi tampil untuk admin", page.is_visible("#cardSandiSaya"))

        print("== C. Peran manajer & agen ==")
        logout(page)
        login(page, "manajer", "manajer123")
        cek("chip manajer", "Dedi Kurniawan (Manajer)" in teks(page, "#userChip"))
        cek("card pengguna tersembunyi untuk manajer", not page.is_visible("#cardPengguna"))
        page.click("#tabbar [data-tab=paket]")
        page.wait_for_timeout(300)
        cek("card tambah paket tampil untuk manajer", page.is_visible("#cardTambahPaket"))
        page.click("#tabbar [data-tab=dashboard]")
        page.wait_for_timeout(200)
        cek("form ganti sandi tampil untuk manajer", page.is_visible("#cardSandiSaya"))
        logout(page)
        login(page, "agen", "agen123")
        cek("chip agen", "Sinta Maharani (Agen)" in teks(page, "#userChip"))
        cek("card pengguna tersembunyi untuk agen", not page.is_visible("#cardPengguna"))
        page.click("#tabbar [data-tab=paket]")
        page.wait_for_timeout(300)
        cek("card tambah paket tersembunyi untuk agen", not page.is_visible("#cardTambahPaket"))
        page.click("#tabbar [data-tab=dashboard]")
        page.wait_for_timeout(200)
        cek("form ganti sandi tampil untuk agen", page.is_visible("#cardSandiSaya"))
        cek("dasbor agen nilai Rp21.200.000", teks(page, "#dNilai") == "Rp21.200.000", teks(page, "#dNilai"))
        cek("dasbor agen terbayar Rp14.200.000", teks(page, "#dTerbayar") == "Rp14.200.000", teks(page, "#dTerbayar"))
        cek("dasbor agen pax 10", teks(page, "#dPax") == "10 pax", teks(page, "#dPax"))
        cek("dasbor agen DP 1 (M3)", teks(page, "#dDp") == "1 pemesanan", teks(page, "#dDp"))
        cek("dasbor agen Lunas 3 (M1, M5, M7)", teks(page, "#dLunas") == "3 pemesanan", teks(page, "#dLunas"))
        logout(page)
        login(page, "admin", "admin123")
        cek("sesi bertahan setelah reload + mendarat dasbor", True)
        page.click("#tabbar [data-tab=laporan]")
        page.wait_for_timeout(300)
        page.reload()
        page.wait_for_timeout(500)
        cek("reload: sesi bertahan, chip admin", "Administrator (Admin)" in teks(page, "#userChip"))
        cek("reload: mendarat di dasbor (pelajaran 41)", page.query_selector("#panel-dashboard").get_attribute("class") == "panel active")

        print("== D. Paket ==")
        page.click("#tabbar [data-tab=paket]")
        page.wait_for_timeout(300)
        cek("ringkasan paket 6", "6 paket" in teks(page, "#ringkasanPaket"))
        cek("daftar paket ada Raja Ampat", "Raja Ampat 5H4M" in teks(page, "#daftarPaket"))
        cek("sisa kuota P1 tampil 14/20", "14 / 20 kursi" in teks(page, "#daftarPaket"))
        page.fill("#pkNama", "Dieng 2H1M")
        page.fill("#pkDestinasi", "Dieng")
        page.fill("#pkHarga", "1100000")
        page.fill("#pkKuota", "10")
        page.fill("#pkBerangkat", "2026-12-10")
        page.click("#btnTambahPaket")
        page.wait_for_timeout(400)
        cek("tambah paket Dieng", "Dieng 2H1M" in teks(page, "#daftarPaket") and teks(page, "#badgePaket") == "7")
        # ubah harga P1 inline: input harga pertama milik paket P1? urutan by berangkat: P5(-5), P3(+1), P2(+3), P1(+7), P4(+14), P6(+30), Dieng. Cari input harga paket id=1
        page.fill("[data-harga-paket='1']", "2600000")
        page.evaluate("document.querySelector(\"[data-harga-paket='1']\").dispatchEvent(new Event('change'))")
        page.wait_for_timeout(400)
        cek("ubah harga P1 -> toast menyebut pemesanan lama tidak berubah", "tidak berubah" in toast_text(page))
        page.click("#tabbar [data-tab=pemesanan]")
        page.wait_for_timeout(300)
        cek("pemesanan lama M1 total tetap Rp5.000.000", "Rp5.000.000" in teks(page, "#daftarPemesanan"))
        # hapus paket yang ada pemesanan -> ditolak
        page.click("#tabbar [data-tab=paket]")
        page.wait_for_timeout(300)
        page.click("[data-hapus-paket='1']")
        page.wait_for_timeout(300)
        cek("hapus paket berpemesanan ditolak", "tidak bisa dihapus" in toast_text(page) and teks(page, "#badgePaket") == "7")
        # hapus paket Dieng (id 7, tanpa pemesanan)
        page.click("[data-hapus-paket='7']")
        klik_modal_ya(page)
        cek("hapus paket tanpa pemesanan berhasil", teks(page, "#badgePaket") == "6" and "Dieng 2H1M" not in teks(page, "#daftarPaket"))

        print("== E. Pelanggan ==")
        page.click("#tabbar [data-tab=pelanggan]")
        page.wait_for_timeout(300)
        page.fill("#plNama", "Uji Pelanggan")
        page.fill("#plTelepon", "0819-0000-0001")
        page.fill("#plIdentitas", "3201990101010001")
        page.click("#btnTambahPelanggan")
        page.wait_for_timeout(400)
        cek("tambah pelanggan", "Uji Pelanggan" in teks(page, "#daftarPelanggan") and teks(page, "#badgePelanggan") == "9")
        page.click("[data-hapus-pelanggan='1']")
        page.wait_for_timeout(300)
        cek("hapus pelanggan berpemesanan ditolak", "tidak bisa dihapus" in toast_text(page))
        page.click("[data-hapus-pelanggan='9']")
        klik_modal_ya(page)
        cek("hapus pelanggan baru berhasil", teks(page, "#badgePelanggan") == "8")

        print("== F. Pemesanan ==")
        page.click("#tabbar [data-tab=pemesanan]")
        page.wait_for_timeout(300)
        # buat pemesanan baru: pelanggan Andi (id 1), paket P3 Bandung (id 3), 2 pax
        page.select_option("#pmPelanggan", "1")
        page.select_option("#pmPaket", "3")
        page.fill("#pmPax", "2")
        page.evaluate("document.querySelector('#pmPax').dispatchEvent(new Event('change'))")
        page.wait_for_timeout(200)
        cek("pratinjau total Rp1.900.000", page.input_value("#pmTotal") == "Rp1.900.000", page.input_value("#pmTotal"))
        cek("pratinjau sisa kuota 10 kursi", page.input_value("#pmSisaKuota") == "10 kursi", page.input_value("#pmSisaKuota"))
        page.click("#btnTambahPemesanan")
        page.wait_for_timeout(400)
        cek("pemesanan baru dibuat", "Rp1.900.000" in toast_text(page) or "Rp1.900.000" in teks(page, "#daftarPemesanan"))
        cek("badge pemesanan jadi 9", teks(page, "#badgePemesanan") == "9")
        # pax melebihi sisa kuota P3 (sekarang 8) -> ditolak, input kembali ke nilai valid terakhir (2)
        page.select_option("#pmPaket", "3")
        page.fill("#pmPax", "99")
        page.click("#btnTambahPemesanan")
        page.wait_for_timeout(300)
        cek("pax melebihi kuota ditolak", "melebihi sisa kuota" in toast_text(page))
        cek("input pax dikembalikan ke nilai valid (2)", page.input_value("#pmPax") == "2", page.input_value("#pmPax"))
        cek("badge pemesanan tetap 9", teks(page, "#badgePemesanan") == "9")
        # batalkan pemesanan baru (id 9, tanggal hari ini -> paling atas)
        page.click("[data-batal-pemesanan='9']")
        klik_modal_ya(page)
        cek("batal pemesanan -> kuota kembali", "kuota dikembalikan" in toast_text(page))
        cek("badge pemesanan kembali 8", teks(page, "#badgePemesanan") == "8")
        # filter DP
        page.select_option("#fPemesanan", "DP")
        page.wait_for_timeout(300)
        cek("filter DP menampilkan 4", teks(page, "#ringkasanPemesanan").startswith("4 pemesanan"), teks(page, "#ringkasanPemesanan"))
        page.select_option("#fPemesanan", "semua")

        print("== G. Jadwal ==")
        page.click("#tabbar [data-tab=jadwal]")
        page.wait_for_timeout(300)
        cek("ringkasan jadwal: segera 3, selesai 1", "Segera 3" in teks(page, "#ringkasanJadwal") and "Selesai 1" in teks(page, "#ringkasanJadwal"), teks(page, "#ringkasanJadwal"))
        page.select_option("#fJadwal", "Segera")
        page.wait_for_timeout(300)
        cek("filter Segera 3 paket", all(x in teks(page, "#daftarJadwal") for x in ["Bali 3H2M", "Yogyakarta 2H1M", "Bandung 2H1M"]))
        page.select_option("#fJadwal", "Selesai")
        page.wait_for_timeout(300)
        cek("filter Selesai hanya Malang-Bromo", "Malang-Bromo 3H2M" in teks(page, "#daftarJadwal") and "Bali 3H2M" not in teks(page, "#daftarJadwal"))
        page.select_option("#fJadwal", "semua")

        print("== H. Pembayaran & DP ==")
        # buat pemesanan baru untuk uji DP: pelanggan Sari (2), paket P4 Lombok (4), 1 pax = 3.750.000
        page.click("#tabbar [data-tab=pemesanan]")
        page.wait_for_timeout(300)
        page.select_option("#pmPelanggan", "2")
        page.select_option("#pmPaket", "4")
        page.fill("#pmPax", "1")
        page.click("#btnTambahPemesanan")
        page.wait_for_timeout(400)
        cek("pemesanan uji DP dibuat (id 10)", teks(page, "#badgePemesanan") == "9")
        page.click("#tabbar [data-tab=pembayaran]")
        page.wait_for_timeout(300)
        page.select_option("#pbPemesanan", "10")
        page.wait_for_timeout(200)
        cek("pratinjau sisa tagihan Rp3.750.000", page.input_value("#pbSisa") == "Rp3.750.000", page.input_value("#pbSisa"))
        cek("pratinjau DP min 30% Rp1.125.000", "Rp1.125.000" in page.input_value("#pbDpMin"), page.input_value("#pbDpMin"))
        page.fill("#pbJumlah", "500000")
        page.click("#btnTambahPembayaran")
        page.wait_for_timeout(300)
        cek("DP di bawah 30% ditolak", "minimal 30%" in toast_text(page))
        page.fill("#pbJumlah", "1125000")
        page.evaluate("document.querySelector('#pbJumlah').dispatchEvent(new Event('change'))")
        page.click("#btnTambahPembayaran")
        page.wait_for_timeout(400)
        cek("DP 30% diterima, status DP", "status DP" in toast_text(page))
        page.select_option("#pbPemesanan", "10")
        page.wait_for_timeout(200)
        cek("sisa tagihan jadi Rp2.625.000", page.input_value("#pbSisa") == "Rp2.625.000", page.input_value("#pbSisa"))
        page.fill("#pbJumlah", "3000000")
        page.click("#btnTambahPembayaran")
        page.wait_for_timeout(300)
        cek("bayar melebihi sisa ditolak", "melebihi sisa tagihan" in toast_text(page))
        page.fill("#pbJumlah", "2625000")
        page.click("#btnTambahPembayaran")
        page.wait_for_timeout(400)
        cek("pelunasan -> status LUNAS", "LUNAS" in toast_text(page))
        cek("pemesanan lunas hilang dari select bayar", "Sari Wijaya — Lombok 4H3M" not in page.inner_text("#pbPemesanan"))

        print("== I. Laporan & CSV ==")
        page.click("#tabbar [data-tab=laporan]")
        page.wait_for_timeout(300)
        cek("bulan laporan default bulan berjalan (2026-11)", page.input_value("#fBulanLaporan") == "2026-11", page.input_value("#fBulanLaporan"))
        cek("laporan per paket Bali nilai Rp15.000.000", "Rp15.000.000" in teks(page, "#tabelPerPaket"))
        cek("laporan per paket Bali terbayar Rp8.000.000", "Rp8.000.000" in teks(page, "#tabelPerPaket"))
        cek("laporan per bulan Nov 7 pemesanan", "November 2026" in teks(page, "#tabelPerBulan"))
        cek("laporan per bulan Okt 1 pemesanan", "Oktober 2026" in teks(page, "#tabelPerBulan"))
        cek("pemasukan Lunas Rp18.700.000 (14.950.000 + 3.750.000 uji)", "Rp18.700.000" in teks(page, "#tabelDpLunas"), teks(page, "#tabelDpLunas"))
        cek("pemasukan DP Rp8.600.000", "Rp8.600.000" in teks(page, "#tabelDpLunas"))
        # CSV Nov: 7 pemesanan seed + id 9 (batal, tetap tercatat) + id 10 uji = 9 baris + header = 10
        page.select_option("#fBulanLaporan", "2026-11")
        with page.expect_download() as dl:
            page.click("#btnCsvLaporan")
        dl.value.save_as("/tmp/travel-nov.csv")
        lines = open("/tmp/travel-nov.csv").read().strip().split("\n")
        cek("CSV Nov 10 baris (9 + header)", len(lines) == 10, f"{len(lines)} baris")
        page.select_option("#fBulanLaporan", "2026-10")
        with page.expect_download() as dl2:
            page.click("#btnCsvLaporan")
        dl2.value.save_as("/tmp/travel-okt.csv")
        lines2 = open("/tmp/travel-okt.csv").read().strip().split("\n")
        cek("CSV Okt 2 baris (1 + header)", len(lines2) == 2, f"{len(lines2)} baris")

        print("== J. Backup / restore / reset ==")
        with page.expect_download() as dl3:
            page.click("#btnBackup")
        dl3.value.save_as("/tmp/travel-backup.json")
        data = json.load(open("/tmp/travel-backup.json"))
        cek("backup JSON berisi state + users", "state" in data and "users" in data and len(data["state"]["paket"]) == 6)
        data["state"]["pelanggan"].append({"id": 99, "nama": "RESTORE-TEST", "telepon": "0800", "identitas": "X"})
        json.dump(data, open("/tmp/travel-restore.json", "w"))
        page.set_input_files("#inputRestore", "/tmp/travel-restore.json")
        page.wait_for_timeout(600)
        page.click("#tabbar [data-tab=pelanggan]")
        page.wait_for_timeout(300)
        cek("restore: pelanggan RESTORE-TEST tampil", "RESTORE-TEST" in teks(page, "#daftarPelanggan"))
        open("/tmp/travel-bad.json", "w").write("{bukan json")
        page.click("#tabbar [data-tab=laporan]")
        page.wait_for_timeout(300)
        page.set_input_files("#inputRestore", "/tmp/travel-bad.json")
        page.wait_for_timeout(500)
        cek("restore file tidak valid ditolak", "tidak valid" in toast_text(page))
        page.click("#btnResetData")
        klik_modal_ya(page)
        cek("reset -> paket kembali 6", teks(page, "#badgePaket") == "6")
        page.click("#tabbar [data-tab=pelanggan]")
        page.wait_for_timeout(300)
        cek("reset -> RESTORE-TEST hilang", "RESTORE-TEST" not in teks(page, "#daftarPelanggan"))

        print("== K. Ganti kata sandi (agen) ==")
        logout(page)
        login(page, "agen", "agen123")
        page.fill("#sandiLama", "salah123")
        page.fill("#sandiBaru", "agen123baru")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        cek("sandi lama salah -> pesan", "salah" in teks(page, "#pesanSandi"))
        page.fill("#sandiLama", "agen123")
        page.fill("#sandiBaru", "agen123baru")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        cek("ganti sandi berhasil", "berhasil diubah" in teks(page, "#pesanSandi"))
        logout(page)
        login(page, "agen", "agen123baru")
        cek("login dengan sandi baru berhasil", "Sinta Maharani (Agen)" in teks(page, "#userChip"))
        logout(page)
        login(page, "admin", "admin123")
        page.click("#tabbar [data-tab=dashboard]")
        page.wait_for_timeout(300)
        page.click("[data-reset-user='agen']")
        klik_modal_ya(page)
        cek("reset sandi agen -> bk123", "bk123" in toast_text(page))
        logout(page)
        login(page, "agen", "bk123")
        cek("login agen dengan bk123 berhasil", "Sinta Maharani (Agen)" in teks(page, "#userChip"))

        print("== L. Console / page error ==")
        cek("0 console error", len(console_errors) == 0, str(console_errors[:3]))
        cek("0 page error", len(page_errors) == 0, str(page_errors[:3]))
        browser.close()

    print(f"\nHASIL: {LOLOS} lolos, {GAGAL} gagal")
    if GAGAL:
        print("Gagal:", ERRORS)
        sys.exit(1)


if __name__ == "__main__":
    main()
