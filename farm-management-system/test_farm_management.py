"""Tes Farm Management System (file lokal, Playwright Chromium).
Hari ini 2026-11-20. Data seed (tanggal relatif) — diuji silang Python (/tmp/cek_farm.py):
  Lahan 5 (Aktif 4), luas total 9,0 ha.
  Tanaman 7: Tumbuh 4, Siap Panen 2, Panen 1.
  Biaya 21 entri, total Rp15.300.000. Hasil 4 entri, total Rp29.950.000. Laba Rp14.650.000.
    Per lahan: L1 8.100.000/24.750.000/16.650.000; L2 1.600.000/2.800.000/1.200.000;
      L3 3.300.000/2.400.000/-900.000; L4 2.300.000/0/-2.300.000; L5 0/0/0.
    Per kategori biaya: Benih 4.600.000, Pupuk 3.550.000, Tenaga Kerja 6.400.000, Obat 750.000.
    Per bulan: Nov biaya 2.600.000 (5) hasil 5.200.000 (3) laba 2.600.000;
      Okt biaya 4.450.000 (8) hasil 0; Sep biaya 4.900.000 (4) hasil 24.750.000 (1) laba 19.850.000;
      Agu biaya 1.550.000 (2); Jun biaya 800.000 (1); Mei biaya 1.000.000 (1).
    Petani: biaya 950.000 (3 catatan), hasil 400.000 (1), laba -550.000.
  Jadwal: segera 5, lewat 2, bulan ini 9 (7 belum + 2 kegiatan selesai).
  Stok 6 item, nilai Rp5.180.000; menipis 2 (Pupuk NPK 35<50, Benih Jagung 8<10).
  RESTORE-TEST: biaya "RESTORE-TEST" Rp123.456 di Lahan 1 -> total biaya 15.423.456.
Urutan tes: label + login salah, A petani (baseline + peran + ganti sandi),
  B manajer (baseline + bisa kelola, tidak bisa kelola pengguna),
  C admin (baseline + lahan + tanaman + jadwal + biaya + hasil + stok + laporan + CSV),
  D admin (modal panen Tomat + CSV semua),
  E admin (RESTORE-TEST + backup/reset/restore + file tidak valid + hapus),
  F admin (reset sandi petani -> login bk123 -> kembalikan petani123).
"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = "file://" + str(ROOT / "farm-management-system" / "index.html")

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
        check("hero bertuliskan Farm Management System", "Farm Management System" in text(page, ".hero"))
        check("login menampilkan 3 akun demo", "admin / admin123" in text(page, ".login-note") and "manajer / manajer123" in text(page, ".login-note") and "petani / petani123" in text(page, ".login-note"))
        login(page, "admin", "salah123")
        check("login salah ditolak", visible(page, "#loginError"))
        check("overlay login masih tampil setelah login salah", visible(page, "#loginOverlay"))

        # ---------- A. Petani ----------
        login(page, "petani", "petani123")
        check("petani masuk, overlay hilang", not visible(page, "#loginOverlay"))
        check("petani mendarat di dasbor", "active" in (page.query_selector("#panel-dashboard").get_attribute("class") or ""))
        check("chip pengguna petani", "Budi Santoso (Petani)" in text(page, "#userChip"))
        check("petani dasbor biaya 950.000", "950.000" in text(page, "#dBiaya"))
        check("petani dasbor hasil 400.000", "400.000" in text(page, "#dHasil"))
        check("petani dasbor laba -550.000", "550.000" in text(page, "#dLaba"))
        check("petani dasbor biaya sub milik Anda", "milik Anda" in text(page, "#dBiayaSub"))
        check("petani tidak melihat kartu kelola pengguna", not visible(page, "#cardPengguna"))
        tab(page, "lahan")
        check("petani form tambah lahan tersembunyi", not visible(page, "#panel-lahan .hanya-kelola"))
        check("petani melihat 5 lahan", "5 lahan" in text(page, "#ringkasanLahan"))
        tab(page, "biaya")
        check("petani daftar biaya hanya miliknya (3 catatan)", "3 catatan biaya" in text(page, "#ringkasanBiaya"))
        check("petani daftar hasil hanya miliknya (1 panen)", "1 hasil panen" in text(page, "#ringkasanHasil"))
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
        check("manajer dasbor biaya 15.300.000", "15.300.000" in text(page, "#dBiaya"))
        check("manajer dasbor hasil 29.950.000", "29.950.000" in text(page, "#dHasil"))
        check("manajer dasbor laba 14.650.000", "14.650.000" in text(page, "#dLaba"))
        check("manajer tidak melihat kartu kelola pengguna", not visible(page, "#cardPengguna"))
        tab(page, "lahan")
        check("manajer bisa melihat form tambah lahan", visible(page, "#panel-lahan .hanya-kelola"))
        logout(page)

        # ---------- C. Admin baseline + CRUD ----------
        login(page, "admin", "admin123")
        check("admin masuk", not visible(page, "#loginOverlay"))
        check("admin dasbor biaya 15.300.000", "15.300.000" in text(page, "#dBiaya"))
        check("admin dasbor hasil 29.950.000", "29.950.000" in text(page, "#dHasil"))
        check("admin dasbor laba 14.650.000", "14.650.000" in text(page, "#dLaba"))
        check("admin dasbor lahan aktif 4", text(page, "#dLahan").strip() == "4")
        check("admin dasbor tanaman tumbuh 4", text(page, "#dTanamanTumbuh").strip() == "4")
        check("admin dasbor jadwal segera 5", text(page, "#dJadwalSegera").strip() == "5")
        check("admin dasbor jadwal lewat 2", text(page, "#dJadwalLewat").strip() == "2")
        check("admin dasbor stok menipis 2", text(page, "#dStokMenipis").strip() == "2")
        check("admin dasbor laba L1 16.650.000", "16.650.000" in text(page, "#daftarLabaLahan"))
        check("admin dasbor laba L3 -900.000", "900.000" in text(page, "#daftarLabaLahan"))
        check("admin melihat kartu kelola pengguna", visible(page, "#cardPengguna"))
        check("admin melihat 3 pengguna", text(page, "#daftarPengguna").count("@") == 3)

        # Lahan: tambah + hapus + tolak hapus L1
        tab(page, "lahan")
        page.fill("#lNama", "Lahan Uji")
        page.fill("#lLokasi", "Desa Uji")
        page.fill("#lLuas", "0.5")
        page.click("#btnTambahLahan")
        page.wait_for_timeout(300)
        check("tambah lahan -> 6 lahan", "6 lahan" in text(page, "#ringkasanLahan"))
        page.click("[data-hapus-lahan='6']")
        klik_modal_ya(page)
        check("hapus lahan uji -> 5 lahan", "5 lahan" in text(page, "#ringkasanLahan"))
        page.click("[data-hapus-lahan='1']")
        page.wait_for_timeout(300)
        check("hapus lahan L1 ditolak (ada tanaman)", "tidak bisa dihapus" in text(page, "#toast"))
        check("lahan tetap 5 setelah tolak", "5 lahan" in text(page, "#ringkasanLahan"))

        # Tanaman: tambah + hapus + tolak hapus T5 (ada hasil)
        tab(page, "tanaman")
        check("tanaman 7 (tumbuh 4, siap 2, panen 1)", "7 tanaman" in text(page, "#ringkasanTanaman"))
        page.fill("#tJenis", "Kangkung")
        page.fill("#tVarietas", "Hijau")
        page.fill("#tLuas", "0.5")
        page.click("#btnTambahTanaman")
        page.wait_for_timeout(300)
        check("tambah tanaman -> 8 tanaman", "8 tanaman" in text(page, "#ringkasanTanaman"))
        page.click("[data-hapus-tanaman='8']")
        klik_modal_ya(page)
        check("hapus tanaman uji -> 7 tanaman", "7 tanaman" in text(page, "#ringkasanTanaman"))
        page.click("[data-hapus-tanaman='5']")
        page.wait_for_timeout(300)
        check("hapus tanaman T5 ditolak (ada hasil panen)", "tidak bisa dihapus" in text(page, "#toast"))

        # Jadwal: filter segera/lewat/bulan + tambah kegiatan + selesai + hapus
        tab(page, "jadwal")
        page.select_option("#fJadwal", "segera")
        page.wait_for_timeout(300)
        check("jadwal segera 5", "5 jadwal" in text(page, "#ringkasanJadwal"))
        check("jadwal segera ada Panen Cabai", "Panen Cabai Merah" in text(page, "#daftarJadwal"))
        page.select_option("#fJadwal", "lewat")
        page.wait_for_timeout(300)
        check("jadwal lewat 2", "2 jadwal" in text(page, "#ringkasanJadwal"))
        check("jadwal lewat ada Panen Bayam", "Panen Bayam" in text(page, "#daftarJadwal"))
        page.select_option("#fJadwal", "bulan")
        page.wait_for_timeout(300)
        check("jadwal bulan ini 9", "9 jadwal" in text(page, "#ringkasanJadwal"))
        page.select_option("#fJadwal", "semua")
        page.wait_for_timeout(300)
        check("jadwal semua 11", "11 jadwal" in text(page, "#ringkasanJadwal"))
        page.fill("#kNama", "Kegiatan Uji")
        page.click("#btnTambahKegiatan")
        page.wait_for_timeout(300)
        check("tambah kegiatan -> 12 jadwal", "12 jadwal" in text(page, "#ringkasanJadwal"))
        page.click("[data-kegiatan-selesai='6']")
        page.wait_for_timeout(300)
        check("kegiatan uji ditandai selesai", "Selesai" in text(page, "#daftarJadwal"))
        page.click("[data-hapus-kegiatan='6']")
        klik_modal_ya(page)
        check("hapus kegiatan uji -> 11 jadwal", "11 jadwal" in text(page, "#ringkasanJadwal"))

        # Biaya: filter Nov + tambah + hapus
        tab(page, "biaya")
        page.select_option("#fBulanBiaya", "2026-11")
        page.wait_for_timeout(300)
        check("biaya Nov 5 catatan 2.600.000", "5 catatan biaya" in text(page, "#ringkasanBiaya") and "2.600.000" in text(page, "#ringkasanBiaya"))
        page.select_option("#fBulanBiaya", "semua")
        page.wait_for_timeout(300)
        check("biaya semua 21 catatan 15.300.000", "21 catatan biaya" in text(page, "#ringkasanBiaya") and "15.300.000" in text(page, "#ringkasanBiaya"))
        page.fill("#bKeterangan", "Biaya Uji")
        page.fill("#bJumlah", "500000")
        page.click("#btnTambahBiaya")
        page.wait_for_timeout(300)
        check("tambah biaya -> 22 catatan 15.800.000", "22 catatan biaya" in text(page, "#ringkasanBiaya") and "15.800.000" in text(page, "#ringkasanBiaya"))
        page.click("[data-hapus-biaya='22']")
        klik_modal_ya(page)
        check("hapus biaya uji -> 21 catatan", "21 catatan biaya" in text(page, "#ringkasanBiaya"))

        # Hasil: tambah via form + hapus
        check("hasil semua 4 panen 29.950.000", "4 hasil panen" in text(page, "#ringkasanHasil") and "29.950.000" in text(page, "#ringkasanHasil"))
        page.select_option("#hTanaman", "2")
        page.fill("#hKg", "50")
        page.fill("#hHarga", "12000")
        page.wait_for_timeout(200)
        check("pratinjau nilai hasil 600.000", "600.000" in text(page, "#hNilai"))
        page.click("#btnTambahHasil")
        page.wait_for_timeout(300)
        check("tambah hasil -> 5 panen 30.550.000", "5 hasil panen" in text(page, "#ringkasanHasil") and "30.550.000" in text(page, "#ringkasanHasil"))
        page.click("[data-hapus-hasil='5']")
        klik_modal_ya(page)
        check("hapus hasil uji -> 4 panen", "4 hasil panen" in text(page, "#ringkasanHasil"))

        # Stok: masuk/keluar + tolak keluar berlebih + tambah item + hapus ditolak
        tab(page, "stok")
        check("stok 6 item nilai 5.180.000 menipis 2", "6 item" in text(page, "#ringkasanStok") and "5.180.000" in text(page, "#ringkasanStok") and "menipis 2" in text(page, "#ringkasanStok"))
        page.click("[data-stok-masuk='2']")
        page.wait_for_timeout(300)
        page.fill("#stJumlah", "20")
        page.fill("#stKet", "Beli tambahan NPK")
        page.click("#modalStokYa")
        page.wait_for_timeout(300)
        check("stok masuk NPK +20 -> menipis tinggal 1", "menipis 1" in text(page, "#ringkasanStok"))
        check("nilai stok jadi 5.460.000", "5.460.000" in text(page, "#ringkasanStok"))
        page.click("[data-stok-keluar='1']")
        page.wait_for_timeout(300)
        page.fill("#stJumlah", "20")
        page.fill("#stKet", "Pemupukan susulan")
        page.click("#modalStokYa")
        page.wait_for_timeout(300)
        check("stok keluar Urea -20 -> nilai 5.220.000", "5.220.000" in text(page, "#ringkasanStok"))
        page.click("[data-stok-keluar='1']")
        page.wait_for_timeout(300)
        page.fill("#stJumlah", "500")
        page.click("#modalStokYa")
        page.wait_for_timeout(300)
        check("keluar melebihi stok ditolak", "melebihi stok" in text(page, "#pesanStok"))
        page.click("#modalStokBatal")
        page.wait_for_timeout(200)
        check("stok Urea tetap 100 setelah tolak", "100 kg" in text(page, "#daftarStok"))
        page.fill("#sNama", "Stok Uji")
        page.fill("#sSatuan", "kg")
        page.fill("#sJumlah", "10")
        page.fill("#sMin", "5")
        page.fill("#sHarga", "10000")
        page.click("#btnTambahStok")
        page.wait_for_timeout(300)
        check("tambah item stok -> 7 item", "7 item" in text(page, "#ringkasanStok"))
        page.click("[data-hapus-stok='1']")
        page.wait_for_timeout(300)
        check("hapus stok Urea ditolak (ada riwayat)", "tidak bisa dihapus" in text(page, "#toast"))
        page.click("[data-hapus-stok='7']")
        klik_modal_ya(page)
        check("hapus stok uji -> 6 item", "6 item" in text(page, "#ringkasanStok"))

        # Laporan + CSV Nov (sebelum mutasi panen)
        tab(page, "laporan")
        check("laporan per lahan L1 laba 16.650.000", "16.650.000" in text(page, "#tabelPerLahan"))
        check("laporan per lahan L3 rugi 900.000", "900.000" in text(page, "#tabelPerLahan"))
        check("laporan per bulan Nov laba 2.600.000", "2.600.000" in text(page, "#tabelPerBulan"))
        check("laporan per bulan Sep laba 19.850.000", "19.850.000" in text(page, "#tabelPerBulan"))
        check("laporan kategori Benih 4.600.000", "4.600.000" in text(page, "#tabelKatBiaya"))
        check("laporan kategori Tenaga Kerja 6.400.000", "6.400.000" in text(page, "#tabelKatBiaya"))
        check("laporan hasil per tanaman Padi Ciherang 4.500 kg", "4.500 kg" in text(page, "#tabelPerTanaman"))
        page.select_option("#fBulanLaporan", "2026-11")
        page.wait_for_timeout(200)
        with page.expect_download() as dl:
            page.click("#btnCsvLaporan")
        csv_nov = dl.value.suggested_filename and Path(dl.value.path()).read_text(encoding="utf-8")
        baris_nov = [b for b in csv_nov.strip().split("\n")]
        check("CSV Nov 8 baris + header", len(baris_nov) == 9, f"dapat {len(baris_nov)}")
        check("CSV Nov berisi Upah panen Tomat", "Upah panen Tomat" in csv_nov)

        # ---------- D. Modal Catat Panen Tomat ----------
        tab(page, "tanaman")
        page.click("[data-catat-panen='4']")
        page.wait_for_timeout(300)
        check("modal panen terbuka untuk Tomat", "Catat Panen" in text(page, "#modalPanenJudul") and "Tomat" in text(page, "#modalPanenJudul"))
        page.fill("#pKg", "200")
        page.fill("#pHarga", "9000")
        page.wait_for_timeout(200)
        check("modal panen nilai 1.800.000", "1.800.000" in text(page, "#pNilai"))
        page.click("#modalPanenYa")
        page.wait_for_timeout(400)
        check("Tomat jadi status Panen", "Panen" in text(page, "#daftarTanaman"))
        tab(page, "dashboard")
        check("setelah panen Tomat hasil 31.750.000", "31.750.000" in text(page, "#dHasil"))
        check("setelah panen Tomat laba 16.450.000", "16.450.000" in text(page, "#dLaba"))
        check("setelah panen Tomat segera jadi 4", text(page, "#dJadwalSegera").strip() == "4")
        tab(page, "laporan")
        page.select_option("#fBulanLaporan", "semua")
        page.wait_for_timeout(200)
        with page.expect_download() as dl2:
            page.click("#btnCsvLaporan")
        csv_semua = Path(dl2.value.path()).read_text(encoding="utf-8")
        baris_semua = [b for b in csv_semua.strip().split("\n")]
        check("CSV semua 26 baris + header", len(baris_semua) == 27, f"dapat {len(baris_semua)}")

        # ---------- E. RESTORE-TEST + backup/reset/restore ----------
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
        check("backup berisi panen Tomat 200 kg", any(h.get("kg") == 200 for h in backup["state"]["hasil"]))
        page.click("#btnResetData")
        klik_modal_ya(page)
        check("reset kembalikan biaya 15.300.000", "15.300.000" in text(page, "#ringkasanLaporan"))
        check("reset kembalikan hasil 29.950.000", "29.950.000" in text(page, "#ringkasanLaporan"))
        # file tidak valid ditolak
        Path("/tmp/farm_tidak_valid.json").write_text("bukan json", encoding="utf-8")
        page.set_input_files("#inputRestore", "/tmp/farm_tidak_valid.json")
        page.wait_for_timeout(500)
        check("restore file tidak valid ditolak", "tidak valid" in text(page, "#toast"))
        check("data tetap seed setelah restore gagal", "15.300.000" in text(page, "#ringkasanLaporan"))
        page.set_input_files("#inputRestore", backup_path)
        page.wait_for_timeout(500)
        check("restore backup berhasil", "berhasil dipulihkan" in text(page, "#toast"))
        check("setelah restore biaya 15.423.456", "15.423.456" in text(page, "#ringkasanLaporan"))
        check("setelah restore hasil 31.750.000", "31.750.000" in text(page, "#ringkasanLaporan"))
        tab(page, "biaya")
        page.click("[data-hapus-biaya='23']")
        klik_modal_ya(page)
        check("hapus RESTORE-TEST -> biaya 15.300.000", "15.300.000" in text(page, "#ringkasanBiaya"))

        # ---------- F. Reset sandi petani oleh admin ----------
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
