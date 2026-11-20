"""Tes otomatis Event Organizer (demo #59). Playwright headless, file lokal.
Jalankan: python3 tests/test_event_organizer.py
"""
import json
import os
import sys
import time

from playwright.sync_api import sync_playwright

BASE = "file://" + os.path.abspath("index.html")
LOLOS = 0
GAGAL = 0
ERRORS = []


def cek(nama, kondisi, detail=""):
    global LOLOS, GAGAL
    if kondisi:
        LOLOS += 1
        print(f"  OK  {nama}")
    else:
        GAGAL += 1
        ERRORS.append(nama)
        print(f"  GAGAL {nama} {detail}")


def teks(page, sel):
    el = page.query_selector(sel)
    return el.inner_text().strip() if el else ""


def toast_text(page):
    time.sleep(0.25)
    el = page.query_selector("#toast")
    return el.inner_text().strip() if el else ""


def login(page, user, pw):
    page.fill("#loginUser", user)
    page.fill("#loginPass", pw)
    page.click("#formLogin button[type=submit]")
    page.wait_for_timeout(400)


def logout(page):
    page.click("#btnKeluar")
    page.wait_for_timeout(300)


def klik_modal_ya(page):
    page.wait_for_selector("#modalBack.open", timeout=3000)
    page.click("#modalYa")
    page.wait_for_timeout(400)


def tab(page, nama):
    page.click(f"#tabbar [data-tab={nama}]")
    page.wait_for_timeout(300)


