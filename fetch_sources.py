#!/usr/bin/env python3
"""fetch_sources.py — Mengambil sumber data baru untuk website Podcast Meong.

Sumber yang dipakai (HANYA yang terverifikasi aman/andal — keputusan Cipta
18 Nov 2026 "masukan yang aman2 aja"):
  - Video: feed RSS channel YouTube (tanpa login/API key).
  - eBook: halaman produk Mayar per URL terdaftar (judul + harga).
  - Puisi/cerpen: halaman detail buku KBM per URL terdaftar (judul saja).
  - Foto: ledger internal upload-ledger.md (angka Adobe/Dreamstime terbaru).
  - Konten/berita: TIDAK di-scrape dari sosmed — berita baru masuk lewat
    entri manual di content.json ("manual") atau lewat video/eBook/KBM baru.

YANG SENGAJA TIDAK DIPAKAI: KaryaKarsa (SPA, tidak ada data di HTML),
Lynk.id (HTTP 403), Zazzle (JS, daftar produk tidak di HTML), Adobe /
Dreamstime (HTTP 403), musik & lagu (DIKELUARKAN dari website).

Aturan: hanya MENAMBAH item baru ke content.json, tidak pernah menghapus.
Kegagalan jaringan pada satu sumber -> peringatan, lanjut ke sumber lain,
data lama dipertahankan.

Penggunaan:
  python3 fetch_sources.py [--content content.json] [--dry-run]
  --dry-run: tampilkan perubahan tanpa menulis content.json.
"""

import argparse
import json
import re
import shutil
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"}
YT_CHANNEL_ID = "UCKXJjhKdYjeECojBrF8aegA"
YT_RSS = "https://www.youtube.com/feeds/videos.xml?channel_id=" + YT_CHANNEL_ID
ADOBE_URL = "https://stock.adobe.com/contributor/212791327/masduki"
DREAMSTIME_URL = "https://www.dreamstime.com/masduki1189_info"


def fetch_text(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="ignore"), resp.status


def clean_title(title):
    title = re.sub(r"\s+", " ", title or "").strip()
    title = re.sub(r"\s*-\s*Podcast Meong\s*$", "", title)
    return title


def fetch_youtube_rss():
    """Kembalikan daftar video: video_id, title, url, date, thumb, description."""
    text, status = fetch_text(YT_RSS)
    if status != 200:
        raise RuntimeError("RSS YouTube HTTP {}".format(status))
    ns = {"a": "http://www.w3.org/2005/Atom",
          "m": "http://search.yahoo.com/mrss/"}
    root = ET.fromstring(text)
    videos = []
    for entry in root.findall("a:entry", ns):
        vid = entry.find("a:id", ns).text.split(":")[-1]
        link = entry.find("a:link", ns).get("href")
        published = entry.find("a:published", ns).text[:10]
        title = (entry.find("a:title", ns).text or "").strip()
        group = entry.find("m:group", ns)
        thumb = ""
        desc = ""
        if group is not None:
            t = group.find("m:thumbnail", ns)
            if t is not None:
                thumb = t.get("url", "")
            d = group.find("m:description", ns)
            if d is not None:
                desc = (d.text or "").strip()
        videos.append({"video_id": vid, "title": title, "url": link,
                       "date": published, "thumb": thumb, "description": desc})
    return videos


def fetch_mayar(url):
    """Judul + harga (int Rupiah) dari halaman produk Mayar."""
    text, status = fetch_text(url)
    if status != 200:
        raise RuntimeError("Mayar HTTP {}".format(status))
    m = re.search(r"<title>(.*?)</title>", text, re.S)
    title = clean_title(m.group(1)) if m else ""
    # Harga Mayar tersimpan sebagai "amount":29000 di HTML — kadang dengan
    # quote yang di-escape (\"amount\":29000) di dalam string JSON.
    # JANGAN menebak dari angka 5 digit bebas — ID produk (86389) juga
    # 5 digit dan akan salah terpilih. Bila tidak ditemukan lewat kunci
    # amount/price, kembalikan None (pemanggil mempertahankan harga lama).
    price = None
    amounts = re.findall(r'\\?"amount\\?"\s*:\s*(\d+)', text)
    if amounts:
        price = int(max(set(amounts), key=amounts.count))
    else:
        m2 = re.search(r'\\?"price\\?"\s*:\s*"?(\d+)"?', text)
        if m2:
            price = int(m2.group(1))
    return {"title": title, "price": price}


