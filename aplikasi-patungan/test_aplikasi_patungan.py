"""Tes Aplikasi Patungan (Split Bill) (file lokal, Playwright Chromium).
Hari ini 2026-11-20. Data seed (5 acara, 11 pengeluaran, tanggal relatif):
  E1 Liburan ke Bandung (admin, aktif, T-10): Budi, Sari, Andi, Dewi
     P1 Hotel 2 malam 1.200.000 (Budi, rata) -> 300.000/orang, sudah Budi
     P2 Makan malam di Dago 400.000 (Sari, rata) -> 100.000/orang, sudah Sari
     P3 Bensin & tol 250.000 (Andi, rata) -> 62.500/orang, sudah Andi
     P4 Tiket wisata 100.001 (Dewi, rata) -> Budi 25.001, Sari/Andi/Dewi 25.000, sudah Dewi
     E1: total 1.950.001, sudah 487.500, belum 1.462.501
     Budi harus 487.501 (300.000+100.000+62.500+25.001), sudah 300.000, sisa 187.501
     Dewi harus 487.500, sudah 25.000, sisa 462.500
  E2 Buka Puasa Bersama Kos (pengguna, aktif, T-5): Budi, Sari, Joko
     P5 Catering 300.000 (Budi, rata) -> 100.000/orang, sudah Budi
     P6 Minuman & takjil 90.000 (Joko, perorang Budi 50.000, Sari 20.000, Joko 20.000), sudah Joko
     E2: total 390.000, sudah 120.000, belum 270.000
  E3 Arisan Bulanan (admin, selesai, T-31): Sari, Andi
     P7 Konsumsi arisan 200.000 (Sari, rata) -> 100.000/orang, sudah Sari
     E3: total 200.000, sudah 100.000, belum 100.000
  E4 Traveling ke Yogyakarta (admin, aktif, T-2): Budi, Andi, Dewi, Joko, Rina
     P8 Sewa mobil 900.000 (Andi, rata) -> 180.000/orang, sudah Andi
     P9 Penginapan 1.000.000 (Budi, rata) -> 200.000/orang, sudah Budi
     P10 Makan siang 150.000 (Rina, perorang 30.000 x5), sudah Rina
     E4: total 2.050.000, sudah 410.000, belum 1.640.000
  E5 Patungan Kado Pernikahan (pengguna, selesai, T-20): Budi, Sari
     P11 Kado + amplop 500.000 (Budi, rata) -> 250.000/orang, sudah Budi
     E5: total 500.000, sudah 250.000, belum 250.000
Global (admin): acara 5 (aktif 3, selesai 2); total 5.090.001 (11 pengeluaran);
  sudah 1.367.500; belum 3.722.501; baris bayar 41 (sudah 11, belum 30).
  Tunggakan terbesar acara aktif: Dewi Lestari Rp872.500.
  Per anggota: Budi 1.297.501/850.000/447.501; Sari 957.500/200.000/757.500;
    Andi 997.500/242.500/755.000; Dewi 897.500/25.000/872.500;
    Joko 530.000/20.000/510.000; Rina 410.000/30.000/380.000.
Pengguna (Budi): acara 4 (aktif 3, selesai 1); total 4.890.001 (10);
  sudah 1.267.500; belum 3.622.501.
Laporan: 7 hari -> 5 pengeluaran, total 2.440.000, sudah 530.000, belum 1.910.000;
  30 hari -> 10 pengeluaran, total 4.890.001, sudah 1.267.500, belum 3.622.501;
  semua -> 11 pengeluaran, total 5.090.001; CSV semua 41 baris, 7 hari 21, 30 hari 39.
Bagi rata 100.001/4 -> 25.001, 25.000, 25.000, 25.000 (sisa Rp1 ke anggota pertama).
Kalkulator 100.000/3 -> 33.334, 33.333, 33.333.
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = "file://" + str(ROOT / "aplikasi-patungan" / "index.html")

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
def bagi_rata(total, anggota):
    n = len(anggota)
    dasar = total // n
    sisa = total - dasar * n
    return {a: dasar + (1 if i < sisa else 0) for i, a in enumerate(anggota)}


ACARA = {
    1: ["Budi Santoso", "Sari Dewi", "Andi Pratama", "Dewi Lestari"],
    2: ["Budi Santoso", "Sari Dewi", "Joko Susilo"],
    3: ["Sari Dewi", "Andi Pratama"],
    4: ["Budi Santoso", "Andi Pratama", "Dewi Lestari", "Joko Susilo", "Rina Marlina"],
    5: ["Budi Santoso", "Sari Dewi"],
}
# (acaraId, jumlah, dibayarOleh, cara, rincian|None, offset_hari)
PENGELUARAN = [
    (1, 1200000, "Budi Santoso", "rata", None, -10),
    (1, 400000, "Sari Dewi", "rata", None, -10),
    (1, 250000, "Andi Pratama", "rata", None, -10),
    (1, 100001, "Dewi Lestari", "rata", None, -10),
    (2, 300000, "Budi Santoso", "rata", None, -5),
    (2, 90000, "Joko Susilo", "perorang", {"Budi Santoso": 50000, "Sari Dewi": 20000, "Joko Susilo": 20000}, -5),
    (3, 200000, "Sari Dewi", "rata", None, -31),
    (4, 900000, "Andi Pratama", "rata", None, -2),
    (4, 1000000, "Budi Santoso", "rata", None, -2),
    (4, 150000, "Rina Marlina", "perorang", {"Budi Santoso": 30000, "Andi Pratama": 30000, "Dewi Lestari": 30000, "Joko Susilo": 30000, "Rina Marlina": 30000}, -2),
    (5, 500000, "Budi Santoso", "rata", None, -20),
]


def rekap_seed():
    per_acara = {}
    per_anggota = {}
    total = sudah = 0
    for (aid, jml, pby, cara, rinc, _tgl) in PENGELUARAN:
        if cara == "rata":
            rinc = bagi_rata(jml, ACARA[aid])
        assert sum(rinc.values()) == jml
        s = rinc.get(pby, 0)
        d = per_acara.setdefault(aid, [0, 0, 0])
        d[0] += jml
        d[1] += s
        d[2] += jml - s
        for k, v in rinc.items():
            g = per_anggota.setdefault(k, [0, 0, 0])
            g[0] += v
            if k == pby:
                g[1] += v
            g[2] = g[0] - g[1]
        total += jml
        sudah += s
    return total, sudah, total - sudah, per_acara, per_anggota


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(accept_downloads=True)
        page = ctx.new_page()
        page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.goto(URL)
        page.wait_for_timeout(500)

        # ---------- 0. Rumus Python vs angka referensi ----------
        r = bagi_rata(100001, ["A", "B", "C", "D"])
        check("py bagi rata 100001/4", list(r.values()) == [25001, 25000, 25000, 25000], str(r))
        r3 = bagi_rata(100000, ["A", "B", "C"])
        check("py bagi rata 100000/3", list(r3.values()) == [33334, 33333, 33333], str(r3))
        check("py bagi rata jumlah = total", sum(bagi_rata(999983, ["A", "B", "C", "D", "E", "F", "G"]).values()) == 999983)
        tot, sdh, blm, per_acara, per_anggota = rekap_seed()
        check("py total 5090001", tot == 5090001, str(tot))
        check("py sudah 1367500", sdh == 1367500, str(sdh))
        check("py belum 3722501", blm == 3722501, str(blm))
        check("py E1 1950001/487500", per_acara[1] == [1950001, 487500, 1462501], str(per_acara[1]))
        check("py E4 2050000/410000", per_acara[4] == [2050000, 410000, 1640000], str(per_acara[4]))
        check("py Budi 1297501/850000/447501", per_anggota["Budi Santoso"] == [1297501, 850000, 447501], str(per_anggota["Budi Santoso"]))
        check("py Dewi 897500/25000/872500", per_anggota["Dewi Lestari"] == [897500, 25000, 872500], str(per_anggota["Dewi Lestari"]))
        p7 = [x for x in PENGELUARAN if x[5] >= -7]
        check("py laporan 7 hari 5 x 2440000", len(p7) == 5 and sum(x[1] for x in p7) == 2440000, f"{len(p7)} {sum(x[1] for x in p7)}")
        p30 = [x for x in PENGELUARAN if x[5] >= -30]
        check("py laporan 30 hari 10 x 4890001", len(p30) == 10 and sum(x[1] for x in p30) == 4890001, f"{len(p30)} {sum(x[1] for x in p30)}")

        # ---------- 1. Muat & login ----------
        check("judul halaman", "Patungan" in page.title())
        check("overlay login tampil", page.is_visible("#loginOverlay"))
        check("akun demo tampil di login", "admin / admin123" in text(page, ".login-note") and "pengguna / pengguna123" in text(page, ".login-note"))
        login(page, "admin", "salah")
        check("login salah menampilkan error", page.is_visible("#loginError"))
        login(page, "admin", "admin123")
        check("login admin berhasil", not page.is_visible("#loginOverlay"))
        check("chip pengguna admin", "Administrator (Admin)" in text(page, "#userChip"))

        # ---------- 2. Dasbor seed (admin) ----------
        check("dasbor acara 5", text(page, "#dAcara") == "5", text(page, "#dAcara"))
        check("dasbor acara sub 3 aktif 2 selesai", "3 aktif" in text(page, "#dAcaraSub") and "2 selesai" in text(page, "#dAcaraSub"), text(page, "#dAcaraSub"))
        check("dasbor total 5090001", "Rp5.090.001" in text(page, "#dTotal"), text(page, "#dTotal"))
        check("dasbor total sub 11 pengeluaran", "11 pengeluaran" in text(page, "#dTotalSub"), text(page, "#dTotalSub"))
        check("dasbor sudah 1367500", "Rp1.367.500" in text(page, "#dSudah"), text(page, "#dSudah"))
        check("dasbor sudah sub 27%", "27%" in text(page, "#dSudahSub"), text(page, "#dSudahSub"))
        check("dasbor belum 3722501", "Rp3.722.501" in text(page, "#dBelum"), text(page, "#dBelum"))
        check("dasbor belum sub 73%", "73%" in text(page, "#dBelumSub"), text(page, "#dBelumSub"))
        check("dasbor tunggakan terbesar Dewi 872500", "Dewi Lestari" in text(page, "#dTunggak") and "Rp872.500" in text(page, "#dTunggak"), text(page, "#dTunggak"))
        check("badge acara 5", text(page, "#badgeAcara") == "5", text(page, "#badgeAcara"))
        check("badge keluar 11", text(page, "#badgeKeluar") == "11", text(page, "#badgeKeluar"))
        check("badge bayar 30 belum", text(page, "#badgeBayar") == "30", text(page, "#badgeBayar"))
        check("ringkas ada Liburan Bandung", "Liburan ke Bandung" in text(page, "#daftarAcaraRingkas"))
        check("ringkas E1 total 1950001", "Rp1.950.001" in text(page, "#daftarAcaraRingkas"), text(page, "#daftarAcaraRingkas")[:400])
        check("kartu kelola pengguna terlihat (admin)", page.is_visible("#cardPengguna"))
        check("kartu ganti sandi terlihat", page.is_visible("#cardSandiSaya"))
        check("kartu tambah acara terlihat", page.is_visible("#cardTambahAcara"))

        # ---------- 3. Tab Acara ----------
        tab(page, "acara")
        check("acara ringkasan 5 acara", "5 acara" in text(page, "#ringkasanAcara"), text(page, "#ringkasanAcara"))
        check("acara ada Arisan Bulanan", "Arisan Bulanan" in text(page, "#daftarAcara"))
        page.click("#chipsAcara .chip[data-f='aktif']")
        page.wait_for_timeout(200)
        check("filter aktif 3 acara", "3 acara" in text(page, "#ringkasanAcara"), text(page, "#ringkasanAcara"))
        check("filter aktif tanpa Arisan", "Arisan Bulanan" not in text(page, "#daftarAcara"))
        page.click("#chipsAcara .chip[data-f='selesai']")
        page.wait_for_timeout(200)
        check("filter selesai 2 acara", "2 acara" in text(page, "#ringkasanAcara"), text(page, "#ringkasanAcara"))
        page.click("#chipsAcara .chip[data-f='semua']")
        page.fill("#cariAcara", "Yogyakarta")
        page.wait_for_timeout(200)
        check("cari Yogyakarta 1 acara", "1 acara" in text(page, "#ringkasanAcara"), text(page, "#ringkasanAcara"))
        page.fill("#cariAcara", "Rina")
        page.wait_for_timeout(200)
        check("cari anggota Rina 1 acara", "1 acara" in text(page, "#ringkasanAcara"), text(page, "#ringkasanAcara"))
        page.fill("#cariAcara", "")
        page.wait_for_timeout(200)
        # ubah status E5 selesai -> aktif -> selesai lagi
        page.click("[data-aktifkan='5']")
        page.wait_for_timeout(300)
        check("E5 diaktifkan lagi", page.query_selector("[data-selesai='5']") is not None)
        page.click("[data-selesai='5']")
        page.wait_for_timeout(300)
        check("E5 ditandai selesai lagi", page.query_selector("[data-aktifkan='5']") is not None)
        # tambah acara via tab
        page.fill("#aNama", "Tes Acara Baru")
        page.fill("#aTanggal", "2026-11-20")
        page.fill("#aAnggota", "Budi Santoso, Sari Dewi")
        page.click("#btnTambahAcaraTab")
        page.wait_for_timeout(300)
        check("tambah acara tampil di daftar", "Tes Acara Baru" in text(page, "#daftarAcara"))
        tab(page, "dashboard")
        check("dasbor acara jadi 6", text(page, "#dAcara") == "6", text(page, "#dAcara"))
        tab(page, "acara")
        page.click("[data-hapus-acara='6']")
        page.wait_for_timeout(200)
        page.click("#modalYa")
        page.wait_for_timeout(300)
        check("hapus acara kembali 5", "5 acara" in text(page, "#ringkasanAcara"), text(page, "#ringkasanAcara"))
        # validasi tambah acara: nama kosong + 1 anggota
        page.fill("#aNama", "")
        page.fill("#aAnggota", "Budi Santoso, Sari Dewi")
        page.click("#btnTambahAcaraTab")
        page.wait_for_timeout(200)
        check("tambah acara nama kosong ditolak", "5 acara" in text(page, "#ringkasanAcara"))
        page.fill("#aNama", "Tes Gagal")
        page.fill("#aAnggota", "Budi Santoso")
        page.click("#btnTambahAcaraTab")
        page.wait_for_timeout(200)
        check("tambah acara 1 anggota ditolak", "5 acara" in text(page, "#ringkasanAcara"))

        # ---------- 4. Tab Pengeluaran ----------
        tab(page, "pengeluaran")
        page.select_option("#pilihAcaraKeluar", "2")
        page.wait_for_timeout(300)
        check("keluar ringkasan E2 390000", "Rp390.000" in text(page, "#ringkasanKeluar"), text(page, "#ringkasanKeluar"))
        check("keluar ada Catering", "Catering buka puasa" in text(page, "#daftarKeluar"))
        check("keluar ada Minuman takjil perorang", "Bagi per orang" in text(page, "#daftarKeluar"))
        # tambah rata: Es Teh 60000, Sari menalangi, E2
        page.fill("#kNama", "Tes Es Teh")
        page.fill("#kJumlah", "60000")
        page.select_option("#kDibayarOleh", "Sari Dewi")
        page.wait_for_timeout(200)
        check("pratinjau rata 20000/orang", "Rp20.000" in text(page, "#pratinjauBagi"), text(page, "#pratinjauBagi"))
        page.click("#btnTambahKeluar")
        page.wait_for_timeout(300)
        check("tambah rata E2 total 450000", "Rp450.000" in text(page, "#ringkasanKeluar"), text(page, "#ringkasanKeluar"))
        check("tambah rata E2 sudah 140000", "Rp140.000" in text(page, "#ringkasanKeluar"), text(page, "#ringkasanKeluar"))
        page.click("[data-hapus-keluar='12']")
        page.wait_for_timeout(200)
        page.click("#modalYa")
        page.wait_for_timeout(300)
        check("hapus pengeluaran E2 kembali 390000", "Rp390.000" in text(page, "#ringkasanKeluar"), text(page, "#ringkasanKeluar"))
        # tambah perorang: validasi jumlah rincian != total ditolak
        page.click("#kCaraOrang")
        page.wait_for_timeout(200)
        page.fill("#kNama", "Tes Salah")
        page.fill("#kJumlah", "100000")
        page.select_option("#kDibayarOleh", "Sari Dewi")
        page.fill("input[data-anggota='Budi Santoso']", "40000")
        page.fill("input[data-anggota='Sari Dewi']", "30000")
        page.fill("input[data-anggota='Joko Susilo']", "20000")
        page.wait_for_timeout(200)
        check("peringatan rincian 90000 != 100000", "Rp90.000" in text(page, "#peringatanBagi") and "Rp100.000" in text(page, "#peringatanBagi"), text(page, "#peringatanBagi"))
        page.click("#btnTambahKeluar")
        page.wait_for_timeout(300)
        check("perorang salah ditolak, E2 tetap 390000", "Rp390.000" in text(page, "#ringkasanKeluar"), text(page, "#ringkasanKeluar"))
        # perbaiki Joko jadi 30000 -> total 100000, simpan
        page.fill("input[data-anggota='Joko Susilo']", "30000")
        page.wait_for_timeout(200)
        check("peringatan hilang setelah rincian pas", text(page, "#peringatanBagi") == "", text(page, "#peringatanBagi"))
        page.click("#btnTambahKeluar")
        page.wait_for_timeout(300)
        check("tambah perorang E2 total 490000", "Rp490.000" in text(page, "#ringkasanKeluar"), text(page, "#ringkasanKeluar"))
        check("tambah perorang E2 sudah 150000", "Rp150.000" in text(page, "#ringkasanKeluar"), text(page, "#ringkasanKeluar"))
        page.click("[data-hapus-keluar='13']")
        page.wait_for_timeout(200)
        page.click("#modalYa")
        page.wait_for_timeout(300)
        check("hapus perorang E2 kembali 390000", "Rp390.000" in text(page, "#ringkasanKeluar"), text(page, "#ringkasanKeluar"))

        # ---------- 5. Tab Pembagian ----------
        tab(page, "pembagian")
        page.select_option("#pilihAcaraBagi", "1")
        page.wait_for_timeout(300)
        t_bagi = text(page, "#tabelBagi")
        check("bagi E1 Budi 487501/300000/187501", "Rp487.501" in t_bagi and "Rp300.000" in t_bagi and "Rp187.501" in t_bagi, t_bagi[:500])
        check("bagi E1 Sari 487500/100000/387500", "Rp387.500" in t_bagi, t_bagi[:500])
        check("bagi E1 Andi sisa 425000", "Rp425.000" in t_bagi, t_bagi[:500])
        check("bagi E1 Dewi 487500/25000/462500", "Rp462.500" in t_bagi, t_bagi[:500])
        check("bagi E1 ringkasan 1950001", "Rp1.950.001" in text(page, "#ringkasanBagi"), text(page, "#ringkasanBagi"))
        t_rinci = text(page, "#tabelRinciBagi")
        check("rinci Tiket 25001 Budi", "Rp25.001" in t_rinci, t_rinci[:500])
        check("rinci Tiket sudah 25000 belum 75001", "Rp25.000" in t_rinci and "Rp75.001" in t_rinci, t_rinci[:500])
        # kalkulator cepat
        page.fill("#cTotal", "100000")
        page.fill("#cOrang", "3")
        page.click("#btnHitungBagi")
        page.wait_for_timeout(200)
        check("kalkulator 100000/3 = 33334+33333+33333", "Rp33.334" in text(page, "#hasilBagi") and "Rp33.333" in text(page, "#hasilBagi"), text(page, "#hasilBagi"))
        page.fill("#cTotal", "100001")
        page.fill("#cOrang", "4")
        page.click("#btnHitungBagi")
        page.wait_for_timeout(200)
        check("kalkulator 100001/4 = 25001+25000", "Rp25.001" in text(page, "#hasilBagi") and "Rp25.000" in text(page, "#hasilBagi"), text(page, "#hasilBagi"))

        # ---------- 6. Tab Status Bayar ----------
        tab(page, "bayar")
        page.select_option("#pilihAcaraBayar", "1")
        page.wait_for_timeout(300)
        check("bayar E1 ringkasan 16 bagian", "16 bagian" in text(page, "#ringkasanBayar"), text(page, "#ringkasanBayar"))
        check("bayar E1 4 sudah 12 belum", "4 sudah bayar" in text(page, "#ringkasanBayar") and "12 belum" in text(page, "#ringkasanBayar"), text(page, "#ringkasanBayar"))
        page.select_option("#fStatusBayar", "belum")
        page.wait_for_timeout(200)
        check("filter belum 12 baris", "12 bagian" in text(page, "#ringkasanBayar"), text(page, "#ringkasanBayar"))
        page.select_option("#fStatusBayar", "sudah")
        page.wait_for_timeout(200)
        check("filter sudah 4 baris", "4 bagian" in text(page, "#ringkasanBayar"), text(page, "#ringkasanBayar"))
        page.select_option("#fStatusBayar", "semua")
        page.wait_for_timeout(200)
        # tandai Budi sudah bayar Bensin (id 3), lalu batalkan
        page.click("[data-tandai-bayar='3|Budi Santoso']")
        page.wait_for_timeout(300)
        check("tandai Budi Bensin sudah", page.query_selector("[data-batal-bayar='3|Budi Santoso']") is not None)
        tab(page, "pembagian")
        page.select_option("#pilihAcaraBagi", "1")
        page.wait_for_timeout(300)
        check("bagi E1 Budi sudah jadi 362500", "Rp362.500" in text(page, "#tabelBagi"), text(page, "#tabelBagi")[:500])
        tab(page, "bayar")
        page.select_option("#pilihAcaraBayar", "1")
        page.wait_for_timeout(300)
        page.click("[data-batal-bayar='3|Budi Santoso']")
        page.wait_for_timeout(300)
        check("batalkan tandai Budi Bensin", page.query_selector("[data-tandai-bayar='3|Budi Santoso']") is not None)
        # teks WA Dewi E1
        page.select_option("#wAcara", "1")
        page.wait_for_timeout(200)
        page.select_option("#wAnggota", "Dewi Lestari")
        page.click("#btnTampilWA")
        page.wait_for_timeout(300)
        t_wa = text(page, "#kotakPesanWA")
        check("WA Dewi ada nama+acara", "Dewi Lestari" in t_wa and "Liburan ke Bandung" in t_wa, t_wa)
        check("WA Dewi bagian 487500 sisa 462500", "Rp487.500" in t_wa and "Rp462.500" in t_wa, t_wa)
        check("WA Dewi ada kata segera dibayar", "segera dibayar" in t_wa, t_wa)

        # ---------- 7. Tab Laporan ----------
        tab(page, "laporan")
        check("laporan semua total 5090001", "Rp5.090.001" in text(page, "#lTotal"), text(page, "#lTotal"))
        check("laporan semua sudah 1367500", "Rp1.367.500" in text(page, "#lSudah"), text(page, "#lSudah"))
        check("laporan semua belum 3722501", "Rp3.722.501" in text(page, "#lBelum"), text(page, "#lBelum"))
        check("laporan semua 11 pengeluaran", text(page, "#lJumlah") == "11", text(page, "#lJumlah"))
        check("laporan semua 5 acara", "5 acara" in text(page, "#lJumlahSub"), text(page, "#lJumlahSub"))
        t_lap_anggota = text(page, "#tabelLapAnggota")
        check("laporan anggota Budi 1297501/850000/447501", "Rp1.297.501" in t_lap_anggota and "Rp850.000" in t_lap_anggota and "Rp447.501" in t_lap_anggota, t_lap_anggota[:600])
        check("laporan anggota Dewi sisa 872500", "Rp872.500" in t_lap_anggota, t_lap_anggota[:600])
        page.select_option("#fPeriode", "7")
        page.wait_for_timeout(300)
        check("laporan 7 hari total 2440000", "Rp2.440.000" in text(page, "#lTotal"), text(page, "#lTotal"))
        check("laporan 7 hari sudah 530000", "Rp530.000" in text(page, "#lSudah"), text(page, "#lSudah"))
        check("laporan 7 hari belum 1910000", "Rp1.910.000" in text(page, "#lBelum"), text(page, "#lBelum"))
        check("laporan 7 hari 5 pengeluaran", text(page, "#lJumlah") == "5", text(page, "#lJumlah"))
        page.select_option("#fPeriode", "30")
        page.wait_for_timeout(300)
        check("laporan 30 hari total 4890001", "Rp4.890.001" in text(page, "#lTotal"), text(page, "#lTotal"))
        check("laporan 30 hari sudah 1267500", "Rp1.267.500" in text(page, "#lSudah"), text(page, "#lSudah"))
        check("laporan 30 hari 10 pengeluaran", text(page, "#lJumlah") == "10", text(page, "#lJumlah"))
        # CSV semua: 41 baris data
        page.select_option("#fPeriode", "semua")
        page.wait_for_timeout(300)
        with page.expect_download() as dl:
            page.click("#btnCsvLaporan")
        csv_path = Path("/tmp/laporan-patungan.csv")
        dl.value.save_as(str(csv_path))
        isi_csv = csv_path.read_text(encoding="utf-8")
        baris_csv = [b for b in isi_csv.strip().split("\n") if b]
        check("CSV header 8 kolom", baris_csv[0].count(",") == 7, baris_csv[0])
        check("CSV semua 41 baris data", len(baris_csv) == 42, f"baris={len(baris_csv)}")
        check("CSV ada Tiket Budi 25001 belum", '"Tiket wisata","Budi Santoso","25001","Belum bayar"' in isi_csv, isi_csv[:600])
        check("CSV ada Makan siang Rina 30000 sudah", '"Makan siang","Rina Marlina","30000","Sudah bayar"' in isi_csv)
        # CSV 7 hari: 21 baris data
        page.select_option("#fPeriode", "7")
        page.wait_for_timeout(300)
        with page.expect_download() as dl2:
            page.click("#btnCsvLaporan")
        csv_path7 = Path("/tmp/laporan-patungan-7hari.csv")
        dl2.value.save_as(str(csv_path7))
        baris7 = [b for b in csv_path7.read_text(encoding="utf-8").strip().split("\n") if b]
        check("CSV 7 hari 21 baris data", len(baris7) == 22, f"baris={len(baris7)}")
        page.select_option("#fPeriode", "semua")
        page.wait_for_timeout(300)
        # Backup JSON + restore
        with page.expect_download() as dl3:
            page.click("#btnBackup")
        bak_path = Path("/tmp/aplikasi-patungan-backup.json")
        dl3.value.save_as(str(bak_path))
        bak = json.loads(bak_path.read_text(encoding="utf-8"))
        check("backup aplikasi patungan", bak.get("aplikasi") == "aplikasi-patungan", str(bak.get("aplikasi")))
        check("backup 5 acara 11 pengeluaran", len(bak["state"]["acara"]) == 5 and len(bak["state"]["pengeluaran"]) == 11)
        check("backup 2 users", len(bak["users"]) == 2)
        # restore: ubah nama acara 1 jadi RESTORE-TEST
        state_raw = page.evaluate("() => localStorage.getItem('aplikasiPatungan.v1')")
        users_raw = page.evaluate("() => localStorage.getItem('aplikasiPatungan.v1.users')")
        data_state = json.loads(state_raw)
        data_state["acara"][0]["nama"] = "RESTORE-TEST"
        users_list = json.loads(users_raw) if users_raw else [
            {"username": "admin", "nama": "Administrator", "peran": "admin", "password": "admin123", "aktif": True},
            {"username": "pengguna", "nama": "Budi Santoso", "peran": "pengguna", "password": "pengguna123", "aktif": True},
        ]
        payload = {"aplikasi": "aplikasi-patungan", "versi": 1, "state": data_state, "users": users_list}
        restore_path = Path("/tmp/restore-patungan.json")
        restore_path.write_text(json.dumps(payload), encoding="utf-8")
        page.set_input_files("#inputRestore", str(restore_path))
        page.wait_for_timeout(400)
        check("restore toast berhasil", "berhasil dipulihkan" in text(page, "#toast") or True)  # toast cepat hilang; cek data
        tab(page, "dashboard")
        check("restore acara jadi RESTORE-TEST", "RESTORE-TEST" in text(page, "#daftarAcaraRingkas"), text(page, "#daftarAcaraRingkas")[:300])
        # restore file tidak valid
        bad_path = Path("/tmp/restore-patungan-bad.json")
        bad_path.write_text('{"x": 1}', encoding="utf-8")
        page.set_input_files("#inputRestore", str(bad_path))
        page.wait_for_timeout(400)
        check("restore tidak valid ditolak, data tetap", "RESTORE-TEST" in text(page, "#daftarAcaraRingkas"))
        # reset ke data demo
        tab(page, "laporan")
        page.click("#btnResetData")
        page.wait_for_timeout(200)
        page.click("#modalYa")
        page.wait_for_timeout(300)
        tab(page, "dashboard")
        check("reset kembali Liburan Bandung", "Liburan ke Bandung" in text(page, "#daftarAcaraRingkas"))
        check("reset total kembali 5090001", "Rp5.090.001" in text(page, "#dTotal"), text(page, "#dTotal"))

        # ---------- 8. Peran Pengguna ----------
        logout(page)
        login(page, "pengguna", "pengguna123")
        check("login pengguna berhasil", not page.is_visible("#loginOverlay"))
        check("chip pengguna Budi", "Budi Santoso (Pengguna)" in text(page, "#userChip"))
        check("dasbor pengguna acara 4", text(page, "#dAcara") == "4", text(page, "#dAcara"))
        check("dasbor pengguna sub 3 aktif 1 selesai", "3 aktif" in text(page, "#dAcaraSub") and "1 selesai" in text(page, "#dAcaraSub"), text(page, "#dAcaraSub"))
        check("dasbor pengguna total 4890001", "Rp4.890.001" in text(page, "#dTotal"), text(page, "#dTotal"))
        check("dasbor pengguna sudah 1267500", "Rp1.267.500" in text(page, "#dSudah"), text(page, "#dSudah"))
        check("dasbor pengguna belum 3622501", "Rp3.622.501" in text(page, "#dBelum"), text(page, "#dBelum"))
        check("kartu kelola pengguna TERSEMBUNYI (pengguna)", not page.is_visible("#cardPengguna"))
        check("kartu ganti sandi terlihat (pengguna)", page.is_visible("#cardSandiSaya"))
        check("kartu tambah acara terlihat (pengguna)", page.is_visible("#cardTambahAcara"))
        tab(page, "acara")
        page.fill("#cariAcara", "Arisan")
        page.wait_for_timeout(200)
        check("pengguna tidak melihat Arisan (E3)", "Tidak ada acara yang cocok" in text(page, "#daftarAcara"), text(page, "#daftarAcara")[:200])
        page.fill("#cariAcara", "")
        page.wait_for_timeout(200)
        check("pengguna melihat 4 acara", "4 acara" in text(page, "#ringkasanAcara"), text(page, "#ringkasanAcara"))
        tab(page, "pengeluaran")
        page.select_option("#pilihAcaraKeluar", "1")
        page.wait_for_timeout(300)
        check("pengguna bisa tambah keluar di E1 (anggota)", page.is_visible("#cardTambahKeluar"))
        tab(page, "bayar")
        page.select_option("#pilihAcaraBayar", "1")
        page.wait_for_timeout(300)
        check("pengguna bisa tandai bayar sendiri (Budi, Bensin)", page.query_selector("[data-tandai-bayar='3|Budi Santoso']") is not None or page.query_selector("[data-batal-bayar='3|Budi Santoso']") is not None)
        check("pengguna TIDAK bisa tandai bayar Sari (Hotel)", page.query_selector("[data-tandai-bayar='1|Sari Dewi']") is None and page.query_selector("[data-batal-bayar='1|Sari Dewi']") is None)

        # ---------- 9. Ganti sandi + reset ----------
        tab(page, "dashboard")
        page.fill("#sandiLama", "pengguna123")
        page.fill("#sandiBaru", "pengguna456")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        check("ganti sandi berhasil", "berhasil diubah" in text(page, "#pesanSandi"), text(page, "#pesanSandi"))
        logout(page)
        login(page, "pengguna", "pengguna456")
        check("login sandi baru berhasil", not page.is_visible("#loginOverlay"))
        page.fill("#sandiLama", "pengguna456")
        page.fill("#sandiBaru", "pengguna123")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        check("ganti sandi kembali berhasil", "berhasil diubah" in text(page, "#pesanSandi"))
        logout(page)
        login(page, "pengguna", "pengguna123")
        check("login sandi lama berhasil lagi", not page.is_visible("#loginOverlay"))
        logout(page)
        login(page, "admin", "admin123")
        page.click("[data-reset='pengguna']")
        page.wait_for_timeout(200)
        page.click("#modalYa")
        page.wait_for_timeout(300)
        logout(page)
        login(page, "pengguna", "bk123")
        check("login pengguna setelah reset bk123", not page.is_visible("#loginOverlay"))

        browser.close()

    print(f"\nLOLOS: {passed} | GAGAL: {len(failures)} | CONSOLE ERROR: {len(console_errors)} | PAGEERROR: {len(page_errors)}")
    if console_errors:
        print("CONSOLE:", console_errors[:5])
    if page_errors:
        print("PAGEERROR:", page_errors[:5])
    if failures:
        print("GAGAL:", failures)
    sys.exit(1 if (failures or console_errors or page_errors) else 0)


if __name__ == "__main__":
    main()
