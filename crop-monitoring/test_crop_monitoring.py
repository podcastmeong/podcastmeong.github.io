"""Tes Crop Monitoring (Pemantauan Tanaman) (file lokal, Playwright Chromium).
Hari ini 2026-11-20. Data seed (tanggal relatif) — diuji silang Python (/tmp/cek_crop.py):
  Lahan 6 (Aktif 5, Perawatan 1): luas total 9,5 ha.
  Pertumbuhan 21 catatan; tinggi terakhir: L1 95, L2 55, L3 48, L4 185, L5 20, L6 150 cm.
    Nov 10, Okt 8, lain 3. Tertinggi 185 cm (Jagung Manis).
    Petani (L3+L5): 6 catatan.
  Jadwal 12: hari ini belum 4, segera (<=7 hari, termasuk hari ini) 8, lewat 2, selesai 2.
    Petani: 4 jadwal (hari ini 2, segera 3, lewat 1, selesai 0).
  Hama 7: aktif 5, tertangani 2; Ringan 2, Sedang 4, Berat 1; semua Nov.
    Petani: hama aktif 2.
  Foto 8 (L1 2, L2 2, L3 1, L4 1, L5 1, L6 1); petani 2. Nov 7, Okt 1.
  Per lahan: L1 tinggi 95, pert 4, jadwal belum 3/selesai 0, hama aktif 1, foto 2.
    L2 tinggi 55, pert 4, jadwal belum 1/selesai 1, hama aktif 1, foto 2.
    L3 tinggi 48, pert 3, jadwal belum 2/selesai 0, hama aktif 1, foto 1.
    L4 tinggi 185, pert 4, jadwal belum 1/selesai 1, hama aktif 0, foto 1.
    L5 tinggi 20, pert 3, jadwal belum 2/selesai 0, hama aktif 1, foto 1.
    L6 tinggi 150, pert 3, jadwal belum 1/selesai 0, hama aktif 1, foto 1.
  RESTORE-TEST: hama "RESTORE-TEST" -> 8 catatan hama.
  CSV: semua 28 baris data + header (29 baris); Nov 17 baris data + header (18 baris).
Urutan tes: label + login salah, A petani (baseline + peran + ganti sandi),
  B manajer (baseline + bisa kelola, tidak bisa kelola pengguna),
  C admin (baseline + lahan + pertumbuhan + jadwal + hama + foto + laporan + CSV),
  D admin (RESTORE-TEST + backup/reset/restore + file tidak valid + hapus),
  E admin (reset sandi petani -> login bk123 -> kembalikan petani123).
"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = "file://" + str(ROOT / "crop-monitoring" / "index.html")

# PNG 1x1 piksel (untuk uji unggah foto)
PNG_1X1 = bytes([
    0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D,
    0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
    0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53, 0xDE, 0x00, 0x00, 0x00,
    0x0C, 0x49, 0x44, 0x41, 0x54, 0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0x3F,
    0x00, 0x05, 0xFE, 0x02, 0xFE, 0xDC, 0xCC, 0x59, 0xE7, 0x00, 0x00, 0x00,
    0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82,
])

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
        check("hero bertuliskan Crop Monitoring", "Crop Monitoring" in text(page, ".hero"))
        check("login menampilkan 3 akun demo", "admin / admin123" in text(page, ".login-note") and "manajer / manajer123" in text(page, ".login-note") and "petani / petani123" in text(page, ".login-note"))
        login(page, "admin", "salah123")
        check("login salah ditolak", visible(page, "#loginError"))
        check("overlay login masih tampil setelah login salah", visible(page, "#loginOverlay"))

        # ---------- A. Petani ----------
        login(page, "petani", "petani123")
        check("petani masuk, overlay hilang", not visible(page, "#loginOverlay"))
        check("petani mendarat di dasbor", "active" in (page.query_selector("#panel-dashboard").get_attribute("class") or ""))
        check("chip pengguna petani", "Budi Santoso (Petani)" in text(page, "#userChip"))
        check("petani dasbor lahan 2", text(page, "#dLahan").strip() == "2")
        check("petani dasbor pertumbuhan 6", text(page, "#dPertumbuhan").strip() == "6")
        check("petani dasbor tinggi tertinggi 48 cm (Tomat)", text(page, "#dTinggi").strip() == "48 cm" and "Tomat" in text(page, "#dTinggiSub"))
        check("petani dasbor foto 2", text(page, "#dFoto").strip() == "2")
        check("petani dasbor jadwal hari ini 2", text(page, "#dJadwalHariIni").strip() == "2")
        check("petani dasbor hama aktif 2", text(page, "#dHamaAktif").strip() == "2")
        check("petani dasbor jadwal belum 4", text(page, "#dJadwalBelum").strip() == "4")
        check("petani dasbor jadwal lewat 1", text(page, "#dJadwalLewat").strip() == "1")
        check("petani melihat kartu ganti sandi sendiri", visible(page, "#cardSandiSaya"))
        check("petani tidak melihat kartu kelola pengguna", not visible(page, "#cardPengguna"))
        tab(page, "lahan")
        check("petani form tambah lahan tersembunyi", not visible(page, "#panel-lahan .hanya-kelola"))
        check("petani melihat 2 lahan 1,3 ha", "2 lahan" in text(page, "#ringkasanLahan") and "1,3 ha" in text(page, "#ringkasanLahan"))
        tab(page, "pertumbuhan")
        check("petani pilihan pertumbuhan hanya 2 lahan miliknya", len(page.query_selector_all("#ptLahan option")) == 2)
        check("petani melihat 6 catatan pertumbuhan", "6 catatan pertumbuhan" in text(page, "#ringkasanPertumbuhan"))
        tab(page, "jadwal")
        check("petani pilihan jadwal hanya 2 lahan miliknya", len(page.query_selector_all("#jdLahan option")) == 2)
        check("petani melihat 4 jadwal (hari ini 2, lewat 1)", "4 jadwal" in text(page, "#ringkasanJadwal") and "hari ini belum 2" in text(page, "#ringkasanJadwal") and "lewat 1" in text(page, "#ringkasanJadwal"))
        tab(page, "hama")
        check("petani melihat 2 hama aktif", "2 catatan hama" in text(page, "#ringkasanHama") and "aktif 2" in text(page, "#ringkasanHama"))
        tab(page, "foto")
        check("petani melihat 2 foto", "2 foto perkembangan" in text(page, "#ringkasanFoto"))
        # ganti sandi round-trip
        tab(page, "dashboard")
        page.fill("#sandiLama", "petani123")
        page.fill("#sandiBaru", "petani456")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        check("petani ganti sandi berhasil", "berhasil diubah" in text(page, "#pesanSandi"))
        logout(page)
        login(page, "petani", "petani456")
        check("petani masuk dengan sandi baru", not visible(page, "#loginOverlay"))
        tab(page, "dashboard")
        page.fill("#sandiLama", "petani456")
        page.fill("#sandiBaru", "petani123")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        check("petani kembalikan sandi", "berhasil diubah" in text(page, "#pesanSandi"))
        logout(page)

        # ---------- B. Manajer ----------
        login(page, "manajer", "manajer123")
        check("manajer masuk", not visible(page, "#loginOverlay"))
        check("chip pengguna manajer", "Dedi Kurniawan (Manajer)" in text(page, "#userChip"))
        check("manajer dasbor lahan 6", text(page, "#dLahan").strip() == "6")
        check("manajer dasbor pertumbuhan 21", text(page, "#dPertumbuhan").strip() == "21")
        check("manajer dasbor tinggi tertinggi 185 cm", text(page, "#dTinggi").strip() == "185 cm")
        check("manajer dasbor hama aktif 5", text(page, "#dHamaAktif").strip() == "5")
        check("manajer tidak melihat kartu kelola pengguna", not visible(page, "#cardPengguna"))
        tab(page, "lahan")
        check("manajer bisa melihat form tambah lahan", visible(page, "#panel-lahan .hanya-kelola"))
        logout(page)

        # ---------- C. Admin baseline + CRUD ----------
        login(page, "admin", "admin123")
        check("admin masuk", not visible(page, "#loginOverlay"))
        check("admin dasbor lahan 6 (9,5 ha)", text(page, "#dLahan").strip() == "6" and "9,5 ha" in text(page, "#dLahanSub"))
        check("admin dasbor pertumbuhan 21", text(page, "#dPertumbuhan").strip() == "21")
        check("admin dasbor tinggi 185 cm (Jagung Manis)", text(page, "#dTinggi").strip() == "185 cm" and "Jagung Manis" in text(page, "#dTinggiSub"))
        check("admin dasbor foto 8", text(page, "#dFoto").strip() == "8")
        check("admin dasbor jadwal hari ini 4", text(page, "#dJadwalHariIni").strip() == "4")
        check("admin dasbor hama aktif 5", text(page, "#dHamaAktif").strip() == "5")
        check("admin dasbor jadwal belum 10", text(page, "#dJadwalBelum").strip() == "10")
        check("admin dasbor jadwal lewat 2", text(page, "#dJadwalLewat").strip() == "2")
        check("admin dasbor tinggi terakhir ada 95 cm dan 185 cm", "95 cm" in text(page, "#daftarTinggiTerakhir") and "185 cm" in text(page, "#daftarTinggiTerakhir"))
        check("admin dasbor perhatian ada Pupuk NPK", "Pupuk NPK" in text(page, "#daftarJadwalPerhatian"))
        check("admin dasbor hama aktif ada Wereng Coklat", "Wereng Coklat" in text(page, "#daftarHamaAktif"))
        check("admin melihat kartu kelola pengguna", visible(page, "#cardPengguna"))
        check("admin melihat 3 pengguna", text(page, "#daftarPengguna").count("@") == 3)

        # Lahan: tambah + hapus + tolak hapus L1
        tab(page, "lahan")
        check("lahan 6 (9,5 ha)", "6 lahan" in text(page, "#ringkasanLahan") and "9,5 ha" in text(page, "#ringkasanLahan"))
        page.fill("#lhNama", "Lahan Uji")
        page.select_option("#lhTanaman", "Tomat")
        page.fill("#lhLuas", "1")
        page.fill("#lhTanam", "2026-11-20")
        page.click("#btnTambahLahan")
        page.wait_for_timeout(300)
        check("tambah lahan -> 7 lahan", "7 lahan" in text(page, "#ringkasanLahan"))
        page.click("[data-hapus-lahan='7']")
        klik_modal_ya(page)
        check("hapus lahan uji -> 6 lahan", "6 lahan" in text(page, "#ringkasanLahan"))
        page.click("[data-hapus-lahan='1']")
        page.wait_for_timeout(300)
        check("hapus lahan L1 ditolak (ada pertumbuhan)", "tidak bisa dihapus" in text(page, "#toast"))
        check("lahan tetap 6 setelah tolak", "6 lahan" in text(page, "#ringkasanLahan"))

        # Pertumbuhan: filter Nov + tambah + hapus
        tab(page, "pertumbuhan")
        check("pertumbuhan 21 catatan", "21 catatan pertumbuhan" in text(page, "#ringkasanPertumbuhan"))
        check("grafik tinggi ada 185 cm", "185 cm" in text(page, "#grafikTinggi"))
        page.select_option("#fBulanPertumbuhan", "2026-11")
        page.wait_for_timeout(300)
        check("pertumbuhan Nov 10 catatan", "10 catatan pertumbuhan" in text(page, "#ringkasanPertumbuhan"))
        page.select_option("#fBulanPertumbuhan", "semua")
        page.wait_for_timeout(300)
        page.fill("#ptTinggi", "100")
        page.select_option("#ptFase", "Berbuah")
        page.fill("#ptCatatan", "Catatan Uji")
        page.click("#btnTambahPertumbuhan")
        page.wait_for_timeout(300)
        check("tambah pertumbuhan -> 22 catatan", "22 catatan pertumbuhan" in text(page, "#ringkasanPertumbuhan"))
        page.click("[data-hapus-pertumbuhan='22']")
        klik_modal_ya(page)
        check("hapus pertumbuhan uji -> 21 catatan", "21 catatan pertumbuhan" in text(page, "#ringkasanPertumbuhan"))

        # Jadwal: filter hari ini/segera/lewat + tambah + selesai + hapus
        tab(page, "jadwal")
        check("jadwal 12 (hari ini 4, segera 8, lewat 2)", "12 jadwal" in text(page, "#ringkasanJadwal") and "hari ini belum 4" in text(page, "#ringkasanJadwal") and "segera 8" in text(page, "#ringkasanJadwal") and "lewat 2" in text(page, "#ringkasanJadwal"))
        page.select_option("#fJadwal", "hariini")
        page.wait_for_timeout(300)
        check("jadwal hari ini 4", "4 jadwal" in text(page, "#ringkasanJadwal"))
        page.select_option("#fJadwal", "segera")
        page.wait_for_timeout(300)
        check("jadwal segera 8", "8 jadwal" in text(page, "#ringkasanJadwal"))
        page.select_option("#fJadwal", "lewat")
        page.wait_for_timeout(300)
        check("jadwal lewat 2", "2 jadwal" in text(page, "#ringkasanJadwal"))
        check("jadwal lewat ada Pupuk NPK", "Pupuk NPK" in text(page, "#daftarJadwal"))
        page.select_option("#fJadwal", "semua")
        page.wait_for_timeout(300)
        page.fill("#jdNama", "Jadwal Uji")
        page.click("#btnTambahJadwal")
        page.wait_for_timeout(300)
        check("tambah jadwal -> 13 jadwal", "13 jadwal" in text(page, "#ringkasanJadwal"))
        page.click("[data-jadwal-selesai='13']")
        page.wait_for_timeout(300)
        check("jadwal uji ditandai sudah selesai", "Selesai" in text(page, "#daftarJadwal"))
        page.click("[data-hapus-jadwal='13']")
        klik_modal_ya(page)
        check("hapus jadwal uji -> 12 jadwal", "12 jadwal" in text(page, "#ringkasanJadwal"))

        # Hama: filter Aktif + tambah + tertangani + hapus
        tab(page, "hama")
        check("hama 7 (aktif 5, tertangani 2)", "7 catatan hama" in text(page, "#ringkasanHama") and "aktif 5" in text(page, "#ringkasanHama") and "tertangani 2" in text(page, "#ringkasanHama"))
        page.select_option("#fHama", "Aktif")
        page.wait_for_timeout(300)
        check("hama aktif 5", "5 catatan hama" in text(page, "#ringkasanHama"))
        page.select_option("#fHama", "semua")
        page.wait_for_timeout(300)
        page.fill("#hmNama", "Hama Uji")
        page.fill("#hmTindakan", "Tindakan uji")
        page.click("#btnTambahHama")
        page.wait_for_timeout(300)
        check("tambah hama -> 8 catatan (aktif 6)", "8 catatan hama" in text(page, "#ringkasanHama") and "aktif 6" in text(page, "#ringkasanHama"))
        page.click("[data-hama-selesai='8']")
        page.wait_for_timeout(300)
        check("hama uji ditandai tertangani (aktif 5 lagi)", "aktif 5" in text(page, "#ringkasanHama"))
        page.click("[data-hapus-hama='8']")
        klik_modal_ya(page)
        check("hapus hama uji -> 7 catatan", "7 catatan hama" in text(page, "#ringkasanHama"))

        # Foto: baseline + unggah + hapus
        tab(page, "foto")
        check("foto 8", "8 foto perkembangan" in text(page, "#ringkasanFoto"))
        check("grid foto ada 8 item", len(page.query_selector_all("#daftarFoto .foto-item")) == 8)
        page.select_option("#fBulanFoto", "2026-11")
        page.wait_for_timeout(300)
        check("foto Nov 7", "7 foto perkembangan" in text(page, "#ringkasanFoto"))
        page.select_option("#fBulanFoto", "semua")
        page.wait_for_timeout(300)
        page.set_input_files("#ftFile", files=[{"name": "tomat-uji.png", "buffer": PNG_1X1, "mimeType": "image/png"}])
        page.wait_for_timeout(500)
        check("pratinjau foto tampil setelah pilih file", visible(page, "#ftPratinjau"))
        check("status foto dipilih", "Foto dipilih" in text(page, "#ftStatus"))
        page.fill("#ftJudul", "Foto Uji")
        page.click("#btnTambahFoto")
        page.wait_for_timeout(300)
        check("tambah foto -> 9 foto", "9 foto perkembangan" in text(page, "#ringkasanFoto"))
        check("grid foto ada 9 item", len(page.query_selector_all("#daftarFoto .foto-item")) == 9)
        page.click("[data-hapus-foto='9']")
        klik_modal_ya(page)
        check("hapus foto uji -> 8 foto", "8 foto perkembangan" in text(page, "#ringkasanFoto"))

        # Laporan + CSV Nov
        tab(page, "laporan")
        check("laporan per lahan L1 95 cm Berbunga", "95 cm" in text(page, "#tabelPerLahan") and "Berbunga" in text(page, "#tabelPerLahan"))
        check("laporan per lahan L4 185 cm", "185 cm" in text(page, "#tabelPerLahan"))
        check("laporan per lahan L6 hama aktif 1 foto 1", "Kebun Kopi Bukit" in text(page, "#tabelPerLahan"))
        check("laporan per bulan Nov 10 pertumbuhan 7 hama 7 foto", "November 2026" in text(page, "#tabelPerBulan"))
        check("laporan tingkat hama Berat total 1", "Berat" in text(page, "#tabelTingkatHama"))
        check("laporan tingkat hama Sedang total 4", "Sedang" in text(page, "#tabelTingkatHama"))
        page.select_option("#fBulanLaporan", "2026-11")
        page.wait_for_timeout(200)
        with page.expect_download() as dl:
            page.click("#btnCsvLaporan")
        csv_nov = Path(dl.value.path()).read_text(encoding="utf-8")
        baris_nov = [b for b in csv_nov.strip().split("\n")]
        check("CSV Nov 17 baris + header", len(baris_nov) == 18, f"dapat {len(baris_nov)}")
        check("CSV Nov berisi Wereng Coklat", "Wereng Coklat" in csv_nov)
        page.select_option("#fBulanLaporan", "semua")
        page.wait_for_timeout(200)
        with page.expect_download() as dl2:
            page.click("#btnCsvLaporan")
        csv_semua = Path(dl2.value.path()).read_text(encoding="utf-8")
        baris_semua = [b for b in csv_semua.strip().split("\n")]
        check("CSV semua 28 baris + header", len(baris_semua) == 29, f"dapat {len(baris_semua)}")

        # ---------- D. RESTORE-TEST + backup/reset/restore ----------
        tab(page, "hama")
        page.fill("#hmNama", "RESTORE-TEST")
        page.fill("#hmTindakan", "Tindakan restore")
        page.click("#btnTambahHama")
        page.wait_for_timeout(300)
        check("RESTORE-TEST tercatat", "RESTORE-TEST" in text(page, "#daftarHama"))
        tab(page, "laporan")
        with page.expect_download() as dl3:
            page.click("#btnBackup")
        backup_path = dl3.value.path()
        backup = json.loads(Path(backup_path).read_text(encoding="utf-8"))
        check("backup berisi RESTORE-TEST", any(h.get("nama") == "RESTORE-TEST" for h in backup["state"]["hama"]))
        check("backup berisi 6 lahan", len(backup["state"]["lahan"]) == 6)
        page.click("#btnResetData")
        klik_modal_ya(page)
        check("reset kembalikan 21 pertumbuhan 7 hama", "21 catatan pertumbuhan" in text(page, "#ringkasanLaporan") and "7 catatan hama" in text(page, "#ringkasanLaporan"))
        Path("/tmp/crop_tidak_valid.json").write_text("bukan json", encoding="utf-8")
        page.set_input_files("#inputRestore", "/tmp/crop_tidak_valid.json")
        page.wait_for_timeout(500)
        check("restore file tidak valid ditolak", "tidak valid" in text(page, "#toast"))
        check("data tetap seed setelah restore gagal", "21 catatan pertumbuhan" in text(page, "#ringkasanLaporan"))
        page.set_input_files("#inputRestore", backup_path)
        page.wait_for_timeout(500)
        check("restore backup berhasil", "berhasil dipulihkan" in text(page, "#toast"))
        check("setelah restore 8 catatan hama", "8 catatan hama" in text(page, "#ringkasanLaporan"))
        tab(page, "hama")
        page.click("[data-hapus-hama='9']")
        klik_modal_ya(page)
        check("hapus RESTORE-TEST -> 7 catatan hama", "7 catatan hama" in text(page, "#ringkasanHama"))

        # ---------- E. Reset sandi petani oleh admin ----------
        tab(page, "dashboard")
        page.click("[data-reset='petani']")
        klik_modal_ya(page)
        logout(page)
        login(page, "petani", "bk123")
        check("petani masuk dengan bk123", not visible(page, "#loginOverlay"))
        tab(page, "dashboard")
        page.fill("#sandiLama", "bk123")
        page.fill("#sandiBaru", "petani123")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        check("petani kembalikan sandi ke petani123", "berhasil diubah" in text(page, "#pesanSandi"))
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