def fetch_kbm(url):
    """Judul dari halaman detail buku KBM (harga tidak tersedia di halaman)."""
    text, status = fetch_text(url)
    if status != 200:
        raise RuntimeError("KBM HTTP {}".format(status))
    m = re.search(r'og:title"\s+content="([^"]+)"', text)
    if not m:
        m = re.search(r"<title>(.*?)</title>", text, re.S)
        title = m.group(1) if m else ""
    else:
        title = m.group(1)
    return {"title": clean_title(title)}


def parse_ledger(ledger_path):
    """Baca angka foto terbaru dari ledger internal.

    Mengambil bagian '## YYYY-MM-DD' terakhir, lalu angka terakhir untuk:
    Adobe In review (bentuk '46->48' diutamakan), portofolio, Dreamstime pending.
    Kembalikan dict + tanggal bagian tersebut, atau None bila tidak ditemukan.
    """
    text = Path(ledger_path).read_text(encoding="utf-8")
    sections = re.split(r"^## (\d{4}-\d{2}-\d{2})", text, flags=re.M)
    if len(sections) < 3:
        return None
    date = sections[-2]
    body = sections[-1]
    stats = {"as_of": date}
    m = re.findall(r"In review (\d+)\s*(?:->|→)\s*(\d+)", body)
    if m:
        stats["adobe_in_review"] = int(m[-1][1])
    else:
        m2 = re.findall(r"In review (\d+)", body)
        if m2:
            stats["adobe_in_review"] = int(m2[-1])
    m3 = re.findall(r"[Pp]ort(?:folio|ofolio) (\d+)", body)
    if m3:
        stats["adobe_approved"] = int(m3[-1])
    m4 = re.findall(r"[Dd]reamstime pending[^0-9]*?(\d+)", body)
    if not m4:
        m4 = re.findall(r"pending review kini (\d+)", body)
    if not m4:
        m4 = re.findall(r"Pending (\d+)", body)
    if m4:
        stats["dreamstime_pending"] = int(m4[-1])
    return stats if len(stats) > 1 else None


def short_desc(description, limit=140):
    desc = re.sub(r"\s+", " ", description or "").strip()
    if len(desc) > limit:
        desc = desc[:limit].rsplit(" ", 1)[0] + "…"
    return desc or "Episode terbaru Podcast Meong — Oyen & Momo."


