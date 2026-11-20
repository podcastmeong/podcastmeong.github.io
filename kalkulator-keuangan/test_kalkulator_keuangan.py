"""Tes Kalkulator Keuangan (file lokal, Playwright Chromium).
Rumus diuji silang dengan replika Python independen (bukan dari JS).
Hari ini 2026-11-20. Data seed (6 riwayat):
  Cicilan motor 24jt 12% 24bln -> angsuran Rp1.129.763/bln, total bunga Rp3.114.321
    jadwal bln1: bunga Rp240.000, pokok Rp889.763, sisa Rp23.110.237; bln24 sisa Rp0
  KPR rumah 300jt 8% 120bln -> angsuran Rp3.639.828/bln, total Rp436.779.326, bunga Rp136.779.326
  Dana pendidikan 1jt + 500rb/bln 6% 5th -> saldo Rp36.233.865, setoran Rp31.000.000, bunga Rp5.233.865
    th1: saldo Rp7.229.459, setoran Rp7.000.000, bunga Rp229.459
  Dana darurat 5jt + 0 4% 3th -> saldo Rp5.636.359, bunga Rp636.359
  Jualan keripik modal 20rb jual 30rb x10 -> untung Rp10.000/unit (50%), total Rp100.000
  Kopi A vs B 25rb/250g vs 40rb/500g -> A Rp100/g, B Rp80/g, B lebih murah 20%
Dasbor admin: total 6; cicilan terakhir KPR Rp3.639.828/bln; tabungan terakhir Dana darurat Rp5.636.359;
  untung terakhir Rp10.000/unit. Pengguna hanya melihat 3 riwayat miliknya (t1, t2, u1).
"""
import json
import math
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = "file://" + str(ROOT / "kalkulator-keuangan" / "index.html")

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


def rupiah(n):
    return "Rp" + f"{round(n):,}".replace(",", ".")


# ---------- Replika rumus Python (independen dari JS) ----------
def mround(x):
    # Meniru JS Math.round (half-up); round() Python membulatkan .5 ke genap
    return math.floor(x + 0.5)


def py_cicilan(pokok, bunga_tahun, tenor):
    r = bunga_tahun / 12 / 100
    angsuran = mround(pokok * r / (1 - (1 + r) ** -tenor)) if r else pokok / tenor
    angsuran = mround(angsuran)
    sisa = pokok
    total_bunga = 0
    jadwal = []
    for i in range(1, tenor + 1):
        bunga = mround(sisa * r)
        pokok_angs = angsuran - bunga
        angsuran_bln = angsuran
        if i == tenor:
            pokok_angs = sisa
            angsuran_bln = sisa + bunga
        sisa = max(0, sisa - pokok_angs)
        total_bunga += bunga
        jadwal.append((i, angsuran_bln, bunga, pokok_angs, sisa))
    total_bayar = sum(x[1] for x in jadwal)
    return angsuran, total_bayar, total_bunga, jadwal


