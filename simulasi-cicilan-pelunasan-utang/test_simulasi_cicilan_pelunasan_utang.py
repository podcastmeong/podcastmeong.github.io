"""Tes Simulasi Cicilan & Pelunasan Utang (file lokal, Playwright Chromium).
Hari ini 2026-11-20. Data seed (9 pinjaman, tanggal relatif terhadap hari ini):
  S1 KPR Rumah admin 240jt, 9%, 120 bln, mulai T-61, bayar 2
     angsuran Rp3.040.219, total bunga Rp124.826.195, total bayar Rp364.826.195
  S2 Kredit Motor pengguna 24jt, 12%, 24 bln, mulai T-31, bayar 1
     angsuran Rp1.129.763, total bunga Rp3.114.321, total bayar Rp27.114.321
  S3 Pinjaman Koperasi pengguna 10jt, 6%, 12 bln, mulai T-10, bayar 0
     angsuran Rp860.664, total bunga Rp327.973
  S4 Cicilan HP admin 6jt, 0%, 6 bln, mulai T-5, bayar 0 -> angsuran Rp1.000.000
  S5 Kredit Mobil admin 150jt, 10%, 36 bln, mulai T-92, bayar 3
     angsuran Rp4.840.078, total bunga Rp24.242.809
  S6 Pinjaman Online pengguna 5jt, 24%, 6 bln, mulai T-40, bayar 0
     angsuran Rp892.629, total bunga Rp355.775; jatuh tempo berikut T-10 (LEWAT)
  S7 Cicilan Laptop admin 12jt, 12%, 12 bln, mulai T-25, bayar 0
     angsuran Rp1.066.185, total bunga Rp794.226; jatuh tempo berikut T+6 (SEGERA)
  S8 Cicilan Kulkas pengguna 8jt, 8%, 10 bln, mulai T-76, bayar 2
     angsuran Rp829.626, total bunga Rp296.256
  S9 Cicilan TV pengguna 4,8jt, 0%, 6 bln, mulai T-194, bayar 6 -> LUNAS
Dasbor admin: pokok aktif Rp455.000.000 (8), angsuran/bln Rp13.659.164,
  segera 1, lewat 1, total bayar aktif Rp608.957.555.
Dasbor pengguna: pokok aktif Rp47.000.000 (4), angsuran/bln Rp3.712.682,
  segera 0, lewat 1, total bayar aktif Rp51.094.325.
Laporan semua: total pokok Rp459.800.000, angsuran/bln Rp14.459.164,
  total bunga Rp153.957.555, total bayar Rp613.757.555; aktif 8, lunas 1.
  Periode 7 hari: 1 pinjaman (HP, Rp6.000.000).
  Periode 30 hari: 3 pinjaman (Koperasi, HP, Laptop, Rp28.000.000).
Simulasi form 120jt/12%/12bln: angsuran Rp10.661.855, bunga Rp7.942.256,
  total Rp127.942.256.
Pelunasan Motor +500rb/bln: tenor 17 (hemat 7), bunga Rp2.092.023 (hemat Rp1.022.298).
Pelunasan Motor lump 5jt bln-6: tenor 19 (hemat 5), bunga Rp2.258.267 (hemat Rp856.054).
Pelunasan Motor +500rb & lump 5jt: tenor 13 (hemat 11), bunga Rp1.634.550 (hemat Rp1.479.771).
Banding A 24jt/12%/24 vs B 24jt/10%/36: A total Rp27.114.321, B total Rp27.878.852,
  A lebih murah Rp764.531; angsuran A Rp1.129.763, B Rp774.412.
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = "file://" + str(ROOT / "simulasi-cicilan-pelunasan-utang" / "index.html")

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
    page.wait_for_timeout(250)


# ---------- Perhitungan independen (uji silang rumus halaman) ----------
def anuitas(pokok, bunga_thn, tenor):
    r = bunga_thn / 12 / 100
    angs = pokok / tenor if r == 0 else pokok * r / (1 - (1 + r) ** (-tenor))
    angs = round(angs)
    sisa = pokok
    total_bunga = 0
    jadwal = []
    for i in range(1, tenor + 1):
        bunga = round(sisa * r)
        pokok_angs = angs - bunga
        angs_bln = angs
        if i == tenor:
            pokok_angs = sisa
            angs_bln = sisa + bunga
        sisa -= pokok_angs
        total_bunga += bunga
        jadwal.append((i, angs_bln, bunga, pokok_angs, max(0, sisa)))
    return angs, total_bunga, pokok + total_bunga, jadwal


def percepat(pokok, bunga_thn, tenor, extra=0, lump_bulan=None, lump=0):
    angs, tb, _, _ = anuitas(pokok, bunga_thn, tenor)
    r = bunga_thn / 12 / 100
    sisa = pokok
    total_bunga = 0
    bulan = 0
    while sisa > 0 and bulan < 600:
        bulan += 1
        bunga = round(sisa * r)
        pokok_angs = angs + extra - bunga
        if pokok_angs > sisa:
            pokok_angs = sisa
        sisa -= pokok_angs
        total_bunga += bunga
        if lump_bulan and bulan == lump_bulan and sisa > 0:
            sisa -= min(lump, sisa)
    return bulan, total_bunga, pokok + total_bunga


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.goto(URL)
        page.wait_for_timeout(500)

        # ---------- 0. Rumus Python vs angka referensi ----------
        a, tb, tot, j = anuitas(120_000_000, 12, 12)
        check("py anuitas 120jt/12%/12", a == 10661855 and tb == 7942256 and tot == 127942256, f"{a} {tb} {tot}")
        check("py jadwal berakhir 0", j[-1][4] == 0)
        a2, tb2, tot2, j2 = anuitas(24_000_000, 12, 24)
        check("py motor angsuran 1129763", a2 == 1129763 and tb2 == 3114321, f"{a2} {tb2}")
        b, tb3, _ = percepat(24_000_000, 12, 24, extra=500_000)
        check("py percepat motor +500rb tenor 17", b == 17 and tb3 == 2092023, f"{b} {tb3}")

        # ---------- 1. Muat & login ----------
        check("judul halaman", "Simulasi Cicilan" in page.title())
        check("overlay login tampil", page.is_visible("#loginOverlay"))
        check("akun demo tampil di login", "admin / admin123" in text(page, ".login-note") and "pengguna / pengguna123" in text(page, ".login-note"))
        login(page, "admin", "salah")
        check("login salah menampilkan error", page.is_visible("#loginError"))
        login(page, "admin", "admin123")
        check("login admin berhasil", not page.is_visible("#loginOverlay"))
        check("chip pengguna admin", "Administrator (Admin)" in text(page, "#userChip"))

        # ---------- 2. Dasbor seed (admin) ----------
        check("dasbor pokok aktif 455jt", "Rp455.000.000" in text(page, "#dPokok"), text(page, "#dPokok"))
        check("dasbor pokok sub 8 pinjaman", "8 pinjaman aktif" in text(page, "#dPokokSub"), text(page, "#dPokokSub"))
        check("dasbor angsuran 13,65jt", "Rp13.659.164" in text(page, "#dAngsuran"), text(page, "#dAngsuran"))
        check("dasbor segera 1", text(page, "#dSegera") == "1", text(page, "#dSegera"))
        check("dasbor lewat 1", text(page, "#dLewat") == "1", text(page, "#dLewat"))
        check("dasbor total bayar 608,95jt", "Rp608.957.555" in text(page, "#dTotalBayar"), text(page, "#dTotalBayar"))
        check("badge jadwal 9", text(page, "#badgeJadwal") == "9", text(page, "#badgeJadwal"))
        check("badge ingat 2", text(page, "#badgeIngat") == "2", text(page, "#badgeIngat"))
        check("terdekat pertama Pinjaman Online", "Pinjaman Online" in text(page, "#daftarTerbaru").split("\n")[0], text(page, "#daftarTerbaru")[:200])
        check("terdekat ada Cicilan Laptop", "Cicilan Laptop" in text(page, "#daftarTerbaru"))
        check("kartu kelola pengguna terlihat (admin)", page.is_visible("#cardPengguna"))
        check("kartu ganti sandi terlihat", page.is_visible("#cardSandiSaya"))
        check("kartu tambah cepat terlihat", page.is_visible("#cardTambahCepat"))

        # ---------- 3. Tab Simulasi ----------
        tab(page, "simulasi")
        page.fill("#sPokok", "120000000")
        page.fill("#sBunga", "12")
        page.fill("#sTenor", "12")
        page.wait_for_timeout(200)
        check("pratinjau angsuran 10,66jt", "Rp10.661.855" in text(page, "#pratinjauSimulasi"), text(page, "#pratinjauSimulasi"))
        page.click("#btnHitungSimulasi")
        page.wait_for_timeout(300)
        check("simulasi angsuran 10,66jt", "Rp10.661.855" in text(page, "#hAngsuran"), text(page, "#hAngsuran"))
        check("simulasi total bunga 7,94jt", "Rp7.942.256" in text(page, "#hBunga"), text(page, "#hBunga"))
        check("simulasi total bayar 127,94jt", "Rp127.942.256" in text(page, "#hTotal"), text(page, "#hTotal"))
        check("simulasi tenor 12 bln", "12 bln" in text(page, "#hTenor"))
        rows_s = page.query_selector_all("#tabelSimulasi tr")
        check("tabel simulasi 12 + header", len(rows_s) == 13, str(len(rows_s)))
        check("simulasi bln 1 bunga 1,2jt", "Rp1.200.000" in rows_s[1].inner_text(), rows_s[1].inner_text())
        check("simulasi bln 1 pokok 9,46jt", "Rp9.461.855" in rows_s[1].inner_text(), rows_s[1].inner_text())
        check("simulasi bln akhir sisa Rp0", "Rp0" in rows_s[-1].inner_text(), rows_s[-1].inner_text())
        page.fill("#sPokok", "6000000")
        page.fill("#sBunga", "0")
        page.fill("#sTenor", "6")
        page.click("#btnHitungSimulasi")
        page.wait_for_timeout(300)
        check("simulasi 0% angsuran 1jt", "Rp1.000.000" in text(page, "#hAngsuran"), text(page, "#hAngsuran"))
        check("simulasi 0% bunga Rp0", "Rp0" in text(page, "#hBunga"), text(page, "#hBunga"))
        check("tabel simulasi 0% 6 + header", len(page.query_selector_all("#tabelSimulasi tr")) == 7)

        # ---------- 4. Simpan simulasi + jadwal + bayar + lunas + batal + hapus ----------
        page.fill("#sPokok", "3000000")
        page.fill("#sBunga", "0")
        page.fill("#sTenor", "3")
        page.fill("#sNama", "Simulasi Test")
        page.click("#btnSimpanSimulasi")
        page.wait_for_timeout(300)
        tab(page, "dashboard")
        check("dasbor pokok 458jt setelah Simulasi Test", "Rp458.000.000" in text(page, "#dPokok"), text(page, "#dPokok"))
        tab(page, "jadwal")
        check("jadwal daftar 10 pinjaman", len(page.query_selector_all("#daftarPinjaman .baris")) == 10, str(len(page.query_selector_all("#daftarPinjaman .baris"))))
        page.select_option("#pilihPinjaman", "10")
        page.wait_for_timeout(300)
        check("jadwal ringkasan Simulasi Test", "Simulasi Test" in text(page, "#ringkasanJadwal"), text(page, "#ringkasanJadwal"))
        rows_j = page.query_selector_all("#tabelJadwal tr")
        check("jadwal Simulasi Test 3 + header", len(rows_j) == 4, str(len(rows_j)))
        check("jadwal test bln 1 Belum", "Belum" in rows_j[1].inner_text(), rows_j[1].inner_text())
        page.click("#daftarPinjaman [data-bayar='10']")
        page.wait_for_timeout(300)
        rows_j = page.query_selector_all("#tabelJadwal tr")
        check("jadwal test bln 1 Lunas setelah bayar", "Lunas" in rows_j[1].inner_text(), rows_j[1].inner_text())
        check("jadwal test ringkasan 1/3", "1/3" in text(page, "#ringkasanJadwal"), text(page, "#ringkasanJadwal"))
        page.click("#daftarPinjaman [data-lunas='10']")
        page.wait_for_timeout(300)
        tab(page, "dashboard")
        check("dasbor pokok kembali 455jt setelah lunas", "Rp455.000.000" in text(page, "#dPokok"), text(page, "#dPokok"))
        tab(page, "jadwal")
        page.click("#daftarPinjaman [data-batal='10']")
        page.wait_for_timeout(300)
        check("jadwal test kembali aktif 1/3", "1/3" in text(page, "#ringkasanJadwal"), text(page, "#ringkasanJadwal"))
        page.click("#daftarPinjaman [data-hapus='10']")
        page.wait_for_timeout(200)
        page.click("#modalYa")
        page.wait_for_timeout(300)
        check("jadwal kembali 9 pinjaman setelah hapus", len(page.query_selector_all("#daftarPinjaman .baris")) == 9, str(len(page.query_selector_all("#daftarPinjaman .baris"))))

        # ---------- 5. Jadwal Kredit Motor (baca saja) ----------
        page.select_option("#pilihPinjaman", "2")
        page.wait_for_timeout(300)
        check("jadwal motor ringkasan angsuran", "Rp1.129.763" in text(page, "#ringkasanJadwal"), text(page, "#ringkasanJadwal"))
        rows_m = page.query_selector_all("#tabelJadwal tr")
        check("jadwal motor 24 + header", len(rows_m) == 25, str(len(rows_m)))
        check("jadwal motor bln 1 bunga 240rb", "Rp240.000" in rows_m[1].inner_text(), rows_m[1].inner_text())
        check("jadwal motor bln 1 pokok 889.763", "Rp889.763" in rows_m[1].inner_text(), rows_m[1].inner_text())
        check("jadwal motor bln 1 Lunas (bayar 1)", "Lunas" in rows_m[1].inner_text(), rows_m[1].inner_text())
        check("jadwal motor bln 2 Belum", "Belum" in rows_m[2].inner_text(), rows_m[2].inner_text())
        check("jadwal motor bln 24 angsuran 1.129.772", "Rp1.129.772" in rows_m[-1].inner_text(), rows_m[-1].inner_text())
        check("jadwal motor bln 24 sisa Rp0", "Rp0" in rows_m[-1].inner_text(), rows_m[-1].inner_text())
        page.select_option("#pilihPinjaman", "1")
        page.wait_for_timeout(300)
        rows_k = page.query_selector_all("#tabelJadwal tr")
        check("jadwal KPR 120 + header", len(rows_k) == 121, str(len(rows_k)))
        check("jadwal KPR bln 1 bunga 1,8jt", "Rp1.800.000" in rows_k[1].inner_text(), rows_k[1].inner_text())
        check("jadwal KPR bln akhir angsuran 3.040.134", "Rp3.040.134" in rows_k[-1].inner_text(), rows_k[-1].inner_text())

        # ---------- 6. Tab Pelunasan ----------
        tab(page, "pelunasan")
        page.select_option("#pilihLunas", "2")
        page.fill("#lExtra", "500000")
        page.fill("#lLump", "0")
        page.fill("#lLumpBulan", "")
        page.click("#btnHitungLunas")
        page.wait_for_timeout(300)
        check("pelunasan extra tenor 17 bln", "17 bln" in text(page, "#pTenorBaru"), text(page, "#pTenorBaru"))
        check("pelunasan extra hemat 7 bulan", "hemat 7 bulan" in text(page, "#pHematBulan"), text(page, "#pHematBulan"))
        check("pelunasan extra bunga 2,09jt", "Rp2.092.023" in text(page, "#pBungaBaru"), text(page, "#pBungaBaru"))
        check("pelunasan extra hemat bunga 1,02jt", "Rp1.022.298" in text(page, "#pHematBunga"), text(page, "#pHematBunga"))
        page.fill("#lExtra", "0")
        page.fill("#lLump", "5000000")
        page.fill("#lLumpBulan", "6")
        page.click("#btnHitungLunas")
        page.wait_for_timeout(300)
        check("pelunasan lump tenor 19 bln", "19 bln" in text(page, "#pTenorBaru"), text(page, "#pTenorBaru"))
        check("pelunasan lump hemat 5 bulan", "hemat 5 bulan" in text(page, "#pHematBulan"), text(page, "#pHematBulan"))
        check("pelunasan lump bunga 2,25jt", "Rp2.258.267" in text(page, "#pBungaBaru"), text(page, "#pBungaBaru"))
        check("pelunasan lump hemat bunga 856rb", "Rp856.054" in text(page, "#pHematBunga"), text(page, "#pHematBunga"))
        page.fill("#lExtra", "500000")
        page.fill("#lLump", "5000000")
        page.fill("#lLumpBulan", "6")
        page.click("#btnHitungLunas")
        page.wait_for_timeout(300)
        check("pelunasan gabung tenor 13 bln", "13 bln" in text(page, "#pTenorBaru"), text(page, "#pTenorBaru"))
        check("pelunasan gabung hemat 11 bulan", "hemat 11 bulan" in text(page, "#pHematBulan"), text(page, "#pHematBulan"))
        check("pelunasan gabung bunga 1,63jt", "Rp1.634.550" in text(page, "#pBungaBaru"), text(page, "#pBungaBaru"))
        check("pelunasan gabung hemat bunga 1,47jt", "Rp1.479.771" in text(page, "#pHematBunga"), text(page, "#pHematBunga"))
        page.fill("#lExtra", "0")
        page.fill("#lLump", "0")
        page.click("#btnHitungLunas")
        page.wait_for_timeout(300)
        check("pelunasan kosong tampil peringatan", "Isi tambahan bayar" in text(page, "#pPeringatan"), text(page, "#pPeringatan"))

        # ---------- 7. Tab Perbandingan ----------
        tab(page, "perbandingan")
        page.click("#btnBanding")
        page.wait_for_timeout(300)
        check("banding tabel tampil", page.is_visible("#cardHasilBanding"))
        tabel_b = text(page, "#tabelBanding")
        check("banding A angsuran 1.129.763", "Rp1.129.763" in tabel_b, tabel_b)
        check("banding B angsuran 774.412", "Rp774.412" in tabel_b, tabel_b)
        check("banding A total 27,11jt", "Rp27.114.321" in tabel_b, tabel_b)
        check("banding B total 27,87jt", "Rp27.878.852" in tabel_b, tabel_b)
        check("banding verdict A lebih murah 764.531", "Skema A lebih murah" in text(page, "#verdictBanding") and "Rp764.531" in text(page, "#verdictBanding"), text(page, "#verdictBanding"))
        page.fill("#bTenor", "12")
        page.click("#btnBanding")
        page.wait_for_timeout(300)
        check("banding B tenor 12 lebih murah", "Skema B lebih murah" in text(page, "#verdictBanding"), text(page, "#verdictBanding"))
        page.fill("#bTenor", "36")

        # ---------- 8. Tab Pengingat + teks WA ----------
        tab(page, "pengingat")
        check("pengingat 2 item", len(page.query_selector_all("#daftarIngat .baris")) == 2, str(len(page.query_selector_all("#daftarIngat .baris"))))
        check("pengingat ringkasan 2 catatan", "2 pinjaman" in text(page, "#ringkasanIngat"), text(page, "#ringkasanIngat"))
        check("pengingat ringkasan 1 lewat", "1 lewat jatuh tempo" in text(page, "#ringkasanIngat"), text(page, "#ringkasanIngat"))
        page.click("#daftarIngat [data-wa='7']")
        page.wait_for_timeout(300)
        check("kotak pesan tampil", page.is_visible("#cardPesan"))
        pesan = text(page, "#kotakPesan")
        check("teks WA ada Cicilan Laptop", "Cicilan Laptop" in pesan, pesan)
        check("teks WA ada Rp1.066.185", "Rp1.066.185" in pesan, pesan)
        check("teks WA ada jatuh tempo 26/11/2026", "26/11/2026" in pesan, pesan)
        check("teks WA ada sisa 12 angsuran", "Sisa 12 angsuran" in pesan, pesan)
        page.click("#daftarIngat [data-wa='6']")
        page.wait_for_timeout(300)
        pesan2 = text(page, "#kotakPesan")
        check("teks WA Online ada Rp892.629", "Rp892.629" in pesan2, pesan2)
        page.click("#daftarIngat [data-bayar-ingat='7']")
        page.wait_for_timeout(300)
        check("pengingat tinggal 1 setelah bayar Laptop", len(page.query_selector_all("#daftarIngat .baris")) == 1, str(len(page.query_selector_all("#daftarIngat .baris"))))
        tab(page, "dashboard")
        check("dasbor segera 0 setelah bayar Laptop", text(page, "#dSegera") == "0", text(page, "#dSegera"))

        # ---------- 9. Laporan ----------
        tab(page, "laporan")
        check("laporan pokok 459,8jt", "Rp459.800.000" in text(page, "#lPokok"), text(page, "#lPokok"))
        check("laporan pokok sub 9 pinjaman", "9 pinjaman pada periode ini" in text(page, "#lPokokSub"), text(page, "#lPokokSub"))
        check("laporan angsuran 14,45jt", "Rp14.459.164" in text(page, "#lAngsuran"), text(page, "#lAngsuran"))
        check("laporan bunga 153,95jt", "Rp153.957.555" in text(page, "#lBunga"), text(page, "#lBunga"))
        check("laporan total 613,75jt", "Rp613.757.555" in text(page, "#lTotal"), text(page, "#lTotal"))
        prows = page.query_selector_all("#tabelPinjaman tr")
        check("tabel per pinjaman 9 + header", len(prows) == 10, str(len(prows)))
        check("tabel pinjaman ada KPR Rumah", "KPR Rumah" in text(page, "#tabelPinjaman"))
        check("tabel pinjaman ada Cicilan TV", "Cicilan TV" in text(page, "#tabelPinjaman"))
        srows = page.query_selector_all("#tabelStatus tr")
        check("tabel status 2 + header", len(srows) == 3, str(len(srows)))
        check("tabel status aktif 455jt", "Rp455.000.000" in srows[1].inner_text(), srows[1].inner_text())
        check("tabel status lunas 4,8jt", "Rp4.800.000" in srows[2].inner_text(), srows[2].inner_text())
        page.select_option("#fPeriode", "7")
        page.wait_for_timeout(200)
        check("periode 7 hari pokok 6jt", "Rp6.000.000" in text(page, "#lPokok"), text(page, "#lPokok"))
        check("periode 7 hari 1 pinjaman", "1 pinjaman pada periode ini" in text(page, "#lPokokSub"), text(page, "#lPokokSub"))
        page.select_option("#fPeriode", "30")
        page.wait_for_timeout(200)
        check("periode 30 hari pokok 28jt", "Rp28.000.000" in text(page, "#lPokok"), text(page, "#lPokok"))
        check("periode 30 hari 3 pinjaman", "3 pinjaman pada periode ini" in text(page, "#lPokokSub"), text(page, "#lPokokSub"))
        page.select_option("#fPeriode", "semua")
        page.wait_for_timeout(200)

        # ---------- 10. CSV ekspor ----------
        with page.expect_download() as dl_info:
            page.click("#btnCsvLaporan")
        dl = dl_info.value
        csv_path = "/tmp/cicilan-test.csv"
        dl.save_as(csv_path)
        isi_csv = Path(csv_path).read_text(encoding="utf-8")
        baris_csv = [b for b in isi_csv.split("\n") if b.strip()]
        check("CSV header", baris_csv[0].startswith('"Pinjaman","Pengguna"'), baris_csv[0])
        check("CSV 9 data + header", len(baris_csv) == 10, str(len(baris_csv)))
        check("CSV berisi KPR Rumah", "KPR Rumah" in isi_csv)
        check("CSV berisi Cicilan TV", "Cicilan TV" in isi_csv)

        # ---------- 11. Backup JSON ----------
        with page.expect_download() as dl_info:
            page.click("#btnBackup")
        dl = dl_info.value
        bak_path = "/tmp/cicilan-test-backup.json"
        dl.save_as(bak_path)
        data_bak = json.loads(Path(bak_path).read_text(encoding="utf-8"))
        check("backup aplikasi simulasi-cicilan-pelunasan-utang", data_bak.get("aplikasi") == "simulasi-cicilan-pelunasan-utang")
        check("backup pinjaman 9", len(data_bak["state"]["pinjaman"]) == 9, str(len(data_bak["state"]["pinjaman"])))
        check("backup users 2", len(data_bak["users"]) == 2, str(len(data_bak["users"])))

        # ---------- 12. Tambah cepat Kamera + hapus ----------
        tab(page, "dashboard")
        page.fill("#qNama", "Cicilan Kamera")
        page.fill("#qPokok", "3000000")
        page.fill("#qBunga", "0")
        page.fill("#qTenor", "3")
        page.fill("#qMulai", "2026-11-20")
        page.fill("#qCatatan", "Kamera untuk foto produk")
        page.click("#btnTambahCepat")
        page.wait_for_timeout(300)
        check("dasbor pokok 458jt setelah Kamera", "Rp458.000.000" in text(page, "#dPokok"), text(page, "#dPokok"))
        tab(page, "jadwal")
        check("jadwal daftar 10 setelah Kamera", len(page.query_selector_all("#daftarPinjaman .baris")) == 10, str(len(page.query_selector_all("#daftarPinjaman .baris"))))
        page.click("#daftarPinjaman [data-hapus='11']")
        page.wait_for_timeout(200)
        page.click("#modalYa")
        page.wait_for_timeout(300)
        tab(page, "dashboard")
        check("dasbor pokok 455jt setelah hapus Kamera", "Rp455.000.000" in text(page, "#dPokok"), text(page, "#dPokok"))

        # ---------- 13. Peran Pengguna ----------
        logout(page)
        login(page, "pengguna", "pengguna123")
        check("login pengguna berhasil", "Budi Santoso (Pengguna)" in text(page, "#userChip"))
        tab(page, "dashboard")
        check("kartu kelola pengguna tersembunyi", not page.is_visible("#cardPengguna"))
        check("kartu ganti sandi selalu terlihat (pengguna)", page.is_visible("#cardSandiSaya"))
        check("kartu tambah cepat terlihat (pengguna)", page.is_visible("#cardTambahCepat"))
        check("pengguna pokok 47jt", "Rp47.000.000" in text(page, "#dPokok"), text(page, "#dPokok"))
        check("pengguna angsuran 3,71jt", "Rp3.712.682" in text(page, "#dAngsuran"), text(page, "#dAngsuran"))
        check("pengguna segera 0", text(page, "#dSegera") == "0", text(page, "#dSegera"))
        check("pengguna lewat 1", text(page, "#dLewat") == "1", text(page, "#dLewat"))
        check("pengguna total bayar 51,09jt", "Rp51.094.325" in text(page, "#dTotalBayar"), text(page, "#dTotalBayar"))
        check("pengguna badge jadwal 5", text(page, "#badgeJadwal") == "5", text(page, "#badgeJadwal"))
        check("pengguna badge ingat 1", text(page, "#badgeIngat") == "1", text(page, "#badgeIngat"))
        tab(page, "jadwal")
        check("pengguna jadwal 5 baris", len(page.query_selector_all("#daftarPinjaman .baris")) == 5, str(len(page.query_selector_all("#daftarPinjaman .baris"))))
        check("pengguna tidak melihat KPR Rumah", "KPR Rumah" not in text(page, "#daftarPinjaman"))
        tab(page, "pengingat")
        check("pengguna pengingat 1 item", len(page.query_selector_all("#daftarIngat .baris")) == 1, str(len(page.query_selector_all("#daftarIngat .baris"))))

        # ---------- 14. Ganti sandi pengguna round-trip ----------
        tab(page, "dashboard")
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

        # ---------- 15. Admin reset sandi pengguna -> bk123 ----------
        logout(page)
        login(page, "admin", "admin123")
        tab(page, "dashboard")
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

        # ---------- 16. Tambah & hapus pengguna ----------
        login(page, "admin", "admin123")
        tab(page, "dashboard")
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
        tab(page, "dashboard")
        page.click("#daftarPengguna [data-hapus-user='sari']")
        page.wait_for_timeout(200)
        page.click("#modalYa")
        page.wait_for_timeout(300)
        check("pengguna sari dihapus", "Sari Dewi" not in text(page, "#daftarPengguna"))
        logout(page)
        login(page, "sari", "sari123")
        check("login sari gagal setelah dihapus", page.is_visible("#loginError"))

        # ---------- 17. Restore dengan penanda ----------
        data_bak["state"]["pinjaman"].insert(0, {
            "id": 999, "nama": "RESTORE-TEST", "pokok": 123456, "bunga": 0, "tenor": 1,
            "mulai": "2026-11-20", "dibuat": "2026-11-20", "bayar": 0, "lunas": False,
            "pengguna": "admin", "catatan": "penanda pulihkan"
        })
        data_bak["state"]["nextId"] = 1000
        Path("/tmp/cicilan-test-restore.json").write_text(json.dumps(data_bak), encoding="utf-8")
        login(page, "admin", "admin123")
        tab(page, "laporan")
        page.set_input_files("#inputRestore", "/tmp/cicilan-test-restore.json")
        page.wait_for_timeout(500)
        check("restore menampilkan RESTORE-TEST", "RESTORE-TEST" in text(page, "#tabelPinjaman"))
        check("restore tabel 10 + header", len(page.query_selector_all("#tabelPinjaman tr")) == 11, str(len(page.query_selector_all("#tabelPinjaman tr"))))
        tab(page, "jadwal")
        page.click("#daftarPinjaman [data-hapus='999']")
        page.wait_for_timeout(200)
        page.click("#modalYa")
        page.wait_for_timeout(300)
        check("jadwal kembali 9 setelah hapus marker", len(page.query_selector_all("#daftarPinjaman .baris")) == 9, str(len(page.query_selector_all("#daftarPinjaman .baris"))))

        # ---------- 18. Reset data demo ----------
        tab(page, "laporan")
        page.click("#btnResetData")
        page.wait_for_timeout(200)
        page.click("#modalYa")
        page.wait_for_timeout(400)
        tab(page, "dashboard")
        check("reset kembali pokok 455jt", "Rp455.000.000" in text(page, "#dPokok"), text(page, "#dPokok"))
        check("reset kembali angsuran 13,65jt", "Rp13.659.164" in text(page, "#dAngsuran"), text(page, "#dAngsuran"))

        # ---------- 19. Panduan ----------
        tab(page, "panduan")
        panduan = text(page, "#panel-panduan")
        check("panduan ada harga Basic 499rb", "Rp499.000" in panduan)
        check("panduan ada APK +400rb", "Rp400.000" in panduan)
        check("panduan batas jujur localStorage", "localStorage" in panduan)
        check("panduan bukan payment gateway", "bukan payment gateway" in panduan)
        check("panduan tidak mengirim pesan", "tidak mengirim pesan" in panduan)
        check("panduan akun demo", "admin / admin123" in panduan and "pengguna / pengguna123" in panduan)
        check("panduan garansi 30/60/90", "30 hari" in panduan and "90 hari" in panduan)
        check("panduan rumus anuitas", "anuitas" in panduan)
        check("panduan pelunasan dipercepat", "Pelunasan" in panduan)

        # ---------- 20. Console / page error ----------
        check("tanpa console error", len(console_errors) == 0, str(console_errors[:3]))
        check("tanpa pageerror", len(page_errors) == 0, str(page_errors[:3]))

        browser.close()

    print(f"\n{passed} lolos, {len(failures)} gagal")
    if failures:
        print("GAGAL:", failures)
        sys.exit(1)


if __name__ == "__main__":
    main()
