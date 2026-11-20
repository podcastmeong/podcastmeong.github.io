"""Tes Livestock Management (Peternakan) (file lokal, Playwright Chromium).
Hari ini 2026-11-20. Data seed (tanggal relatif) — diuji silang Python (/tmp/cek_livestock.py):
  Ternak 6 kelompok: total 995 ekor (sehat 971, sakit 19, mati 5).
    Per jenis: Ayam 800 (781/15/4), Sapi 20 (19/1/0), Kambing 25 (24/1/0), Bebek 150 (147/2/1).
    Peternak (T4+T5): 33 ekor (sehat 32, sakit 1, mati 0); pakan hari ini belum 0; vaksin 2 (lewat 1, selesai 1).
  Pakan 12 entri: hari ini belum 4 (165 kg), segera 8, lewat 2, sudah diberi 2.
  Vaksin 7 entri: segera 4, lewat 1, sudah divaksin 2.
  Kesehatan 10 catatan: Sakit 19 ekor, Pulih 9 ekor, Mati 5 ekor (konsisten dengan jumlah sakit/mati).
  Biaya 15 entri, total Rp7.375.000.
    Per kategori: Pakan 5.525.000, Obat 600.000, Vaksin 950.000, Perawatan 300.000.
    Per kelompok: T1 1.400.000, T2 1.130.000, T3 1.750.000, T4 1.750.000, T5 495.000, T6 850.000.
    Per bulan: Nov 13 entri Rp6.075.000; Okt 2 entri Rp1.300.000.
    Peternak: Rp1.795.000 (4 catatan); Manajer: Rp5.580.000 (11 catatan).
  RESTORE-TEST: biaya "RESTORE-TEST" Rp123.456 -> total biaya 7.498.456.
Urutan tes: label + login salah, A peternak (baseline + peran + ganti sandi),
  B manajer (baseline + bisa kelola, tidak bisa kelola pengguna),
  C admin (baseline + ternak + pakan + vaksin + kesehatan + biaya + laporan + CSV),
  D admin (RESTORE-TEST + backup/reset/restore + file tidak valid + hapus),
  E admin (reset sandi peternak -> login bk123 -> kembalikan peternak123).
"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = "file://" + str(ROOT / "livestock-management" / "index.html")

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
        check("hero bertuliskan Livestock Management", "Livestock Management" in text(page, ".hero"))
        check("login menampilkan 3 akun demo", "admin / admin123" in text(page, ".login-note") and "manajer / manajer123" in text(page, ".login-note") and "peternak / peternak123" in text(page, ".login-note"))
        login(page, "admin", "salah123")
        check("login salah ditolak", visible(page, "#loginError"))
        check("overlay login masih tampil setelah login salah", visible(page, "#loginOverlay"))

        # ---------- A. Peternak ----------
        login(page, "peternak", "peternak123")
        check("peternak masuk, overlay hilang", not visible(page, "#loginOverlay"))
        check("peternak mendarat di dasbor", "active" in (page.query_selector("#panel-dashboard").get_attribute("class") or ""))
        check("chip pengguna peternak", "Budi Santoso (Peternak)" in text(page, "#userChip"))
        check("peternak dasbor ekor 33", text(page, "#dEkor").strip() == "33")
        check("peternak dasbor sehat 32", text(page, "#dSehat").strip() == "32")
        check("peternak dasbor sakit 1", text(page, "#dSakit").strip() == "1")
        check("peternak dasbor mati 0", text(page, "#dMati").strip() == "0")
        check("peternak dasbor pakan hari ini 0", text(page, "#dPakanHariIni").strip() == "0")
        check("peternak dasbor vaksin segera 0", text(page, "#dVaksinSegera").strip() == "0")
        check("peternak dasbor vaksin lewat 1", text(page, "#dVaksinLewat").strip() == "1")
        check("peternak dasbor biaya 1.795.000", "1.795.000" in text(page, "#dBiaya"))
        check("peternak dasbor biaya sub milik Anda", "milik Anda" in text(page, "#dBiayaSub"))
        check("peternak tidak melihat kartu kelola pengguna", not visible(page, "#cardPengguna"))
        tab(page, "ternak")
        check("peternak form tambah ternak tersembunyi", not visible(page, "#panel-ternak .hanya-kelola"))
        check("peternak melihat 2 kelompok 33 ekor", "2 kelompok" in text(page, "#ringkasanTernak") and "33 ekor" in text(page, "#ringkasanTernak"))
        tab(page, "pakan")
        check("peternak pilihan pakan hanya 2 kelompok miliknya", len(page.query_selector_all("#pkTernak option")) == 2)
        check("peternak melihat 3 jadwal pakan miliknya", "3 jadwal pakan" in text(page, "#ringkasanPakan"))
        tab(page, "vaksin")
        check("peternak form tambah vaksin tersembunyi", not visible(page, "#panel-vaksin .hanya-kelola"))
        check("peternak melihat 2 jadwal vaksin (lewat 1, selesai 1)", "2 jadwal vaksin" in text(page, "#ringkasanVaksin") and "lewat 1" in text(page, "#ringkasanVaksin") and "sudah divaksin 1" in text(page, "#ringkasanVaksin"))
        tab(page, "kesehatan")
        check("peternak pilihan kesehatan hanya 2 kelompok miliknya", len(page.query_selector_all("#kTernak option")) == 2)
        check("peternak melihat 1 catatan kesehatan", "1 catatan kesehatan" in text(page, "#ringkasanKesehatan"))
        tab(page, "biaya")
        check("peternak daftar biaya hanya miliknya (4 catatan)", "4 catatan biaya" in text(page, "#ringkasanBiaya") and "1.795.000" in text(page, "#ringkasanBiaya"))
        # ganti sandi round-trip
        tab(page, "dashboard")
        page.fill("#sandiLama", "peternak123")
        page.fill("#sandiBaru", "peternak456")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        check("peternak ganti sandi berhasil", "berhasil diubah" in text(page, "#pesanSandi"))
        logout(page)
        login(page, "peternak", "peternak456")
        check("peternak masuk dengan sandi baru", not visible(page, "#loginOverlay"))
        tab(page, "dashboard")
        page.fill("#sandiLama", "peternak456")
        page.fill("#sandiBaru", "peternak123")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        check("peternak kembalikan sandi", "berhasil diubah" in text(page, "#pesanSandi"))
        logout(page)

        # ---------- B. Manajer ----------
        login(page, "manajer", "manajer123")
        check("manajer masuk", not visible(page, "#loginOverlay"))
        check("chip pengguna manajer", "Dedi Kurniawan (Manajer)" in text(page, "#userChip"))
        check("manajer dasbor ekor 995", text(page, "#dEkor").strip() == "995")
        check("manajer dasbor sehat 971", text(page, "#dSehat").strip() == "971")
        check("manajer dasbor sakit 19", text(page, "#dSakit").strip() == "19")
        check("manajer dasbor mati 5", text(page, "#dMati").strip() == "5")
        check("manajer dasbor biaya 7.375.000", "7.375.000" in text(page, "#dBiaya"))
        check("manajer tidak melihat kartu kelola pengguna", not visible(page, "#cardPengguna"))
        tab(page, "ternak")
        check("manajer bisa melihat form tambah ternak", visible(page, "#panel-ternak .hanya-kelola"))
        logout(page)

        # ---------- C. Admin baseline + CRUD ----------
        login(page, "admin", "admin123")
        check("admin masuk", not visible(page, "#loginOverlay"))
        check("admin dasbor ekor 995", text(page, "#dEkor").strip() == "995")
        check("admin dasbor sehat 971", text(page, "#dSehat").strip() == "971")
        check("admin dasbor sakit 19", text(page, "#dSakit").strip() == "19")
        check("admin dasbor mati 5", text(page, "#dMati").strip() == "5")
        check("admin dasbor pakan hari ini 4 (165 kg)", text(page, "#dPakanHariIni").strip() == "4" and "165 kg" in text(page, "#dPakanHariIniSub"))
        check("admin dasbor vaksin segera 4", text(page, "#dVaksinSegera").strip() == "4")
        check("admin dasbor vaksin lewat 1", text(page, "#dVaksinLewat").strip() == "1")
        check("admin dasbor biaya 7.375.000", "7.375.000" in text(page, "#dBiaya"))
        check("admin dasbor perhatian ada Vaksin PMK", "Vaksin PMK" in text(page, "#daftarJadwalPerhatian"))
        check("admin dasbor perhatian ada Vaksin Enterotoksemia lewat", "Enterotoksemia" in text(page, "#daftarJadwalPerhatian"))
        check("admin dasbor kelompok sakit Broiler 12 ekor", "12 ekor sakit" in text(page, "#daftarKelompokSakit"))
        check("admin dasbor biaya kategori Pakan 5.525.000", "5.525.000" in text(page, "#daftarBiayaKategori"))
        check("admin melihat kartu kelola pengguna", visible(page, "#cardPengguna"))
        check("admin melihat 3 pengguna", text(page, "#daftarPengguna").count("@") == 3)

        # Ternak: tambah + hapus + tolak hapus T1
        tab(page, "ternak")
        check("ternak 6 kelompok 995 ekor", "6 kelompok" in text(page, "#ringkasanTernak") and "995 ekor" in text(page, "#ringkasanTernak"))
        page.fill("#trNama", "Ternak Uji")
        page.select_option("#trJenis", "Ayam")
        page.fill("#trJumlah", "100")
        page.fill("#trUmur", "10")
        page.fill("#trKandang", "Kandang Uji")
        page.click("#btnTambahTernak")
        page.wait_for_timeout(300)
        check("tambah ternak -> 7 kelompok 1095 ekor", "7 kelompok" in text(page, "#ringkasanTernak") and "1095 ekor" in text(page, "#ringkasanTernak"))
        page.click("[data-hapus-ternak='7']")
        klik_modal_ya(page)
        check("hapus ternak uji -> 6 kelompok", "6 kelompok" in text(page, "#ringkasanTernak"))
        page.click("[data-hapus-ternak='1']")
        page.wait_for_timeout(300)
        check("hapus ternak T1 ditolak (ada pakan)", "tidak bisa dihapus" in text(page, "#toast"))
        check("ternak tetap 6 setelah tolak", "6 kelompok" in text(page, "#ringkasanTernak"))

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
        check("pakan lewat ada Sapi Potong", "Sapi Potong" in text(page, "#daftarPakan"))
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

        # Vaksin: filter segera/lewat + tambah + selesai + hapus
        tab(page, "vaksin")
        check("vaksin 7 jadwal (segera 4, lewat 1)", "7 jadwal vaksin" in text(page, "#ringkasanVaksin") and "segera 4" in text(page, "#ringkasanVaksin") and "lewat 1" in text(page, "#ringkasanVaksin"))
        page.select_option("#fVaksin", "segera")
        page.wait_for_timeout(300)
        check("vaksin segera 4", "4 jadwal vaksin" in text(page, "#ringkasanVaksin"))
        check("vaksin segera ada Vaksin PMK", "Vaksin PMK" in text(page, "#daftarVaksin"))
        page.select_option("#fVaksin", "lewat")
        page.wait_for_timeout(300)
        check("vaksin lewat 1", "1 jadwal vaksin" in text(page, "#ringkasanVaksin"))
        check("vaksin lewat ada Enterotoksemia", "Enterotoksemia" in text(page, "#daftarVaksin"))
        page.select_option("#fVaksin", "semua")
        page.wait_for_timeout(300)
        page.fill("#vNama", "Vaksin Uji")
        page.click("#btnTambahVaksin")
        page.wait_for_timeout(300)
        check("tambah vaksin -> 8 jadwal", "8 jadwal vaksin" in text(page, "#ringkasanVaksin"))
        page.click("[data-vaksin-selesai='8']")
        page.wait_for_timeout(300)
        check("vaksin uji ditandai sudah divaksin", "Sudah Divaksin" in text(page, "#daftarVaksin"))
        page.click("[data-hapus-vaksin='8']")
        klik_modal_ya(page)
        check("hapus vaksin uji -> 7 jadwal", "7 jadwal vaksin" in text(page, "#ringkasanVaksin"))

        # Kesehatan: baseline + validasi + tambah sakit (jumlah ikut berubah) + hapus kembali
        tab(page, "kesehatan")
        check("kesehatan 10 catatan (sakit 19, pulih 9, mati 5)", "10 catatan kesehatan" in text(page, "#ringkasanKesehatan") and "sakit 19 ekor" in text(page, "#ringkasanKesehatan") and "pulih 9 ekor" in text(page, "#ringkasanKesehatan") and "mati 5 ekor" in text(page, "#ringkasanKesehatan"))
        page.select_option("#kTernak", "1")
        page.fill("#kGejala", "Sakit Uji Terlalu Banyak")
        page.fill("#kJumlah", "600")
        page.click("#btnTambahKesehatan")
        page.wait_for_timeout(300)
        check("sakit 600 ekor ditolak (melebihi sehat)", "melebihi ternak sehat" in text(page, "#toast"))
        page.select_option("#kStatus", "Pulih")
        page.fill("#kGejala", "Pulih Uji Terlalu Banyak")
        page.fill("#kJumlah", "20")
        page.click("#btnTambahKesehatan")
        page.wait_for_timeout(300)
        check("pulih 20 ekor ditolak (melebihi sakit)", "melebihi ternak sakit" in text(page, "#toast"))
        check("kesehatan tetap 10 setelah tolak", "10 catatan kesehatan" in text(page, "#ringkasanKesehatan"))
        page.select_option("#kTernak", "2")
        page.select_option("#kStatus", "Sakit")
        page.fill("#kGejala", "Ayam lesu uji")
        page.fill("#kObat", "Vitamin uji")
        page.fill("#kJumlah", "5")
        page.click("#btnTambahKesehatan")
        page.wait_for_timeout(300)
        check("tambah sakit 5 ekor T2 -> 11 catatan", "11 catatan kesehatan" in text(page, "#ringkasanKesehatan") and "sakit 24 ekor" in text(page, "#ringkasanKesehatan"))
        tab(page, "dashboard")
        check("setelah sakit +5: sakit 24, sehat 966", text(page, "#dSakit").strip() == "24" and text(page, "#dSehat").strip() == "966")
        tab(page, "kesehatan")
        page.click("[data-hapus-kes='11']")
        klik_modal_ya(page)
        check("hapus catatan sakit uji -> 10 catatan, sakit 19", "10 catatan kesehatan" in text(page, "#ringkasanKesehatan") and "sakit 19 ekor" in text(page, "#ringkasanKesehatan"))
        tab(page, "dashboard")
        check("setelah hapus: sakit 19, sehat 971", text(page, "#dSakit").strip() == "19" and text(page, "#dSehat").strip() == "971")

        # Biaya: filter Nov + tambah + hapus
        tab(page, "biaya")
        page.select_option("#fBulanBiaya", "2026-11")
        page.wait_for_timeout(300)
        check("biaya Nov 13 catatan 6.075.000", "13 catatan biaya" in text(page, "#ringkasanBiaya") and "6.075.000" in text(page, "#ringkasanBiaya"))
        page.select_option("#fBulanBiaya", "semua")
        page.wait_for_timeout(300)
        check("biaya semua 15 catatan 7.375.000", "15 catatan biaya" in text(page, "#ringkasanBiaya") and "7.375.000" in text(page, "#ringkasanBiaya"))
        page.fill("#bKeterangan", "Biaya Uji")
        page.fill("#bJumlah", "500000")
        page.click("#btnTambahBiaya")
        page.wait_for_timeout(300)
        check("tambah biaya -> 16 catatan 7.875.000", "16 catatan biaya" in text(page, "#ringkasanBiaya") and "7.875.000" in text(page, "#ringkasanBiaya"))
        page.click("[data-hapus-biaya='16']")
        klik_modal_ya(page)
        check("hapus biaya uji -> 15 catatan", "15 catatan biaya" in text(page, "#ringkasanBiaya"))

        # Laporan + CSV Nov
        tab(page, "laporan")
        check("laporan per jenis Ayam 800/781/15/4", "800" in text(page, "#tabelPerJenis") and "781" in text(page, "#tabelPerJenis"))
        check("laporan per jenis Bebek 150 ekor", "150" in text(page, "#tabelPerJenis"))
        check("laporan per kelompok T1 biaya 1.400.000", "1.400.000" in text(page, "#tabelPerKelompok"))
        check("laporan per kelompok T5 biaya 495.000", "495.000" in text(page, "#tabelPerKelompok"))
        check("laporan per bulan Nov 6.075.000 (13)", "6.075.000" in text(page, "#tabelPerBulan"))
        check("laporan per bulan Okt 1.300.000 (2)", "1.300.000" in text(page, "#tabelPerBulan"))
        check("laporan kategori Pakan 5.525.000", "5.525.000" in text(page, "#tabelKatBiaya"))
        check("laporan kategori Vaksin 950.000", "950.000" in text(page, "#tabelKatBiaya"))
        page.select_option("#fBulanLaporan", "2026-11")
        page.wait_for_timeout(200)
        with page.expect_download() as dl:
            page.click("#btnCsvLaporan")
        csv_nov = Path(dl.value.path()).read_text(encoding="utf-8")
        baris_nov = [b for b in csv_nov.strip().split("\n")]
        check("CSV Nov 19 baris + header", len(baris_nov) == 20, f"dapat {len(baris_nov)}")
        check("CSV Nov berisi Pakan broiler 50 kg", "Pakan broiler 50 kg" in csv_nov)
        page.select_option("#fBulanLaporan", "semua")
        page.wait_for_timeout(200)
        with page.expect_download() as dl2:
            page.click("#btnCsvLaporan")
        csv_semua = Path(dl2.value.path()).read_text(encoding="utf-8")
        baris_semua = [b for b in csv_semua.strip().split("\n")]
        check("CSV semua 21 baris + header", len(baris_semua) == 22, f"dapat {len(baris_semua)}")

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
        check("backup berisi 6 kelompok ternak", len(backup["state"]["ternak"]) == 6)
        page.click("#btnResetData")
        klik_modal_ya(page)
        check("reset kembalikan biaya 7.375.000", "7.375.000" in text(page, "#ringkasanLaporan"))
        Path("/tmp/livestock_tidak_valid.json").write_text("bukan json", encoding="utf-8")
        page.set_input_files("#inputRestore", "/tmp/livestock_tidak_valid.json")
        page.wait_for_timeout(500)
        check("restore file tidak valid ditolak", "tidak valid" in text(page, "#toast"))
        check("data tetap seed setelah restore gagal", "7.375.000" in text(page, "#ringkasanLaporan"))
        page.set_input_files("#inputRestore", backup_path)
        page.wait_for_timeout(500)
        check("restore backup berhasil", "berhasil dipulihkan" in text(page, "#toast"))
        check("setelah restore biaya 7.498.456", "7.498.456" in text(page, "#ringkasanLaporan"))
        tab(page, "biaya")
        page.click("[data-hapus-biaya='17']")
        klik_modal_ya(page)
        check("hapus RESTORE-TEST -> biaya 7.375.000", "7.375.000" in text(page, "#ringkasanBiaya"))

        # ---------- E. Reset sandi peternak oleh admin ----------
        tab(page, "dashboard")
        page.click("[data-reset='peternak']")
        klik_modal_ya(page)
        logout(page)
        login(page, "peternak", "bk123")
        check("peternak masuk dengan bk123", not visible(page, "#loginOverlay"))
        tab(page, "dashboard")
        page.fill("#sandiLama", "bk123")
        page.fill("#sandiBaru", "peternak123")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        check("peternak kembalikan sandi ke peternak123", "berhasil diubah" in text(page, "#pesanSandi"))
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
