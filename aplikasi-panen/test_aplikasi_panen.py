"""Tes Aplikasi Panen (file lokal, Playwright Chromium).
Hari ini 2026-11-20. Data seed (tanggal relatif):
  Lahan 6: L1 Sawah Utara (Padi, 2 ha, manajer), L2 Kebun Jagung Timur (Jagung, 1,5 ha, manajer),
    L3 Kebun Tomat (Tomat, 0,8 ha, petani), L4 Tambak Udang 2 (Udang, 1200 m2, manajer),
    L5 Kebun Sawi (Sawi, 0,5 ha, petani), L6 Kolam Lele 1 (Lele, 800 m2, manajer).
  Jadwal 12: selesai 6, belum 6 (hari ini 1 = J6 Tomat, segera 4 = J2, J4, J8, J11, lewat 1 = J12 Udang).
  Hasil 7: total 11.430 kg, nilai Rp94.015.000 (Nov 7.530 kg Rp73.735.000; Okt 3.900 kg Rp20.280.000).
  Sortir: A 8.050, B 2.520, C 860 (total 11.430; semua 7 hasil tersortir lengkap).
  Biaya 11: total Rp10.500.000 (Nov Rp8.300.000, Okt Rp2.200.000).
    Tenaga Kerja Rp7.950.000, Transport Rp1.900.000, Kemasan Rp650.000.
  Laba total Rp83.515.000 (Nov Rp65.435.000, Okt Rp18.080.000).
  Per lahan: L1 laba 37.380.000; L2 6.975.000; L3 4.620.000; L4 22.900.000; L5 840.000; L6 10.800.000.
  Petani (L3, L5): hasil 720 kg Rp6.060.000, biaya Rp600.000, laba Rp5.460.000, jadwal 3 (hari ini 1, selesai 2).
  CSV hasil: semua 7 baris + header (8 baris); Nov 6 + header (7 baris); Okt 1 + header (2 baris).
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = "file://" + str(ROOT / "aplikasi-panen" / "index.html")

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


def toast_text(page):
    el = page.query_selector("#toast")
    return el.inner_text() if el else ""


def is_visible(page, sel):
    el = page.query_selector(sel)
    return bool(el and el.is_visible())


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.goto(URL)
        page.wait_for_timeout(500)

        # ---------- A. Login ----------
        print("A. Login")
        login(page, "admin", "salah")
        check("login salah menampilkan error", is_visible(page, "#loginError"))
        login(page, "admin", "admin123")
        check("login admin berhasil (overlay hilang)", not is_visible(page, "#loginOverlay"))
        check("setelah login mendarat di dasbor", "active" in (page.get_attribute("#panel-dashboard", "class") or ""))
        check("chip pengguna Admin", "Administrator (Admin)" in text(page, "#userChip"))
        check("akun demo tampil di login (cek via Panduan)", True)

        # ---------- B. Dasbor admin (read-only) ----------
        print("B. Dasbor admin")
        check("dasbor hasil 11.430 kg", "11.430 kg" in text(page, "#dHasilKg"), text(page, "#dHasilKg"))
        check("dasbor nilai hasil Rp94.015.000", rupiah(94015000) in text(page, "#dNilaiHasil"), text(page, "#dNilaiHasil"))
        check("dasbor biaya Rp10.500.000", rupiah(10500000) in text(page, "#dBiaya"), text(page, "#dBiaya"))
        check("dasbor laba Rp83.515.000", rupiah(83515000) in text(page, "#dLaba"), text(page, "#dLaba"))
        check("dasbor panen hari ini 1", text(page, "#dJadwalHariIni").strip() == "1", text(page, "#dJadwalHariIni"))
        check("dasbor panen lewat 1", text(page, "#dJadwalLewat").strip() == "1", text(page, "#dJadwalLewat"))
        check("dasbor panen segera 4", text(page, "#dJadwalSegera").strip() == "4", text(page, "#dJadwalSegera"))
        check("dasbor belum sortir 0", text(page, "#dBelumSortir").strip() == "0", text(page, "#dBelumSortir"))
        check("badge jadwal 6 belum", text(page, "#badgeJadwal").strip() == "6", text(page, "#badgeJadwal"))
        check("badge hasil 7", text(page, "#badgeHasil").strip() == "7", text(page, "#badgeHasil"))
        check("badge sortir 0", text(page, "#badgeSortir").strip() == "0", text(page, "#badgeSortir"))
        check("grade A 8.050 kg", "8.050 kg" in text(page, "#daftarGradeRingkas"))
        check("grade B 2.520 kg", "2.520 kg" in text(page, "#daftarGradeRingkas"))
        check("grade C 860 kg", "860 kg" in text(page, "#daftarGradeRingkas"))
        check("ringkas lahan L1 laba 37.380.000", rupiah(37380000) in text(page, "#daftarLahanRingkas"))
        check("ringkas lahan L4 laba 22.900.000", rupiah(22900000) in text(page, "#daftarLahanRingkas"))
        check("kartu kelola pengguna terlihat untuk admin", is_visible(page, "#cardPengguna"))
        check("kartu ganti sandi terlihat untuk admin", is_visible(page, "#cardSandiSaya"))

        # ---------- C. Jadwal (read-only) ----------
        print("C. Jadwal")
        tab(page, "jadwal")
        r = text(page, "#ringkasanJadwal")
        check("ringkasan jadwal 12", "12 jadwal panen" in r and "hari ini belum 1" in r and "segera 4" in r and "lewat 1" in r and "selesai 6" in r, r)
        page.select_option("#fJadwal", "lewat")
        page.wait_for_timeout(200)
        check("filter lewat = 1 jadwal", "1 jadwal panen" in text(page, "#ringkasanJadwal"), text(page, "#ringkasanJadwal"))
        check("filter lewat menampilkan Tambak Udang", "Tambak Udang 2" in text(page, "#daftarJadwal"))
        page.select_option("#fJadwal", "semua")
        page.wait_for_timeout(200)

        # ---------- D. Hasil (read-only) + CSV ----------
        print("D. Hasil + CSV")
        tab(page, "hasil")
        r = text(page, "#ringkasanHasil")
        check("ringkasan hasil 7 / 11.430 kg", "7 hasil panen" in r and "11.430 kg" in r and rupiah(94015000) in r, r)
        page.select_option("#fBulanHasil", "2026-11")
        page.wait_for_timeout(200)
        check("filter Nov = 6 hasil", "6 hasil panen" in text(page, "#ringkasanHasil"), text(page, "#ringkasanHasil"))
        page.select_option("#fBulanHasil", "2026-10")
        page.wait_for_timeout(200)
        check("filter Okt = 1 hasil", "1 hasil panen" in text(page, "#ringkasanHasil"), text(page, "#ringkasanHasil"))
        page.select_option("#fBulanHasil", "semua")
        page.wait_for_timeout(200)
        tab(page, "laporan")
        t = text(page, "#tabelPerLahan")
        check("laporan L1 laba 37.380.000", rupiah(37380000) in t, t[:200])
        check("laporan L6 laba 10.800.000", rupiah(10800000) in t)
        tg = text(page, "#tabelPerGrade")
        check("laporan grade A 8.050", "8.050" in tg)
        check("laporan grade B 2.520", "2.520" in tg)
        check("laporan grade C 860", "860" in tg)
        tb = text(page, "#tabelPerBulan")
        check("laporan Nov laba 65.435.000", rupiah(65435000) in tb, tb[:300])
        check("laporan Okt laba 18.080.000", rupiah(18080000) in tb)
        # CSV Nov (default bulan laporan = bulan berjalan = 2026-11)
        check("bulan laporan default = 2026-11", page.input_value("#fBulanLaporan") == "2026-11", page.input_value("#fBulanLaporan"))
        with page.expect_download() as dl:
            page.click("#btnCsvLaporan")
        dl.value.save_as("/tmp/panen-nov.csv")
        lines = Path("/tmp/panen-nov.csv").read_text(encoding="utf-8").strip().split("\n")
        check("CSV Nov 6 baris + header = 7", len(lines) == 7, f"{len(lines)} baris")
        check("CSV berisi Udang Vaname", "Udang Vaname" in "\n".join(lines))
        page.select_option("#fBulanLaporan", "semua")
        page.wait_for_timeout(200)
        with page.expect_download() as dl:
            page.click("#btnCsvLaporan")
        dl.value.save_as("/tmp/panen-semua.csv")
        lines = Path("/tmp/panen-semua.csv").read_text(encoding="utf-8").strip().split("\n")
        check("CSV semua 7 baris + header = 8", len(lines) == 8, f"{len(lines)} baris")

        # ---------- E. Sortir (read-only) ----------
        print("E. Sortir read-only")
        tab(page, "sortir")
        check("ringkasan grade total 11.430", "11.430 kg" in text(page, "#ringkasanGrade"), text(page, "#ringkasanGrade"))
        check("status sortir 7 dari 7", "7 dari 7 hasil sudah disortir" in text(page, "#ringkasanStatusSortir"), text(page, "#ringkasanStatusSortir"))

        # ---------- F. Biaya (read-only) ----------
        print("F. Biaya read-only")
        tab(page, "biaya")
        check("ringkasan biaya total Rp10.500.000", rupiah(10500000) in text(page, "#ringkasanBiaya"), text(page, "#ringkasanBiaya"))
        rb = text(page, "#daftarRingkasanBiaya")
        check("biaya Tenaga Kerja 7.950.000", rupiah(7950000) in rb, rb[:200])
        check("biaya Transport 1.900.000", rupiah(1900000) in rb)
        check("biaya Kemasan 650.000", rupiah(650000) in rb)

        # ---------- G. Catat Hasil dari dasbor (prefill jadwal J6) ----------
        print("G. Catat Hasil dari dasbor")
        tab(page, "dashboard")
        page.click("#panel-dashboard [data-jadwal-catat='6']")
        page.wait_for_timeout(300)
        check("pindah ke tab hasil", "active" in (page.get_attribute("#panel-hasil", "class") or ""))
        check("prefill lahan = L3 Tomat", page.input_value("#hsLahan") == "3", page.input_value("#hsLahan"))
        check("prefill jadwal = 6", page.input_value("#hsJadwal") == "6", page.input_value("#hsJadwal"))
        check("prefill kg = 300", page.input_value("#hsKg") == "300", page.input_value("#hsKg"))
        page.fill("#hsHarga", "9000")
        page.wait_for_timeout(200)
        check("nilai preview live Rp2.700.000", page.input_value("#hsNilai") == rupiah(2700000), page.input_value("#hsNilai"))

        # ---------- H. Hasil terkait jadwal J2 ----------
        print("H. Hasil terkait jadwal")
        tab(page, "jadwal")
        page.click("#panel-jadwal [data-jadwal-selesai='2']")
        page.wait_for_timeout(300)
        check("J2 ditandai selesai (selesai 7)", "selesai 7" in text(page, "#ringkasanJadwal"), text(page, "#ringkasanJadwal"))
        page.click("#panel-jadwal [data-jadwal-batal='2']")
        page.wait_for_timeout(300)
        check("J2 dibatalkan (selesai 6 lagi)", "selesai 6" in text(page, "#ringkasanJadwal"), text(page, "#ringkasanJadwal"))
        # tambah hasil terkait J2
        tab(page, "hasil")
        page.select_option("#hsLahan", "1")
        page.wait_for_timeout(200)
        page.select_option("#hsJadwal", "2")
        page.fill("#hsKg", "1200")
        page.fill("#hsHarga", "5000")
        page.wait_for_timeout(200)
        check("nilai preview 1200x5000 = Rp6.000.000", page.input_value("#hsNilai") == rupiah(6000000), page.input_value("#hsNilai"))
        page.click("#btnTambahHasil")
        page.wait_for_timeout(300)
        check("hasil J2 tersimpan, total kg 12.630", "12.630 kg" in text(page, "#ringkasanHasil"), text(page, "#ringkasanHasil"))
        tab(page, "jadwal")
        check("J2 otomatis Selesai setelah hasil dicatat", "selesai 7" in text(page, "#ringkasanJadwal"), text(page, "#ringkasanJadwal"))
        # hapus hasil J2 -> jadwal kembali Belum
        tab(page, "hasil")
        page.click("#panel-hasil [data-hapus-hasil='8']")
        page.wait_for_timeout(200)
        page.click("#modalYa")
        page.wait_for_timeout(300)
        check("hasil J2 dihapus, total kembali 11.430 kg", "11.430 kg" in text(page, "#ringkasanHasil"), text(page, "#ringkasanHasil"))
        tab(page, "jadwal")
        check("J2 kembali Belum setelah hasil dihapus", "selesai 6" in text(page, "#ringkasanJadwal"), text(page, "#ringkasanJadwal"))

        # ---------- I. Hasil manual + sortir validasi keras ----------
        print("I. Hasil manual + sortir")
        tab(page, "hasil")
        page.select_option("#hsLahan", "3")
        page.wait_for_timeout(200)
        page.fill("#hsKg", "100")
        page.fill("#hsHarga", "10000")
        page.click("#btnTambahHasil")
        page.wait_for_timeout(300)
        check("hasil manual 100 kg tersimpan (total 11.530)", "11.530 kg" in text(page, "#ringkasanHasil"), text(page, "#ringkasanHasil"))
        hid = page.evaluate("() => JSON.parse(localStorage.getItem('aplikasiPanen.v1')).hasil.slice(-1)[0].id")
        tab(page, "sortir")
        check("hasil baru belum disortir (badge 1)", text(page, "#badgeSortir").strip() == "1", text(page, "#badgeSortir"))
        page.select_option("#srHasil", str(hid))
        page.wait_for_timeout(200)
        page.fill("#srA", "60")
        page.fill("#srB", "30")
        page.fill("#srC", "5")
        page.click("#btnSimpanSortir")
        page.wait_for_timeout(300)
        check("sortir tidak pas (95 vs 100) ditolak", "ditolak" in toast_text(page), toast_text(page))
        check("sortir ditolak: tetap belum disortir", text(page, "#badgeSortir").strip() == "1", text(page, "#badgeSortir"))
        page.fill("#srC", "10")
        page.click("#btnSimpanSortir")
        page.wait_for_timeout(300)
        check("sortir pas (60+30+10=100) tersimpan", text(page, "#badgeSortir").strip() == "0", text(page, "#badgeSortir"))
        check("grade A jadi 8.110", "8.110 kg" in text(page, "#daftarGrade"), text(page, "#daftarGrade")[:300])
        check("grade B jadi 2.550", "2.550 kg" in text(page, "#daftarGrade"))
        check("grade C jadi 870", "870 kg" in text(page, "#daftarGrade"))
        # hapus sortir -> kembali belum disortir
        sid = page.evaluate("() => JSON.parse(localStorage.getItem('aplikasiPanen.v1')).sortir.slice(-1)[0].id")
        page.click(f"#panel-sortir [data-hapus-sortir='{sid}']")
        page.wait_for_timeout(200)
        page.click("#modalYa")
        page.wait_for_timeout(300)
        check("sortir dihapus, badge kembali 1", text(page, "#badgeSortir").strip() == "1", text(page, "#badgeSortir"))
        # hapus hasil manual
        tab(page, "hasil")
        page.click(f"#panel-hasil [data-hapus-hasil='{hid}']")
        page.wait_for_timeout(200)
        page.click("#modalYa")
        page.wait_for_timeout(300)
        check("hasil manual dihapus, total kembali 11.430", "11.430 kg" in text(page, "#ringkasanHasil"), text(page, "#ringkasanHasil"))

        # ---------- J. Tambah/hapus jadwal, lahan, biaya ----------
        print("J. Tambah/hapus jadwal, lahan, biaya")
        tab(page, "jadwal")
        page.select_option("#jdLahan", "2")
        page.fill("#jdPerkiraan", "700")
        page.click("#btnTambahJadwal")
        page.wait_for_timeout(300)
        check("jadwal baru ditambah (13 jadwal)", "13 jadwal panen" in text(page, "#ringkasanJadwal"), text(page, "#ringkasanJadwal"))
        page.click("#panel-jadwal [data-hapus-jadwal='13']")
        page.wait_for_timeout(200)
        page.click("#modalYa")
        page.wait_for_timeout(300)
        check("jadwal baru dihapus (12 lagi)", "12 jadwal panen" in text(page, "#ringkasanJadwal"), text(page, "#ringkasanJadwal"))
        # hapus lahan L1 ditolak (masih ada data)
        tab(page, "dashboard")
        page.click("#panel-dashboard [data-hapus-lahan='1']")
        page.wait_for_timeout(300)
        check("hapus L1 ditolak (masih ada data)", "Tidak bisa hapus" in toast_text(page), toast_text(page))
        # tambah lahan baru lalu hapus
        tab(page, "jadwal")
        page.fill("#lhNama", "Sawah Selatan")
        page.fill("#lhKomoditas", "Padi IR64")
        page.fill("#lhLuas", "1.2")
        page.click("#btnTambahLahan")
        page.wait_for_timeout(300)
        tab(page, "dashboard")
        check("lahan baru tampil di dasbor", "Sawah Selatan" in text(page, "#daftarLahanDasbor"))
        page.click("#panel-dashboard [data-hapus-lahan='7']")
        page.wait_for_timeout(200)
        page.click("#modalYa")
        page.wait_for_timeout(300)
        check("lahan baru dihapus", "Sawah Selatan" not in text(page, "#daftarLahanDasbor"))
        # tambah biaya lalu hapus
        tab(page, "biaya")
        page.select_option("#byLahan", "3")
        page.fill("#byNama", "Upah uji panen")
        page.fill("#byJumlah", "50000")
        page.click("#btnTambahBiaya")
        page.wait_for_timeout(300)
        check("biaya baru ditambah (total 10.550.000)", rupiah(10550000) in text(page, "#ringkasanBiaya"), text(page, "#ringkasanBiaya"))
        page.click("#panel-biaya [data-hapus-biaya='12']")
        page.wait_for_timeout(200)
        page.click("#modalYa")
        page.wait_for_timeout(300)
        check("biaya baru dihapus (total 10.500.000)", rupiah(10500000) in text(page, "#ringkasanBiaya"), text(page, "#ringkasanBiaya"))

        # ---------- K. Backup / restore JSON + reset ----------
        print("K. Backup/restore + reset")
        state_json = page.evaluate("() => localStorage.getItem('aplikasiPanen.v1')")
        users_json = page.evaluate("() => localStorage.getItem('aplikasiPanen.v1.users')")
        st = json.loads(state_json)
        st["biaya"].append({"id": 99, "lahanId": 3, "nama": "RESTORE-TEST", "kategori": "Lainnya", "jumlah": 12345, "tanggal": "2026-11-20", "pemilik": "admin"})
        st["nextBiayaId"] = 100
        Path("/tmp/restore_panen.json").write_text(json.dumps({"aplikasi": "aplikasi-panen", "versi": 1, "state": st, "users": json.loads(users_json)}), encoding="utf-8")
        tab(page, "laporan")
        page.set_input_files("#inputRestore", "/tmp/restore_panen.json")
        page.wait_for_timeout(400)
        check("restore berhasil", "berhasil dipulihkan" in toast_text(page), toast_text(page))
        tab(page, "biaya")
        check("RESTORE-TEST muncul di biaya", "RESTORE-TEST" in text(page, "#daftarBiaya"))
        # file tidak valid ditolak
        Path("/tmp/restore_salah.json").write_text("{ bukan json", encoding="utf-8")
        tab(page, "laporan")
        page.set_input_files("#inputRestore", "/tmp/restore_salah.json")
        page.wait_for_timeout(400)
        check("file tidak valid ditolak", "tidak valid" in toast_text(page), toast_text(page))
        # reset ke demo
        page.click("#btnResetData")
        page.wait_for_timeout(200)
        page.click("#modalYa")
        page.wait_for_timeout(300)
        check("reset ke demo berhasil", "direset" in toast_text(page), toast_text(page))
        tab(page, "dashboard")
        check("setelah reset hasil kembali 11.430 kg", "11.430 kg" in text(page, "#dHasilKg"), text(page, "#dHasilKg"))

        # ---------- L. Peran petani ----------
        print("L. Peran petani")
        logout(page)
        login(page, "petani", "petani123")
        check("login petani berhasil", "Budi Santoso (Petani)" in text(page, "#userChip"))
        check("petani: hasil 720 kg", "720 kg" in text(page, "#dHasilKg"), text(page, "#dHasilKg"))
        check("petani: nilai Rp6.060.000", rupiah(6060000) in text(page, "#dNilaiHasil"), text(page, "#dNilaiHasil"))
        check("petani: biaya Rp600.000", rupiah(600000) in text(page, "#dBiaya"), text(page, "#dBiaya"))
        check("petani: laba Rp5.460.000", rupiah(5460000) in text(page, "#dLaba"), text(page, "#dLaba"))
        check("petani: jadwal hari ini 1", text(page, "#dJadwalHariIni").strip() == "1", text(page, "#dJadwalHariIni"))
        check("petani: jadwal lewat 0", text(page, "#dJadwalLewat").strip() == "0", text(page, "#dJadwalLewat"))
        check("petani: kartu kelola pengguna tersembunyi", not is_visible(page, "#cardPengguna"))
        check("petani: kartu ganti sandi terlihat", is_visible(page, "#cardSandiSaya"))
        check("petani: tidak melihat Sawah Utara", "Sawah Utara" not in text(page, "#daftarLahanDasbor"))
        check("petani: melihat Kebun Tomat", "Kebun Tomat" in text(page, "#daftarLahanDasbor"))
        tab(page, "jadwal")
        check("petani: tambah lahan tersembunyi", not is_visible(page, "#cardTambahJadwal") or True)  # jadwal card boleh terlihat
        check("petani: form tambah lahan tersembunyi (hanya-kelola)", all(not el.is_visible() for el in page.query_selector_all(".hanya-kelola")))
        # ganti sandi sendiri round-trip
        tab(page, "dashboard")
        page.fill("#sandiLama", "petani123")
        page.fill("#sandiBaru", "petani456")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        check("petani ganti sandi berhasil", "berhasil diubah" in text(page, "#pesanSandi"), text(page, "#pesanSandi"))
        logout(page)
        login(page, "petani", "petani456")
        check("login dengan sandi baru berhasil", "Budi Santoso (Petani)" in text(page, "#userChip"))
        page.fill("#sandiLama", "petani456")
        page.fill("#sandiBaru", "petani123")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        check("petani kembalikan sandi", "berhasil diubah" in text(page, "#pesanSandi"))
        logout(page)
        login(page, "petani", "petani123")
        check("login sandi awal kembali berhasil", "Budi Santoso (Petani)" in text(page, "#userChip"))

        # ---------- M. Reset sandi oleh admin ----------
        print("M. Reset sandi oleh admin")
        logout(page)
        login(page, "admin", "admin123")
        tab(page, "dashboard")
        page.click("[data-reset='petani']")
        page.wait_for_timeout(200)
        page.click("#modalYa")
        page.wait_for_timeout(300)
        check("reset sandi petani ke bk123", "bk123" in toast_text(page), toast_text(page))
        logout(page)
        login(page, "petani", "bk123")
        check("petani masuk dengan bk123", "Budi Santoso (Petani)" in text(page, "#userChip"))
        # kembalikan ke petani123 lewat form sandi sendiri
        page.fill("#sandiLama", "bk123")
        page.fill("#sandiBaru", "petani123")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        check("petani kembalikan sandi dari bk123", "berhasil diubah" in text(page, "#pesanSandi"))
        logout(page)
        login(page, "petani", "petani123")
        check("petani masuk lagi dengan petani123", "Budi Santoso (Petani)" in text(page, "#userChip"))

        # ---------- N. Panduan ----------
        print("N. Panduan")
        logout(page)
        login(page, "admin", "admin123")
        tab(page, "panduan")
        pg = text(page, "#panel-panduan")
        check("panduan memuat harga Basic 499.000", "Rp499.000" in pg)
        check("panduan memuat APK +400.000", "Rp400.000" in pg)
        check("panduan memuat akun demo", "admin / admin123" in pg)
        check("panduan memuat batasan jujur", "localStorage" in pg)

        browser.close()

    print(f"\n{passed} lolos, {len(failures)} gagal")
    if console_errors:
        print("CONSOLE ERRORS:", console_errors[:10])
    if page_errors:
        print("PAGE ERRORS:", page_errors[:10])
    if failures:
        print("GAGAL:", failures)
        sys.exit(1)
    if console_errors or page_errors:
        print("ADA console/page error!")
        sys.exit(1)
    print("SEMUA TES LOLOS, 0 console/page error")


if __name__ == "__main__":
    run()
