"""Tes Fishery Management (Perikanan) (file lokal, Playwright Chromium).
Hari ini 2026-11-20. Data seed (tanggal relatif) — diuji silang Python (/tmp/cek_fishery.py):
  Kolam 6 (Aktif 5, Perawatan 1): luas total 2700 m2, tebar total 42800 ekor.
  Tangkapan 10: total 850 kg, nilai Rp29.525.000.
    Nov: 8 tangkapan, 735 kg, Rp24.160.000. Okt: 2 tangkapan, 115 kg, Rp5.365.000.
    Per kolam: K1 200 kg/5.000.000, K2 250 kg/7.500.000, K3 105 kg/8.925.000,
      K4 25 kg/1.500.000, K5 160 kg/3.520.000, K6 110 kg/3.080.000.
    Nelayan (K4+K5): 3 tangkapan, 185 kg, Rp5.020.000 (Nov 2 tangkapan, 115 kg, Rp3.480.000).
  Pakan 12 jadwal: hari ini belum 4 (100 kg), segera 8, lewat 2, sudah diberi 2.
    Nelayan: 4 jadwal (hari ini belum 1, segera 1, lewat 2, selesai 1).
  Stok 6 item, nilai Rp4.875.000; menipis 2 (Pelet Udang 45<50, Pelet Patin 15<20).
  Biaya 10 entri, total Rp4.910.000 (Pakan 4.360.000, Obat 150.000, Perawatan 400.000).
    Nov: 8 entri Rp4.300.000; Okt: 2 entri Rp610.000. Nelayan: 3 catatan Rp830.000.
  Laba (nilai tangkapan - biaya): Rp24.615.000.
    Per kolam: K1 3.650.000, K2 6.460.000, K3 7.715.000, K4 1.220.000, K5 2.970.000, K6 2.600.000.
    Per bulan: Nov laba 19.860.000 (24.160.000 - 4.300.000); Okt laba 4.755.000 (5.365.000 - 610.000).
  RESTORE-TEST: biaya "RESTORE-TEST" Rp123.456 -> total biaya 5.033.456.
  CSV: semua 20 baris data + header (21 baris); Nov 16 baris data + header (17 baris).
Urutan tes: label + login salah, A nelayan (baseline + peran + ganti sandi),
  B manajer (baseline + bisa kelola, tidak bisa kelola pengguna),
  C admin (baseline + kolam + tangkapan + pakan + stok + biaya + laporan + CSV),
  D admin (RESTORE-TEST + backup/reset/restore + file tidak valid + hapus),
  E admin (reset sandi nelayan -> login bk123 -> kembalikan nelayan123).
"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = "file://" + str(ROOT / "fishery-management" / "index.html")

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


def klik_modal_ya(page):
    page.click("#modalYa")
    page.wait_for_timeout(400)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(accept_downloads=True)
        page = ctx.new_page()
        page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.goto(URL)
        page.wait_for_timeout(500)

        # ---------- Label + login salah ----------
        check("hero bertuliskan Fishery Management", "Fishery Management" in text(page, ".hero"))
        check("login menampilkan 3 akun demo", "admin / admin123" in text(page, ".login-note") and "manajer / manajer123" in text(page, ".login-note") and "nelayan / nelayan123" in text(page, ".login-note"))
        login(page, "admin", "salah123")
        check("login salah ditolak", visible(page, "#loginError"))
        check("overlay login masih tampil setelah login salah", visible(page, "#loginOverlay"))

        # ---------- A. Nelayan ----------
        login(page, "nelayan", "nelayan123")
        check("nelayan masuk, overlay hilang", not visible(page, "#loginOverlay"))
        check("nelayan mendarat di dasbor", "active" in (page.query_selector("#panel-dashboard").get_attribute("class") or ""))
        check("chip pengguna nelayan", "Budi Santoso (Nelayan)" in text(page, "#userChip"))
        check("nelayan dasbor kolam 2", text(page, "#dKolam").strip() == "2")
        check("nelayan dasbor tangkapan 185 kg", text(page, "#dTangkapanKg").strip() == "185 kg")
        check("nelayan dasbor nilai 5.020.000", "5.020.000" in text(page, "#dNilai"))
        check("nelayan dasbor laba 4.190.000", "4.190.000" in text(page, "#dLaba"))
        check("nelayan dasbor pakan hari ini 1 (15 kg)", text(page, "#dPakanHariIni").strip() == "1" and "15 kg" in text(page, "#dPakanHariIniSub"))
        check("nelayan dasbor stok menipis 2", text(page, "#dStokMenipis").strip() == "2")
        check("nelayan dasbor biaya 830.000", "830.000" in text(page, "#dBiaya"))
        check("nelayan dasbor nilai stok 4.875.000", "4.875.000" in text(page, "#dNilaiStok"))
        check("nelayan tidak melihat kartu kelola pengguna", not visible(page, "#cardPengguna"))
        tab(page, "kolam")
        check("nelayan form tambah kolam tersembunyi", not visible(page, "#panel-kolam .hanya-kelola"))
        check("nelayan melihat 2 kolam 400 m2 3800 ekor", "2 kolam/tambak" in text(page, "#ringkasanKolam") and "400 m" in text(page, "#ringkasanKolam") and "3.800 ekor" in text(page, "#ringkasanKolam"))
        tab(page, "tangkapan")
        check("nelayan pilihan tangkapan hanya 2 kolam miliknya", len(page.query_selector_all("#tgKolam option")) == 2)
        check("nelayan melihat 3 tangkapan 185 kg 5.020.000", "3 tangkapan" in text(page, "#ringkasanTangkapan") and "185 kg" in text(page, "#ringkasanTangkapan") and "5.020.000" in text(page, "#ringkasanTangkapan"))
        tab(page, "pakan")
        check("nelayan pilihan pakan hanya 2 kolam miliknya", len(page.query_selector_all("#pkKolam option")) == 2)
        check("nelayan melihat 4 jadwal pakan (hari ini 1, segera 1, lewat 2)", "4 jadwal pakan" in text(page, "#ringkasanPakan") and "hari ini belum 1" in text(page, "#ringkasanPakan") and "segera 1" in text(page, "#ringkasanPakan") and "lewat 2" in text(page, "#ringkasanPakan"))
        tab(page, "stok")
        check("nelayan form stok tersembunyi", not visible(page, "#panel-stok .hanya-kelola"))
        check("nelayan melihat 6 item stok 4.875.000 menipis 2", "6 item stok pakan" in text(page, "#ringkasanStok") and "4.875.000" in text(page, "#ringkasanStok") and "menipis 2" in text(page, "#ringkasanStok"))
        tab(page, "biaya")
        check("nelayan daftar biaya hanya miliknya (3 catatan 830.000)", "3 catatan biaya" in text(page, "#ringkasanBiaya") and "830.000" in text(page, "#ringkasanBiaya"))
        # ganti sandi round-trip
        tab(page, "dashboard")
        page.fill("#sandiLama", "nelayan123")
        page.fill("#sandiBaru", "nelayan456")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        check("nelayan ganti sandi berhasil", "berhasil diubah" in text(page, "#pesanSandi"))
        logout(page)
        login(page, "nelayan", "nelayan456")
        check("nelayan masuk dengan sandi baru", not visible(page, "#loginOverlay"))
        tab(page, "dashboard")
        page.fill("#sandiLama", "nelayan456")
        page.fill("#sandiBaru", "nelayan123")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        check("nelayan kembalikan sandi", "berhasil diubah" in text(page, "#pesanSandi"))
        logout(page)

        # ---------- B. Manajer ----------
        login(page, "manajer", "manajer123")
        check("manajer masuk", not visible(page, "#loginOverlay"))
        check("chip pengguna manajer", "Dedi Kurniawan (Manajer)" in text(page, "#userChip"))
        check("manajer dasbor kolam 6", text(page, "#dKolam").strip() == "6")
        check("manajer dasbor tangkapan 850 kg", text(page, "#dTangkapanKg").strip() == "850 kg")
        check("manajer dasbor nilai 29.525.000", "29.525.000" in text(page, "#dNilai"))
        check("manajer dasbor laba 24.615.000", "24.615.000" in text(page, "#dLaba"))
        check("manajer dasbor biaya 4.910.000", "4.910.000" in text(page, "#dBiaya"))
        check("manajer tidak melihat kartu kelola pengguna", not visible(page, "#cardPengguna"))
        tab(page, "kolam")
        check("manajer bisa melihat form tambah kolam", visible(page, "#panel-kolam .hanya-kelola"))
        logout(page)

        # ---------- C. Admin baseline + CRUD ----------
        login(page, "admin", "admin123")
        check("admin masuk", not visible(page, "#loginOverlay"))
        check("admin dasbor kolam 6", text(page, "#dKolam").strip() == "6")
        check("admin dasbor tangkapan 850 kg", text(page, "#dTangkapanKg").strip() == "850 kg")
        check("admin dasbor nilai 29.525.000", "29.525.000" in text(page, "#dNilai"))
        check("admin dasbor laba 24.615.000", "24.615.000" in text(page, "#dLaba"))
        check("admin dasbor pakan hari ini 4 (100 kg)", text(page, "#dPakanHariIni").strip() == "4" and "100 kg" in text(page, "#dPakanHariIniSub"))
        check("admin dasbor stok menipis 2", text(page, "#dStokMenipis").strip() == "2")
        check("admin dasbor biaya 4.910.000", "4.910.000" in text(page, "#dBiaya"))
        check("admin dasbor nilai stok 4.875.000", "4.875.000" in text(page, "#dNilaiStok"))
        check("admin dasbor perhatian ada Kolam Gurame D lewat", "Kolam Gurame D" in text(page, "#daftarJadwalPerhatian"))
        check("admin dasbor stok menipis ada Pelet Udang", "Pelet Udang" in text(page, "#daftarStokMenipis"))
        check("admin dasbor tangkapan terbaru ada Panen udang", "Panen udang" in text(page, "#daftarTangkapanTerbaru"))
        check("admin melihat kartu kelola pengguna", visible(page, "#cardPengguna"))
        check("admin melihat 3 pengguna", text(page, "#daftarPengguna").count("@") == 3)

        # Kolam: tambah + hapus + tolak hapus K1
        tab(page, "kolam")
        check("kolam 6 (2700 m2, 42800 ekor)", "6 kolam/tambak" in text(page, "#ringkasanKolam") and "2.700 m" in text(page, "#ringkasanKolam") and "42.800 ekor" in text(page, "#ringkasanKolam"))
        page.fill("#klNama", "Kolam Uji")
        page.select_option("#klJenis", "Lele")
        page.fill("#klLuas", "100")
        page.fill("#klTebar", "1000")
        page.click("#btnTambahKolam")
        page.wait_for_timeout(300)
        check("tambah kolam -> 7 kolam", "7 kolam/tambak" in text(page, "#ringkasanKolam"))
        page.click("[data-hapus-kolam='7']")
        klik_modal_ya(page)
        check("hapus kolam uji -> 6 kolam", "6 kolam/tambak" in text(page, "#ringkasanKolam"))
        page.click("[data-hapus-kolam='1']")
        page.wait_for_timeout(300)
        check("hapus kolam K1 ditolak (ada tangkapan)", "tidak bisa dihapus" in text(page, "#toast"))
        check("kolam tetap 6 setelah tolak", "6 kolam/tambak" in text(page, "#ringkasanKolam"))

        # Tangkapan: filter Nov + pratinjau nilai + tambah + hapus
        tab(page, "tangkapan")
        check("tangkapan 10 (850 kg, 29.525.000)", "10 tangkapan" in text(page, "#ringkasanTangkapan") and "850 kg" in text(page, "#ringkasanTangkapan") and "29.525.000" in text(page, "#ringkasanTangkapan"))
        page.select_option("#fBulanTangkapan", "2026-11")
        page.wait_for_timeout(300)
        check("tangkapan Nov 8 (735 kg, 24.160.000)", "8 tangkapan" in text(page, "#ringkasanTangkapan") and "735 kg" in text(page, "#ringkasanTangkapan") and "24.160.000" in text(page, "#ringkasanTangkapan"))
        page.select_option("#fBulanTangkapan", "semua")
        page.wait_for_timeout(300)
        page.fill("#tgKg", "10")
        page.fill("#tgHarga", "25000")
        page.wait_for_timeout(200)
        check("pratinjau nilai 10 kg x 25000 = 250.000", "250.000" in text(page, "#tgNilaiPratinjau"))
        page.fill("#tgKet", "Tangkapan Uji")
        page.click("#btnTambahTangkapan")
        page.wait_for_timeout(300)
        check("tambah tangkapan -> 11 (860 kg, 29.775.000)", "11 tangkapan" in text(page, "#ringkasanTangkapan") and "860 kg" in text(page, "#ringkasanTangkapan") and "29.775.000" in text(page, "#ringkasanTangkapan"))
        page.click("[data-hapus-tangkapan='11']")
        klik_modal_ya(page)
        check("hapus tangkapan uji -> 10 tangkapan", "10 tangkapan" in text(page, "#ringkasanTangkapan"))

        # Pakan: filter hari ini/segera/lewat + tambah + selesai + hapus
        tab(page, "pakan")
        check("pakan 12 jadwal (hari ini 4, segera 8, lewat 2)", "12 jadwal pakan" in text(page, "#ringkasanPakan") and "hari ini belum 4" in text(page, "#ringkasanPakan") and "segera 8" in text(page, "#ringkasanPakan") and "lewat 2" in text(page, "#ringkasanPakan"))
        page.select_option("#fPakan", "hariini")
        page.wait_for_timeout(300)
        check("pakan hari ini 4", "4 jadwal pakan" in text(page, "#ringkasanPakan"))
        page.select_option("#fPakan", "segera")
        page.wait_for_timeout(300)
        check("pakan segera 8", "8 jadwal pakan" in text(page, "#ringkasanPakan"))
        page.select_option("#fPakan", "lewat")
        page.wait_for_timeout(300)
        check("pakan lewat 2", "2 jadwal pakan" in text(page, "#ringkasanPakan"))
        check("pakan lewat ada Kolam Gurame D", "Kolam Gurame D" in text(page, "#daftarPakan"))
        page.select_option("#fPakan", "semua")
        page.wait_for_timeout(300)
        page.fill("#pkNama", "Pakan Uji")
        page.fill("#pkKg", "10")
        page.click("#btnTambahPakan")
        page.wait_for_timeout(300)
        check("tambah pakan -> 13 jadwal", "13 jadwal pakan" in text(page, "#ringkasanPakan"))
        page.click("[data-pakan-selesai='13']")
        page.wait_for_timeout(300)
        check("pakan uji ditandai sudah diberi", "Sudah Diberi" in text(page, "#daftarPakan"))
        page.click("[data-hapus-pakan='13']")
        klik_modal_ya(page)
        check("hapus pakan uji -> 12 jadwal", "12 jadwal pakan" in text(page, "#ringkasanPakan"))

        # Stok: baseline + tambah + keluar melebihi stok ditolak + masuk/keluar + hapus
        tab(page, "stok")
        check("stok 6 item nilai 4.875.000 menipis 2", "6 item stok pakan" in text(page, "#ringkasanStok") and "4.875.000" in text(page, "#ringkasanStok") and "menipis 2" in text(page, "#ringkasanStok"))
        check("riwayat stok 4 pergerakan", "4 pergerakan stok" in text(page, "#ringkasanRiwayatStok"))
        page.fill("#stNama", "Stok Uji")
        page.fill("#stJumlah", "10")
        page.fill("#stMin", "5")
        page.fill("#stHarga", "1000")
        page.click("#btnTambahStok")
        page.wait_for_timeout(300)
        check("tambah stok -> 7 item", "7 item stok pakan" in text(page, "#ringkasanStok"))
        page.select_option("#gsStok", "3")
        page.select_option("#gsJenis", "Keluar")
        page.fill("#gsJumlah", "200")
        page.click("#btnSimpanGerak")
        page.wait_for_timeout(300)
        check("keluar 200 kg Pelet Udang ditolak (stok 45)", "tidak mencukupi" in text(page, "#toast"))
        page.select_option("#gsJenis", "Masuk")
        page.fill("#gsJumlah", "10")
        page.click("#btnSimpanGerak")
        page.wait_for_timeout(300)
        check("masuk 10 kg Pelet Udang -> menipis 1", "menipis 1" in text(page, "#ringkasanStok"))
        page.select_option("#gsJenis", "Keluar")
        page.fill("#gsJumlah", "10")
        page.click("#btnSimpanGerak")
        page.wait_for_timeout(300)
        check("keluar 10 kg Pelet Udang -> menipis 2 lagi", "menipis 2" in text(page, "#ringkasanStok"))
        check("riwayat stok jadi 6 pergerakan", "6 pergerakan stok" in text(page, "#ringkasanRiwayatStok"))
        page.click("[data-hapus-stok='7']")
        klik_modal_ya(page)
        check("hapus stok uji -> 6 item", "6 item stok pakan" in text(page, "#ringkasanStok"))
        page.click("[data-hapus-stok='1']")
        page.wait_for_timeout(300)
        check("hapus stok Pelet Lele ditolak (ada riwayat)", "tidak bisa dihapus" in text(page, "#toast"))
        check("stok tetap 6 setelah tolak", "6 item stok pakan" in text(page, "#ringkasanStok"))

        # Biaya: filter Nov + tambah + hapus
        tab(page, "biaya")
        page.select_option("#fBulanBiaya", "2026-11")
        page.wait_for_timeout(300)
        check("biaya Nov 8 catatan 4.300.000", "8 catatan biaya" in text(page, "#ringkasanBiaya") and "4.300.000" in text(page, "#ringkasanBiaya"))
        page.select_option("#fBulanBiaya", "semua")
        page.wait_for_timeout(300)
        check("biaya semua 10 catatan 4.910.000", "10 catatan biaya" in text(page, "#ringkasanBiaya") and "4.910.000" in text(page, "#ringkasanBiaya"))
        page.fill("#bKeterangan", "Biaya Uji")
        page.fill("#bJumlah", "500000")
        page.click("#btnTambahBiaya")
        page.wait_for_timeout(300)
        check("tambah biaya -> 11 catatan 5.410.000", "11 catatan biaya" in text(page, "#ringkasanBiaya") and "5.410.000" in text(page, "#ringkasanBiaya"))
        page.click("[data-hapus-biaya='11']")
        klik_modal_ya(page)
        check("hapus biaya uji -> 10 catatan", "10 catatan biaya" in text(page, "#ringkasanBiaya"))

        # Laporan + CSV Nov
        tab(page, "laporan")
        check("laporan per kolam K1 laba 3.650.000", "3.650.000" in text(page, "#tabelPerKolam"))
        check("laporan per kolam K3 laba 7.715.000", "7.715.000" in text(page, "#tabelPerKolam"))
        check("laporan per jenis Udang Vaname 105 kg 8.925.000", "105" in text(page, "#tabelPerJenis") and "8.925.000" in text(page, "#tabelPerJenis"))
        check("laporan per bulan Nov laba 19.860.000", "19.860.000" in text(page, "#tabelPerBulan"))
        check("laporan per bulan Okt laba 4.755.000", "4.755.000" in text(page, "#tabelPerBulan"))
        check("laporan kategori Pakan 4.360.000", "4.360.000" in text(page, "#tabelKatBiaya"))
        check("laporan kategori Perawatan 400.000", "400.000" in text(page, "#tabelKatBiaya"))
        page.select_option("#fBulanLaporan", "2026-11")
        page.wait_for_timeout(200)
        with page.expect_download() as dl:
            page.click("#btnCsvLaporan")
        csv_nov = Path(dl.value.path()).read_text(encoding="utf-8")
        baris_nov = [b for b in csv_nov.strip().split("\n")]
        check("CSV Nov 16 baris + header", len(baris_nov) == 17, f"dapat {len(baris_nov)}")
        check("CSV Nov berisi Pelet lele 100 kg", "Pelet lele 100 kg" in csv_nov)
        page.select_option("#fBulanLaporan", "semua")
        page.wait_for_timeout(200)
        with page.expect_download() as dl2:
            page.click("#btnCsvLaporan")
        csv_semua = Path(dl2.value.path()).read_text(encoding="utf-8")
        baris_semua = [b for b in csv_semua.strip().split("\n")]
        check("CSV semua 20 baris + header", len(baris_semua) == 21, f"dapat {len(baris_semua)}")

        # ---------- D. RESTORE-TEST + backup/reset/restore ----------
        tab(page, "biaya")
        page.fill("#bKeterangan", "RESTORE-TEST")
        page.fill("#bJumlah", "123456")
        page.click("#btnTambahBiaya")
        page.wait_for_timeout(300)
        check("RESTORE-TEST tercatat", "RESTORE-TEST" in text(page, "#daftarBiaya"))
        tab(page, "laporan")
        with page.expect_download() as dl3:
            page.click("#btnBackup")
        backup_path = dl3.value.path()
        backup = json.loads(Path(backup_path).read_text(encoding="utf-8"))
        check("backup berisi RESTORE-TEST", any(b.get("keterangan") == "RESTORE-TEST" for b in backup["state"]["biaya"]))
        check("backup berisi 6 kolam", len(backup["state"]["kolam"]) == 6)
        page.click("#btnResetData")
        klik_modal_ya(page)
        check("reset kembalikan biaya 4.910.000", "4.910.000" in text(page, "#ringkasanLaporan"))
        Path("/tmp/fishery_tidak_valid.json").write_text("bukan json", encoding="utf-8")
        page.set_input_files("#inputRestore", "/tmp/fishery_tidak_valid.json")
        page.wait_for_timeout(500)
        check("restore file tidak valid ditolak", "tidak valid" in text(page, "#toast"))
        check("data tetap seed setelah restore gagal", "4.910.000" in text(page, "#ringkasanLaporan"))
        page.set_input_files("#inputRestore", backup_path)
        page.wait_for_timeout(500)
        check("restore backup berhasil", "berhasil dipulihkan" in text(page, "#toast"))
        check("setelah restore biaya 5.033.456", "5.033.456" in text(page, "#ringkasanLaporan"))
        tab(page, "biaya")
        page.click("[data-hapus-biaya='12']")
        klik_modal_ya(page)
        check("hapus RESTORE-TEST -> biaya 4.910.000", "4.910.000" in text(page, "#ringkasanBiaya"))

        # ---------- E. Reset sandi nelayan oleh admin ----------
        tab(page, "dashboard")
        page.click("[data-reset='nelayan']")
        klik_modal_ya(page)
        logout(page)
        login(page, "nelayan", "bk123")
        check("nelayan masuk dengan bk123", not visible(page, "#loginOverlay"))
        tab(page, "dashboard")
        page.fill("#sandiLama", "bk123")
        page.fill("#sandiBaru", "nelayan123")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        check("nelayan kembalikan sandi ke nelayan123", "berhasil diubah" in text(page, "#pesanSandi"))
        logout(page)
        login(page, "admin", "admin123")
        check("admin masuk lagi, ganti sandi admin round-trip", not visible(page, "#loginOverlay"))
        tab(page, "dashboard")
        page.fill("#sandiLama", "admin123")
        page.fill("#sandiBaru", "admin456")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        check("admin ganti sandi berhasil", "berhasil diubah" in text(page, "#pesanSandi"))
        logout(page)
        login(page, "admin", "admin456")
        check("admin masuk dengan sandi baru", not visible(page, "#loginOverlay"))
        tab(page, "dashboard")
        page.fill("#sandiLama", "admin456")
        page.fill("#sandiBaru", "admin123")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        check("admin kembalikan sandi", "berhasil diubah" in text(page, "#pesanSandi"))

        # ---------- Ringkasan ----------
        print(f"\nLolos: {passed} | Gagal: {len(failures)}")
        if failures:
            print("GAGAL:", failures)
        print("Console errors:", console_errors)
        print("Page errors:", page_errors)
        check("tidak ada console error", len(console_errors) == 0, str(console_errors[:3]))
        check("tidak ada page error", len(page_errors) == 0, str(page_errors[:3]))
        browser.close()
        return len(failures) == 0


if __name__ == "__main__":
    ok = main()
    raise SystemExit(0 if ok else 1)
