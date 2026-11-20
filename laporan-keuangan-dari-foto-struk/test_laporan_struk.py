"""Tes Laporan Keuangan dari Foto Struk (file lokal, Playwright Chromium).
Hari ini 2026-11-20. Data seed (tanggal relatif) — diuji silang Python (/tmp/cek_struk.py):
  Struk: 8 (20 item), total Rp477.500.
    Nov 2026 (5 struk, 12 item, Rp342.500): S1 Warung Makan Sederhana 40.000 (pengguna),
      S2 Supermarket Sejahtera 132.500 (pengguna), S3 SPBU Pertamina 100.000 (pengguna),
      S4 Kopi Senja 30.000 (admin), S5 Apotek Sehat 40.000 (pengguna).
      Per kategori Nov: Makan 70.000, Belanja 132.500, Transport 100.000, Kesehatan 40.000.
      Kategori terbesar Nov: Belanja 132.500. Rata-rata/struk Nov: 68.500 (admin), 78.125 (pengguna).
    Okt 2026 (3 struk, 8 item, Rp135.000): S6 Toko Buku Cerdas 35.000 (admin),
      S7 Restoran Padang Sederhana 39.000 (pengguna), S8 Minimarket 24 Jam 61.000 (admin).
    Per kategori semua: Makan 109.000, Belanja 193.500, Transport 100.000, Kesehatan 40.000, Pendidikan 35.000.
    Pengguna: Nov 312.500 (4 struk, 10 item), semua 351.500 (5 struk, 13 item).
  Parsing (diuji silang Python):
    Contoh 1 (Warung Makan Sederhana, 20/11/2026): 3 item — Nasi Goreng 2x15000=30.000,
      Ayam Bakar 20.000, Es Teh Manis 5.000; total tertera 55.000 = total hitung.
      Baris alamat "Jl. Merdeka No. 10" dilewati; Tunai/Kembali/terima kasih dilewati.
    Contoh 2 (Supermarket Sejahtera, 18/11/2026): 3 item Belanja, total 115.000.
    Selisih: "Nasi Goreng 15000 / Total 99999" -> hitung 15.000 vs tertera 99.999.
  RESTORE-TEST: struk "RESTORE-TEST" 20/11/2026, item "Kopi Test" 25.000 Makan -> Nov jadi 367.500,
    struk Nov 6, total semua 502.500; CSV Nov 13 baris + header, CSV semua 21 baris + header.
Urutan tes: label OCR + login salah, A pengguna (baseline + ganti sandi),
  B admin (baseline + OCR tanpa foto + urai contoh 1 + ubah kategori + simpan + hapus,
    urai contoh 2 + buang draf, selisih, unggah foto + simpan + detail modal + hapus),
  C admin (RESTORE-TEST + backup/reset/restore + CSV + ubah kategori bolak-balik +
    hapus RESTORE-TEST + reset sandi pengguna + ganti sandi admin),
  D pengguna (tidak melihat struk admin + tambah + hapus struk sendiri).
OCR CDN TIDAK diuji (tes harus lolos offline) — hanya tombol tanpa foto.
"""
import base64
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = "file://" + str(ROOT / "laporan-keuangan-dari-foto-struk" / "index.html")

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


CONTOH_1 = """WARUNG MAKAN SEDERHANA
Jl. Merdeka No. 10
20/11/2026
Nasi Goreng 2 x 15000
Ayam Bakar 20000
Es Teh Manis 5000
Total 55000
Tunai 60000
Kembali 5000
Terima kasih"""

CONTOH_2 = """SUPERMARKET SEJAHTERA
18/11/2026
Beras 5kg 65000
Minyak Goreng 2L 38000
Sabun Mandi 12000
Total 115000"""