def main(argv=None):
    parser = argparse.ArgumentParser(description="Fetcher sumber auto-update website")
    parser.add_argument("--content", default="content.json")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    base = Path(__file__).resolve().parent
    content_path = Path(args.content)
    if not content_path.is_absolute():
        content_path = base / content_path
    data = json.loads(content_path.read_text(encoding="utf-8"))
    changes = {"episodes": 0, "news": 0, "shop": 0, "ebooks_checked": 0,
               "kbm_added": 0, "photos_updated": False}
    warnings = []

    # ---- 1. YouTube RSS: video baru ----
    try:
        videos = fetch_youtube_rss()
        known = set(data.get("known_video_ids", []))
        skip_words = [w.lower() for w in data.get("video_skip_keywords", [])]
        for v in videos:
            if v["video_id"] in known:
                continue
            known.add(v["video_id"])
            title_low = v["title"].lower()
            if any(w in title_low for w in skip_words):
                warnings.append("Video dilewati (bukan episode): {} — {}".format(
                    v["video_id"], v["title"][:60]))
                continue
            data.setdefault("episodes", []).append({
                "video_id": v["video_id"], "title": v["title"],
                "synopsis": short_desc(v["description"]),
                "url": v["url"], "thumb": v["thumb"], "date": v["date"],
                "in_template": False,
            })
            data.setdefault("news", []).append({
                "tag": "Episode Baru", "title": v["title"],
                "text": "Tayang {} — tonton di YouTube.".format(v["date"]),
                "url": v["url"], "date": v["date"], "in_template": False,
            })
            changes["episodes"] += 1
            changes["news"] += 1
        data["known_video_ids"] = sorted(known)
    except Exception as exc:  # noqa: BLE001
        warnings.append("RSS YouTube gagal: {}".format(exc))

    # ---- 2. Mayar: verifikasi produk terdaftar ----
    for url in data.get("tracked_urls", {}).get("mayar", []):
        try:
            got = fetch_mayar(url)
            changes["ebooks_checked"] += 1
            existing = next((e for e in data.get("ebooks", [])
                             if e.get("url") == url), None)
            if existing:
                if got["price"] is None:
                    warnings.append("Harga Mayar tidak ditemukan di halaman {} "
                                    "— harga lama dipertahankan.".format(url))
                elif existing.get("price") != got["price"]:
                    warnings.append("HARGA BERUBAH di Mayar {}: {} -> {} "
                                    "(kartu lama di template TIDAK diubah otomatis)".format(
                                        url, existing.get("price"), got["price"]))
                    existing["price"] = got["price"]
                if got["title"]:
                    existing["title"] = got["title"]
            else:
                data.setdefault("shop", []).append({
                    "store": "Mayar — Toko Utama", "title": got["title"],
                    "desc": "eBook Podcast Meong.", "price": got["price"],
                    "price_unit": "eBook", "url": url,
                    "button": "Beli Sekarang", "date": "", "in_template": False,
                })
                data.setdefault("news", []).append({
                    "tag": "eBook Baru", "title": got["title"],
                    "text": "eBook baru tersedia di Mayar.",
                    "url": url, "date": "", "in_template": False,
                })
                changes["shop"] += 1
                changes["news"] += 1
        except Exception as exc:  # noqa: BLE001
            warnings.append("Mayar gagal ({}): {}".format(url, exc))

    # ---- 3. KBM: buku baru ----
    for url in data.get("tracked_urls", {}).get("kbm", []):
        try:
            got = fetch_kbm(url)
            existing = next((b for b in data.get("kbm_books", [])
                             if b.get("url") == url), None)
            if existing:
                if got["title"]:
                    existing["title"] = got["title"]
                continue
            data.setdefault("kbm_books", []).append({
                "title": got["title"], "url": url, "in_template": False,
            })
            data.setdefault("shop", []).append({
                "store": "KBM", "title": got["title"],
                "desc": "Baca di KBM.", "price": None,
                "url": url, "button": "Baca di KBM",
                "date": "", "in_template": False,
            })
            data.setdefault("news", []).append({
                "tag": "Buku Baru · KBM", "title": got["title"],
                "text": "Buku baru tersedia di KBM.",
                "url": url, "date": "", "in_template": False,
            })
            changes["kbm_added"] += 1
            changes["shop"] += 1
            changes["news"] += 1
        except Exception as exc:  # noqa: BLE001
            warnings.append("KBM gagal ({}): {}".format(url, exc))

    # ---- 4. Ledger internal: angka foto ----
    ledger_path = (Path.home() / "workspace" / "goals" / "cuan-dari-foto-ai"
                   / "hidden_files" / "upload-ledger.md")
    try:
        stats = parse_ledger(ledger_path)
        if stats:
            old = data.get("photos", {})
            changed = any(old.get(k) != v for k, v in stats.items() if k != "as_of")
            if changed:
                data["photos"] = {"source": "upload-ledger.md", **stats}
                data.setdefault("news", []).append({
                    "tag": "KikiLab · Foto AI",
                    "title": "Update Foto Stock: {} Disetujui Adobe Stock".format(
                        stats.get("adobe_approved", old.get("adobe_approved", "?"))),
                    "text": ("Adobe Stock: {} disetujui, {} In review. "
                             "Dreamstime: {} file pending review.").format(
                                 stats.get("adobe_approved", "?"),
                                 stats.get("adobe_in_review", "?"),
                                 stats.get("dreamstime_pending", "?")),
                    "url": ADOBE_URL, "date": stats.get("as_of", ""),
                    "in_template": False,
                })
                changes["news"] += 1
                changes["photos_updated"] = True
    except Exception as exc:  # noqa: BLE001
        warnings.append("Ledger foto gagal dibaca: {}".format(exc))

    print("Perubahan: {}".format(changes))
    for w in warnings:
        print("PERINGATAN: {}".format(w))

    if args.dry_run:
        print("DRY-RUN: content.json TIDAK ditulis.")
        return 0
    backup = content_path.with_suffix(".json.bak")
    shutil.copy2(content_path, backup)
    content_path.write_text(json.dumps(data, ensure_ascii=False, indent=1,
                                       sort_keys=True), encoding="utf-8")
    print("OK: content.json ditulis (backup: {}).".format(backup.name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