def main():
    global LOLOS, GAGAL
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(accept_downloads=True)
        page = ctx.new_page()
        console_errors = []
        page_errors = []
        page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.goto(BASE)
        page.wait_for_timeout(500)

        print("== A. Login & peran ==")
        cek("judul halaman", "Event Organizer" in page.title())
        cek("akun demo tampil di login", "admin / admin123" in teks(page, ".login-note") and "koordinator / koordinator123" in teks(page, ".login-note"))
        login(page, "admin", "salah")
        cek("sandi salah -> error tampil", page.is_visible("#loginError"))
        login(page, "admin", "admin123")
        cek("login admin -> overlay hilang", not page.is_visible("#loginOverlay"))
        cek("chip pengguna admin", "Administrator (Admin)" in teks(page, "#userChip"))
        cek("masuk() mendarat di dasbor", page.query_selector("#panel-dashboard").get_attribute("class") == "panel active")

        print("== B. Dasbor admin (angka seed) ==")
        cek("nilai kontrak Rp790.000.000", teks(page, "#dKontrak") == "Rp790.000.000", teks(page, "#dKontrak"))
        cek("total biaya Rp575.000.000", teks(page, "#dBiaya") == "Rp575.000.000", teks(page, "#dBiaya"))
        cek("laba Rp215.000.000", teks(page, "#dLaba") == "Rp215.000.000", teks(page, "#dLaba"))
        cek("total acara 6", teks(page, "#dAcara") == "6 acara", teks(page, "#dAcara"))
        cek("acara hari ini 0", teks(page, "#dHariIni") == "0 acara", teks(page, "#dHariIni"))
        cek("acara segera 2", teks(page, "#dSegera") == "2 acara", teks(page, "#dSegera"))
        cek("acara lewat 1", teks(page, "#dLewat") == "1 acara", teks(page, "#dLewat"))
        cek("checklist 17/29", teks(page, "#dChecklist") == "17 / 29", teks(page, "#dChecklist"))
        cek("badge acara 6", teks(page, "#badgeAcara") == "6")
        cek("acara dekat ada Pernikahan + Seminar", all(x in teks(page, "#daftarAcaraDekat") for x in ["Pernikahan Andi & Sari", "Seminar Digital Marketing 2026"]))
        cek("progres A4 100% tampil", "4/4" in teks(page, "#daftarProgres"))
        cek("card kelola pengguna tampil untuk admin", page.is_visible("#cardPengguna"))
        tab(page, "acara")
        cek("card tambah acara tampil untuk admin", page.is_visible("#cardTambahAcara"))
        cek("peringatan A1 melebihi anggaran tampil", "Melebihi anggaran Rp5.000.000" in teks(page, "#daftarAcara"), teks(page, "#daftarAcara")[:400])
        tab(page, "dashboard")
        cek("form ganti sandi tampil untuk admin", page.is_visible("#cardSandiSaya"))

        print("== C. Peran manajer & koordinator ==")
        logout(page)
        login(page, "manajer", "manajer123")
        cek("chip manajer", "Dedi Kurniawan (Manajer)" in teks(page, "#userChip"))
        cek("card pengguna tersembunyi untuk manajer", not page.is_visible("#cardPengguna"))
        tab(page, "acara")
        cek("card tambah acara tampil untuk manajer", page.is_visible("#cardTambahAcara"))
        tab(page, "dashboard")
        cek("dasbor manajer kontrak Rp790.000.000", teks(page, "#dKontrak") == "Rp790.000.000", teks(page, "#dKontrak"))
        logout(page)
        login(page, "koordinator", "koordinator123")
        cek("chip koordinator", "Budi Santoso (Koordinator)" in teks(page, "#userChip"))
        cek("card pengguna tersembunyi untuk koordinator", not page.is_visible("#cardPengguna"))
        tab(page, "acara")
        cek("card tambah acara tersembunyi untuk koordinator", not page.is_visible("#cardTambahAcara"))
        tab(page, "dashboard")
        cek("form ganti sandi tampil untuk koordinator", page.is_visible("#cardSandiSaya"))
        cek("dasbor koordinator kontrak Rp265.000.000", teks(page, "#dKontrak") == "Rp265.000.000", teks(page, "#dKontrak"))
        cek("dasbor koordinator biaya Rp210.000.000", teks(page, "#dBiaya") == "Rp210.000.000", teks(page, "#dBiaya"))
        cek("dasbor koordinator laba Rp55.000.000", teks(page, "#dLaba") == "Rp55.000.000", teks(page, "#dLaba"))
        cek("dasbor koordinator acara 3", teks(page, "#dAcara") == "3 acara", teks(page, "#dAcara"))
        cek("dasbor koordinator segera 2", teks(page, "#dSegera") == "2 acara", teks(page, "#dSegera"))
        cek("dasbor koordinator lewat 0", teks(page, "#dLewat") == "0 acara", teks(page, "#dLewat"))
        cek("dasbor koordinator checklist 10/15", teks(page, "#dChecklist") == "10 / 15", teks(page, "#dChecklist"))
        cek("koordinator tidak melihat Konser Amal", "Konser Amal" not in teks(page, "#daftarAcaraDekat") and "Konser Amal" not in teks(page, "#daftarProgres"))
        logout(page)
        login(page, "admin", "admin123")
        tab(page, "laporan")
        page.reload()
        page.wait_for_timeout(500)
        cek("reload: sesi bertahan, chip admin", "Administrator (Admin)" in teks(page, "#userChip"))
        cek("reload: mendarat di dasbor (pelajaran 41)", page.query_selector("#panel-dashboard").get_attribute("class") == "panel active")

        print("== D. Acara & klien ==")
        tab(page, "acara")
        cek("ringkasan acara 6 + 1 melebihi anggaran", "6 acara" in teks(page, "#ringkasanAcara") and "1 acara melebihi anggaran" in teks(page, "#ringkasanAcara"), teks(page, "#ringkasanAcara"))
        cek("daftar acara ada Pameran Otomotif", "Pameran Otomotif 2026" in teks(page, "#daftarAcara"))
        cek("laba A1 negatif tampil (Rp-5.000.000)", "Rp-5.000.000" in teks(page, "#daftarAcara"))
        page.fill("#acNama", "Uji Acara EO")
        page.select_option("#acKlien", "1")
        page.fill("#acTanggal", "2026-12-20")
        page.fill("#acLokasi", "Hall Uji")
        page.fill("#acKontrak", "50000000")
        page.select_option("#acKoordinator", "koordinator")
        page.click("#btnTambahAcara")
        page.wait_for_timeout(400)
        cek("tambah acara Uji Acara EO", "Uji Acara EO" in teks(page, "#daftarAcara") and teks(page, "#badgeAcara") == "7")
        # ubah status acara baru -> Selesai
        page.select_option("[data-status-acara='7']", "Selesai")
        page.wait_for_timeout(400)
        cek("ubah status acara baru ke Selesai", "Selesai" in toast_text(page))
        # hapus acara yang punya data -> ditolak (A1)
        page.click("[data-hapus-acara='1']")
        page.wait_for_timeout(300)
        cek("hapus acara berdata ditolak", "tidak bisa dihapus" in toast_text(page) and teks(page, "#badgeAcara") == "7")
        # hapus acara baru (id 7, tanpa data)
        page.click("[data-hapus-acara='7']")
        klik_modal_ya(page)
        cek("hapus acara baru berhasil", teks(page, "#badgeAcara") == "6" and "Uji Acara EO" not in teks(page, "#daftarAcara"))
        # klien
        page.fill("#klNama", "Uji Klien")
        page.fill("#klTelepon", "0819-0000-0002")
        page.click("#btnTambahKlien")
        page.wait_for_timeout(400)
        cek("tambah klien Uji Klien", "Uji Klien" in teks(page, "#daftarKlien"))
        page.click("[data-hapus-klien='1']")
        page.wait_for_timeout(300)
        cek("hapus klien beracara ditolak", "tidak bisa dihapus" in toast_text(page))
        page.click("[data-hapus-klien='7']")
        klik_modal_ya(page)
        cek("hapus klien baru berhasil", "Uji Klien" not in teks(page, "#daftarKlien"))

        print("== E. Anggaran ==")
        tab(page, "anggaran")
        cek("ringkasan anggaran 23 item Rp575.000.000", "23 item" in teks(page, "#ringkasanAnggaran") and "Rp575.000.000" in teks(page, "#ringkasanAnggaran"), teks(page, "#ringkasanAnggaran"))
        cek("A1 peringatan melebihi anggaran di tab anggaran", "Melebihi anggaran Rp5.000.000" in teks(page, "#daftarAnggaran"))
        cek("laba A3 Rp75.000.000 tampil", "Rp75.000.000" in teks(page, "#daftarAnggaran"))
        page.select_option("#agAcara", "1")
        page.fill("#agItem", "Uji Anggaran")
        page.fill("#agJumlah", "5000000")
        page.click("#btnTambahAnggaran")
        page.wait_for_timeout(400)
        cek("tambah item anggaran A1", "Uji Anggaran" in teks(page, "#daftarAnggaran") and "24 item" in teks(page, "#ringkasanAnggaran"))
        cek("peringatan A1 jadi Rp10.000.000", "Melebihi anggaran Rp10.000.000" in teks(page, "#daftarAnggaran"))
        page.click("[data-hapus-anggaran='24']")
        klik_modal_ya(page)
        cek("hapus item anggaran uji", "Uji Anggaran" not in teks(page, "#daftarAnggaran") and "23 item" in teks(page, "#ringkasanAnggaran"))
        # jumlah tidak valid -> ditolak, ringkasan tidak berubah
        page.fill("#agJumlah", "-1000")
        page.click("#btnTambahAnggaran")
        page.wait_for_timeout(300)
        cek("jumlah anggaran negatif ditolak", "Lengkapi" in toast_text(page) and "23 item" in teks(page, "#ringkasanAnggaran"))

        print("== F. Jadwal & rundown ==")
        tab(page, "jadwal")
        cek("ringkasan jadwal 26 rundown", "26 rundown" in teks(page, "#ringkasanJadwal"), teks(page, "#ringkasanJadwal"))
        cek("rundown A1 ada Akad nikah 10:00", "Akad nikah" in teks(page, "#daftarJadwal"))
        page.select_option("#jdAcara", "1")
        page.fill("#jdJam", "10:00")
        page.fill("#jdKegiatan", "Tes Bentrok")
        page.fill("#jdPenanggungJawab", "Budi Santoso")
        page.click("#btnTambahJadwal")
        page.wait_for_timeout(300)
        cek("rundown jam bentrok ditolak", "bentrok" in toast_text(page) and "Tes Bentrok" not in teks(page, "#daftarJadwal"))
        page.fill("#jdJam", "16:00")
        page.fill("#jdKegiatan", "Tes Rundown Baru")
        page.fill("#jdPenanggungJawab", "Budi Santoso")
        page.click("#btnTambahJadwal")
        page.wait_for_timeout(400)
        cek("tambah rundown 16:00 berhasil", "Tes Rundown Baru" in teks(page, "#daftarJadwal") and "27 rundown" in teks(page, "#ringkasanJadwal"))
        page.click("[data-hapus-jadwal='27']")
        klik_modal_ya(page)
        cek("hapus rundown uji", "Tes Rundown Baru" not in teks(page, "#daftarJadwal"))

        print("== G. Vendor & tim ==")
        tab(page, "vendor")
        cek("ringkasan vendor 8", "8 vendor" in teks(page, "#ringkasanVendor"), teks(page, "#ringkasanVendor"))
        cek("total biaya vendor Rp196.000.000", "Rp196.000.000" in teks(page, "#ringkasanVendor"))
        page.select_option("#vdAcara", "2")
        page.fill("#vdNama", "Uji Vendor")
        page.fill("#vdLayanan", "Catering")
        page.fill("#vdBiaya", "1000000")
        page.click("#btnTambahVendor")
        page.wait_for_timeout(400)
        cek("tambah vendor Uji Vendor", "Uji Vendor" in teks(page, "#daftarVendor") and "9 vendor" in teks(page, "#ringkasanVendor"))
        page.select_option("[data-status-vendor='9']", "Selesai")
        page.wait_for_timeout(400)
        cek("ubah status vendor baru ke Selesai", "Selesai" in toast_text(page))
        page.click("[data-hapus-vendor='9']")
        klik_modal_ya(page)
        cek("hapus vendor uji", "Uji Vendor" not in teks(page, "#daftarVendor"))
        page.fill("#tmNama", "Uji Tim")
        page.fill("#tmPeran", "Fotografer")
        page.fill("#tmTelepon", "0819-0000-0003")
        page.click("#btnTambahTim")
        page.wait_for_timeout(400)
        cek("tambah anggota tim", "Uji Tim" in teks(page, "#daftarTim"))
        page.click("[data-hapus-tim='6']")
        klik_modal_ya(page)
        cek("hapus anggota tim uji", "Uji Tim" not in teks(page, "#daftarTim"))

        print("== H. Checklist (koordinator boleh ubah miliknya) ==")
        tab(page, "checklist")
        cek("ringkasan checklist 29 item 17 selesai", "29 item" in teks(page, "#ringkasanChecklist") and "17" in teks(page, "#ringkasanChecklist"), teks(page, "#ringkasanChecklist"))
        cek("progres A6 1/5 tampil", "1/5" in teks(page, "#daftarChecklist"))
        logout(page)
        login(page, "koordinator", "koordinator123")
        tab(page, "checklist")
        cek("card tambah checklist tersembunyi untuk koordinator", not page.is_visible("#cardTambahChecklist"))
        cek("koordinator melihat checklist A1", "Venue dipesan" in teks(page, "#daftarChecklist"))
        cek("koordinator tidak melihat checklist A3", "Izin keramaian" not in teks(page, "#daftarChecklist"))
        page.click("[data-toggle-checklist='4']")
        page.wait_for_timeout(400)
        cek("koordinator tandai Dekorasi selesai", "ditandai selesai" in toast_text(page))
        tab(page, "dashboard")
        cek("dasbor koordinator checklist jadi 11/15", teks(page, "#dChecklist") == "11 / 15", teks(page, "#dChecklist"))
        logout(page)
        login(page, "admin", "admin123")
        tab(page, "checklist")
        page.click("[data-toggle-checklist='4']")
        page.wait_for_timeout(400)
        cek("admin kembalikan Dekorasi ke Belum", "Belum" in toast_text(page) or "dikembalikan" in toast_text(page))
        tab(page, "dashboard")
        cek("dasbor admin checklist kembali 17/29", teks(page, "#dChecklist") == "17 / 29", teks(page, "#dChecklist"))

        print("== I. Laporan, CSV, backup/restore ==")
        tab(page, "laporan")
        cek("ringkasan laporan kontrak 790jt", "Rp790.000.000" in teks(page, "#ringkasanLaporan"), teks(page, "#ringkasanLaporan"))
        cek("per klien ada PT Kreasi Digital Rp120.000.000", "PT Kreasi Digital" in teks(page, "#tabelPerKlien") and "Rp120.000.000" in teks(page, "#tabelPerKlien"))
        cek("per bulan Nov 4 acara kontrak 360jt", "November 2026" in teks(page, "#tabelPerBulan") and "Rp360.000.000" in teks(page, "#tabelPerBulan"))
        cek("per bulan Des 2 acara kontrak 430jt", "Desember 2026" in teks(page, "#tabelPerBulan") and "Rp430.000.000" in teks(page, "#tabelPerBulan"))
        cek("per acara A1 biaya Rp90.000.000", "Rp90.000.000" in teks(page, "#tabelPerAcara"))
        cek("bulan laporan default November 2026", page.input_value("#fBulanLaporan") == "2026-11", page.input_value("#fBulanLaporan"))
        with page.expect_download() as dl:
            page.click("#btnCsvLaporan")
        dl.value.save_as("/tmp/eo-nov.csv")
        baris_nov = open("/tmp/eo-nov.csv", encoding="utf-8").read().strip().split("\n")
        cek("CSV Nov 4 baris + header = 5", len(baris_nov) == 5, str(len(baris_nov)))
        page.select_option("#fBulanLaporan", "semua")
        page.wait_for_timeout(300)
        with page.expect_download() as dl2:
            page.click("#btnCsvLaporan")
        dl2.value.save_as("/tmp/eo-semua.csv")
        baris_semua = open("/tmp/eo-semua.csv", encoding="utf-8").read().strip().split("\n")
        cek("CSV semua 6 baris + header = 7", len(baris_semua) == 7, str(len(baris_semua)))
        # restore end-to-end dengan penanda RESTORE-TEST
        raw_state = page.evaluate("localStorage.getItem('eventOrganizer.v1')")
        raw_users = page.evaluate("localStorage.getItem('eventOrganizer.v1.users')")
        st = json.loads(raw_state)
        st["acara"].append({"id": 99, "nama": "RESTORE-TEST", "klienId": 1, "tanggal": "2026-12-25", "lokasi": "Hall Tes", "kontrak": 1000000, "status": "Perencanaan", "koordinator": "manajer"})
        with open("/tmp/eo-restore.json", "w", encoding="utf-8") as f:
            json.dump({"state": st, "users": json.loads(raw_users)}, f)
        page.set_input_files("#inputRestore", "/tmp/eo-restore.json")
        page.wait_for_timeout(500)
        cek("restore berhasil", "berhasil dipulihkan" in toast_text(page))
        tab(page, "acara")
        cek("acara RESTORE-TEST muncul setelah restore", "RESTORE-TEST" in teks(page, "#daftarAcara"))
        # file tidak valid ditolak
        with open("/tmp/eo-bad.json", "w", encoding="utf-8") as f:
            f.write("{bukan json")
        page.set_input_files("#inputRestore", "/tmp/eo-bad.json")
        page.wait_for_timeout(500)
        cek("file cadangan tidak valid ditolak", "tidak valid" in toast_text(page))
        # reset ke data demo
        tab(page, "laporan")
        page.click("#btnResetData")
        klik_modal_ya(page)
        cek("reset ke data demo: badge acara 6", teks(page, "#badgeAcara") == "6")

        print("== J. Ganti kata sandi + reset (pelajaran 40) ==")
        logout(page)
        login(page, "koordinator", "koordinator123")
        tab(page, "dashboard")
        page.fill("#sandiLama", "salah123")
        page.fill("#sandiBaru", "baru123456")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        cek("sandi lama salah -> pesan", "salah" in teks(page, "#pesanSandi"))
        page.fill("#sandiLama", "koordinator123")
        page.fill("#sandiBaru", "baru123456")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        cek("ganti sandi berhasil", "berhasil diubah" in teks(page, "#pesanSandi"))
        logout(page)
        login(page, "koordinator", "baru123456")
        cek("login dengan sandi baru berhasil", "Budi Santoso (Koordinator)" in teks(page, "#userChip"))
        logout(page)
        login(page, "admin", "admin123")
        tab(page, "dashboard")
        page.click("[data-reset-user='koordinator']")
        klik_modal_ya(page)
        cek("reset koordinator -> bk123", "direset ke bk123" in toast_text(page))
        logout(page)
        login(page, "koordinator", "bk123")
        cek("login koordinator dengan bk123", "Budi Santoso (Koordinator)" in teks(page, "#userChip"))
        # kembalikan sandi koordinator ke semula agar demo tetap utuh
        tab(page, "dashboard")
        page.fill("#sandiLama", "bk123")
        page.fill("#sandiBaru", "koordinator123")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        cek("kembalikan sandi koordinator123", "berhasil diubah" in teks(page, "#pesanSandi"))
        logout(page)
        login(page, "admin", "admin123")
        cek("admin masih bisa masuk setelah reset/restore (pelajaran 40)", "Administrator (Admin)" in teks(page, "#userChip"))

        print("== K. Console & page errors ==")
        cek("0 console error", len(console_errors) == 0, str(console_errors[:3]))
        cek("0 page error", len(page_errors) == 0, str(page_errors[:3]))
        browser.close()

    print(f"\nHASIL: {LOLOS} lolos, {GAGAL} gagal")
    if ERRORS:
        print("Gagal:", ERRORS)
    sys.exit(1 if GAGAL else 0)


if __name__ == "__main__":
    main()
