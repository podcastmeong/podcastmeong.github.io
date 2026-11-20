PODCAST MEONG 2.0 - PANDUAN PEMASANGAN
======================================

ISI PEMBARUAN
- index.html: beranda lama dipertahankan, klaim "paling ramai" diganti, navigasi 6 halaman dan gaya visual baru ditambahkan.
- toko.html: katalog asli dipertahankan (59 aplikasi + 12 eBook + 2 game + 14 kaos POD + 8 jasa + 1 cerbung = 96 produk); ditambahkan navigasi 6 halaman, keranjang berbasis localStorage, tombol tambah keranjang dan checkout WhatsApp.
- episode.html: halaman episode baru membaca data episode dari content.json.
- dunia-kiki.html: halaman cerita dan edukasi, menghubungkan artikel lama dan kategori eBook.
- studio.html: halaman KikiLab dan KikiWorks, portofolio dan paket jasa.
- tentang.html: profil lima merek dan kontak.
- Sitemap diperbarui dengan empat halaman baru.
- Folder aplikasi/demo, foto, file konten, artikel, dan tautan lama tetap disertakan.

CARA DEPLOY KE GITHUB PAGES
1. Unduh dan ekstrak ZIP ini.
2. Buat backup repository GitHub yang sedang aktif sebelum mengganti file.
3. Unggah seluruh isi folder hasil ekstrak ke root repository podcastmeong.github.io.
4. Pilih commit ke branch dan folder publikasi yang sama seperti pengaturan GitHub Pages saat ini.
5. Tunggu proses deploy GitHub Pages selesai.
6. Tes beranda, toko, kategori, tombol demo, tautan produk, pencarian, filter, tambah keranjang, hapus keranjang, dan checkout WhatsApp.

CATATAN PENTING
- Hosting tetap GitHub Pages; tidak ada layanan berbayar atau server baru.
- GA4 G-DDFJJKCB7F tetap dipertahankan pada index.html dan toko.html. Halaman tambahan memakai ID GA4 yang sama.
- Meta verifikasi Google Search Console yang ada pada index.html dipertahankan. Jangan menghapus token verifikasi.
- Nomor WhatsApp toko tetap 6281247986994.
- Keranjang tersimpan lokal di browser/perangkat masing-masing. Checkout membuka WhatsApp; ini bukan gateway pembayaran otomatis.
- Harga yang tidak dapat dibaca dari kartu akan dikirim sebagai "Harga dikonfirmasi" agar tidak mengarang nominal. Penjual mengonfirmasi total sebelum pembayaran.
- Jumlah halaman eBook Nabi Nuh yang bertentangan (17 dan 20) dihapus dari materi publik; gunakan jumlah final setelah PDF final diverifikasi.
- Google Analytics dan Search Console tidak perlu didaftarkan ulang.

PEMERIKSAAN YANG DILAKUKAN
- Seluruh file sumber asli tetap disertakan dalam ZIP.
- Referensi file lokal dari enam halaman utama diperiksa: tidak ditemukan target lokal yang hilang.
- JavaScript inline pada enam halaman diperiksa dengan Node.js: lolos pemeriksaan sintaks.
- Pengujian visual browser otomatis belum dijalankan karena Chromium tidak tersedia di lingkungan build ini. Lakukan tes akhir setelah deploy.
