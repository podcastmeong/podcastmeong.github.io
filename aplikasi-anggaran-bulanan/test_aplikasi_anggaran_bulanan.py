"""Tes Aplikasi Anggaran Bulanan (file lokal, Playwright Chromium).
Hari ini 2026-11-20. Data seed (tanggal relatif):
  Kategori (8): Makan, Transport, Hiburan, Belanja, Tagihan, Kesehatan, Pendidikan, Lainnya
  Anggaran November 2026 (total 5.500.000; Hiburan + Lainnya milik admin, sisanya pengguna):
    Makan 1.500.000, Transport 600.000, Hiburan 300.000, Belanja 800.000,
    Tagihan 1.200.000, Kesehatan 400.000, Pendidikan 500.000, Lainnya 200.000
  Anggaran Oktober 2026 (total 4.950.000; semua milik pengguna):
    Makan 1.400.000, Transport 500.000, Hiburan 250.000, Belanja 700.000,
    Tagihan 1.100.000, Kesehatan 350.000, Pendidikan 500.000, Lainnya 150.000
  Realisasi November 2026 (17 pengeluaran, total 4.230.000):
    Makan 1.350.000 (450+300+250+350); Transport 480.000 (300+120+60);
    Hiburan 350.000 (150+120 admin+80); Belanja 500.000 (350+150);
    Tagihan 1.150.000 (450+500+200); Kesehatan 150.000; Pendidikan 0;
    Lainnya 250.000 (admin)
  Realisasi Oktober 2026 (8 pengeluaran, total 4.450.000):
    Makan 1.300.000, Transport 450.000, Hiburan 200.000, Belanja 650.000,
    Tagihan 1.050.000, Kesehatan 300.000, Pendidikan 400.000, Lainnya 100.000
  Admin Nov: anggaran 5.500.000, realisasi 4.230.000, sisa 1.270.000, 76,9%;
    peringatan 5 (Makan 90%, Transport 80%, Hiburan 116,7%, Tagihan 95,8%, Lainnya 125%),
    lewat batas 2 (Hiburan, Lainnya).
  Pengguna Nov: anggaran 5.000.000, realisasi 3.860.000, sisa 1.140.000, 77,2%;
    peringatan 3 (Makan, Transport, Tagihan); Hiburan tanpa anggaran (realisasi 230.000).
  Oktober: anggaran 4.950.000, realisasi 4.450.000, sisa 500.000, 89,9%;
    peringatan 7 (semua kecuali Lainnya 66,7%), lewat batas 0.
  Salin bulan lalu (pengguna, Okt -> Nov): 2 disalin (Hiburan 250.000, Lainnya 150.000),
    6 sudah ada; anggaran pengguna jadi 5.400.000; peringatan jadi 4 (Hiburan 92%).
  Status: Aman <80%; Hampir habis 80-100%; Lewat batas >100%.
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = "file://" + str(ROOT / "aplikasi-anggaran-bulanan" / "index.html")

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
KATEGORI = ["Makan", "Transport", "Hiburan", "Belanja", "Tagihan", "Kesehatan", "Pendidikan", "Lainnya"]
ANGGARAN_NOV = {"Makan": 1500000, "Transport": 600000, "Hiburan": 300000, "Belanja": 800000,
                "Tagihan": 1200000, "Kesehatan": 400000, "Pendidikan": 500000, "Lainnya": 200000}
ANGGARAN_OKT = {"Makan": 1400000, "Transport": 500000, "Hiburan": 250000, "Belanja": 700000,
                "Tagihan": 1100000, "Kesehatan": 350000, "Pendidikan": 500000, "Lainnya": 150000}
REALISASI_NOV = {"Makan": 1350000, "Transport": 480000, "Hiburan": 350000, "Belanja": 500000,
                 "Tagihan": 1150000, "Kesehatan": 150000, "Pendidikan": 0, "Lainnya": 250000}
REALISASI_OKT = {"Makan": 1300000, "Transport": 450000, "Hiburan": 200000, "Belanja": 650000,
                 "Tagihan": 1050000, "Kesehatan": 300000, "Pendidikan": 400000, "Lainnya": 100000}
PEMILIK_ADMIN_NOV = {"Hiburan": 120000, "Lainnya": 250000}  # realisasi admin di Nov


def status(anggaran, realisasi):
    if anggaran <= 0:
        return "tanpa" if realisasi > 0 else "aman"
    p = realisasi / anggaran * 100
    return "lewat" if p > 100 else "peringatan" if p >= 80 else "aman"


def rekap(anggaran, realisasi):
    tot_a = sum(anggaran.values())
    tot_r = sum(realisasi.values())
    per = {k: (realisasi[k] / anggaran[k] * 100 if anggaran[k] > 0 else None) for k in KATEGORI}
    peringatan = [k for k in KATEGORI if status(anggaran[k], realisasi[k]) in ("peringatan", "lewat")]
    lewat = [k for k in KATEGORI if status(anggaran[k], realisasi[k]) == "lewat"]
    return tot_a, tot_r, tot_a - tot_r, per, peringatan, lewat


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
        ta, tr, sisa, per, pr, lw = rekap(ANGGARAN_NOV, REALISASI_NOV)
        check("py Nov 5500000/4230000/1270000", (ta, tr, sisa) == (5500000, 4230000, 1270000), f"{ta} {tr} {sisa}")
        check("py Nov persen 76,9", abs(tr / ta * 100 - 76.909) < 0.01, str(tr / ta * 100))
        check("py Nov peringatan 5 lewat 2", len(pr) == 5 and len(lw) == 2, f"{pr} {lw}")
        check("py Nov Makan 90 Transport 80", abs(per["Makan"] - 90) < 0.01 and abs(per["Transport"] - 80) < 0.01, str(per))
        check("py Nov Hiburan 116,7 Lainnya 125", abs(per["Hiburan"] - 116.667) < 0.01 and abs(per["Lainnya"] - 125) < 0.01, str(per))
        ta_o, tr_o, sisa_o, per_o, pr_o, lw_o = rekap(ANGGARAN_OKT, REALISASI_OKT)
        check("py Okt 4950000/4450000/500000", (ta_o, tr_o, sisa_o) == (4950000, 4450000, 500000), f"{ta_o} {tr_o} {sisa_o}")
        check("py Okt persen 89,9 peringatan 7 lewat 0", abs(tr_o / ta_o * 100 - 89.899) < 0.01 and len(pr_o) == 7 and len(lw_o) == 0, f"{tr_o/ta_o*100} {pr_o}")
        # pengguna Nov = admin Nov minus entri admin (anggaran Hiburan+Lainnya, realisasi streaming+kado)
        ang_p = {k: (0 if k in ("Hiburan", "Lainnya") else ANGGARAN_NOV[k]) for k in KATEGORI}
        rea_p = {k: (REALISASI_NOV[k] - PEMILIK_ADMIN_NOV.get(k, 0)) for k in KATEGORI}
        ta_p, tr_p, sisa_p, per_p, pr_p, lw_p = rekap(ang_p, rea_p)
        check("py pengguna Nov 5000000/3860000/1140000", (ta_p, tr_p, sisa_p) == (5000000, 3860000, 1140000), f"{ta_p} {tr_p} {sisa_p}")
        check("py pengguna persen 77,2 peringatan 3", abs(tr_p / ta_p * 100 - 77.2) < 0.01 and len(pr_p) == 3, f"{tr_p/ta_p*100} {pr_p}")
        check("py pengguna Hiburan tanpa anggaran", status(ang_p["Hiburan"], rea_p["Hiburan"]) == "tanpa" and rea_p["Hiburan"] == 230000, str(rea_p["Hiburan"]))
        # salin Okt -> Nov (pengguna): Hiburan 250000 + Lainnya 150000
        ang_p2 = dict(ang_p)
        ang_p2["Hiburan"] = ANGGARAN_OKT["Hiburan"]
        ang_p2["Lainnya"] = ANGGARAN_OKT["Lainnya"]
        ta2, tr2, sisa2, per2, pr2, lw2 = rekap(ang_p2, rea_p)
        check("py salin pengguna 5400000 peringatan 4", ta2 == 5400000 and len(pr2) == 4, f"{ta2} {pr2}")
        check("py salin Hiburan 92%", abs(per2["Hiburan"] - 92) < 0.01, str(per2["Hiburan"]))

        # ---------- 1. Muat & login ----------
        check("judul halaman", "Anggaran Bulanan" in page.title())
        check("overlay login tampil", page.is_visible("#loginOverlay"))
        check("akun demo tampil di login", "admin / admin123" in text(page, ".login-note") and "pengguna / pengguna123" in text(page, ".login-note"))
        login(page, "admin", "salah")
        check("login salah menampilkan error", page.is_visible("#loginError"))
        login(page, "admin", "admin123")
        check("login admin berhasil", not page.is_visible("#loginOverlay"))
        check("chip pengguna admin", "Administrator (Admin)" in text(page, "#userChip"))

        # ---------- 2. Dasbor seed (admin) ----------
        check("dasbor judul November 2026", "November 2026" in text(page, "#dJudulBulan"), text(page, "#dJudulBulan"))
        check("dasbor anggaran 5500000", "Rp5.500.000" in text(page, "#dAnggaran"), text(page, "#dAnggaran"))
        check("dasbor anggaran sub 8 kategori", "8 kategori beranggaran" in text(page, "#dAnggaranSub"), text(page, "#dAnggaranSub"))
        check("dasbor realisasi 4230000", "Rp4.230.000" in text(page, "#dRealisasi"), text(page, "#dRealisasi"))
        check("dasbor realisasi sub 17 pengeluaran", "17 pengeluaran" in text(page, "#dRealisasiSub"), text(page, "#dRealisasiSub"))
        check("dasbor sisa 1270000", "Rp1.270.000" in text(page, "#dSisa"), text(page, "#dSisa"))
        check("dasbor persen 76,9%", "76,9%" in text(page, "#dPersen"), text(page, "#dPersen"))
        check("dasbor peringatan 5 kategori 2 lewat", "5 kategori" in text(page, "#dPeringatan") and "2 lewat batas" in text(page, "#dPeringatan"), text(page, "#dPeringatan"))
        check("dasbor top Lainnya 125%", "Lainnya" in text(page, "#dTopKategori") and "125%" in text(page, "#dTopKategori"), text(page, "#dTopKategori"))
        check("dasbor terbaru ada Top up game", "Top up game" in text(page, "#daftarRealisasiTerbaru"), text(page, "#daftarRealisasiTerbaru")[:300])
        check("badge kategori 8", text(page, "#badgeKategori") == "8", text(page, "#badgeKategori"))
        check("badge realisasi 17", text(page, "#badgeRealisasi") == "17", text(page, "#badgeRealisasi"))
        check("badge peringatan 5", text(page, "#badgePeringatan") == "5", text(page, "#badgePeringatan"))
        check("kartu kelola pengguna terlihat (admin)", page.is_visible("#cardPengguna"))
        check("kartu ganti sandi terlihat", page.is_visible("#cardSandiSaya"))
        check("kartu catat cepat terlihat", page.is_visible("#cardTambahCepat"))

        # ---------- 3. Tab Anggaran ----------
        tab(page, "anggaran")
        check("anggaran ringkasan 8 kategori 5500000", "8 kategori" in text(page, "#ringkasanAnggaran") and "Rp5.500.000" in text(page, "#ringkasanAnggaran"), text(page, "#ringkasanAnggaran"))
        t_ang = text(page, "#tabelAnggaran")
        check("anggaran Makan 90%", "Makan" in t_ang and "90%" in t_ang, t_ang[:500])
        check("anggaran Hiburan 116,7%", "116,7%" in t_ang, t_ang[:500])
        check("anggaran Lainnya 125%", "125%" in t_ang, t_ang[:500])
        check("anggaran Pendidikan 0%", "Pendidikan" in t_ang and "0%" in t_ang, t_ang[:500])
        check("anggaran Transport 80% sisa 120000", "80%" in t_ang and "Rp120.000" in t_ang, t_ang[:800])
        # salin bulan lalu (admin): Nov sudah lengkap -> 0 disalin
        page.click("#btnSalinBulanLalu")
        page.wait_for_timeout(300)
        check("salin admin 0 disalin 8 sudah ada", "0 kategori disalin" in text(page, "#hasilSalin") and "8 sudah ada" in text(page, "#hasilSalin"), text(page, "#hasilSalin"))
        # ubah anggaran Pendidikan 500000 -> 600000, lalu kembalikan
        page.select_option("#aKategori", "7")
        page.fill("#aJumlah", "600000")
        page.click("#btnSimpanAnggaran")
        page.wait_for_timeout(300)
        check("ubah Pendidikan total jadi 5600000", "Rp5.600.000" in text(page, "#ringkasanAnggaran"), text(page, "#ringkasanAnggaran"))
        page.select_option("#aKategori", "7")
        page.fill("#aJumlah", "500000")
        page.click("#btnSimpanAnggaran")
        page.wait_for_timeout(300)
        check("kembalikan Pendidikan total 5500000", "Rp5.500.000" in text(page, "#ringkasanAnggaran"), text(page, "#ringkasanAnggaran"))

        # ---------- 4. Tab Kategori ----------
        tab(page, "kategori")
        check("kategori ringkasan 8 kategori", "8 kategori" in text(page, "#ringkasanKategori"), text(page, "#ringkasanKategori"))
        check("kategori Makan realisasi 1350000", "Makan" in text(page, "#daftarKategori") and "Rp1.350.000" in text(page, "#daftarKategori"), text(page, "#daftarKategori")[:400])
        page.fill("#kNamaKat", "Donasi")
        page.fill("#kDeskKat", "Sedekah dan donasi rutin")
        page.click("#btnTambahKategori")
        page.wait_for_timeout(300)
        check("tambah kategori Donasi jadi 9", "9 kategori" in text(page, "#ringkasanKategori"), text(page, "#ringkasanKategori"))
        page.click("[data-hapus-kategori='9']")
        page.wait_for_timeout(200)
        page.click("#modalYa")
        page.wait_for_timeout(300)
        check("hapus Donasi kembali 8", "8 kategori" in text(page, "#ringkasanKategori"), text(page, "#ringkasanKategori"))
        page.click("[data-hapus-kategori='1']")
        page.wait_for_timeout(300)
        check("hapus Makan ditolak (masih dipakai)", "8 kategori" in text(page, "#ringkasanKategori"), text(page, "#ringkasanKategori"))

        # ---------- 5. Tab Realisasi ----------
        tab(page, "realisasi")
        page.select_option("#fKategoriRealisasi", "1")
        page.wait_for_timeout(300)
        check("filter Makan 4 pengeluaran 1350000", "4 pengeluaran" in text(page, "#ringkasanRealisasi") and "Rp1.350.000" in text(page, "#ringkasanRealisasi"), text(page, "#ringkasanRealisasi"))
        page.select_option("#fBulanRealisasi", "")
        page.wait_for_timeout(300)
        check("semua bulan Makan 5 x 2650000", "5 pengeluaran" in text(page, "#ringkasanRealisasi") and "Rp2.650.000" in text(page, "#ringkasanRealisasi"), text(page, "#ringkasanRealisasi"))
        page.select_option("#fKategoriRealisasi", "")
        page.wait_for_timeout(300)
        check("semua bulan 25 pengeluaran 8680000", "25 pengeluaran" in text(page, "#ringkasanRealisasi") and "Rp8.680.000" in text(page, "#ringkasanRealisasi"), text(page, "#ringkasanRealisasi"))
        page.select_option("#fBulanRealisasi", "2026-11")
        page.wait_for_timeout(300)
        check("kembali Nov 17 pengeluaran 4230000", "17 pengeluaran" in text(page, "#ringkasanRealisasi") and "Rp4.230.000" in text(page, "#ringkasanRealisasi"), text(page, "#ringkasanRealisasi"))
        page.fill("#cariRealisasi", "Bensin")
        page.wait_for_timeout(300)
        check("cari Bensin 1 pengeluaran", "1 pengeluaran" in text(page, "#ringkasanRealisasi"), text(page, "#ringkasanRealisasi"))
        page.fill("#cariRealisasi", "")
        page.wait_for_timeout(200)
        # tambah realisasi Makan +100000, lalu hapus
        page.select_option("#rKategori", "1")
        page.fill("#rTanggal", "2026-11-20")
        page.fill("#rNama", "Tes Jajan")
        page.fill("#rJumlah", "100000")
        page.click("#btnTambahRealisasi")
        page.wait_for_timeout(300)
        page.select_option("#fKategoriRealisasi", "1")
        page.wait_for_timeout(300)
        check("tambah realisasi Makan jadi 5 x 1450000", "5 pengeluaran" in text(page, "#ringkasanRealisasi") and "Rp1.450.000" in text(page, "#ringkasanRealisasi"), text(page, "#ringkasanRealisasi"))
        tab(page, "dashboard")
        check("dasbor realisasi jadi 4330000", "Rp4.330.000" in text(page, "#dRealisasi"), text(page, "#dRealisasi"))
        check("dasbor persen jadi 78,7%", "78,7%" in text(page, "#dPersen"), text(page, "#dPersen"))
        tab(page, "realisasi")
        page.click("[data-hapus-realisasi='26']")
        page.wait_for_timeout(200)
        page.click("#modalYa")
        page.wait_for_timeout(300)
        check("hapus Tes Jajan Makan kembali 1350000", "4 pengeluaran" in text(page, "#ringkasanRealisasi") and "Rp1.350.000" in text(page, "#ringkasanRealisasi"), text(page, "#ringkasanRealisasi"))

        # ---------- 6. Tab Peringatan ----------
        tab(page, "peringatan")
        check("peringatan Nov ringkasan 5 kategori 2 lewat", "5 kategori" in text(page, "#ringkasanPeringatan") and "2 lewat batas" in text(page, "#ringkasanPeringatan"), text(page, "#ringkasanPeringatan"))
        t_per = text(page, "#tabelPeringatan")
        check("peringatan Hiburan 116,7% lewat", "Hiburan" in t_per and "116,7%" in t_per and "Lewat batas" in t_per, t_per[:500])
        check("peringatan Makan 90% hampir habis", "Makan" in t_per and "90%" in t_per and "Hampir habis" in t_per, t_per[:500])
        check("peringatan Nov tanpa anggaran kosong", "Tidak ada kategori tanpa anggaran" in text(page, "#daftarTanpaAnggaran"), text(page, "#daftarTanpaAnggaran"))
        page.select_option("#fBulanPeringatan", "2026-10")
        page.wait_for_timeout(300)
        check("peringatan Okt ringkasan 7 kategori 0 lewat", "7 kategori" in text(page, "#ringkasanPeringatan") and "0 lewat batas" in text(page, "#ringkasanPeringatan"), text(page, "#ringkasanPeringatan"))
        check("peringatan Okt ada Tagihan 95,5%", "Tagihan" in text(page, "#tabelPeringatan") and "95,5%" in text(page, "#tabelPeringatan"), text(page, "#tabelPeringatan")[:500])
        page.select_option("#fBulanPeringatan", "2026-11")
        page.wait_for_timeout(300)

        # ---------- 7. Tab Laporan ----------
        tab(page, "laporan")
        check("laporan Nov anggaran 5500000", "Rp5.500.000" in text(page, "#lAnggaran"), text(page, "#lAnggaran"))
        check("laporan Nov realisasi 4230000", "Rp4.230.000" in text(page, "#lRealisasi"), text(page, "#lRealisasi"))
        check("laporan Nov sisa 1270000", "Rp1.270.000" in text(page, "#lSisa"), text(page, "#lSisa"))
        check("laporan Nov persen 76,9%", "76,9%" in text(page, "#lPersen"), text(page, "#lPersen"))
        t_bln = text(page, "#tabelLapBulan")
        check("laporan per bulan Okt 4950000/4450000/89,9%", "Oktober 2026" in t_bln and "Rp4.950.000" in t_bln and "Rp4.450.000" in t_bln and "89,9%" in t_bln, t_bln[:500])
        check("laporan per bulan Nov 5500000/4230000/76,9%", "November 2026" in t_bln and "Rp5.500.000" in t_bln and "76,9%" in t_bln, t_bln[:500])
        # CSV November: 8 baris data
        with page.expect_download() as dl:
            page.click("#btnCsvLaporan")
        csv_path = Path("/tmp/laporan-anggaran-2026-11.csv")
        dl.value.save_as(str(csv_path))
        isi_csv = csv_path.read_text(encoding="utf-8")
        baris_csv = [b for b in isi_csv.strip().split("\n") if b]
        check("CSV header 7 kolom", baris_csv[0].count(",") == 6, baris_csv[0])
        check("CSV Nov 8 baris data", len(baris_csv) == 9, f"baris={len(baris_csv)}")
        check("CSV Makan 1500000/1350000", '"Makan","1500000","1350000"' in isi_csv, isi_csv[:400])
        check("CSV Hiburan status Lewat batas", '"Hiburan","300000","350000"' in isi_csv and "Lewat batas" in isi_csv, isi_csv[:600])
        # CSV Oktober: 8 baris data
        page.select_option("#fBulanLaporan", "2026-10")
        page.wait_for_timeout(300)
        with page.expect_download() as dl2:
            page.click("#btnCsvLaporan")
        csv_path10 = Path("/tmp/laporan-anggaran-2026-10.csv")
        dl2.value.save_as(str(csv_path10))
        baris10 = [b for b in csv_path10.read_text(encoding="utf-8").strip().split("\n") if b]
        check("CSV Okt 8 baris data", len(baris10) == 9, f"baris={len(baris10)}")
        check("CSV Okt Makan 1400000/1300000", '"Makan","1400000","1300000"' in csv_path10.read_text(encoding="utf-8"))
        page.select_option("#fBulanLaporan", "2026-11")
        page.wait_for_timeout(300)
        # Backup JSON + restore
        with page.expect_download() as dl3:
            page.click("#btnBackup")
        bak_path = Path("/tmp/aplikasi-anggaran-bulanan-backup.json")
        dl3.value.save_as(str(bak_path))
        bak = json.loads(bak_path.read_text(encoding="utf-8"))
        check("backup aplikasi anggaran bulanan", bak.get("aplikasi") == "aplikasi-anggaran-bulanan", str(bak.get("aplikasi")))
        check("backup 8 kategori 16 anggaran 25 realisasi", len(bak["state"]["kategori"]) == 8 and len(bak["state"]["anggaran"]) == 16 and len(bak["state"]["realisasi"]) == 25, f"{len(bak['state']['kategori'])} {len(bak['state']['anggaran'])} {len(bak['state']['realisasi'])}")
        check("backup 2 users", len(bak["users"]) == 2)
        # restore: ubah nama realisasi pertama jadi RESTORE-TEST
        state_raw = page.evaluate("() => localStorage.getItem('aplikasiAnggaranBulanan.v1')")
        users_raw = page.evaluate("() => localStorage.getItem('aplikasiAnggaranBulanan.v1.users')")
        data_state = json.loads(state_raw)
        data_state["realisasi"][0]["nama"] = "RESTORE-TEST"
        users_list = json.loads(users_raw) if users_raw else [
            {"username": "admin", "nama": "Administrator", "peran": "admin", "password": "admin123", "aktif": True},
            {"username": "pengguna", "nama": "Budi Santoso", "peran": "pengguna", "password": "pengguna123", "aktif": True},
        ]
        payload = {"aplikasi": "aplikasi-anggaran-bulanan", "versi": 1, "state": data_state, "users": users_list}
        restore_path = Path("/tmp/restore-anggaran.json")
        restore_path.write_text(json.dumps(payload), encoding="utf-8")
        page.set_input_files("#inputRestore", str(restore_path))
        page.wait_for_timeout(400)
        tab(page, "realisasi")
        page.fill("#cariRealisasi", "RESTORE-TEST")
        page.wait_for_timeout(300)
        check("restore realisasi jadi RESTORE-TEST", "1 pengeluaran" in text(page, "#ringkasanRealisasi"), text(page, "#ringkasanRealisasi"))
        page.fill("#cariRealisasi", "")
        page.wait_for_timeout(200)
        # restore file tidak valid
        bad_path = Path("/tmp/restore-anggaran-bad.json")
        bad_path.write_text('{"x": 1}', encoding="utf-8")
        page.set_input_files("#inputRestore", str(bad_path))
        page.wait_for_timeout(400)
        page.fill("#cariRealisasi", "RESTORE-TEST")
        page.wait_for_timeout(300)
        check("restore tidak valid ditolak, data tetap", "1 pengeluaran" in text(page, "#ringkasanRealisasi"), text(page, "#ringkasanRealisasi"))
        page.fill("#cariRealisasi", "")
        page.wait_for_timeout(200)
        # reset ke data demo
        tab(page, "laporan")
        page.click("#btnResetData")
        page.wait_for_timeout(200)
        page.click("#modalYa")
        page.wait_for_timeout(300)
        tab(page, "dashboard")
        check("reset total kembali 5500000", "Rp5.500.000" in text(page, "#dAnggaran"), text(page, "#dAnggaran"))

        # ---------- 8. Peran Pengguna ----------
        logout(page)
        login(page, "pengguna", "pengguna123")
        check("login pengguna berhasil", not page.is_visible("#loginOverlay"))
        check("chip pengguna Budi", "Budi Santoso (Pengguna)" in text(page, "#userChip"))
        check("dasbor pengguna anggaran 5000000", "Rp5.000.000" in text(page, "#dAnggaran"), text(page, "#dAnggaran"))
        check("dasbor pengguna realisasi 3860000", "Rp3.860.000" in text(page, "#dRealisasi"), text(page, "#dRealisasi"))
        check("dasbor pengguna sisa 1140000", "Rp1.140.000" in text(page, "#dSisa"), text(page, "#dSisa"))
        check("dasbor pengguna persen 77,2%", "77,2%" in text(page, "#dPersen"), text(page, "#dPersen"))
        check("dasbor pengguna peringatan 3 kategori", "3 kategori" in text(page, "#dPeringatan"), text(page, "#dPeringatan"))
        check("badge peringatan pengguna 3", text(page, "#badgePeringatan") == "3", text(page, "#badgePeringatan"))
        check("badge realisasi pengguna 15", text(page, "#badgeRealisasi") == "15", text(page, "#badgeRealisasi"))
        check("kartu kelola pengguna TERSEMBUNYI (pengguna)", not page.is_visible("#cardPengguna"))
        check("kartu ganti sandi terlihat (pengguna)", page.is_visible("#cardSandiSaya"))
        check("kartu catat cepat terlihat (pengguna)", page.is_visible("#cardTambahCepat"))
        tab(page, "peringatan")
        check("peringatan pengguna 3 kategori", "3 kategori" in text(page, "#ringkasanPeringatan"), text(page, "#ringkasanPeringatan"))
        check("pengguna Hiburan tanpa anggaran 230000", "Hiburan" in text(page, "#daftarTanpaAnggaran") and "Rp230.000" in text(page, "#daftarTanpaAnggaran"), text(page, "#daftarTanpaAnggaran"))
        tab(page, "anggaran")
        check("anggaran pengguna 7 kategori", "7 kategori" in text(page, "#ringkasanAnggaran"), text(page, "#ringkasanAnggaran"))
        check("anggaran pengguna Hiburan tanpa anggaran", "Hiburan" in text(page, "#tabelAnggaran") and "Tanpa anggaran" in text(page, "#tabelAnggaran"), text(page, "#tabelAnggaran")[:600])
        # salin bulan lalu (pengguna): 2 disalin, 6 sudah ada
        page.click("#btnSalinBulanLalu")
        page.wait_for_timeout(300)
        check("salin pengguna 2 disalin 6 sudah ada", "2 kategori disalin" in text(page, "#hasilSalin") and "6 sudah ada" in text(page, "#hasilSalin"), text(page, "#hasilSalin"))
        check("anggaran pengguna jadi 5400000", "Rp5.400.000" in text(page, "#ringkasanAnggaran"), text(page, "#ringkasanAnggaran"))
        tab(page, "dashboard")
        check("dasbor pengguna anggaran 5400000", "Rp5.400.000" in text(page, "#dAnggaran"), text(page, "#dAnggaran"))
        check("badge peringatan pengguna jadi 4", text(page, "#badgePeringatan") == "4", text(page, "#badgePeringatan"))
        tab(page, "peringatan")
        check("peringatan pengguna jadi 4 (Hiburan 92%)", "4 kategori" in text(page, "#ringkasanPeringatan") and "92%" in text(page, "#tabelPeringatan"), text(page, "#tabelPeringatan")[:500])
        # reset lagi agar data kembali ke seed
        tab(page, "laporan")
        page.click("#btnResetData")
        page.wait_for_timeout(200)
        page.click("#modalYa")
        page.wait_for_timeout(300)
        tab(page, "dashboard")
        check("reset pengguna anggaran kembali 5000000", "Rp5.000.000" in text(page, "#dAnggaran"), text(page, "#dAnggaran"))

        # ---------- 9. Ganti sandi + reset ----------
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