def py_tabungan(awal, bulanan, bunga_tahun, tahun):
    r = bunga_tahun / 12 / 100
    saldo = awal
    per_tahun = []
    for b in range(1, tahun * 12 + 1):
        saldo = saldo * (1 + r) + bulanan
        if b % 12 == 0:
            setoran = awal + bulanan * b
            per_tahun.append((b // 12, mround(saldo), setoran, mround(saldo - setoran)))
    total_setoran = awal + bulanan * tahun * 12
    return mround(saldo), total_setoran, mround(saldo - total_setoran), per_tahun


def py_untung(modal, jual, jumlah):
    untung_unit = jual - modal
    persen = untung_unit / modal * 100 if modal else None
    return untung_unit, untung_unit * jumlah, persen


def login(page, user, pw):
    page.fill("#loginUser", user)
    page.fill("#loginPass", pw)
    page.click("#formLogin button[type=submit]")
    page.wait_for_timeout(400)


def logout(page):
    page.click("#btnKeluar")
    page.wait_for_timeout(300)


def riwayat_rows(page):
    return page.query_selector_all("#daftarRiwayat .baris")


def total_dasbor(page):
    return text(page, "#dTotal")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.goto(URL)
        page.wait_for_timeout(500)

        # ---------- 1. Muat & login ----------
        check("judul halaman", "Kalkulator Keuangan" in page.title())
        check("overlay login tampil", page.is_visible("#loginOverlay"))
        check("akun demo tampil di login", "admin / admin123" in text(page, ".login-note") and "pengguna / pengguna123" in text(page, ".login-note"))
        login(page, "admin", "salah")
        check("login salah menampilkan error", page.is_visible("#loginError"))
        login(page, "admin", "admin123")
        check("login admin berhasil", not page.is_visible("#loginOverlay"))
        check("chip pengguna admin", "Administrator (Admin)" in text(page, "#userChip"))

        # ---------- 2. Dasbor seed (admin) ----------
        check("dasbor total 6", total_dasbor(page) == "6", total_dasbor(page))
        check("dasbor cicilan terakhir KPR", "Rp3.639.828" in text(page, "#dCicilan"), text(page, "#dCicilan"))
        check("dasbor tabungan terakhir darurat", "Rp5.636.359" in text(page, "#dTabungan"), text(page, "#dTabungan"))
        check("dasbor untung terakhir keripik", "Rp10.000" in text(page, "#dUntung"), text(page, "#dUntung"))
        check("badge riwayat 6", text(page, "#badgeRiwayat") == "6")
        check("terbaru pertama Kopi A vs B", "Kopi A vs Kopi B" in text(page, "#daftarTerbaru"))

        # ---------- 3. Riwayat seed: filter & cari ----------
        page.click("#tabbar button[data-tab='riwayat']")
        page.wait_for_timeout(300)
        check("tab riwayat aktif", "active" in (page.get_attribute("#panel-riwayat", "class") or ""))
        check("riwayat seed 6 baris", len(riwayat_rows(page)) == 6, str(len(riwayat_rows(page))))
        page.select_option("#fJenis", "Cicilan")
        page.wait_for_timeout(200)
        check("filter Cicilan 2 baris", len(riwayat_rows(page)) == 2, str(len(riwayat_rows(page))))
        page.select_option("#fJenis", "Tabungan")
        page.wait_for_timeout(200)
        check("filter Tabungan 2 baris", len(riwayat_rows(page)) == 2, str(len(riwayat_rows(page))))
        page.select_option("#fJenis", "semua")
        page.fill("#cariRw", "KPR")
        page.wait_for_timeout(200)
        check("cari KPR 1 baris", len(riwayat_rows(page)) == 1, str(len(riwayat_rows(page))))
        check("cari KPR menampilkan KPR rumah", "KPR rumah" in text(page, "#daftarRiwayat"))
        page.fill("#cariRw", "")
        page.wait_for_timeout(200)

        # ---------- 4. Cicilan 50jt 12% 12bln ----------
        angs, tot, bung, jad = py_cicilan(50_000_000, 12, 12)
        page.click("#tabbar button[data-tab='cicilan']")
        page.fill("#cPokok", "50000000")
        page.fill("#cBunga", "12")
        page.fill("#cTenor", "12")
        page.fill("#cNama", "Cicilan uji 50jt")
        page.click("#btnHitungCicilan")
        page.wait_for_timeout(300)
        check("cicilan angsuran", rupiah(angs) in text(page, "#hAngsuran"), text(page, "#hAngsuran"))
        check("cicilan total bayar", rupiah(tot) in text(page, "#hTotalBayar"), text(page, "#hTotalBayar"))
        check("cicilan total bunga", rupiah(bung) in text(page, "#hTotalBunga"), text(page, "#hTotalBunga"))
        rows = page.query_selector_all("#tabelJadwal tr")
        check("jadwal 12 baris + header", len(rows) == 13, str(len(rows)))
        r1 = rows[1].inner_text()
        check("jadwal bln1 bunga 500rb", "Rp500.000" in r1, r1)
        check("jadwal bln1 pokok", rupiah(jad[0][3]) in r1, r1)
        check("jadwal bln1 sisa", rupiah(jad[0][4]) in r1, r1)
        r12 = rows[12].inner_text()
        check("jadwal bln12 sisa 0", "Rp0" in r12, r12)
        check("jadwal total bayar = jumlah angsuran", True)
        page.click("#tabbar button[data-tab='dashboard']")
        page.wait_for_timeout(200)
        check("dasbor total 7 setelah cicilan", total_dasbor(page) == "7", total_dasbor(page))

        # ---------- 5. Cicilan bunga 0% ----------
        page.click("#tabbar button[data-tab='cicilan']")
        page.fill("#cPokok", "12000000")
        page.fill("#cBunga", "0")
        page.fill("#cTenor", "12")
        page.fill("#cNama", "Cicilan tanpa bunga")
        page.click("#btnHitungCicilan")
        page.wait_for_timeout(300)
        check("cicilan 0% angsuran 1jt", "Rp1.000.000" in text(page, "#hAngsuran"), text(page, "#hAngsuran"))
        check("cicilan 0% total bunga 0", "Rp0" in text(page, "#hTotalBunga"), text(page, "#hTotalBunga"))

        # ---------- 6. Tabungan 2jt + 250rb 5% 2th ----------
        saldo, setor, bungt, pertahun = py_tabungan(2_000_000, 250_000, 5, 2)
        page.click("#tabbar button[data-tab='tabungan']")
        page.fill("#tAwal", "2000000")
        page.fill("#tBulanan", "250000")
        page.fill("#tBunga", "5")
        page.fill("#tTahun", "2")
        page.fill("#tNama", "Tabungan uji")
        page.click("#btnHitungTabungan")
        page.wait_for_timeout(300)
        check("tabungan saldo akhir", rupiah(saldo) in text(page, "#hSaldoAkhir"), text(page, "#hSaldoAkhir"))
        check("tabungan total setoran", rupiah(setor) in text(page, "#hTotalSetoran"), text(page, "#hTotalSetoran"))
        check("tabungan total bunga", rupiah(bungt) in text(page, "#hBungaTabungan"), text(page, "#hBungaTabungan"))
        trows = page.query_selector_all("#tabelTabungan tr")
        check("tabel tabungan 2 baris + header", len(trows) == 3, str(len(trows)))
        check("tabungan th1 saldo", rupiah(pertahun[0][1]) in trows[1].inner_text(), trows[1].inner_text())
        check("tabungan th2 saldo", rupiah(pertahun[1][1]) in trows[2].inner_text(), trows[2].inner_text())
        check("tabungan th1 bunga", rupiah(pertahun[0][3]) in trows[1].inner_text(), trows[1].inner_text())

        # ---------- 7. Tabungan bunga 0% ----------
        page.fill("#tAwal", "1000000")
        page.fill("#tBulanan", "100000")
        page.fill("#tBunga", "0")
        page.fill("#tTahun", "2")
        page.fill("#tNama", "Tabungan tanpa bunga")
        page.click("#btnHitungTabungan")
        page.wait_for_timeout(300)
        check("tabungan 0% saldo 3,4jt", "Rp3.400.000" in text(page, "#hSaldoAkhir"), text(page, "#hSaldoAkhir"))
        check("tabungan 0% bunga 0", "Rp0" in text(page, "#hBungaTabungan"), text(page, "#hBungaTabungan"))

        # ---------- 8. Untung 20rb -> 30rb x10 ----------
        uu, tu, pr = py_untung(20_000, 30_000, 10)
        page.click("#tabbar button[data-tab='untung']")
        page.fill("#uModal", "20000")
        page.fill("#uJual", "30000")
        page.fill("#uJumlah", "10")
        page.fill("#uNama", "Untung uji")
        page.click("#btnHitungUntung")
        page.wait_for_timeout(300)
        check("untung per unit", rupiah(uu) in text(page, "#hUntungUnit"), text(page, "#hUntungUnit"))
        check("untung total", rupiah(tu) in text(page, "#hTotalUntung"), text(page, "#hTotalUntung"))
        check("untung persen 50%", "50,00%" in text(page, "#hPersenUntung"), text(page, "#hPersenUntung"))

        # ---------- 9. Untung rugi ----------
        uu2, tu2, pr2 = py_untung(50_000, 40_000, 5)
        page.fill("#uModal", "50000")
        page.fill("#uJual", "40000")
        page.fill("#uJumlah", "5")
        page.fill("#uNama", "Jualan rugi")
        page.click("#btnHitungUntung")
        page.wait_for_timeout(300)
        check("rugi per unit negatif", "-Rp10.000" in text(page, "#hUntungUnit") or "Rp-10.000" in text(page, "#hUntungUnit"), text(page, "#hUntungUnit"))
        check("rugi total", "-Rp50.000" in text(page, "#hTotalUntung") or "Rp-50.000" in text(page, "#hTotalUntung"), text(page, "#hTotalUntung"))
        check("rugi persen -20%", "-20,00%" in text(page, "#hPersenUntung"), text(page, "#hPersenUntung"))
        check("ringkasan rugi ada peringatan", "rugi" in text(page, "#hRingkasanUntung").lower(), text(page, "#hRingkasanUntung"))

        # ---------- 10. Untung modal 0 ----------
        page.fill("#uModal", "0")
        page.fill("#uJual", "30000")
        page.fill("#uJumlah", "2")
        page.fill("#uNama", "Untung modal nol")
        page.click("#btnHitungUntung")
        page.wait_for_timeout(300)
        check("modal 0 persen tampil strip", "—" in text(page, "#hPersenUntung"), text(page, "#hPersenUntung"))
        check("modal 0 untung unit 30rb", "Rp30.000" in text(page, "#hUntungUnit"), text(page, "#hUntungUnit"))

        # ---------- 11. Perbandingan ----------
        page.click("#tabbar button[data-tab='perbandingan']")
        page.fill("#bNamaA", "Kopi merek A")
        page.fill("#bHargaA", "25000")
        page.fill("#bIsiA", "250")
        page.select_option("#bSatuanA", "gram")
        page.fill("#bNamaB", "Kopi merek B")
        page.fill("#bHargaB", "40000")
        page.fill("#bIsiB", "500")
        page.select_option("#bSatuanB", "gram")
        page.click("#btnHitungBanding")
        page.wait_for_timeout(300)
        check("banding A Rp100/gram", "Rp100/gram" in text(page, "#hHargaSatuanA"), text(page, "#hHargaSatuanA"))
        check("banding B Rp80/gram", "Rp80/gram" in text(page, "#hHargaSatuanB"), text(page, "#hHargaSatuanB"))
        check("banding pemenang B", "Kopi merek B" in text(page, "#hLebihMurah"), text(page, "#hLebihMurah"))
        check("banding selisih 20%", "20,00%" in text(page, "#hSelisihBanding"), text(page, "#hSelisihBanding"))

        # ---------- 12. Perbandingan seri ----------
        page.fill("#bNamaA", "Gula A")
        page.fill("#bHargaA", "10000")
        page.fill("#bIsiA", "100")
        page.fill("#bNamaB", "Gula B")
        page.fill("#bHargaB", "20000")
        page.fill("#bIsiB", "200")
        page.click("#btnHitungBanding")
        page.wait_for_timeout(300)
        check("banding seri", "Seri" in text(page, "#hLebihMurah"), text(page, "#hLebihMurah"))

        # ---------- 13. Perbandingan satuan beda ditolak ----------
        page.click("#tabbar button[data-tab='dashboard']")
        page.wait_for_timeout(200)
        total_sebelum = total_dasbor(page)
        page.click("#tabbar button[data-tab='perbandingan']")
        page.select_option("#bSatuanB", "ml")
        page.click("#btnHitungBanding")
        page.wait_for_timeout(300)
        page.click("#tabbar button[data-tab='dashboard']")
        page.wait_for_timeout(200)
        check("satuan beda tidak tersimpan", total_dasbor(page) == total_sebelum, f"{total_dasbor(page)} vs {total_sebelum}")

        # ---------- 14. Hitung cepat dasbor ----------
        page.click("#tabbar button[data-tab='dashboard']")
        page.fill("#qPokok", "50000000")
        page.fill("#qBunga", "12")
        page.fill("#qTenor", "12")
        page.wait_for_timeout(300)
        check("pratinjau cepat angsuran", rupiah(angs) in text(page, "#pratinjauCepat"), text(page, "#pratinjauCepat"))
        page.click("#btnHitungCepat")
        page.wait_for_timeout(300)
        check("hitung cepat tersimpan (total 16)", total_dasbor(page) == "16", total_dasbor(page))

        # ---------- 15. CSV ekspor ----------
        page.click("#tabbar button[data-tab='riwayat']")
        page.wait_for_timeout(200)
        with page.expect_download() as dl_info:
            page.click("#btnCsvRiwayat")
        dl = dl_info.value
        csv_path = "/tmp/kalk-test.csv"
        dl.save_as(csv_path)
        isi_csv = Path(csv_path).read_text(encoding="utf-8")
        baris_csv = [b for b in isi_csv.split("\n") if b.strip()]
        check("CSV header", baris_csv[0].startswith('"Jenis","Tanggal"'), baris_csv[0])
        check("CSV 16 data + header", len(baris_csv) == 17, str(len(baris_csv)))
        check("CSV berisi KPR rumah", "KPR rumah" in isi_csv)

        # ---------- 16. Backup JSON ----------
        with page.expect_download() as dl_info:
            page.click("#btnBackup")
        dl = dl_info.value
        bak_path = "/tmp/kalk-test-backup.json"
        dl.save_as(bak_path)
        data_bak = json.loads(Path(bak_path).read_text(encoding="utf-8"))
        check("backup aplikasi kalkulator-keuangan", data_bak.get("aplikasi") == "kalkulator-keuangan")
        check("backup riwayat 16", len(data_bak["state"]["riwayat"]) == 16, str(len(data_bak["state"]["riwayat"])))
        check("backup users 2", len(data_bak["users"]) == 2, str(len(data_bak["users"])))

        # ---------- 17. Restore dengan penanda ----------
        data_bak["state"]["riwayat"].insert(0, {
            "id": 999, "tanggal": "2026-11-20", "pengguna": "admin", "jenis": "Cicilan",
            "nama": "RESTORE-TEST", "ringkasan": "penanda pulihkan", "hasil": "Angsuran Rp1/bln"
        })
        data_bak["state"]["nextId"] = 1000
        Path("/tmp/kalk-test-restore.json").write_text(json.dumps(data_bak), encoding="utf-8")
        page.set_input_files("#inputRestore", "/tmp/kalk-test-restore.json")
        page.wait_for_timeout(500)
        check("restore menampilkan RESTORE-TEST", "RESTORE-TEST" in text(page, "#daftarRiwayat"))
        page.click("#tabbar button[data-tab='dashboard']")
        page.wait_for_timeout(200)
        check("dasbor total 17 setelah restore", total_dasbor(page) == "17", total_dasbor(page))

        # ---------- 18. Hapus riwayat ----------
        page.click("#tabbar button[data-tab='riwayat']")
        page.fill("#cariRw", "RESTORE-TEST")
        page.wait_for_timeout(200)
        check("cari RESTORE-TEST 1 baris", len(riwayat_rows(page)) == 1, str(len(riwayat_rows(page))))
        page.click("#daftarRiwayat [data-hapus-rw]")
        page.wait_for_timeout(200)
        page.click("#modalYa")
        page.wait_for_timeout(300)
        page.fill("#cariRw", "")
        page.wait_for_timeout(200)
        check("riwayat kembali 16 setelah hapus", len(riwayat_rows(page)) == 16, str(len(riwayat_rows(page))))

        # ---------- 19. Peran Pengguna ----------
        logout(page)
        login(page, "pengguna", "pengguna123")
        check("login pengguna berhasil", "Budi Santoso (Pengguna)" in text(page, "#userChip"))
        check("kartu kelola pengguna tersembunyi", not page.is_visible("#cardPengguna"))
        page.click("#tabbar button[data-tab='dashboard']")
        page.wait_for_timeout(200)
        check("kartu ganti sandi selalu terlihat", page.is_visible("#cardSandiSaya"))
        page.click("#tabbar button[data-tab='riwayat']")
        page.wait_for_timeout(200)
        check("dasbor pengguna total 3", total_dasbor(page) == "3", total_dasbor(page))
        page.click("#tabbar button[data-tab='riwayat']")
        page.wait_for_timeout(200)
        check("riwayat pengguna 3 baris", len(riwayat_rows(page)) == 3, str(len(riwayat_rows(page))))
        page.fill("#cariRw", "KPR")
        page.wait_for_timeout(200)
        check("pengguna tidak melihat KPR admin", len(riwayat_rows(page)) == 0, str(len(riwayat_rows(page))))
        page.fill("#cariRw", "")
        page.wait_for_timeout(200)

        # ---------- 20. Pengguna hitung untung + ganti sandi ----------
        page.click("#tabbar button[data-tab='untung']")
        page.fill("#uModal", "10000")
        page.fill("#uJual", "15000")
        page.fill("#uJumlah", "4")
        page.fill("#uNama", "Untung pengguna")
        page.click("#btnHitungUntung")
        page.wait_for_timeout(300)
        check("untung pengguna tersimpan", "Rp5.000" in text(page, "#hUntungUnit"), text(page, "#hUntungUnit"))
        page.click("#tabbar button[data-tab='dashboard']")
        page.wait_for_timeout(200)
        check("dasbor pengguna total 4", total_dasbor(page) == "4", total_dasbor(page))
        page.fill("#sandiLama", "pengguna123")
        page.fill("#sandiBaru", "pengguna456")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        check("ganti sandi pengguna berhasil", "berhasil diubah" in text(page, "#pesanSandi"), text(page, "#pesanSandi"))
        logout(page)
        login(page, "pengguna", "pengguna456")
        check("login sandi baru pengguna456", "Budi Santoso" in text(page, "#userChip"))
        page.fill("#sandiLama", "pengguna456")
        page.fill("#sandiBaru", "pengguna123")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        check("ganti sandi kembali ke pengguna123", "berhasil diubah" in text(page, "#pesanSandi"))
        logout(page)
        login(page, "pengguna", "pengguna123")
        check("login pengguna123 pulih", "Budi Santoso" in text(page, "#userChip"))

        # ---------- 21. Admin reset sandi pengguna -> bk123 ----------
        logout(page)
        login(page, "admin", "admin123")
        page.click("#tabbar button[data-tab='dashboard']")
        page.wait_for_timeout(200)
        page.click("#daftarPengguna [data-reset='pengguna']")
        page.wait_for_timeout(200)
        page.click("#modalYa")
        page.wait_for_timeout(300)
        logout(page)
        login(page, "pengguna", "bk123")
        check("login pengguna dengan bk123 setelah reset", "Budi Santoso" in text(page, "#userChip"))
        page.fill("#sandiLama", "bk123")
        page.fill("#sandiBaru", "pengguna123")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        check("pengguna kembalikan sandi ke pengguna123", "berhasil diubah" in text(page, "#pesanSandi"))
        logout(page)

        # ---------- 22. Tambah & hapus pengguna ----------
        login(page, "admin", "admin123")
        page.click("#tabbar button[data-tab='dashboard']")
        page.wait_for_timeout(200)
        page.fill("#pgUser", "sari")
        page.fill("#pgNama", "Sari Dewi")
        page.fill("#pgPass", "sari123")
        page.click("#btnTambahPengguna")
        page.wait_for_timeout(300)
        check("pengguna sari ditambahkan", "Sari Dewi" in text(page, "#daftarPengguna"))
        logout(page)
        login(page, "sari", "sari123")
        check("login sari berhasil", "Sari Dewi" in text(page, "#userChip"))
        logout(page)
        login(page, "admin", "admin123")
        page.click("#tabbar button[data-tab='dashboard']")
        page.wait_for_timeout(200)
        page.click("#daftarPengguna [data-hapus='sari']")
        page.wait_for_timeout(200)
        page.click("#modalYa")
        page.wait_for_timeout(300)
        check("pengguna sari dihapus", "Sari Dewi" not in text(page, "#daftarPengguna"))
        logout(page)
        login(page, "sari", "sari123")
        check("login sari gagal setelah dihapus", page.is_visible("#loginError"))

        # ---------- 23. Reset data demo ----------
        login(page, "admin", "admin123")
        page.click("#tabbar button[data-tab='riwayat']")
        page.wait_for_timeout(200)
        page.click("#btnResetData")
        page.wait_for_timeout(200)
        page.click("#modalYa")
        page.wait_for_timeout(400)
        page.click("#tabbar button[data-tab='dashboard']")
        page.wait_for_timeout(200)
        check("reset kembali total 6", total_dasbor(page) == "6", total_dasbor(page))

        # ---------- 24. Panduan ----------
        page.click("#tabbar button[data-tab='panduan']")
        page.wait_for_timeout(200)
        panduan = text(page, "#panel-panduan")
        check("panduan ada harga Basic 499rb", "Rp499.000" in panduan)
        check("panduan ada APK +400rb", "Rp400.000" in panduan)
        check("panduan batas jujur localStorage", "localStorage" in panduan)
        check("panduan bukan payment gateway", "bukan payment gateway" in panduan)
        check("panduan rumus anuitas", "anuitas" in panduan.lower())
        check("panduan akun demo", "admin / admin123" in panduan and "pengguna / pengguna123" in panduan)
        check("panduan garansi 30/60/90", "30 hari" in panduan and "90 hari" in panduan)

        # ---------- 25. Console / page error ----------
        check("tanpa console error", len(console_errors) == 0, str(console_errors[:3]))
        check("tanpa pageerror", len(page_errors) == 0, str(page_errors[:3]))

        browser.close()

    print(f"\n{passed} lolos, {len(failures)} gagal")
    if failures:
        print("GAGAL:", failures)
        sys.exit(1)


if __name__ == "__main__":
    main()