def main():
    # PNG 1x1 merah untuk uji unggah foto
    foto = Path("/tmp/struk_test.png")
    foto.write_bytes(base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="))

    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(accept_downloads=True)
        page = ctx.new_page()
        page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.goto(URL)
        page.wait_for_timeout(500)

        # ---------- Label OCR jujur ----------
        check("hero bertuliskan Foto Struk", "Foto Struk" in text(page, ".hero"))
        check("hero menegaskan OCR BUTUH INTERNET", "OCR BUTUH INTERNET" in text(page, ".hero"))
        check("hero menegaskan SELALU periksa", "SELALU periksa" in text(page, ".hero"))
        check("login menegaskan OCR BUTUH INTERNET", "OCR BUTUH INTERNET" in text(page, "#loginOverlay"))
        check("panduan menegaskan OCR BUTUH INTERNET", "OCR BUTUH INTERNET" in text(page, "#panel-panduan"))
        check("panduan menegaskan selalu koreksi", "SELALU periksa dan koreksi" in text(page, "#panel-panduan"))

        # ---------- Login salah ----------
        page.fill("#loginUser", "admin")
        page.fill("#loginPass", "salah123")
        page.click("#formLogin button[type=submit]")
        page.wait_for_timeout(300)
        check("login salah menampilkan error", visible(page, "#loginError"))

        # ================= FASE A — pengguna =================
        login(page, "pengguna", "pengguna123")
        check("A: pengguna masuk, chip Budi Santoso", "Budi Santoso (Pengguna)" in text(page, "#userChip"))
        check("A: mendarat di dasbor (panel aktif)", "active" in (page.get_attribute("#panel-dashboard", "class") or ""))
        check("A: total bulan ini 312.500", text(page, "#dTotalBulan") == rupiah(312500), text(page, "#dTotalBulan"))
        check("A: struk bulan ini 4", text(page, "#dStrukBulan") == "4", text(page, "#dStrukBulan"))
        check("A: kategori terbesar Belanja", text(page, "#dKatTerbesar") == "Belanja", text(page, "#dKatTerbesar"))
        check("A: kategori terbesar 132.500", "Rp132.500" in text(page, "#dKatTerbesarSub"), text(page, "#dKatTerbesarSub"))
        check("A: total semua 351.500", text(page, "#dTotalSemua") == rupiah(351500), text(page, "#dTotalSemua"))
        check("A: item bulan ini 10", text(page, "#dItemBulan") == "10", text(page, "#dItemBulan"))
        check("A: rata-rata/struk 78.125", text(page, "#dRataStruk") == rupiah(78125), text(page, "#dRataStruk"))
        check("A: total struk 5", text(page, "#dStrukSemua") == "5", text(page, "#dStrukSemua"))
        check("A: total item 13", text(page, "#dItemSemua") == "13", text(page, "#dItemSemua"))
        check("A: badge rekap 5", text(page, "#badgeRekap") == "5", text(page, "#badgeRekap"))
        check("A: cardPengguna tersembunyi untuk pengguna", not visible(page, "#cardPengguna"))
        check("A: cardSandiSaya terlihat untuk pengguna", visible(page, "#cardSandiSaya"))

        tab(page, "rekap")
        check("A: rekap hanya 5 struk milik pengguna", "5 struk" in text(page, "#ringkasanRekap"), text(page, "#ringkasanRekap"))
        check("A: rekap tidak menampilkan Kopi Senja (admin)", "Kopi Senja" not in text(page, "#daftarRekap"))
        check("A: rekap menampilkan Warung Makan Sederhana", "Warung Makan Sederhana" in text(page, "#daftarRekap"))
        tab(page, "kategori")
        check("A: kategori Nov Belanja 132.500", "Rp132.500" in text(page, "#tabelKategori"), text(page, "#tabelKategori"))
        check("A: kategori Nov Makan 40.000", "Rp40.000" in text(page, "#tabelKategori"))
        tab(page, "laporan")
        check("A: laporan total 351.500", "Rp351.500" in text(page, "#ringkasanLaporan"), text(page, "#ringkasanLaporan"))
        check("A: laporan Nov 4 struk", "4" in text(page, "#tabelPerBulan"))

        # Ganti sandi pengguna round-trip
        tab(page, "dashboard")
        page.fill("#sandiLama", "pengguna123")
        page.fill("#sandiBaru", "pengguna456")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        check("A: ganti sandi pengguna berhasil", "berhasil diubah" in text(page, "#pesanSandi"))
        logout(page)
        login(page, "pengguna", "pengguna456")
        check("A: pengguna masuk dengan sandi baru", "Budi Santoso (Pengguna)" in text(page, "#userChip"))
        page.fill("#sandiLama", "pengguna456")
        page.fill("#sandiBaru", "pengguna123")
        page.click("#formSandiSaya button[type=submit]")
        page.wait_for_timeout(300)
        logout(page)
        login(page, "pengguna", "pengguna123")
        check("A: pengguna kembali ke pengguna123", "Budi Santoso (Pengguna)" in text(page, "#userChip"))
        logout(page)

        # ================= FASE B — admin =================
        login(page, "admin", "admin123")
        check("B: admin masuk", "Administrator (Admin)" in text(page, "#userChip"))
        check("B: total bulan ini 342.500", text(page, "#dTotalBulan") == rupiah(342500), text(page, "#dTotalBulan"))
        check("B: struk bulan ini 5", text(page, "#dStrukBulan") == "5", text(page, "#dStrukBulan"))
        check("B: kategori terbesar Belanja", text(page, "#dKatTerbesar") == "Belanja", text(page, "#dKatTerbesar"))
        check("B: total semua 477.500", text(page, "#dTotalSemua") == rupiah(477500), text(page, "#dTotalSemua"))
        check("B: item bulan ini 12", text(page, "#dItemBulan") == "12", text(page, "#dItemBulan"))
        check("B: rata-rata/struk 68.500", text(page, "#dRataStruk") == rupiah(68500), text(page, "#dRataStruk"))
        check("B: total struk 8", text(page, "#dStrukSemua") == "8", text(page, "#dStrukSemua"))
        check("B: total item 20", text(page, "#dItemSemua") == "20", text(page, "#dItemSemua"))
        check("B: cardPengguna terlihat untuk admin", visible(page, "#cardPengguna"))
        check("B: struk terbaru berisi Warung Makan Sederhana", "Warung Makan Sederhana" in text(page, "#daftarStrukTerbaru"))

        # OCR tanpa foto -> peringatan
        tab(page, "unggah")
        page.click("#btnOcr")
        page.wait_for_timeout(300)
        check("B: OCR tanpa foto minta pilih foto dulu", "Pilih foto struk dulu" in text(page, "#ocrStatus"), text(page, "#ocrStatus"))

        # Muat contoh 1 -> urai -> ekstrak
        page.click("#btnContoh")
        page.wait_for_timeout(200)
        check("B: contoh teks dimuat", "WARUNG MAKAN SEDERHANA" in page.input_value("#uTeks"))
        page.click("#btnUrai")
        page.wait_for_timeout(400)
        check("B: urai pindah ke tab ekstrak", "active" in (page.get_attribute("#panel-ekstrak", "class") or ""))
        tabel_d = page.inner_html("#tabelDraft")
        check("B: draf 3 item (Nasi Goreng, Ayam Bakar, Es Teh Manis)", "Nasi Goreng" in tabel_d and "Ayam Bakar" in tabel_d and "Es Teh Manis" in tabel_d, tabel_d[:300])
        check("B: draf Nasi Goreng 2 x 15000 = 30.000", "Rp30.000" in tabel_d, tabel_d[:300])
        check("B: draf alamat Jl. Merdeka tidak jadi item", "Jl. Merdeka" not in tabel_d)
        check("B: total hitung 55.000 cocok dengan tertera", "Rp55.000" in text(page, "#eTotalBox") and "Cocok" in text(page, "#eTotalBox"), text(page, "#eTotalBox"))
        check("B: judul draf Warung Makan Sederhana", "WARUNG MAKAN SEDERHANA" in text(page, "#eJudul"), text(page, "#eJudul"))
        check("B: tanggal draf 20/11/2026", "20/11/2026" in text(page, "#eInfo"), text(page, "#eInfo"))

        # Ubah kategori Es Teh Manis (baris 2) jadi Lainnya, lalu simpan
        page.select_option("[data-dkat='2']", "Lainnya")
        page.wait_for_timeout(200)
        page.click("#btnSimpanStruk")
        page.wait_for_timeout(400)
        check("B: simpan pindah ke tab rekap", "active" in (page.get_attribute("#panel-rekap", "class") or ""))
        tab(page, "dashboard")
        check("B: total bulan ini jadi 397.500 setelah simpan contoh", text(page, "#dTotalBulan") == rupiah(397500), text(page, "#dTotalBulan"))
        check("B: struk bulan ini jadi 6", text(page, "#dStrukBulan") == "6", text(page, "#dStrukBulan"))
        tab(page, "kategori")
        tabel_k = text(page, "#tabelKategori")
        check("B: kategori Nov Makan jadi 120.000 (seed 70.000 + Nasi Goreng 30.000 + Ayam Bakar 20.000)", "Rp120.000" in tabel_k, tabel_k[:400])
        check("B: kategori Nov Lainnya 5.000", "Rp5.000" in tabel_k)

        # Hapus struk contoh baru (id 9) -> kembali baseline
        tab(page, "rekap")
        page.click("[data-hapus-struk='9']")
        page.wait_for_timeout(300)
        page.click("#modalYa")
        page.wait_for_timeout(400)
        tab(page, "dashboard")
        check("B: total bulan ini kembali 342.500 setelah hapus", text(page, "#dTotalBulan") == rupiah(342500), text(page, "#dTotalBulan"))

        # Urai contoh 2 tanpa simpan, lalu buang draf
        tab(page, "unggah")
        page.fill("#uTeks", CONTOH_2)
        page.click("#btnUrai")
        page.wait_for_timeout(400)
        tabel_d2 = page.inner_html("#tabelDraft")
        check("B: contoh 2 terurai 3 item Belanja", "Beras 5kg" in tabel_d2 and "Minyak Goreng 2L" in tabel_d2 and "Sabun Mandi" in tabel_d2, tabel_d2[:300])
        check("B: contoh 2 total 115.000 cocok", "Rp115.000" in text(page, "#eTotalBox") and "Cocok" in text(page, "#eTotalBox"))
        page.click("#btnBuangDraf")
        page.wait_for_timeout(300)
        check("B: buang draf menampilkan keadaan kosong", visible(page, "#ekstrakKosong"))

        # Selisih total tertera vs hitung
        tab(page, "unggah")
        page.fill("#uTeks", "Nasi Goreng 15000\nTotal 99999")
        page.click("#btnUrai")
        page.wait_for_timeout(400)
        check("B: selisih diperingatkan", "Selisih" in text(page, "#eTotalBox") and "Rp99.999" in text(page, "#eTotalBox"), text(page, "#eTotalBox"))
        page.click("#btnBuangDraf")
        page.wait_for_timeout(300)

        # Unggah foto + simpan dengan foto -> detail modal menampilkan foto
        tab(page, "unggah")
        page.set_input_files("#uFoto", str(foto))
        page.wait_for_timeout(600)
        check("B: pratinjau foto terlihat", visible(page, "#uPratinjau"))
        check("B: status foto siap", "siap" in text(page, "#uStatusFoto"), text(page, "#uStatusFoto"))
        page.fill("#uTeks", CONTOH_1)
        page.click("#btnUrai")
        page.wait_for_timeout(400)
        page.click("#btnSimpanStruk")
        page.wait_for_timeout(400)
        tab(page, "rekap")
        page.click("[data-lihat='10']")
        page.wait_for_timeout(300)
        check("B: modal detail terbuka", visible(page, "#modalStrukBack"))
        isi_modal = page.inner_html("#modalStrukIsi")
        check("B: modal menampilkan foto data URL", "data:image/png" in isi_modal)
        check("B: modal menampilkan teks mentah", "WARUNG MAKAN SEDERHANA" in text(page, "#modalStrukIsi"))
        check("B: modal menampilkan total 55.000", "Rp55.000" in text(page, "#modalStrukIsi"))
        page.click("#modalStrukTutup")
        page.wait_for_timeout(200)
        check("B: modal detail tertutup", not visible(page, "#modalStrukBack"))
        page.click("[data-hapus-struk='10']")
        page.wait_for_timeout(300)
        page.click("#modalYa")
        page.wait_for_timeout(400)
        tab(page, "dashboard")
        check("B: total bulan ini kembali 342.500 setelah hapus foto-struk", text(page, "#dTotalBulan") == rupiah(342500), text(page, "#dTotalBulan"))

        # ================= FASE C — admin: RESTORE-TEST + backup/reset/restore + CSV =================
        tab(page, "unggah")
        page.fill("#uToko", "RESTORE-TEST")
        page.fill("#uTanggal", "2026-11-20")
        page.fill("#uTeks", "Kopi Test 25000\nTotal 25000")
        page.click("#btnUrai")
        page.wait_for_timeout(400)
        check("C: RESTORE-TEST terurai 1 item", "Kopi Test" in page.inner_html("#tabelDraft"))
        page.click("#btnSimpanStruk")
        page.wait_for_timeout(400)
        tab(page, "dashboard")
        check("C: total bulan ini jadi 367.500", text(page, "#dTotalBulan") == rupiah(367500), text(page, "#dTotalBulan"))
        check("C: struk bulan ini jadi 6", text(page, "#dStrukBulan") == "6", text(page, "#dStrukBulan"))
        check("C: total semua jadi 502.500", text(page, "#dTotalSemua") == rupiah(502500), text(page, "#dTotalSemua"))

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
        check("C: reset kembalikan total bulan 342.500", text(page, "#dTotalBulan") == rupiah(342500), text(page, "#dTotalBulan"))
        tab(page, "rekap")
        page.fill("#cariRekap", "RESTORE-TEST")
        page.wait_for_timeout(300)
        check("C: RESTORE-TEST hilang setelah reset", "Tidak ada struk" in text(page, "#daftarRekap"))
        page.fill("#cariRekap", "")
        page.wait_for_timeout(200)

        # Restore dari backup
        page.set_input_files("#inputRestore", str(backup_path))
        page.wait_for_timeout(500)
        check("C: restore berhasil (toast)", "berhasil dipulihkan" in text(page, "#toast"))
        tab(page, "dashboard")
        check("C: total bulan kembali 367.500 setelah restore", text(page, "#dTotalBulan") == rupiah(367500), text(page, "#dTotalBulan"))
        check("C: total semua kembali 502.500 setelah restore", text(page, "#dTotalSemua") == rupiah(502500), text(page, "#dTotalSemua"))
        tab(page, "rekap")
        page.fill("#cariRekap", "RESTORE-TEST")
        page.wait_for_timeout(300)
        check("C: RESTORE-TEST kembali setelah restore", "RESTORE-TEST" in text(page, "#daftarRekap"))
        page.fill("#cariRekap", "")
        page.wait_for_timeout(200)

        # Restore file tidak valid ditolak
        bad = Path("/tmp/struk_bad_restore.json")
        bad.write_text("{bukan json", encoding="utf-8")
        page.set_input_files("#inputRestore", str(bad))
        page.wait_for_timeout(500)
        check("C: file cadangan tidak valid ditolak", "tidak valid" in text(page, "#toast"))
        tab(page, "dashboard")
        check("C: total bulan tetap 367.500 setelah restore gagal", text(page, "#dTotalBulan") == rupiah(367500), text(page, "#dTotalBulan"))

        # CSV laporan Nov (13 baris + header) dan semua (21 baris + header)
        tab(page, "laporan")
        page.select_option("#fBulanLaporan", "2026-11")
        page.wait_for_timeout(300)
        with page.expect_download() as dl2:
            page.click("#btnCsvLaporan")
        csv_path = Path(dl2.value.path())
        csv_text = csv_path.read_text(encoding="utf-8")
        lines = [l for l in csv_text.strip().split("\n") if l.strip()]
        check("C: CSV Nov punya header + 13 baris", len(lines) == 14, f"baris={len(lines)}")
        check("C: CSV Nov berisi Kopi Test", "Kopi Test" in csv_text)
        check("C: CSV Nov berisi Nasi Goreng", "Nasi Goreng" in csv_text)
        check("C: CSV header berisi Harga Satuan", "Harga Satuan" in lines[0])
        page.select_option("#fBulanLaporan", "semua")
        page.wait_for_timeout(300)
        with page.expect_download() as dl3:
            page.click("#btnCsvLaporan")
        csv_all = Path(dl3.value.path()).read_text(encoding="utf-8")
        lines_all = [l for l in csv_all.strip().split("\n") if l.strip()]
        check("C: CSV semua punya header + 21 baris", len(lines_all) == 22, f"baris={len(lines_all)}")
        check("C: CSV semua berisi Pulpen (Okt)", "Pulpen" in csv_all)

        # Ubah kategori bolak-balik: Transport -> Lainnya -> Transport
        page.select_option("#fBulanLaporan", "2026-11")
        page.wait_for_timeout(200)
        tab(page, "kategori")
        page.select_option("#fKategoriLihat", "Transport")
        page.wait_for_timeout(300)
        check("C: item Transport berisi Bensin Pertalite", "Bensin Pertalite 10L" in text(page, "#daftarItemKategori"))
        page.select_option("[data-ubahkat]", "Lainnya")
        page.wait_for_timeout(400)
        tabel_k2 = text(page, "#tabelKategori")
        check("C: Transport Nov jadi 0 setelah pindah", "Rp0" in tabel_k2, tabel_k2[:500])
        check("C: Lainnya Nov jadi 100.000 setelah pindah", "Rp100.000" in tabel_k2)
        page.select_option("#fKategoriLihat", "Lainnya")
        page.wait_for_timeout(300)
        check("C: item Lainnya berisi Bensin Pertalite", "Bensin Pertalite 10L" in text(page, "#daftarItemKategori"))
        page.select_option("[data-ubahkat]", "Transport")
        page.wait_for_timeout(400)
        tabel_k3 = text(page, "#tabelKategori")
        check("C: Transport Nov kembali 100.000", "Rp100.000" in tabel_k3, tabel_k3[:500])

        # Hapus RESTORE-TEST -> kembali baseline
        tab(page, "rekap")
        page.click("[data-hapus-struk='11']")
        page.wait_for_timeout(300)
        page.click("#modalYa")
        page.wait_for_timeout(400)
        tab(page, "dashboard")
        check("C: total bulan 342.500 setelah hapus RESTORE-TEST", text(page, "#dTotalBulan") == rupiah(342500), text(page, "#dTotalBulan"))

        # Reset sandi pengguna oleh admin -> bk123, lalu kembali ke pengguna123
        page.fill("#pgUser", "uji-reset")
        page.fill("#pgNama", "Uji Reset")
        page.fill("#pgPass", "uji12345")
        page.select_option("#pgPeran", "pengguna")
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
        check("C: uji-reset masuk dengan bk123", "Uji Reset (Pengguna)" in text(page, "#userChip"))
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

        # ================= FASE D — pengguna tambah + hapus struk sendiri =================
        login(page, "pengguna", "pengguna123")
        check("D: pengguna masuk lagi", "Budi Santoso (Pengguna)" in text(page, "#userChip"))
        tab(page, "rekap")
        page.fill("#cariRekap", "Kopi Senja")
        page.wait_for_timeout(300)
        check("D: pengguna tidak melihat struk admin Kopi Senja", "Tidak ada struk" in text(page, "#daftarRekap"))
        page.fill("#cariRekap", "")
        page.wait_for_timeout(200)
        tab(page, "unggah")
        page.fill("#uToko", "Toko Budi Test")
        page.fill("#uTanggal", "2026-11-20")
        page.fill("#uTeks", "Mie Ayam 10000\nTotal 10000")
        page.click("#btnUrai")
        page.wait_for_timeout(400)
        check("D: struk pengguna terurai 1 item", "Mie Ayam" in page.inner_html("#tabelDraft"))
        page.click("#btnSimpanStruk")
        page.wait_for_timeout(400)
        tab(page, "dashboard")
        check("D: total bulan pengguna jadi 322.500", text(page, "#dTotalBulan") == rupiah(322500), text(page, "#dTotalBulan"))
        tab(page, "rekap")
        page.fill("#cariRekap", "Toko Budi Test")
        page.wait_for_timeout(300)
        check("D: struk baru terlihat di rekap pengguna", "Toko Budi Test" in text(page, "#daftarRekap"))
        page.click("[data-hapus-struk='12']")
        page.wait_for_timeout(300)
        page.click("#modalYa")
        page.wait_for_timeout(400)
        tab(page, "dashboard")
        check("D: total bulan kembali 312.500 setelah hapus", text(page, "#dTotalBulan") == rupiah(312500), text(page, "#dTotalBulan"))

        browser.close()

    print(f"\nLOLOS: {passed}  GAGAL: {len(failures)}")
    if failures:
        print("Gagal:", failures)
    print("Console errors:", console_errors)
    print("Page errors:", page_errors)
    return 0 if not failures and not console_errors and not page_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
