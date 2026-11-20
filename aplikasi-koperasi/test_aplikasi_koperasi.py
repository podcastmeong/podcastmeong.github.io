"""Tes Aplikasi Koperasi (Pencatatan) (file lokal, Playwright Chromium).
Hari ini 2026-11-20. Data seed (tanggal relatif) — diuji silang Python:
  Anggota: 8 (KOP-001 Budi Santoso ... KOP-008 Maya Putri).
  Simpanan: 30 catatan, total Rp6.700.000 (pokok 4.000.000, wajib 1.800.000, sukarela 900.000).
    Budi 1.050.000 | Sari 900.000 | Andi 700.000 | Dewi 1.300.000
    Joko 600.000 | Rina 700.000 | Agus 800.000 | Maya 650.000.
  Pinjaman (7 rencana, anuitas):
    Budi "Pinjaman Usaha" 10jt/12%/12, mulai 21 Sep 2026: angsuran 888.488, total 10.661.856,
      bunga 661.856; bln 1-2 dibayar; sisa 8.415.139; bln 3 (21 Nov) Segera.
    Sari "Pinjaman Pendidikan" 5jt/10%/10, mulai 22 Agu 2026: angsuran 523.202, total 5.232.020,
      bunga 232.020; bln 1-3 dibayar; sisa 3.543.322; bln 4 (22 Nov) Segera.
    Andi "Pinjaman Renovasi" 15jt/12%/18, mulai 23 Jul 2026: angsuran 914.731, total 16.465.158,
      bunga 1.465.158; bln 1-4 dibayar; sisa 11.894.887; bln 5 (23 Nov) Segera.
    Dewi "Pinjaman Modal" 8jt/12%/12, mulai 21 Okt 2026: angsuran 710.790, total 8.529.480,
      bunga 529.480; bln 1 dibayar; sisa 7.369.210; bln 2 (21 Nov) Segera.
    Joko "Pinjaman Konsumsi" 3jt/18%/6, mulai 6 Okt 2026: angsuran 526.576, total 3.159.456,
      bunga 159.456; bln 1 (6 Okt) + bln 2 (6 Nov) Lewat; sisa 3.000.000.
    Rina "Pinjaman Usaha" 12jt/10%/24, mulai 4 Mei 2026: angsuran 553.739, total 13.289.736,
      bunga 1.289.736; bln 1-6 dibayar; sisa 9.220.214; bln 7 (4 Nov) Lewat.
    Agus "Pinjaman Motor" 6jt/0%/6, mulai 23 Jun 2026: angsuran 1.000.000, total 6.000.000;
      bln 1-5 dibayar; sisa 1.000.000; bln 6 (23 Nov) Segera.
  Dasbor seed admin: anggota 8, simpanan 6.700.000, sisa pokok aktif 44.442.772,
    angsuran/bln 5.117.526, segera 5, lewat 3, pinjaman aktif 7, belum bayar 67.
  Anggota Budi: simpanan 1.050.000, sisa pokok 8.415.139, angsuran/bln 888.488,
    segera 1, lewat 0, pinjaman aktif 1/1, belum 10.
  RESTORE-TEST: pinjaman Maya 12jt/12%/12, mulai 20 Des 2026 -> angsuran 1.066.185,
    total 12.794.220, bunga 794.220; sisa pokok admin jadi 56.442.772,
    angsuran/bln 6.183.711, pinjaman aktif 8.
Urutan tes: A anggota (baseline + visibilitas + ganti sandi),
  B pengurus (baseline + tambah simpanan + tambah/hapus anggota + hapus diblokir),
  C admin (jadwal modal + angsuran + pengingat + RESTORE-TEST + backup/reset/restore + CSV +
    hapus + reset sandi pengurus + ganti sandi admin),
  D anggota (tandai bayar angsuran sendiri).
"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = "file://" + str(ROOT / "aplikasi-koperasi" / "index.html")

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


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(accept_downloads=True)
        page = ctx.new_page()
        page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.goto(URL)
        page.wait_for_timeout(500)

        # ---------- Label pencatatan ----------
        check("hero bertuliskan PENCATATAN SAJA", "PENCATATAN SAJA" in text(page, ".hero"))
        check("hero menegaskan bukan lembaga keuangan", "BUKAN LEMBAGA KEUANGAN" in text(page, ".hero"))
        check("login menegaskan bukan lembaga keuangan", "BUKAN LEMBAGA KEUANGAN" in text(page, "#loginOverlay"))
        check("panduan menegaskan bukan lembaga keuangan", "bukan lembaga keuangan" in text(page, "#panel-panduan"))

        # ---------- Login salah ----------
        page.fill("#loginUser", "admin")
        page.fill("#loginPass", "salah123")
        page.click("#formLogin button[type=submit]")
        page.wait_for_timeout(300)
        check("login salah menampilkan error", visible(page, "#loginError"))

        # ================= FASE A — anggota (Budi) =================
        login(page, "anggota", "anggota123")
        check("A: anggota masuk, chip Budi Santoso", "Budi Santoso (Anggota)" in text(page, "#userChip"))
        check("A: mendarat di dasbor (panel aktif)", "active" in (page.get_attribute("#panel-dashboard", "class") or ""))
        check("A: anggota 1 (data sendiri)", text(page, "#dAnggota") == "1", text(page, "#dAnggota"))
        check("A: simpanan 1.050.000", text(page, "#dSimpanan") == rupiah(1050000), text(page, "#dSimpanan"))
        check("A: sisa pokok 8.415.139", text(page, "#dSisaPokok") == rupiah(8415139), text(page, "#dSisaPokok"))
        check("A: angsuran/bln 888.488", text(page, "#dAngsuranBln") == rupiah(888488), text(page, "#dAngsuranBln"))
        check("A: segera 1", text(page, "#dSegera") == "1", text(page, "#dSegera"))
        check("A: lewat 0", text(page, "#dLewat") == "0", text(page, "#dLewat"))
        check("A: pinjaman aktif 1", text(page, "#dPinjamanAktif") == "1", text(page, "#dPinjamanAktif"))
        check("A: belum bayar 10", text(page, "#dBelum") == "10", text(page, "#dBelum"))
        check("A: badge angsuran 10", text(page, "#badgeAngsuran") == "10", text(page, "#badgeAngsuran"))
        check("A: cardPengguna tersembunyi untuk anggota", not visible(page, "#cardPengguna"))
        check("A: cardTambahAnggota tersembunyi untuk anggota", not visible(page, "#cardTambahAnggota"))
        check("A: cardSandiSaya terlihat untuk anggota", visible(page, "#cardSandiSaya"))

        tab(page, "anggota")
        check("A: tab anggota hanya Budi", "Budi Santoso" in text(page, "#daftarAnggota") and "Sari Dewi" not in text(page, "#daftarAnggota"))
        check("A: ringkasan anggota 1", "1 anggota" in text(page, "#ringkasanAnggota"))
        tab(page, "simpanan")
        check("A: cardTambahSimpanan tersembunyi untuk anggota", not visible(page, "#cardTambahSimpanan"))
        check("A: simpanan hanya milik Budi (5 catatan, 1.050.000)", "5 catatan simpanan" in text(page, "#ringkasanSimpanan") and "Rp1.050.000" in text(page, "#ringkasanSimpanan"), text(page, "#ringkasanSimpanan"))
        tab(page, "pinjaman")
        check("A: cardTambahPinjaman tersembunyi untuk anggota", not visible(page, "#cardTambahPinjaman"))
        check("A: pinjaman hanya 1 milik Budi", "1 pinjaman (1 aktif)" in text(page, "#ringkasanPinjaman"), text(page, "#ringkasanPinjaman"))
        tab(page, "laporan")
        check("A: laporan hanya 1 baris Budi", "Budi Santoso" in text(page, "#tabelLaporan") and "Sari Dewi" not in text(page, "#tabelLaporan"))
        tab(page, "angsuran")
        check("A: angsuran milik Budi 10 belum", "10 angsuran belum dibayar" in text(page, "#ringkasanAngsuran"), text(page, "#ringkasanAngsuran"))
        check("A: anggota bisa tandai bayar angsurannya sendiri", visible(page, "[data-bayar]"))

        # Ganti sandi anggota round-trip
        tab(page, "dashboard")
        page.fill("#sandiLama", "anggota123")
        page.fill("#sandiBaru", "anggota456")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        check("A: ganti sandi anggota berhasil", "berhasil diubah" in text(page, "#pesanSandi"))
        logout(page)
        login(page, "anggota", "anggota456")
        check("A: anggota masuk dengan sandi baru", "Budi Santoso (Anggota)" in text(page, "#userChip"))
        page.fill("#sandiLama", "anggota456")
        page.fill("#sandiBaru", "anggota123")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        logout(page)
        login(page, "anggota", "anggota123")
        check("A: anggota kembali ke anggota123", "Budi Santoso (Anggota)" in text(page, "#userChip"))
        logout(page)

        # ================= FASE B — pengurus =================
        login(page, "pengurus", "pengurus123")
        check("B: pengurus masuk, chip Dedi Kurniawan", "Dedi Kurniawan (Pengurus)" in text(page, "#userChip"))
        check("B: anggota 8", text(page, "#dAnggota") == "8", text(page, "#dAnggota"))
        check("B: simpanan 6.700.000", text(page, "#dSimpanan") == rupiah(6700000), text(page, "#dSimpanan"))
        check("B: sisa pokok 44.442.772", text(page, "#dSisaPokok") == rupiah(44442772), text(page, "#dSisaPokok"))
        check("B: angsuran/bln 5.117.526", text(page, "#dAngsuranBln") == rupiah(5117526), text(page, "#dAngsuranBln"))
        check("B: segera 5", text(page, "#dSegera") == "5", text(page, "#dSegera"))
        check("B: lewat 3", text(page, "#dLewat") == "3", text(page, "#dLewat"))
        check("B: pinjaman aktif 7", text(page, "#dPinjamanAktif") == "7", text(page, "#dPinjamanAktif"))
        check("B: belum bayar 67", text(page, "#dBelum") == "67", text(page, "#dBelum"))
        check("B: cardPengguna tersembunyi untuk pengurus", not visible(page, "#cardPengguna"))
        check("B: cardTambahAnggota terlihat untuk pengurus", visible(page, "#cardTambahAnggota"))

        # Tambah simpanan sukarela Budi 50.000
        tab(page, "simpanan")
        check("B: cardTambahSimpanan terlihat untuk pengurus", visible(page, "#cardTambahSimpanan"))
        page.select_option("#sAnggota", "1")
        page.select_option("#sJenis", "sukarela")
        page.fill("#sJumlah", "50000")
        page.click("#btnTambahSimpanan")
        page.wait_for_timeout(300)
        check("B: simpanan tersimpan", "tersimpan (pencatatan)" in text(page, "#pesanSimpanan"), text(page, "#pesanSimpanan"))
        tab(page, "dashboard")
        check("B: total simpanan jadi 6.750.000", text(page, "#dSimpanan") == rupiah(6750000), text(page, "#dSimpanan"))
        tab(page, "anggota")
        page.fill("#cariAnggota", "Budi")
        page.wait_for_timeout(300)
        check("B: simpanan Budi jadi 1.100.000", "Rp1.100.000" in text(page, "#daftarAnggota"))
        page.fill("#cariAnggota", "")
        page.wait_for_timeout(200)

        # Tambah anggota baru lalu hapus
        tab(page, "dashboard")
        page.fill("#qNamaAnggota", "Tono Wijaya")
        page.fill("#qTelpAnggota", "081234567809")
        page.fill("#qAlamatAnggota", "Jl. Mawar No. 3")
        page.click("#btnTambahAnggota")
        page.wait_for_timeout(300)
        check("B: anggota baru KOP-009 tersimpan", "KOP-009" in text(page, "#pesanTambahAnggota"), text(page, "#pesanTambahAnggota"))
        check("B: anggota jadi 9", text(page, "#dAnggota") == "9", text(page, "#dAnggota"))
        tab(page, "anggota")
        page.fill("#cariAnggota", "Tono")
        page.wait_for_timeout(300)
        page.click("[data-hapus-anggota]")
        page.wait_for_timeout(300)
        page.click("#modalYa")
        page.wait_for_timeout(400)
        tab(page, "dashboard")
        check("B: anggota kembali 8 setelah hapus Tono", text(page, "#dAnggota") == "8", text(page, "#dAnggota"))

        # Hapus Budi diblokir (masih ada simpanan/pinjaman)
        tab(page, "anggota")
        page.fill("#cariAnggota", "Budi")
        page.wait_for_timeout(300)
        page.click("[data-hapus-anggota]")
        page.wait_for_timeout(300)
        check("B: hapus Budi diblokir (ada simpanan/pinjaman)", "tidak bisa dihapus" in text(page, "#toast"), text(page, "#toast"))
        page.fill("#cariAnggota", "")
        page.wait_for_timeout(200)
        logout(page)

        # ================= FASE C — admin =================
        login(page, "admin", "admin123")
        check("C: admin masuk", "Administrator (Admin)" in text(page, "#userChip"))
        check("C: anggota 8", text(page, "#dAnggota") == "8", text(page, "#dAnggota"))
        check("C: simpanan 6.750.000 (termasuk +50rb fase B)", text(page, "#dSimpanan") == rupiah(6750000), text(page, "#dSimpanan"))
        check("C: sisa pokok 44.442.772", text(page, "#dSisaPokok") == rupiah(44442772), text(page, "#dSisaPokok"))
        check("C: segera 5", text(page, "#dSegera") == "5", text(page, "#dSegera"))
        check("C: lewat 3", text(page, "#dLewat") == "3", text(page, "#dLewat"))

        # Jadwal modal pinjaman Budi
        tab(page, "pinjaman")
        page.click("[data-jadwal='1']")
        page.wait_for_timeout(300)
        check("C: modal jadwal terbuka", visible(page, "#modalJadwalBack"))
        tabel_j = text(page, "#tabelJadwalModal")
        check("C: jadwal Budi bln1 bunga 100.000", "Rp100.000" in tabel_j, tabel_j[:200])
        check("C: jadwal Budi bln1 sisa 9.211.512", "Rp9.211.512" in tabel_j)
        check("C: jadwal Budi bln12 sisa Rp0", "Rp0" in tabel_j)
        page.click("#modalJadwalTutup")
        page.wait_for_timeout(200)
        check("C: modal jadwal tertutup", not visible(page, "#modalJadwalBack"))

        # Angsuran: filter lewat = 3, tandai bayar Joko bln 1
        tab(page, "angsuran")
        page.click("#chipsAngsuran .chip[data-f='lewat']")
        page.wait_for_timeout(300)
        check("C: filter lewat = 3 angsuran", "3 angsuran belum dibayar" in text(page, "#ringkasanAngsuran"), text(page, "#ringkasanAngsuran"))
        check("C: lewat berisi Joko Konsumsi bln 1", "Pinjaman Konsumsi" in text(page, "#daftarAngsuran"))
        page.click("[data-bayar='5:1']")
        page.wait_for_timeout(400)
        check("C: lewat jadi 2 setelah bayar Joko bln 1", "lewat 2" in text(page, "#ringkasanAngsuran"), text(page, "#ringkasanAngsuran"))
        tab(page, "dashboard")
        check("C: belum bayar jadi 66", text(page, "#dBelum") == "66", text(page, "#dBelum"))

        # Salin pengingat WA (Rina bln 7, lewat)
        tab(page, "angsuran")
        page.click("#chipsAngsuran .chip[data-f='lewat']")
        page.wait_for_timeout(300)
        page.click("[data-ingat='0']")
        page.wait_for_timeout(300)
        kotak = text(page, "#kotakPengingat")
        check("C: pengingat menyebut Rina Marlina", "Rina Marlina" in kotak, kotak)
        check("C: pengingat menyebut bukan tagihan resmi", "bukan tagihan resmi" in kotak)
        page.click("#chipsAngsuran .chip[data-f='semua']")
        page.wait_for_timeout(200)

        # Tambah pinjaman RESTORE-TEST untuk Maya (mulai 20 Des 2026 -> bln 1 belum segera)
        tab(page, "pinjaman")
        page.select_option("#pAnggota", "8")
        page.fill("#pNama", "RESTORE-TEST")
        page.fill("#pPokok", "12000000")
        page.fill("#pBunga", "12")
        page.fill("#pTenor", "12")
        page.fill("#pMulai", "2026-12-20")
        page.click("#btnTambahPinjaman")
        page.wait_for_timeout(300)
        check("C: RESTORE-TEST tersimpan, angsuran 1.066.185", "1.066.185" in text(page, "#pesanPinjaman"), text(page, "#pesanPinjaman"))
        tab(page, "dashboard")
        check("C: sisa pokok jadi 55.961.196 (Joko bln1 sudah dibayar)", text(page, "#dSisaPokok") == rupiah(55961196), text(page, "#dSisaPokok"))
        check("C: angsuran/bln jadi 6.183.711", text(page, "#dAngsuranBln") == rupiah(6183711), text(page, "#dAngsuranBln"))
        check("C: pinjaman aktif jadi 8", text(page, "#dPinjamanAktif") == "8", text(page, "#dPinjamanAktif"))
        check("C: belum bayar jadi 78", text(page, "#dBelum") == "78", text(page, "#dBelum"))

        # Backup JSON
        tab(page, "laporan")
        with page.expect_download() as dl:
            page.click("#btnBackup")
        backup_path = Path(dl.value.path())
        backup_data = json.loads(backup_path.read_text(encoding="utf-8"))
        check("C: backup JSON berisi state+users", "state" in backup_data and "users" in backup_data)
        check("C: backup berisi RESTORE-TEST", "RESTORE-TEST" in backup_path.read_text(encoding="utf-8"))

        # Reset -> seed kembali
        page.click("#btnResetData")
        page.wait_for_timeout(300)
        page.click("#modalYa")
        page.wait_for_timeout(400)
        tab(page, "dashboard")
        check("C: reset kembalikan simpanan seed 6.700.000", text(page, "#dSimpanan") == rupiah(6700000), text(page, "#dSimpanan"))
        check("C: reset kembalikan sisa pokok 44.442.772", text(page, "#dSisaPokok") == rupiah(44442772), text(page, "#dSisaPokok"))
        tab(page, "pinjaman")
        page.fill("#cariPinjaman", "RESTORE-TEST")
        page.wait_for_timeout(300)
        check("C: RESTORE-TEST hilang setelah reset", "Tidak ada pinjaman yang cocok" in text(page, "#daftarPinjaman"))
        page.fill("#cariPinjaman", "")
        page.wait_for_timeout(200)

        # Restore dari backup
        page.set_input_files("#inputRestore", str(backup_path))
        page.wait_for_timeout(500)
        check("C: restore berhasil (toast)", "berhasil dipulihkan" in text(page, "#toast"))
        tab(page, "dashboard")
        check("C: sisa pokok kembali 55.961.196 setelah restore", text(page, "#dSisaPokok") == rupiah(55961196), text(page, "#dSisaPokok"))
        check("C: simpanan kembali 6.750.000 setelah restore", text(page, "#dSimpanan") == rupiah(6750000), text(page, "#dSimpanan"))
        tab(page, "pinjaman")
        page.fill("#cariPinjaman", "RESTORE-TEST")
        page.wait_for_timeout(300)
        check("C: RESTORE-TEST kembali setelah restore", "RESTORE-TEST" in text(page, "#daftarPinjaman"))
        page.fill("#cariPinjaman", "")
        page.wait_for_timeout(200)

        # Restore file tidak valid ditolak
        bad = Path("/tmp/koperasi_bad_restore.json")
        bad.write_text("{bukan json", encoding="utf-8")
        page.set_input_files("#inputRestore", str(bad))
        page.wait_for_timeout(500)
        check("C: file cadangan tidak valid ditolak", "tidak valid" in text(page, "#toast"))
        tab(page, "dashboard")
        check("C: sisa pokok tetap 55.961.196 setelah restore gagal", text(page, "#dSisaPokok") == rupiah(55961196), text(page, "#dSisaPokok"))

        # CSV laporan (8 anggota + header)
        tab(page, "laporan")
        check("C: laporan total simpanan 6.750.000", "Rp6.750.000" in text(page, "#ringkasanLaporan"), text(page, "#ringkasanLaporan"))
        with page.expect_download() as dl2:
            page.click("#btnCsvLaporan")
        csv_path = Path(dl2.value.path())
        csv_text = csv_path.read_text(encoding="utf-8")
        lines = [l for l in csv_text.strip().split("\n") if l.strip()]
        check("C: CSV punya header + 8 baris", len(lines) == 9, f"baris={len(lines)}")
        check("C: CSV berisi Budi Santoso", "Budi Santoso" in csv_text)
        check("C: CSV berisi Dewi Lestari", "Dewi Lestari" in csv_text)
        check("C: CSV berisi sisa pokok Maya 12000000", "12000000" in csv_text)
        check("C: CSV header berisi Total Simpanan", "Total Simpanan" in lines[0])

        # Hapus RESTORE-TEST -> sisa kembali 44.442.772
        tab(page, "pinjaman")
        page.fill("#cariPinjaman", "RESTORE-TEST")
        page.wait_for_timeout(300)
        page.click("[data-hapus-pinjaman]")
        page.wait_for_timeout(300)
        page.click("#modalYa")
        page.wait_for_timeout(400)
        tab(page, "dashboard")
        check("C: sisa pokok 43.961.196 setelah hapus RESTORE-TEST", text(page, "#dSisaPokok") == rupiah(43961196), text(page, "#dSisaPokok"))

        # Reset sandi pengurus oleh admin -> bk123, lalu kembali ke pengurus123
        page.fill("#pgUser", "uji-reset")
        page.fill("#pgNama", "Uji Reset")
        page.fill("#pgPass", "uji12345")
        page.select_option("#pgPeran", "pengurus")
        page.click("#btnTambahPengguna")
        page.wait_for_timeout(300)
        check("C: pengguna uji-reset ditambahkan", "Uji Reset" in text(page, "#daftarPengguna"))
        page.click("[data-reset='uji-reset']")
        page.wait_for_timeout(300)
        page.click("#modalYa")
        page.wait_for_timeout(300)
        check("C: reset sandi uji-reset berhasil (toast)", "bk123" in text(page, "#toast"))
        logout(page)
        login(page, "uji-reset", "bk123")
        check("C: uji-reset masuk dengan bk123", "Uji Reset (Pengurus)" in text(page, "#userChip"))
        page.fill("#sandiLama", "bk123")
        page.fill("#sandiBaru", "uji12345")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        check("C: uji-reset ganti sandi setelah reset berhasil", "berhasil diubah" in text(page, "#pesanSandi"))
        logout(page)
        login(page, "admin", "admin123")
        check("C: admin kembali masuk", "Administrator (Admin)" in text(page, "#userChip"))

        # Ganti sandi admin round-trip (setelah restore — uji ikat ulang currentUser)
        page.fill("#sandiLama", "admin123")
        page.fill("#sandiBaru", "admin456")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        check("C: ganti sandi admin setelah restore berhasil", "berhasil diubah" in text(page, "#pesanSandi"))
        logout(page)
        login(page, "admin", "admin456")
        check("C: admin masuk dengan sandi baru", "Administrator (Admin)" in text(page, "#userChip"))
        page.fill("#sandiLama", "admin456")
        page.fill("#sandiBaru", "admin123")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        logout(page)
        login(page, "admin", "admin123")
        check("C: admin kembali ke admin123", "Administrator (Admin)" in text(page, "#userChip"))
        logout(page)

        # ================= FASE D — anggota tandai bayar sendiri =================
        login(page, "anggota", "anggota123")
        check("D: anggota masuk lagi", "Budi Santoso (Anggota)" in text(page, "#userChip"))
        check("D: segera 1 sebelum bayar", text(page, "#dSegera") == "1", text(page, "#dSegera"))
        tab(page, "angsuran")
        check("D: tombol bayar Budi bln 3 terlihat", visible(page, "[data-bayar='1:3']"))
        page.click("[data-bayar='1:3']")
        page.wait_for_timeout(400)
        tab(page, "dashboard")
        check("D: segera 0 setelah bayar bln 3", text(page, "#dSegera") == "0", text(page, "#dSegera"))
        check("D: belum bayar 9 setelah bayar bln 3", text(page, "#dBelum") == "9", text(page, "#dBelum"))
        check("D: sisa pokok 7.610.803 setelah bayar bln 3", text(page, "#dSisaPokok") == rupiah(7610803), text(page, "#dSisaPokok"))

        browser.close()

    print(f"\nLOLOS: {passed}  GAGAL: {len(failures)}")
    if failures:
        print("Gagal:", failures)
    print("Console errors:", console_errors)
    print("Page errors:", page_errors)
    return 0 if not failures and not console_errors and not page_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
