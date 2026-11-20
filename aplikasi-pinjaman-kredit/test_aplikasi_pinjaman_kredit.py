"""Tes Aplikasi Pinjaman & Kredit (Simulasi) (file lokal, Playwright Chromium).
Hari ini 2026-11-20. Data seed (tanggal relatif):
  Admin — 4 rencana:
    KPR Rumah 300jt/8%/120, mulai 20 Sep 2026: angsuran 3.639.828, total 436.779.360,
      bunga 136.779.360; bln 1-2 dibayar; sisa pokok 296.709.412; bln 3 (20 Nov) Segera.
    Kredit Motor 24jt/12%/24, mulai 22 Agu 2026: angsuran 1.129.763, total 27.114.312,
      bunga 3.114.312; bln 1-3 dibayar; sisa pokok 21.303.928; bln 4 (22 Nov) Segera.
    Pinjaman Renovasi 50jt/10%/36, mulai 4 Mei 2026: angsuran 1.613.359, total 58.080.924,
      bunga 8.080.924; bln 1-6 dibayar; sisa pokok 42.668.585; bln 7 (4 Nov) Lewat.
    Cicilan TV 6jt/0%/6, mulai 24 Mei 2026: angsuran 1.000.000; semua 6 bln dibayar = Lunas.
  Pengguna Budi Santoso — 2 rencana:
    Cicilan HP 6jt/12%/12, mulai 21 Okt 2026: angsuran 533.093, total 6.397.116,
      bunga 397.116; bln 1 dibayar; sisa pokok 5.526.907; bln 2 (21 Nov) Segera.
    Pinjaman Online 3jt/24%/6, mulai 6 Okt 2026: angsuran 535.577, total 3.213.462,
      bunga 213.462; bln 1 (6 Okt) + bln 2 (6 Nov) Lewat; sisa pokok 3.000.000.
  Dasbor seed: admin pokok aktif 369.208.832, angsuran/bln 7.451.620, segera 3, lewat 3,
    badge angsuran 186 (118+21+30+11+6); pengguna pokok aktif 8.526.907,
    angsuran/bln 1.068.670, segera 1, lewat 2, badge 17.
  Simulasi silang Python: 120jt/12%/12 -> angsuran 10.661.855, total 127.942.260,
    bunga 7.942.260; bln1 bunga 1.200.000, pokok 9.461.855, sisa 110.538.145.
  Perbandingan: A 24jt/12%/24 (1.129.763/bln, total 27.114.312) vs B 24jt/10%/36
    (774.412/bln, total 27.878.832) -> A lebih murah 764.520.
Urutan tes: A pengguna (baseline + simulasi + simpan + banding + angsuran + bayar),
  B admin (baseline + cicilan + jadwal + reset sandi), C pengguna (cek sandi baru),
  D admin (simulasi cepat + hapus + RESTORE-TEST + backup/reset/restore + CSV +
  hapus + ganti sandi + panduan).
"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = "file://" + str(ROOT / "aplikasi-pinjaman-kredit" / "index.html")

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

        # ---------- Label simulasi ----------
        check("hero bertuliskan SIMULASI PERENCANAAN", "SIMULASI PERENCANAAN" in text(page, ".hero"))
        check("hero menegaskan bukan pemberi pinjaman", "BUKAN PEMBERI PINJAMAN" in text(page, ".hero"))
        check("login menegaskan bukan pemberi pinjaman", "BUKAN PEMBERI PINJAMAN" in text(page, "#loginOverlay"))
        check("panduan menegaskan bukan pemberi pinjaman", "bukan pemberi pinjaman" in text(page, "#panel-panduan"))

        # ---------- Login salah ----------
        page.fill("#loginUser", "admin")
        page.fill("#loginPass", "salah123")
        page.click("#formLogin button[type=submit]")
        page.wait_for_timeout(300)
        check("login salah menampilkan error", visible(page, "#loginError"))

        # ================= FASE A — pengguna =================
        login(page, "pengguna", "pengguna123")
        check("pengguna masuk, chip Budi Santoso", "Budi Santoso (Pengguna)" in text(page, "#userChip"))
        check("A: mendarat di dasbor (panel aktif)", "active" in (page.get_attribute("#panel-dashboard", "class") or ""))
        check("A: pokok aktif 8.526.907", text(page, "#dPokok") == rupiah(8526907), text(page, "#dPokok"))
        check("A: angsuran/bln 1.068.670", text(page, "#dAngsuran") == rupiah(1068670), text(page, "#dAngsuran"))
        check("A: segera 1", text(page, "#dSegera") == "1", text(page, "#dSegera"))
        check("A: lewat 2", text(page, "#dLewat") == "2", text(page, "#dLewat"))
        check("A: badge angsuran 17", text(page, "#badgeAngsuran") == "17", text(page, "#badgeAngsuran"))
        check("A: cardPengguna tersembunyi untuk pengguna", not visible(page, "#cardPengguna"))
        check("A: cardSandiSaya terlihat untuk pengguna", visible(page, "#cardSandiSaya"))

        # Simulasi tab — 120jt/12%/12
        tab(page, "simulasi")
        page.fill("#sPokok", "120000000")
        page.fill("#sBunga", "12")
        page.fill("#sTenor", "12")
        page.click("#btnHitungSimulasi")
        page.wait_for_timeout(300)
        check("A simulasi: angsuran 10.661.855", text(page, "#hAngsuran") == rupiah(10661855), text(page, "#hAngsuran"))
        check("A simulasi: total bunga 7.942.260", text(page, "#hBunga") == rupiah(7942260), text(page, "#hBunga"))
        check("A simulasi: total bayar 127.942.260", text(page, "#hTotal") == rupiah(127942260), text(page, "#hTotal"))
        tabel = text(page, "#tabelSimulasi")
        check("A jadwal bln1 bunga 1.200.000", "Rp1.200.000" in tabel, tabel[:200])
        check("A jadwal bln1 sisa 110.538.145", "Rp110.538.145" in tabel)
        check("A jadwal bln12 sisa Rp0", "Rp0" in tabel)

        # Bunga 0%
        page.fill("#sPokok", "6000000")
        page.fill("#sBunga", "0")
        page.fill("#sTenor", "6")
        page.click("#btnHitungSimulasi")
        page.wait_for_timeout(300)
        check("A simulasi 0%: angsuran 1.000.000", text(page, "#hAngsuran") == rupiah(1000000), text(page, "#hAngsuran"))
        check("A simulasi 0%: total bunga Rp0", text(page, "#hBunga") == rupiah(0), text(page, "#hBunga"))

        # Simpan tanpa nama ditolak, lalu simpan 120jt sebagai "Simulasi Uji"
        page.fill("#sPokok", "120000000")
        page.fill("#sBunga", "12")
        page.fill("#sTenor", "12")
        page.click("#btnHitungSimulasi")
        page.wait_for_timeout(300)
        page.click("#btnSimpanSimulasi")
        page.wait_for_timeout(300)
        check("A simpan tanpa nama ditolak", "Isi nama rencana dulu" in text(page, "#pesanSimulasi"))
        page.fill("#sNama", "Simulasi Uji")
        page.click("#btnHitungSimulasi")
        page.wait_for_timeout(300)
        page.click("#btnSimpanSimulasi")
        page.wait_for_timeout(300)
        check("A simpan Simulasi Uji berhasil", "tersimpan (simulasi)" in text(page, "#pesanSimulasi"))
        tab(page, "dashboard")
        check("A pokok aktif jadi 128.526.907", text(page, "#dPokok") == rupiah(128526907), text(page, "#dPokok"))
        check("A angsuran/bln jadi 11.730.525", text(page, "#dAngsuran") == rupiah(11730525), text(page, "#dAngsuran"))
        check("A segera jadi 2 (Simulasi Uji bln1 hari ini)", text(page, "#dSegera") == "2", text(page, "#dSegera"))

        # Perbandingan A vs B
        tab(page, "perbandingan")
        page.fill("#aPokok", "24000000"); page.fill("#aBunga", "12"); page.fill("#aTenor", "24")
        page.fill("#bPokok", "24000000"); page.fill("#bBunga", "10"); page.fill("#bTenor", "36")
        page.click("#btnBanding")
        page.wait_for_timeout(300)
        check("A banding: angsuran A 1.129.763", "Rp1.129.763" in text(page, "#tabelBanding"))
        check("A banding: angsuran B 774.412", "Rp774.412" in text(page, "#tabelBanding"))
        check("A banding: total A 27.114.312", "Rp27.114.312" in text(page, "#tabelBanding"))
        check("A banding: total B 27.878.832", "Rp27.878.832" in text(page, "#tabelBanding"))
        check("A banding: putusan A lebih murah 764.520", "Skema A lebih murah" in text(page, "#putusanBanding") and "Rp764.520" in text(page, "#putusanBanding"), text(page, "#putusanBanding"))

        # Angsuran tab — filter
        tab(page, "angsuran")
        check("A angsuran semua = 29 baris (17+12)", "29 angsuran" in text(page, "#ringkasanAngsuran"), text(page, "#ringkasanAngsuran"))
        page.click("#chipsAngsuran .chip[data-f='segera']")
        page.wait_for_timeout(300)
        check("A angsuran segera = 2 baris", "2 angsuran" in text(page, "#ringkasanAngsuran"), text(page, "#ringkasanAngsuran"))
        page.click("#chipsAngsuran .chip[data-f='lewat']")
        page.wait_for_timeout(300)
        check("A angsuran lewat = 2 baris", "2 angsuran" in text(page, "#ringkasanAngsuran"), text(page, "#ringkasanAngsuran"))
        page.click("#chipsAngsuran .chip[data-f='bulanini']")
        page.wait_for_timeout(300)
        check("A angsuran bulan ini = 3 baris", "3 angsuran" in text(page, "#ringkasanAngsuran"), text(page, "#ringkasanAngsuran"))
        page.click("#chipsAngsuran .chip[data-f='segera']")
        page.wait_for_timeout(300)
        # Salin pengingat baris pertama (Simulasi Uji bln1, jatuh tempo hari ini)
        page.click("[data-ingat='0']")
        page.wait_for_timeout(300)
        check("A kotak pengingat muncul", visible(page, "#kotakPengingat"))
        check("A teks pengingat berisi Simulasi Uji", "Simulasi Uji" in text(page, "#kotakPengingat"), text(page, "#kotakPengingat"))
        check("A teks pengingat menegaskan simulasi", "hanya contoh pengingat simulasi" in text(page, "#kotakPengingat"))
        # Tandai sudah bayar HP bln2 (baris kedua di filter segera)
        page.click("[data-bayar='5:2']")
        page.wait_for_timeout(400)
        check("A bayar HP bln2 berhasil (toast)", "ditandai sudah dibayar" in text(page, "#toast"), text(page, "#toast"))
        tab(page, "dashboard")
        check("A segera kembali 1 setelah bayar", text(page, "#dSegera") == "1", text(page, "#dSegera"))
        check("A pokok aktif 128.049.084 setelah bayar", text(page, "#dPokok") == rupiah(128049084), text(page, "#dPokok"))
        logout(page)

        # ================= FASE B — admin =================
        login(page, "admin", "admin123")
        check("B admin masuk", "Administrator (Admin)" in text(page, "#userChip"))
        check("B pokok aktif 488.731.009", text(page, "#dPokok") == rupiah(488731009), text(page, "#dPokok"))
        check("B angsuran/bln 18.113.475", text(page, "#dAngsuran") == rupiah(18113475), text(page, "#dAngsuran"))
        check("B segera 3", text(page, "#dSegera") == "3", text(page, "#dSegera"))
        check("B lewat 3", text(page, "#dLewat") == "3", text(page, "#dLewat"))
        check("B badge angsuran 197", text(page, "#badgeAngsuran") == "197", text(page, "#badgeAngsuran"))
        check("B cardPengguna terlihat untuk admin", visible(page, "#cardPengguna"))
        check("B cardSandiSaya terlihat untuk admin", visible(page, "#cardSandiSaya"))

        # Cicilan tab — filter
        tab(page, "cicilan")
        check("B cicilan aktif = 6 rencana", "6 rencana" in text(page, "#ringkasanCicilan"), text(page, "#ringkasanCicilan"))
        page.select_option("#fStatusRencana", "lunas")
        page.wait_for_timeout(300)
        check("B cicilan lunas = 1 rencana (TV)", "1 rencana" in text(page, "#ringkasanCicilan"), text(page, "#ringkasanCicilan"))
        check("B daftar lunas berisi Cicilan TV", "Cicilan TV" in text(page, "#daftarRencana"))
        page.select_option("#fStatusRencana", "semua")
        page.fill("#cariRencana", "KPR")
        page.wait_for_timeout(300)
        check("B cari KPR = 1 rencana", "1 rencana" in text(page, "#ringkasanCicilan"), text(page, "#ringkasanCicilan"))
        page.fill("#cariRencana", "")
        page.select_option("#fStatusRencana", "aktif")
        page.wait_for_timeout(300)

        # Jadwal tab — KPR
        tab(page, "jadwal")
        page.select_option("#jRencana", "1")
        page.wait_for_timeout(300)
        check("B jadwal KPR ringkasan berisi angsuran 3.639.828", "Rp3.639.828" in text(page, "#ringkasanJadwal"), text(page, "#ringkasanJadwal"))
        check("B jadwal KPR dibayar 2/120", "dibayar 2/120" in text(page, "#ringkasanJadwal"))
        tabel = text(page, "#tabelJadwal")
        check("B jadwal KPR bln1 bunga 2.000.000", "Rp2.000.000" in tabel)
        check("B jadwal KPR bln1 sisa 298.360.172", "Rp298.360.172" in tabel)
        check("B jadwal KPR bln3 Segera", "Segera" in tabel)

        # Reset sandi pengguna -> bk123
        tab(page, "dashboard")
        page.click("[data-reset='pengguna']")
        page.wait_for_timeout(300)
        page.click("#modalYa")
        page.wait_for_timeout(300)
        check("B reset sandi pengguna ke bk123", "direset ke bk123" in text(page, "#toast"))
        logout(page)
        login(page, "pengguna", "bk123")
        check("B pengguna masuk dengan bk123", "Budi Santoso (Pengguna)" in text(page, "#userChip"))

        # ================= FASE C — pengguna ganti sandi kembali =================
        page.fill("#sandiLama", "bk123")
        page.fill("#sandiBaru", "pengguna123")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        check("C ganti sandi kembali berhasil", "berhasil diubah" in text(page, "#pesanSandi"))
        logout(page)
        login(page, "pengguna", "pengguna123")
        check("C pengguna masuk lagi dengan pengguna123", "Budi Santoso (Pengguna)" in text(page, "#userChip"))
        check("C segera pengguna 1 (Simulasi Uji bln1)", text(page, "#dSegera") == "1", text(page, "#dSegera"))
        check("C lewat pengguna 2", text(page, "#dLewat") == "2", text(page, "#dLewat"))
        logout(page)

        # ================= FASE D — admin: simulasi cepat, hapus, backup/restore =================
        login(page, "admin", "admin123")
        page.fill("#qNama", "Rencana Cepat")
        page.fill("#qPokok", "50000000")
        page.fill("#qBunga", "10")
        page.fill("#qTenor", "36")
        page.click("#btnHitungCepat")
        page.wait_for_timeout(300)
        check("D simulasi cepat angsuran 1.613.359", "Rp1.613.359" in text(page, "#qHasil"), text(page, "#qHasil"))
        page.click("#btnSimpanCepat")
        page.wait_for_timeout(300)
        check("D simpan Rencana Cepat berhasil", "tersimpan (simulasi)" in text(page, "#pesanCepat"))
        check("D pokok aktif 538.731.009", text(page, "#dPokok") == rupiah(538731009), text(page, "#dPokok"))
        check("D angsuran/bln 19.726.834", text(page, "#dAngsuran") == rupiah(19726834), text(page, "#dAngsuran"))

        # Hapus Rencana Cepat
        tab(page, "cicilan")
        page.fill("#cariRencana", "Rencana Cepat")
        page.wait_for_timeout(300)
        page.click("[data-hapus-rencana]")
        page.wait_for_timeout(300)
        page.click("#modalYa")
        page.wait_for_timeout(400)
        tab(page, "dashboard")
        check("D pokok aktif kembali 488.731.009", text(page, "#dPokok") == rupiah(488731009), text(page, "#dPokok"))

        # Penanda RESTORE-TEST lewat simulasi
        tab(page, "simulasi")
        page.fill("#sNama", "RESTORE-TEST")
        page.fill("#sPokok", "12000000")
        page.fill("#sBunga", "12")
        page.fill("#sTenor", "12")
        page.click("#btnHitungSimulasi")
        page.wait_for_timeout(300)
        check("D RESTORE-TEST angsuran 1.066.185", text(page, "#hAngsuran") == rupiah(1066185), text(page, "#hAngsuran"))
        page.click("#btnSimpanSimulasi")
        page.wait_for_timeout(300)
        check("D RESTORE-TEST tersimpan", "tersimpan (simulasi)" in text(page, "#pesanSimulasi"))
        tab(page, "dashboard")
        check("D pokok aktif 500.731.009", text(page, "#dPokok") == rupiah(500731009), text(page, "#dPokok"))

        # Backup
        tab(page, "cicilan")
        with page.expect_download() as dl:
            page.click("#btnBackup")
        backup_path = Path(dl.value.path())
        backup_data = json.loads(backup_path.read_text(encoding="utf-8"))
        check("D backup JSON berisi state+users", "state" in backup_data and "users" in backup_data)
        check("D backup berisi RESTORE-TEST", "RESTORE-TEST" in backup_path.read_text(encoding="utf-8"))

        # Reset -> seed kembali
        page.click("#btnResetData")
        page.wait_for_timeout(300)
        page.click("#modalYa")
        page.wait_for_timeout(400)
        tab(page, "dashboard")
        check("D reset kembalikan pokok seed 369.208.832", text(page, "#dPokok") == rupiah(369208832), text(page, "#dPokok"))
        check("D reset kembalikan angsuran/bln 7.451.620", text(page, "#dAngsuran") == rupiah(7451620), text(page, "#dAngsuran"))
        tab(page, "cicilan")
        page.fill("#cariRencana", "RESTORE-TEST")
        page.wait_for_timeout(300)
        check("D RESTORE-TEST hilang setelah reset", "Tidak ada rencana yang cocok" in text(page, "#daftarRencana"))
        page.fill("#cariRencana", "")
        page.wait_for_timeout(200)

        # Restore dari backup
        page.set_input_files("#inputRestore", str(backup_path))
        page.wait_for_timeout(500)
        check("D restore berhasil (toast)", "berhasil dipulihkan" in text(page, "#toast"))
        tab(page, "dashboard")
        check("D pokok kembali 500.731.009 setelah restore", text(page, "#dPokok") == rupiah(500731009), text(page, "#dPokok"))
        tab(page, "cicilan")
        page.fill("#cariRencana", "RESTORE-TEST")
        page.wait_for_timeout(300)
        check("D RESTORE-TEST kembali setelah restore", "RESTORE-TEST" in text(page, "#daftarRencana"))
        page.fill("#cariRencana", "")
        page.wait_for_timeout(200)

        # Restore file tidak valid ditolak
        bad = Path("/tmp/pinjaman_bad_restore.json")
        bad.write_text("{bukan json", encoding="utf-8")
        page.set_input_files("#inputRestore", str(bad))
        page.wait_for_timeout(500)
        check("D file cadangan tidak valid ditolak", "tidak valid" in text(page, "#toast"))
        tab(page, "dashboard")
        check("D pokok tetap 500.731.009 setelah restore gagal", text(page, "#dPokok") == rupiah(500731009), text(page, "#dPokok"))

        # CSV rencana (filter aktif, admin melihat semua):
        # 7 aktif seed+Uji+RESTORE-TEST = 7 baris
        tab(page, "cicilan")
        page.select_option("#fStatusRencana", "aktif")
        page.wait_for_timeout(300)
        with page.expect_download() as dl2:
            page.click("#btnCsvRencana")
        csv_path = Path(dl2.value.path())
        csv_text = csv_path.read_text(encoding="utf-8")
        lines = [l for l in csv_text.strip().split("\n") if l.strip()]
        check("D CSV punya header + 7 baris", len(lines) == 8, f"baris={len(lines)}")
        check("D CSV berisi RESTORE-TEST", "RESTORE-TEST" in csv_text)
        check("D CSV berisi KPR Rumah", "KPR Rumah" in csv_text)
        check("D CSV header berisi Sisa Pokok", "Sisa Pokok" in lines[0])

        # Hapus RESTORE-TEST -> pokok kembali 488.731.009
        page.fill("#cariRencana", "RESTORE-TEST")
        page.wait_for_timeout(300)
        page.click("[data-hapus-rencana]")
        page.wait_for_timeout(300)
        page.click("#modalYa")
        page.wait_for_timeout(400)
        tab(page, "dashboard")
        check("D pokok 488.731.009 setelah hapus RESTORE-TEST", text(page, "#dPokok") == rupiah(488731009), text(page, "#dPokok"))

        # Ganti sandi admin round-trip (setelah restore — uji ikat ulang currentUser)
        page.fill("#sandiLama", "admin123")
        page.fill("#sandiBaru", "admin456")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        check("D ganti sandi admin setelah restore berhasil", "berhasil diubah" in text(page, "#pesanSandi"))
        logout(page)
        login(page, "admin", "admin456")
        check("D admin masuk dengan sandi baru", "Administrator (Admin)" in text(page, "#userChip"))
        page.fill("#sandiLama", "admin456")
        page.fill("#sandiBaru", "admin123")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        logout(page)
        login(page, "admin", "admin123")
        check("D admin kembali ke admin123", "Administrator (Admin)" in text(page, "#userChip"))

        browser.close()

    print(f"\nLOLOS: {passed}  GAGAL: {len(failures)}")
    if failures:
        print("Gagal:", failures)
    print("Console errors:", console_errors)
    print("Page errors:", page_errors)
    return 0 if not failures and not console_errors and not page_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
