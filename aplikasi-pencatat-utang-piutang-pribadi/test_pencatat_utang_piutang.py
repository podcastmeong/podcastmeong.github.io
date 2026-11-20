"""Tes Pencatat Utang & Piutang Pribadi (file lokal, Playwright Chromium).
Hari ini 2026-11-20. Data seed (8 catatan, tanggal relatif terhadap hari ini):
  UT-1 utang Budi Hartono Rp2.500.000, dibuat T-10, tempo T+5, belum, admin
  UT-2 utang Sari Dewi Rp1.000.000, dibuat T-15, tempo T-5, belum, admin
  UT-3 utang Andi Pratama Rp750.000, dibuat T-31, tempo T-19, lunas T-21, pengguna
  UT-4 utang Joko Susilo Rp3.000.000, dibuat T-2, tempo T+28, belum, pengguna
  PT-1 piutang Dewi Lestari Rp1.500.000, dibuat T-12, tempo T+2, belum, admin
  PT-2 piutang Rina Marlina Rp4.000.000, dibuat T-19, tempo T-2, belum, pengguna
  PT-3 piutang Agus Wijaya Rp2.000.000, dibuat T-36, tempo T-21, lunas T-23, admin
  PT-4 piutang Maya Putri Rp900.000, dibuat T-1, tempo T+20, belum, pengguna
Dasbor admin: utang belum Rp6.500.000 (3), piutang belum Rp6.400.000 (3),
  segera 2 (UT-1, PT-1), lewat 2 (UT-2, PT-2), selisih Rp-100.000.
  Terdekat: UT-2, PT-2, PT-1, UT-1, PT-4, UT-4.
Dasbor pengguna: utang belum Rp3.000.000 (1), piutang belum Rp4.900.000 (2),
  segera 0, lewat 1 (PT-2), selisih +Rp1.900.000.
Laporan semua: utang Rp7.250.000, piutang Rp8.400.000, lunas Rp2.750.000,
  belum Rp12.900.000. Periode 7 hari: 2 catatan (UT-4, PT-4).
  Periode 30 hari: 6 catatan (kecuali UT-3, PT-3).
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = "file://" + str(ROOT / "aplikasi-pencatat-utang-piutang-pribadi" / "index.html")

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


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.goto(URL)
        page.wait_for_timeout(500)

        # ---------- 1. Muat & login ----------
        check("judul halaman", "Pencatat Utang" in page.title())
        check("overlay login tampil", page.is_visible("#loginOverlay"))
        check("akun demo tampil di login", "admin / admin123" in text(page, ".login-note") and "pengguna / pengguna123" in text(page, ".login-note"))
        login(page, "admin", "salah")
        check("login salah menampilkan error", page.is_visible("#loginError"))
        login(page, "admin", "admin123")
        check("login admin berhasil", not page.is_visible("#loginOverlay"))
        check("chip pengguna admin", "Administrator (Admin)" in text(page, "#userChip"))

        # ---------- 2. Dasbor seed (admin) ----------
        check("dasbor utang belum 6,5jt", "Rp6.500.000" in text(page, "#dUtang"), text(page, "#dUtang"))
        check("dasbor utang sub 3", "3 utang belum lunas" in text(page, "#dUtangSub"), text(page, "#dUtangSub"))
        check("dasbor piutang belum 6,4jt", "Rp6.400.000" in text(page, "#dPiutang"), text(page, "#dPiutang"))
        check("dasbor piutang sub 3", "3 piutang belum lunas" in text(page, "#dPiutangSub"), text(page, "#dPiutangSub"))
        check("dasbor segera 2", text(page, "#dSegera") == "2", text(page, "#dSegera"))
        check("dasbor lewat 2", text(page, "#dLewat") == "2", text(page, "#dLewat"))
        check("dasbor selisih -100rb", "Rp-100.000" in text(page, "#dSelisih"), text(page, "#dSelisih"))
        check("badge utang 3", text(page, "#badgeUtang") == "3")
        check("badge piutang 3", text(page, "#badgePiutang") == "3")
        check("badge tempo 4", text(page, "#badgeTempo") == "4")
        check("badge ingat 4", text(page, "#badgeIngat") == "4")
        check("badge riwayat 8", text(page, "#badgeRiwayat") == "8")
        check("terdekat pertama Sari Dewi", "Sari Dewi" in text(page, "#daftarTerbaru").split("\n")[0], text(page, "#daftarTerbaru")[:200])
        check("terdekat ada Rina Marlina", "Rina Marlina" in text(page, "#daftarTerbaru"))
        check("kartu kelola pengguna terlihat (admin)", page.is_visible("#cardPengguna"))
        check("kartu ganti sandi terlihat", page.is_visible("#cardSandiSaya"))
        check("kartu tambah cepat terlihat", page.is_visible("#cardTambahCepat"))

        # ---------- 3. Tab Utang ----------
        tab(page, "utang")
        rows_u = page.query_selector_all("#daftarUtang .baris")
        check("utang seed 4 baris", len(rows_u) == 4, str(len(rows_u)))
        page.select_option("#fStatusUtang", "belum")
        page.wait_for_timeout(200)
        check("utang filter belum 3", len(page.query_selector_all("#daftarUtang .baris")) == 3, str(len(page.query_selector_all("#daftarUtang .baris"))))
        page.select_option("#fStatusUtang", "lunas")
        page.wait_for_timeout(200)
        check("utang filter lunas 1", len(page.query_selector_all("#daftarUtang .baris")) == 1)
        check("utang lunas Andi Pratama", "Andi Pratama" in text(page, "#daftarUtang"))
        page.select_option("#fStatusUtang", "semua")
        page.fill("#cariUtang", "Budi")
        page.wait_for_timeout(200)
        check("utang cari Budi 1", len(page.query_selector_all("#daftarUtang .baris")) == 1, str(len(page.query_selector_all("#daftarUtang .baris"))))
        page.fill("#cariUtang", "")
        page.wait_for_timeout(200)

        # ---------- 4. Tab Piutang ----------
        tab(page, "piutang")
        rows_p = page.query_selector_all("#daftarPiutang .baris")
        check("piutang seed 4 baris", len(rows_p) == 4, str(len(rows_p)))
        page.select_option("#fStatusPiutang", "belum")
        page.wait_for_timeout(200)
        check("piutang filter belum 3", len(page.query_selector_all("#daftarPiutang .baris")) == 3)
        page.select_option("#fStatusPiutang", "lunas")
        page.wait_for_timeout(200)
        check("piutang filter lunas 1", len(page.query_selector_all("#daftarPiutang .baris")) == 1)
        check("piutang lunas Agus Wijaya", "Agus Wijaya" in text(page, "#daftarPiutang"))
        page.select_option("#fStatusPiutang", "semua")
        page.fill("#cariPiutang", "Rina")
        page.wait_for_timeout(200)
        check("piutang cari Rina 1", len(page.query_selector_all("#daftarPiutang .baris")) == 1)
        page.fill("#cariPiutang", "")
        page.wait_for_timeout(200)

        # ---------- 5. Tab Jatuh Tempo ----------
        tab(page, "jatuhtempo")
        check("tempo seed 6 baris", len(page.query_selector_all("#daftarTempo .baris")) == 6, str(len(page.query_selector_all("#daftarTempo .baris"))))
        page.select_option("#fTempo", "lewat")
        page.wait_for_timeout(200)
        check("tempo lewat 2", len(page.query_selector_all("#daftarTempo .baris")) == 2, str(len(page.query_selector_all("#daftarTempo .baris"))))
        check("tempo lewat ada Sari + Rina", "Sari Dewi" in text(page, "#daftarTempo") and "Rina Marlina" in text(page, "#daftarTempo"))
        page.select_option("#fTempo", "segera")
        page.wait_for_timeout(200)
        check("tempo segera 2", len(page.query_selector_all("#daftarTempo .baris")) == 2)
        check("tempo segera ada Dewi + Budi", "Dewi Lestari" in text(page, "#daftarTempo") and "Budi Hartono" in text(page, "#daftarTempo"))
        page.select_option("#fTempo", "aman")
        page.wait_for_timeout(200)
        check("tempo aman 2", len(page.query_selector_all("#daftarTempo .baris")) == 2)
        check("tempo aman ada Maya + Joko", "Maya Putri" in text(page, "#daftarTempo") and "Joko Susilo" in text(page, "#daftarTempo"))
        page.select_option("#fTempo", "semua")
        page.fill("#cariTempo", "Maya")
        page.wait_for_timeout(200)
        check("tempo cari Maya 1", len(page.query_selector_all("#daftarTempo .baris")) == 1)
        page.fill("#cariTempo", "")
        page.wait_for_timeout(200)

        # ---------- 6. Tab Pengingat + teks WA ----------
        tab(page, "pengingat")
        check("pengingat 4 item", len(page.query_selector_all("#daftarIngat .baris")) == 4, str(len(page.query_selector_all("#daftarIngat .baris"))))
        check("pengingat ringkasan 4 catatan", "4 catatan" in text(page, "#ringkasanIngat"), text(page, "#ringkasanIngat"))
        check("pengingat ringkasan 2 lewat", "2 lewat jatuh tempo" in text(page, "#ringkasanIngat"), text(page, "#ringkasanIngat"))
        page.click("#daftarIngat [data-wa='2']")
        page.wait_for_timeout(300)
        check("kotak pesan tampil", page.is_visible("#cardPesan"))
        pesan_utang = text(page, "#kotakPesan")
        check("teks WA utang ada Sari Dewi", "Sari Dewi" in pesan_utang, pesan_utang)
        check("teks WA utang ada Rp1.000.000", "Rp1.000.000" in pesan_utang, pesan_utang)
        check("teks WA utang kalimat saya lunasi", "utang saya" in pesan_utang and "lunasi" in pesan_utang, pesan_utang)
        page.click("#daftarIngat [data-wa='5']")
        page.wait_for_timeout(300)
        pesan_piutang = text(page, "#kotakPesan")
        check("teks WA piutang ada Dewi Lestari", "Dewi Lestari" in pesan_piutang, pesan_piutang)
        check("teks WA piutang ada Rp1.500.000", "Rp1.500.000" in pesan_piutang, pesan_piutang)
        check("teks WA piutang kalimat mohon dilunasi", "piutang" in pesan_piutang and "Mohon dilunasi" in pesan_piutang, pesan_piutang)

        # ---------- 7. Laporan (sebelum tambah) ----------
        tab(page, "laporan")
        check("laporan utang 7,25jt", "Rp7.250.000" in text(page, "#lUtang"), text(page, "#lUtang"))
        check("laporan piutang 8,4jt", "Rp8.400.000" in text(page, "#lPiutang"), text(page, "#lPiutang"))
        check("laporan lunas 2,75jt", "Rp2.750.000" in text(page, "#lLunas"), text(page, "#lLunas"))
        check("laporan belum 12,9jt", "Rp12.900.000" in text(page, "#lBelum"), text(page, "#lBelum"))
        check("laporan selisih 1,15jt", "Rp1.150.000" in text(page, "#lSelisih"), text(page, "#lSelisih"))
        trows = page.query_selector_all("#tabelOrang tr")
        check("tabel per orang 8 + header", len(trows) == 9, str(len(trows)))
        check("tabel orang ada Budi Hartono", "Budi Hartono" in text(page, "#tabelOrang"))
        srows = page.query_selector_all("#tabelStatus tr")
        check("tabel status 2 + header", len(srows) == 3, str(len(srows)))
        check("tabel status belum 12,9jt", "Rp12.900.000" in srows[1].inner_text(), srows[1].inner_text())
        check("tabel status lunas 2,75jt", "Rp2.750.000" in srows[2].inner_text(), srows[2].inner_text())
        page.select_option("#fPeriode", "7")
        page.wait_for_timeout(200)
        check("periode 7 hari utang 3jt", "Rp3.000.000" in text(page, "#lUtang"), text(page, "#lUtang"))
        check("periode 7 hari piutang 900rb", "Rp900.000" in text(page, "#lPiutang"), text(page, "#lPiutang"))
        page.select_option("#fPeriode", "30")
        page.wait_for_timeout(200)
        check("periode 30 hari utang 6,5jt", "Rp6.500.000" in text(page, "#lUtang"), text(page, "#lUtang"))
        check("periode 30 hari piutang 6,4jt", "Rp6.400.000" in text(page, "#lPiutang"), text(page, "#lPiutang"))
        page.select_option("#fPeriode", "semua")
        page.wait_for_timeout(200)

        # ---------- 8. CSV ekspor ----------
        with page.expect_download() as dl_info:
            page.click("#btnCsvLaporan")
        dl = dl_info.value
        csv_path = "/tmp/up-test.csv"
        dl.save_as(csv_path)
        isi_csv = Path(csv_path).read_text(encoding="utf-8")
        baris_csv = [b for b in isi_csv.split("\n") if b.strip()]
        check("CSV header", baris_csv[0].startswith('"Jenis","Orang"'), baris_csv[0])
        check("CSV 8 data + header", len(baris_csv) == 9, str(len(baris_csv)))
        check("CSV berisi Budi Hartono", "Budi Hartono" in isi_csv)
        check("CSV berisi Rina Marlina", "Rina Marlina" in isi_csv)

        # ---------- 9. Backup JSON ----------
        with page.expect_download() as dl_info:
            page.click("#btnBackup")
        dl = dl_info.value
        bak_path = "/tmp/up-test-backup.json"
        dl.save_as(bak_path)
        data_bak = json.loads(Path(bak_path).read_text(encoding="utf-8"))
        check("backup aplikasi pencatat-utang-piutang-pribadi", data_bak.get("aplikasi") == "pencatat-utang-piutang-pribadi")
        check("backup catatan 8", len(data_bak["state"]["catatan"]) == 8, str(len(data_bak["state"]["catatan"])))
        check("backup users 2", len(data_bak["users"]) == 2, str(len(data_bak["users"])))

        # ---------- 10. Tambah utang Tono + lunas + batal + hapus ----------
        tab(page, "utang")
        page.fill("#uOrang", "Tono")
        page.fill("#uJumlah", "500000")
        page.fill("#uTempo", "2026-11-30")
        page.fill("#uTanggal", "2026-11-20")
        page.fill("#uCatatan", "Pinjam untuk bensin")
        page.click("#btnTambahUtang")
        page.wait_for_timeout(300)
        check("utang Tono tersimpan 5 baris", len(page.query_selector_all("#daftarUtang .baris")) == 5, str(len(page.query_selector_all("#daftarUtang .baris"))))
        tab(page, "dashboard")
        check("dasbor utang 7jt setelah Tono", "Rp7.000.000" in text(page, "#dUtang"), text(page, "#dUtang"))
        tab(page, "utang")
        page.click("#daftarUtang [data-lunas='9']")
        page.wait_for_timeout(300)
        check("Tono lunas tampil lencana Lunas", "Lunas" in text(page, "#daftarUtang"))
        tab(page, "dashboard")
        check("dasbor utang kembali 6,5jt", "Rp6.500.000" in text(page, "#dUtang"), text(page, "#dUtang"))
        tab(page, "utang")
        page.click("#daftarUtang [data-batal='9']")
        page.wait_for_timeout(300)
        tab(page, "dashboard")
        check("dasbor utang 7jt setelah batal lunas", "Rp7.000.000" in text(page, "#dUtang"), text(page, "#dUtang"))
        tab(page, "utang")
        page.click("#daftarUtang [data-hapus='9']")
        page.wait_for_timeout(200)
        page.click("#modalYa")
        page.wait_for_timeout(300)
        check("utang kembali 4 baris setelah hapus Tono", len(page.query_selector_all("#daftarUtang .baris")) == 4, str(len(page.query_selector_all("#daftarUtang .baris"))))
        tab(page, "dashboard")
        check("dasbor utang 6,5jt setelah hapus", "Rp6.500.000" in text(page, "#dUtang"), text(page, "#dUtang"))

        # ---------- 11. Tambah cepat piutang Lilis + hapus ----------
        page.select_option("#qJenis", "piutang")
        page.fill("#qOrang", "Lilis")
        page.fill("#qJumlah", "700000")
        page.fill("#qTempo", "2026-12-05")
        page.fill("#qCatatan", "Pinjaman arisan")
        page.click("#btnTambahCepat")
        page.wait_for_timeout(300)
        check("dasbor piutang 7,1jt setelah Lilis", "Rp7.100.000" in text(page, "#dPiutang"), text(page, "#dPiutang"))
        tab(page, "piutang")
        page.fill("#cariPiutang", "Lilis")
        page.wait_for_timeout(200)
        check("piutang cari Lilis 1", len(page.query_selector_all("#daftarPiutang .baris")) == 1)
        page.click("#daftarPiutang [data-hapus='10']")
        page.wait_for_timeout(200)
        page.click("#modalYa")
        page.wait_for_timeout(300)
        tab(page, "dashboard")
        check("dasbor piutang 6,4jt setelah hapus Lilis", "Rp6.400.000" in text(page, "#dPiutang"), text(page, "#dPiutang"))

        # ---------- 12. Riwayat ----------
        tab(page, "riwayat")
        check("riwayat seed 8 baris", len(page.query_selector_all("#daftarRiwayat .baris")) == 8, str(len(page.query_selector_all("#daftarRiwayat .baris"))))
        page.select_option("#fJenisRw", "utang")
        page.wait_for_timeout(200)
        check("riwayat filter utang 4", len(page.query_selector_all("#daftarRiwayat .baris")) == 4, str(len(page.query_selector_all("#daftarRiwayat .baris"))))
        page.select_option("#fJenisRw", "piutang")
        page.wait_for_timeout(200)
        check("riwayat filter piutang 4", len(page.query_selector_all("#daftarRiwayat .baris")) == 4)
        page.select_option("#fJenisRw", "semua")
        page.select_option("#fStatusRw", "lunas")
        page.wait_for_timeout(200)
        check("riwayat filter lunas 2", len(page.query_selector_all("#daftarRiwayat .baris")) == 2, str(len(page.query_selector_all("#daftarRiwayat .baris"))))
        page.select_option("#fStatusRw", "semua")
        page.fill("#cariRw", "Rina")
        page.wait_for_timeout(200)
        check("riwayat cari Rina 1", len(page.query_selector_all("#daftarRiwayat .baris")) == 1)
        page.fill("#cariRw", "")
        page.wait_for_timeout(200)

        # ---------- 13. Peran Pengguna ----------
        logout(page)
        login(page, "pengguna", "pengguna123")
        check("login pengguna berhasil", "Budi Santoso (Pengguna)" in text(page, "#userChip"))
        tab(page, "dashboard")
        check("kartu kelola pengguna tersembunyi", not page.is_visible("#cardPengguna"))
        check("kartu ganti sandi selalu terlihat (pengguna)", page.is_visible("#cardSandiSaya"))
        check("kartu tambah cepat terlihat (pengguna)", page.is_visible("#cardTambahCepat"))
        check("pengguna utang 3jt", "Rp3.000.000" in text(page, "#dUtang"), text(page, "#dUtang"))
        check("pengguna piutang 4,9jt", "Rp4.900.000" in text(page, "#dPiutang"), text(page, "#dPiutang"))
        check("pengguna segera 0", text(page, "#dSegera") == "0", text(page, "#dSegera"))
        check("pengguna lewat 1", text(page, "#dLewat") == "1", text(page, "#dLewat"))
        check("pengguna selisih +1,9jt", "Rp1.900.000" in text(page, "#dSelisih"), text(page, "#dSelisih"))
        tab(page, "utang")
        check("pengguna utang 2 baris", len(page.query_selector_all("#daftarUtang .baris")) == 2, str(len(page.query_selector_all("#daftarUtang .baris"))))
        page.fill("#cariUtang", "Budi")
        page.wait_for_timeout(200)
        check("pengguna tidak melihat Budi Hartono (admin)", len(page.query_selector_all("#daftarUtang .baris")) == 0, str(len(page.query_selector_all("#daftarUtang .baris"))))
        page.fill("#cariUtang", "")
        page.wait_for_timeout(200)
        tab(page, "piutang")
        page.fill("#cariPiutang", "")
        page.wait_for_timeout(200)
        check("pengguna piutang 2 baris", len(page.query_selector_all("#daftarPiutang .baris")) == 2, str(len(page.query_selector_all("#daftarPiutang .baris"))))

        # ---------- 14. Pengguna tambah utang Dedi + hapus ----------
        tab(page, "dashboard")
        page.select_option("#qJenis", "utang")
        page.fill("#qOrang", "Dedi")
        page.fill("#qJumlah", "200000")
        page.fill("#qTempo", "2026-11-25")
        page.click("#btnTambahCepat")
        page.wait_for_timeout(300)
        check("pengguna utang 3,2jt setelah Dedi", "Rp3.200.000" in text(page, "#dUtang"), text(page, "#dUtang"))
        tab(page, "utang")
        page.fill("#cariUtang", "Dedi")
        page.wait_for_timeout(200)
        check("pengguna utang cari Dedi 1", len(page.query_selector_all("#daftarUtang .baris")) == 1)
        page.click("#daftarUtang [data-hapus='11']")
        page.wait_for_timeout(200)
        page.click("#modalYa")
        page.wait_for_timeout(300)
        tab(page, "dashboard")
        check("pengguna utang 3jt setelah hapus Dedi", "Rp3.000.000" in text(page, "#dUtang"), text(page, "#dUtang"))

        # ---------- 15. Ganti sandi pengguna round-trip ----------
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

        # ---------- 16. Admin reset sandi pengguna -> bk123 ----------
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

        # ---------- 17. Tambah & hapus pengguna ----------
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

        # ---------- 18. Restore dengan penanda ----------
        data_bak["state"]["catatan"].insert(0, {
            "id": 999, "jenis": "utang", "orang": "RESTORE-TEST", "jumlah": 123456,
            "tanggal": "2026-11-20", "jatuhTempo": "2026-12-20", "status": "lunas",
            "tanggalLunas": "2026-11-20", "pengguna": "admin", "catatan": "penanda pulihkan"
        })
        data_bak["state"]["nextId"] = 1000
        Path("/tmp/up-test-restore.json").write_text(json.dumps(data_bak), encoding="utf-8")
        login(page, "admin", "admin123")
        tab(page, "riwayat")
        page.set_input_files("#inputRestore", "/tmp/up-test-restore.json")
        page.wait_for_timeout(500)
        page.fill("#cariRw", "RESTORE-TEST")
        page.wait_for_timeout(200)
        check("restore menampilkan RESTORE-TEST", "RESTORE-TEST" in text(page, "#daftarRiwayat"))
        check("restore cari RESTORE-TEST 1 baris", len(page.query_selector_all("#daftarRiwayat .baris")) == 1, str(len(page.query_selector_all("#daftarRiwayat .baris"))))
        page.click("#daftarRiwayat [data-hapus='999']")
        page.wait_for_timeout(200)
        page.click("#modalYa")
        page.wait_for_timeout(300)
        page.fill("#cariRw", "")
        page.wait_for_timeout(200)
        check("riwayat kembali 8 setelah hapus marker", len(page.query_selector_all("#daftarRiwayat .baris")) == 8, str(len(page.query_selector_all("#daftarRiwayat .baris"))))

        # ---------- 19. Reset data demo ----------
        tab(page, "laporan")
        page.click("#btnResetData")
        page.wait_for_timeout(200)
        page.click("#modalYa")
        page.wait_for_timeout(400)
        tab(page, "dashboard")
        check("reset kembali utang 6,5jt", "Rp6.500.000" in text(page, "#dUtang"), text(page, "#dUtang"))
        check("reset kembali piutang 6,4jt", "Rp6.400.000" in text(page, "#dPiutang"), text(page, "#dPiutang"))

        # ---------- 20. Panduan ----------
        tab(page, "panduan")
        panduan = text(page, "#panel-panduan")
        check("panduan ada harga Basic 499rb", "Rp499.000" in panduan)
        check("panduan ada APK +400rb", "Rp400.000" in panduan)
        check("panduan batas jujur localStorage", "localStorage" in panduan)
        check("panduan bukan payment gateway", "bukan payment gateway" in panduan)
        check("panduan tidak mengirim pesan", "tidak mengirim pesan" in panduan)
        check("panduan akun demo", "admin / admin123" in panduan and "pengguna / pengguna123" in panduan)
        check("panduan garansi 30/60/90", "30 hari" in panduan and "90 hari" in panduan)
        check("panduan tandai lunas", "Tandai Lunas" in panduan)

        # ---------- 21. Console / page error ----------
        check("tanpa console error", len(console_errors) == 0, str(console_errors[:3]))
        check("tanpa pageerror", len(page_errors) == 0, str(page_errors[:3]))

        browser.close()

    print(f"\n{passed} lolos, {len(failures)} gagal")
    if failures:
        print("GAGAL:", failures)
        sys.exit(1)


if __name__ == "__main__":
    main()
