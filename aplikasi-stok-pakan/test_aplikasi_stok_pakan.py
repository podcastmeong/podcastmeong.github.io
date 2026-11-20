"""Tes Aplikasi Stok Pakan (file lokal, Playwright Chromium).
Hari ini 2026-11-20. Data seed (tanggal relatif) — diuji silang Python (/tmp/cek_pakan.py):
  Pakan 7: P1 Pelet Ayam Starter 250 kg (min 100), P2 Jagung Giling 80 (min 100),
    P3 Konsentrat Sapi 0 (min 50), P4 Pelet Ikan Lele 45 (min 50),
    P5 Dedak Halus 320 (min 100), P6 Pelet Udang 120 (min 60), P7 Vitamin & Premix 15 (min 10).
  Nilai stok total Rp9.410.000. Menipis 2 (P2, P4), habis 1 (P3), peringatan 3.
  Peternak (P4, P5, P7): nilai Rp3.090.000, menipis 1 (P4), habis 0.
  Gerakan: masuk 7 (1.395 kg), keluar manual 3 (100 kg), keluar pemberian 13 (465 kg).
    Masuk total 1.395 kg, keluar total 565 kg.
  Biaya pembelian total Rp16.675.000 (Nov Rp7.175.000, Okt Rp9.500.000);
    biaya tambah Rp225.000 (Transport); total biaya Rp16.900.000 (Nov Rp7.250.000, Okt Rp9.650.000).
  Pemberian 17: sudah 13 (465 kg), belum 4; hari ini belum 2 (B5, B10);
    segera 4 (B5, B10, B12, B14); lewat 0.
    Peternak: 7 pemberian (sudah 5 = 155 kg, belum 2, hari ini 1).
  Per jenis: Ayam stok 330, nilai Rp3.680.000, masuk 500, keluar 170, beli Rp5.300.000.
    Sapi stok 320, nilai Rp1.920.000, masuk 520, keluar 200, beli Rp4.200.000.
    Ikan stok 165, nilai Rp3.135.000, masuk 350, keluar 185, beli Rp6.050.000.
    Lainnya stok 15, nilai Rp675.000, masuk 25, keluar 10, beli Rp1.125.000.
  Per bulan: Nov masuk 375 kg, keluar 545 kg, pemberian sudah 13, biaya Rp7.250.000.
    Okt masuk 1.020 kg, keluar 20 kg, pemberian sudah 0, biaya Rp9.650.000.
  CSV: semua 23 baris data + header (24 baris); Nov 18 baris + header (19 baris); Okt 5 + header (6 baris).
Bagian C mengubah data (pakan uji P8 masuk 50 keluar 10; biaya manual Rp200.000):
  Setelah C: jenis 8, nilai stok Rp9.930.000, total biaya Rp17.750.000,
    Ayam stok 370, beli Ayam Rp5.950.000, Nov masuk 425, keluar 555, biaya Nov Rp8.100.000,
    CSV Nov 20 baris + header (21), CSV semua 25 baris + header (26).
Urutan tes: label + login salah, A peternak (baseline + peran + ganti sandi),
  B manajer (baseline + bisa kelola, tidak bisa kelola pengguna),
  C admin (baseline + stok + pemberian + peringatan + biaya + laporan + CSV),
  D admin (RESTORE-TEST + backup/reset/restore + file tidak valid + hapus),
  E admin (reset sandi peternak -> login bk123 -> kembalikan peternak123).
"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = "file://" + str(ROOT / "aplikasi-stok-pakan" / "index.html")

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
        check("hero bertuliskan Aplikasi Stok Pakan", "Aplikasi Stok Pakan" in text(page, ".hero"))
        check("login menampilkan 3 akun demo", "admin / admin123" in text(page, ".login-note") and "manajer / manajer123" in text(page, ".login-note") and "peternak / peternak123" in text(page, ".login-note"))
        login(page, "admin", "salah123")
        check("login salah ditolak", visible(page, "#loginError"))
        check("overlay login masih tampil setelah login salah", visible(page, "#loginOverlay"))

        # ---------- A. Peternak ----------
        login(page, "peternak", "peternak123")
        check("peternak masuk, overlay hilang", not visible(page, "#loginOverlay"))
        check("peternak mendarat di dasbor", "active" in (page.query_selector("#panel-dashboard").get_attribute("class") or ""))
        check("chip pengguna peternak", "Budi Santoso (Peternak)" in text(page, "#userChip"))
        check("peternak dasbor jenis pakan 3", text(page, "#dPakan").strip() == "3")
        check("peternak dasbor nilai stok Rp3.090.000", text(page, "#dNilaiStok").strip() == "Rp3.090.000")
        check("peternak dasbor peringatan 1 (menipis 1)", text(page, "#dPeringatan").strip() == "1" and "1 menipis" in text(page, "#dPeringatanSub"))
        check("peternak dasbor pemberian hari ini 1", text(page, "#dPemberianHariIni").strip() == "1")
        check("peternak dasbor pemberian belum 2", text(page, "#dPemberianBelum").strip() == "2")
        check("peternak dasbor pemberian sudah 5 (155 kg)", text(page, "#dPemberianSudah").strip() == "5" and "155 kg" in text(page, "#dPemberianSudahSub"))
        check("peternak dasbor total biaya Rp5.250.000", text(page, "#dBiaya").strip() == "Rp5.250.000")
        check("peternak dasbor masuk 575 kg keluar 195 kg", text(page, "#dMasuk").strip() == "575" and "195 kg" in text(page, "#dMasukSub"))
        check("peternak dasbor peringatan ada Pelet Ikan Lele", "Pelet Ikan Lele" in text(page, "#daftarPeringatan"))
        check("peternak dasbor perhatian ada Lele Kolam 1", "Lele Kolam 1" in text(page, "#daftarPemberianPerhatian"))
        check("peternak melihat kartu ganti sandi sendiri", visible(page, "#cardSandiSaya"))
        check("peternak tidak melihat kartu kelola pengguna", not visible(page, "#cardPengguna"))
        tab(page, "stok")
        check("peternak form tambah pakan tersembunyi", not visible(page, "#panel-stok .hanya-kelola"))
        check("peternak pilihan pakan hanya 3 miliknya", len(page.query_selector_all("#msPakan option")) == 3)
        check("peternak melihat 3 jenis pakan nilai Rp3.090.000", "3 jenis pakan" in text(page, "#ringkasanPakan") and "Rp3.090.000" in text(page, "#ringkasanPakan"))
        check("peternak tidak melihat Pelet Ayam Starter", "Pelet Ayam Starter" not in text(page, "#daftarPakan"))
        tab(page, "pemberian")
        check("peternak melihat 7 jadwal (hari ini 1, sudah 5)", "7 jadwal pemberian" in text(page, "#ringkasanPemberian") and "hari ini belum 1" in text(page, "#ringkasanPemberian") and "sudah 5" in text(page, "#ringkasanPemberian"))
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
        check("manajer dasbor jenis pakan 7", text(page, "#dPakan").strip() == "7")
        check("manajer dasbor nilai stok Rp9.410.000", text(page, "#dNilaiStok").strip() == "Rp9.410.000")
        check("manajer dasbor peringatan 3 (habis 1 menipis 2)", text(page, "#dPeringatan").strip() == "3" and "1 habis" in text(page, "#dPeringatanSub") and "2 menipis" in text(page, "#dPeringatanSub"))
        check("manajer dasbor pemberian hari ini 2", text(page, "#dPemberianHariIni").strip() == "2")
        check("manajer dasbor pemberian belum 4", text(page, "#dPemberianBelum").strip() == "4")
        check("manajer dasbor pemberian sudah 13 (465 kg)", text(page, "#dPemberianSudah").strip() == "13" and "465 kg" in text(page, "#dPemberianSudahSub"))
        check("manajer dasbor total biaya Rp16.900.000", text(page, "#dBiaya").strip() == "Rp16.900.000")
        check("manajer dasbor masuk 1.395 kg keluar 565 kg", text(page, "#dMasuk").strip() == "1.395" and "565 kg" in text(page, "#dMasukSub"))
        check("manajer tidak melihat kartu kelola pengguna", not visible(page, "#cardPengguna"))
        tab(page, "stok")
        check("manajer bisa melihat form tambah pakan", visible(page, "#panel-stok .hanya-kelola"))
        logout(page)

        # ---------- C. Admin baseline + CRUD ----------
        login(page, "admin", "admin123")
        check("admin masuk", not visible(page, "#loginOverlay"))
        check("admin dasbor jenis pakan 7", text(page, "#dPakan").strip() == "7")
        check("admin dasbor nilai stok Rp9.410.000", text(page, "#dNilaiStok").strip() == "Rp9.410.000")
        check("admin dasbor peringatan 3", text(page, "#dPeringatan").strip() == "3")
        check("admin dasbor pemberian hari ini 2", text(page, "#dPemberianHariIni").strip() == "2")
        check("admin dasbor perhatian ada Ayam Petelur Kandang B", "Ayam Petelur Kandang B" in text(page, "#daftarPemberianPerhatian"))
        check("dasbor punya tombol aksi cepat Sudah Diberi", len(page.query_selector_all("#daftarPemberianPerhatian [data-pemberian-sudah]")) >= 1)
        check("admin dasbor peringatan ada Konsentrat Sapi", "Konsentrat Sapi" in text(page, "#daftarPeringatan"))
        check("admin melihat kartu kelola pengguna", visible(page, "#cardPengguna"))
        check("admin melihat 3 pengguna", text(page, "#daftarPengguna").count("@") == 3)

        # Stok: tambah jenis pakan + masuk + keluar ditolak + keluar ok + hapus ditolak
        tab(page, "stok")
        check("stok 7 jenis nilai Rp9.410.000", "7 jenis pakan" in text(page, "#ringkasanPakan") and "Rp9.410.000" in text(page, "#ringkasanPakan"))
        page.fill("#pkNama", "Pelet Ayam Finisher")
        page.select_option("#pkJenis", "Ayam")
        page.select_option("#pkSatuan", "kg")
        page.fill("#pkHarga", "13000")
        page.fill("#pkMinimum", "50")
        page.select_option("#pkPemilik", "manajer")
        page.click("#btnTambahPakan")
        page.wait_for_timeout(300)
        check("tambah pakan -> 8 jenis", "8 jenis pakan" in text(page, "#ringkasanPakan"))
        page.select_option("#msPakan", "8")
        page.wait_for_timeout(200)
        check("harga masuk terisi otomatis 13000", page.input_value("#msHarga") == "13000")
        page.fill("#msJumlah", "50")
        page.click("#btnMasukStok")
        page.wait_for_timeout(300)
        check("masuk stok P8 50 kg", "Pelet Ayam Finisher" in text(page, "#daftarPakan") and "50 kg" in text(page, "#daftarPakan"))
        page.select_option("#klPakan", "8")
        page.fill("#klJumlah", "60")
        page.click("#btnKeluarStok")
        page.wait_for_timeout(300)
        check("keluar 60 kg ditolak (stok hanya 50)", "tidak bisa keluar" in text(page, "#toast"))
        page.fill("#klJumlah", "10")
        page.select_option("#klAlasan", "Rusak")
        page.click("#btnKeluarStok")
        page.wait_for_timeout(300)
        check("keluar 10 kg -> stok P8 40 kg", "40 kg" in text(page, "#daftarPakan"))
        page.click("[data-hapus-pakan='1']")
        page.wait_for_timeout(300)
        check("hapus pakan P1 ditolak (ada riwayat)", "Tidak bisa hapus" in text(page, "#toast"))
        check("pakan tetap 8 setelah tolak", "8 jenis pakan" in text(page, "#ringkasanPakan"))

        # Pemberian: tambah + sudah (stok berkurang) + batalkan (stok kembali) + stok kurang ditolak + hapus
        tab(page, "pemberian")
        check("pemberian 17 (hari ini 2, segera 4, sudah 13)", "17 jadwal pemberian" in text(page, "#ringkasanPemberian") and "hari ini belum 2" in text(page, "#ringkasanPemberian") and "segera 4" in text(page, "#ringkasanPemberian") and "sudah 13" in text(page, "#ringkasanPemberian"))
        page.select_option("#pbPakan", "6")
        page.fill("#pbKelompok", "Udang Vaname Tambak 2")
        page.fill("#pbJumlah", "20")
        page.click("#btnTambahPemberian")
        page.wait_for_timeout(300)
        check("tambah pemberian -> 18 jadwal", "18 jadwal pemberian" in text(page, "#ringkasanPemberian"))
        page.click("#panel-pemberian [data-pemberian-sudah='18']")
        page.wait_for_timeout(300)
        check("pemberian uji sudah diberi", "Sudah Diberi" in text(page, "#daftarPemberian"))
        tab(page, "stok")
        check("stok Pelet Udang jadi 100 kg setelah pemberian", "Pelet Udang" in text(page, "#daftarPakan") and "100 kg" in text(page, "#daftarPakan"))
        tab(page, "pemberian")
        page.click("#panel-pemberian [data-pemberian-batal='18']")
        page.wait_for_timeout(300)
        tab(page, "stok")
        check("stok Pelet Udang kembali 120 kg setelah batalkan", "120 kg" in text(page, "#daftarPakan"))
        tab(page, "pemberian")
        page.select_option("#pbPakan", "3")
        page.fill("#pbKelompok", "Sapi Perah Uji")
        page.fill("#pbJumlah", "10")
        page.click("#btnTambahPemberian")
        page.wait_for_timeout(300)
        check("tambah pemberian P3 (stok 0) -> 19 jadwal", "19 jadwal pemberian" in text(page, "#ringkasanPemberian"))
        page.click("#panel-pemberian [data-pemberian-sudah='19']")
        page.wait_for_timeout(300)
        check("pemberian P3 ditolak (stok tidak cukup)", "tidak cukup" in text(page, "#toast"))
        page.click("#panel-pemberian [data-hapus-pemberian='19']")
        klik_modal_ya(page)
        check("hapus pemberian uji -> 18 jadwal", "18 jadwal pemberian" in text(page, "#ringkasanPemberian"))

        # Peringatan
        tab(page, "peringatan")
        check("peringatan menipis ada Jagung Giling dan Pelet Ikan Lele", "Jagung Giling" in text(page, "#daftarMenipis") and "Pelet Ikan Lele" in text(page, "#daftarMenipis"))
        check("peringatan habis ada Konsentrat Sapi", "Konsentrat Sapi" in text(page, "#daftarHabis"))
        check("tidak ada pemberian lewat tanggal", "Tidak ada jadwal pemberian yang lewat" in text(page, "#daftarPemberianLewat"))

        # Biaya: tambah biaya manual
        tab(page, "biaya")
        check("biaya total sebelum tambah Rp17.550.000 (termasuk masuk P8)", "Rp17.550.000" in text(page, "#ringkasanBiaya"))
        page.fill("#byNama", "Perawatan gudang")
        page.select_option("#byKategori", "Perawatan")
        page.fill("#byJumlah", "200000")
        page.click("#btnTambahBiaya")
        page.wait_for_timeout(300)
        check("tambah biaya -> total Rp17.750.000", "Rp17.750.000" in text(page, "#ringkasanBiaya"))
        check("biaya tambah ada Perawatan gudang", "Perawatan gudang" in text(page, "#daftarBiayaTambah"))

        # Laporan + CSV Nov + CSV semua
        tab(page, "laporan")
        check("laporan per jenis Pelet Ayam Starter 250 kg Rp3.000.000", "Pelet Ayam Starter" in text(page, "#tabelPerJenis") and "250 kg" in text(page, "#tabelPerJenis") and "Rp3.000.000" in text(page, "#tabelPerJenis"))
        check("laporan per jenis Pelet Ayam Finisher 40 kg Rp520.000", "Pelet Ayam Finisher" in text(page, "#tabelPerJenis") and "40 kg" in text(page, "#tabelPerJenis") and "Rp520.000" in text(page, "#tabelPerJenis"))
        check("laporan per bulan Nov masuk 425 keluar 555 biaya Rp8.100.000", "November 2026" in text(page, "#tabelPerBulan") and "425" in text(page, "#tabelPerBulan") and "555" in text(page, "#tabelPerBulan") and "Rp8.100.000" in text(page, "#tabelPerBulan"))
        check("laporan per bulan Okt biaya Rp9.650.000", "Oktober 2026" in text(page, "#tabelPerBulan") and "Rp9.650.000" in text(page, "#tabelPerBulan"))
        check("laporan kategori Pembelian Pakan Rp17.325.000", "Pembelian Pakan" in text(page, "#tabelKategoriBiaya") and "Rp17.325.000" in text(page, "#tabelKategoriBiaya"))
        check("laporan kategori Perawatan Rp200.000", "Perawatan" in text(page, "#tabelKategoriBiaya") and "Rp200.000" in text(page, "#tabelKategoriBiaya"))
        page.select_option("#fBulanLaporan", "2026-11")
        page.wait_for_timeout(200)
        with page.expect_download() as dl:
            page.click("#btnCsvLaporan")
        csv_nov = Path(dl.value.path()).read_text(encoding="utf-8")
        baris_nov = [b for b in csv_nov.strip().split("\n")]
        check("CSV Nov 20 baris + header", len(baris_nov) == 21, f"dapat {len(baris_nov)}")
        check("CSV Nov berisi Pelet Ayam Finisher", "Pelet Ayam Finisher" in csv_nov)
        page.select_option("#fBulanLaporan", "semua")
        page.wait_for_timeout(200)
        with page.expect_download() as dl2:
            page.click("#btnCsvLaporan")
        csv_semua = Path(dl2.value.path()).read_text(encoding="utf-8")
        baris_semua = [b for b in csv_semua.strip().split("\n")]
        check("CSV semua 25 baris + header", len(baris_semua) == 26, f"dapat {len(baris_semua)}")

        # ---------- D. RESTORE-TEST + backup/reset/restore ----------
        tab(page, "pemberian")
        page.click("#panel-pemberian [data-hapus-pemberian='18']")
        klik_modal_ya(page)
        check("hapus pemberian uji P6 -> 17 jadwal", "17 jadwal pemberian" in text(page, "#ringkasanPemberian"))
        page.select_option("#pbPakan", "1")
        page.fill("#pbKelompok", "RESTORE-TEST")
        page.fill("#pbJumlah", "5")
        page.click("#btnTambahPemberian")
        page.wait_for_timeout(300)
        check("RESTORE-TEST tercatat", "RESTORE-TEST" in text(page, "#daftarPemberian"))
        tab(page, "laporan")
        with page.expect_download() as dl3:
            page.click("#btnBackup")
        backup_path = dl3.value.path()
        backup = json.loads(Path(backup_path).read_text(encoding="utf-8"))
        check("backup berisi RESTORE-TEST", any(x.get("kelompok") == "RESTORE-TEST" for x in backup["state"]["pemberian"]))
        check("backup berisi 8 jenis pakan", len(backup["state"]["pakan"]) == 8)
        page.click("#btnResetData")
        klik_modal_ya(page)
        check("reset kembalikan 7 jenis pakan 17 pemberian", "7 jenis pakan" in text(page, "#ringkasanLaporan") and "17 jadwal pemberian" in text(page, "#ringkasanLaporan"))
        Path("/tmp/pakan_tidak_valid.json").write_text("bukan json", encoding="utf-8")
        page.set_input_files("#inputRestore", "/tmp/pakan_tidak_valid.json")
        page.wait_for_timeout(500)
        check("restore file tidak valid ditolak", "tidak valid" in text(page, "#toast"))
        check("data tetap seed setelah restore gagal", "7 jenis pakan" in text(page, "#ringkasanLaporan"))
        page.set_input_files("#inputRestore", backup_path)
        page.wait_for_timeout(500)
        check("restore backup berhasil", "berhasil dipulihkan" in text(page, "#toast"))
        check("setelah restore 18 jadwal pemberian", "18 jadwal pemberian" in text(page, "#ringkasanLaporan"))
        tab(page, "pemberian")
        page.click("#panel-pemberian [data-hapus-pemberian='20']")
        klik_modal_ya(page)
        check("hapus RESTORE-TEST -> 17 jadwal", "17 jadwal pemberian" in text(page, "#ringkasanPemberian"))

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
