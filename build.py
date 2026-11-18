#!/usr/bin/env python3
"""build.py — Generator statis website Podcast Meong.

Membaca template.html + content.json, menyisipkan kartu baru ke dalam
marker <!-- AUTO:<section>:start/end -->, menulis index.html.

Prinsip:
- Kartu LAMA (in_template=true) TIDAK di-render ulang — mereka sudah ada di
  template.html dan dibiarkan apa adanya, supaya render pertama identik.
- Hanya item BARU (in_template=false) yang di-render dan disisipkan:
  episode + berita baru di URUTAN TERATAS (terbaru dulu),
  produk toko baru di URUTAN TERAKHIR.
- Validasi wajib sebelum menulis output; gagal satu saja -> exit 1 dan
  TIDAK ADA file output yang ditulis.

Penggunaan:
  python3 build.py [--template template.html] [--content content.json]
                   [--out index.html] [--check-only]

  --check-only: bangun ke file sementara, jalankan validasi + bandingkan
  dengan template (harus identik bila tidak ada item baru), lalu hapus.
"""

import argparse
import html
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

GSC_TOKEN = "ipx7mVdPxPqXvvWHMaxgaWIcMWxApeJeainALC4g0uE"
SECTIONS = ("terbaru", "episode", "toko", "cerita")
MARKER_RE = re.compile(
    r"<!-- AUTO:(terbaru|episode|toko|cerita):start -->(.*?)<!-- AUTO:\1:end -->",
    re.DOTALL,
)


def esc(text):
    return html.escape(str(text), quote=True)


def format_rupiah(amount):
    """29000 -> 'Rp29.000'."""
    return "Rp{:,}".format(int(amount)).replace(",", ".")


def render_ep_card(ep):
    """Kartu episode baru. Class persis kartu lama: .ep-card/.ep-body/.ep-watch."""
    synopsis = ep.get("synopsis") or "Episode terbaru Podcast Meong — Oyen & Momo."
    return (
        '<a class="ep-card" href="{url}">'
        '<img src="{thumb}" alt="{title}">'
        '<div class="ep-body"><h3>{title}</h3><p>{synopsis}</p>'
        '<span class="ep-watch">Tonton \u2192</span></div></a>'
    ).format(url=esc(ep["url"]), thumb=esc(ep.get("thumb", "")),
             title=esc(ep["title"]), synopsis=esc(synopsis))


def render_news_card(item):
    """Kartu berita baru. Class persis kartu lama: .news-card/.news-tag/.news-link/.status-badge."""
    parts = ['<div class="news-card">']
    parts.append('<span class="news-tag">{}</span>'.format(esc(item.get("tag", "Terbaru"))))
    parts.append("<h3>{}</h3>".format(esc(item["title"])))
    if item.get("text"):
        parts.append("<p>{}</p>".format(esc(item["text"])))
    if item.get("url"):
        parts.append(
            '<a class="news-link" href="{}">Lihat \u2192</a>'.format(esc(item["url"]))
        )
    elif item.get("badge"):
        parts.append('<span class="status-badge">{}</span>'.format(esc(item["badge"])))
    parts.append("</div>")
    return "".join(parts)


def render_shop_card(item):
    """Kartu toko baru. Class persis kartu lama: .shop-card/.store/.price/.btn.btn-primary."""
    parts = ['<div class="shop-card">']
    parts.append('<span class="store">{}</span>'.format(esc(item.get("store", "Toko"))))
    parts.append("<h3>{}</h3>".format(esc(item["title"])))
    if item.get("desc"):
        parts.append("<p>{}</p>".format(esc(item["desc"])))
    if item.get("designs"):
        lis = "".join("<li>{}</li>".format(esc(d)) for d in item["designs"])
        parts.append("<ul>{}</ul>".format(lis))
    if item.get("price"):
        parts.append(
            '<p class="price">{} <small>/ {}</small></p>'.format(
                format_rupiah(item["price"]), esc(item.get("price_unit", "produk"))
            )
        )
    button = item.get("button") or ("Beli Sekarang" if item.get("price") else "Lihat \u2192")
    parts.append(
        '<a class="btn btn-primary" href="{}">{}</a>'.format(
            esc(item["url"]), esc(button)
        )
    )
    parts.append("</div>")
    return "".join(parts)


def new_items(data, key):
    """Item baru dari sebuah daftar (in_template=false), terbaru dulu."""
    items = [i for i in data.get(key, []) if not i.get("in_template")]
    items.sort(key=lambda i: i.get("date", ""), reverse=True)
    return items


def build(template_text, data):
    """Sisipkan kartu baru ke dalam marker. Kembalikan (output, laporan)."""
    report = {"inserted": {"terbaru": 0, "episode": 0, "toko": 0, "cerita": 0}}

    # Episode baru + manual -> urutan teratas di #episode.
    eps = new_items(data, "episodes") + [i for i in data.get("manual", {}).get("episodes", [])]
    eps.sort(key=lambda i: i.get("date", ""), reverse=True)
    # Berita baru + manual -> urutan teratas di #terbaru.
    news = new_items(data, "news") + [i for i in data.get("manual", {}).get("news", [])]
    news.sort(key=lambda i: i.get("date", ""), reverse=True)
    # Produk toko baru + manual -> urutan terakhir di #toko.
    shop = new_items(data, "shop") + [i for i in data.get("manual", {}).get("shop", [])]
    shop.sort(key=lambda i: i.get("date", ""))
    # Cerita baru + manual -> urutan terakhir di #cerita.
    cerita = new_items(data, "cerita") + [i for i in data.get("manual", {}).get("cerita", [])]
    cerita.sort(key=lambda i: i.get("date", ""))

    def replace_section(match):
        section = match.group(1)
        inner = match.group(2)
        if section == "episode":
            cards = "".join(render_ep_card(e) for e in eps)
            report["inserted"]["episode"] = len(eps)
            return "<!-- AUTO:episode:start -->" + cards + inner + "<!-- AUTO:episode:end -->"
        if section == "terbaru":
            cards = "".join(render_news_card(n) for n in news)
            report["inserted"]["terbaru"] = len(news)
            return "<!-- AUTO:terbaru:start -->" + cards + inner + "<!-- AUTO:terbaru:end -->"
        if section == "cerita":
            cards = "".join(render_news_card(n) for n in cerita)
            report["inserted"]["cerita"] = len(cerita)
            return "<!-- AUTO:cerita:start -->" + inner + cards + "<!-- AUTO:cerita:end -->"
        cards = "".join(render_shop_card(s) for s in shop)
        report["inserted"]["toko"] = len(shop)
        return "<!-- AUTO:toko:start -->" + inner + cards + "<!-- AUTO:toko:end -->"

    output, n = MARKER_RE.subn(replace_section, template_text)
    if n != len(SECTIONS):
        raise ValueError(
            "Marker AUTO tidak lengkap: ditemukan {} pasangan, harus {}".format(n, len(SECTIONS))
        )
    return output, report


def extract_hrefs(text):
    return set(re.findall(r'href="([^"]+)"', text))


def count_cards(text):
    return {
        "news": text.count('class="news-card"'),
        "ep": text.count('class="ep-card"'),
        "shop": text.count('class="shop-card"'),
    }


class _WellFormedCheck(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.errors = []
        self.void = {"meta", "link", "img", "br", "hr", "input", "source"}

    def handle_starttag(self, tag, attrs):
        if tag not in self.void:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in self.void:
            return
        if not self.stack:
            self.errors.append("tag penutup tanpa pembuka: </{}>".format(tag))
        elif self.stack[-1] == tag:
            self.stack.pop()
        elif tag in self.stack:
            while self.stack and self.stack[-1] != tag:
                self.errors.append("tag tidak tertutup: <{}>".format(self.stack.pop()))
            self.stack.pop()
        else:
            self.errors.append("tag penutup tak cocok: </{}>".format(tag))


def validate(template_text, output):
    """Validasi wajib. Kembalikan daftar error (kosong = lolos)."""
    errors = []
    if GSC_TOKEN not in output:
        errors.append("Token Google Search Console HILANG dari output!")
    missing_hrefs = extract_hrefs(template_text) - extract_hrefs(output)
    if missing_hrefs:
        errors.append("Tautan lama hilang: {}".format(sorted(missing_hrefs)))
    before, after = count_cards(template_text), count_cards(output)
    for key in before:
        if after[key] < before[key]:
            errors.append(
                "Jumlah kartu {} BERKURANG: {} -> {}".format(key, before[key], after[key])
            )
    for section in SECTIONS:
        if "<!-- AUTO:{}:start -->".format(section) not in output:
            errors.append("Marker AUTO:{}:start hilang".format(section))
        if "<!-- AUTO:{}:end -->".format(section) not in output:
            errors.append("Marker AUTO:{}:end hilang".format(section))
    checker = _WellFormedCheck()
    try:
        checker.feed(output)
        checker.close()
    except Exception as exc:  # noqa: BLE001
        errors.append("Gagal parse HTML: {}".format(exc))
    if checker.errors:
        errors.extend(checker.errors[:5])
    if checker.stack:
        errors.append("Tag tidak tertutup di akhir: {}".format(checker.stack[:5]))
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generator statis website Podcast Meong")
    parser.add_argument("--template", default="template.html")
    parser.add_argument("--content", default="content.json")
    parser.add_argument("--out", default="index.html")
    parser.add_argument("--check-only", action="store_true",
                        help="bangun ke file sementara, validasi, bandingkan dengan template")
    args = parser.parse_args(argv)

    base = Path(__file__).resolve().parent
    template_path = Path(args.template)
    if not template_path.is_absolute():
        template_path = base / template_path
    content_path = Path(args.content)
    if not content_path.is_absolute():
        content_path = base / content_path
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = base / out_path

    template_text = template_path.read_text(encoding="utf-8")
    data = json.loads(content_path.read_text(encoding="utf-8"))
    if data.get("meta", {}).get("gsc_token") != GSC_TOKEN:
        print("PERINGATAN: token GSC di content.json tidak cocok dengan token yang dijaga.",
              file=sys.stderr)

    output, report = build(template_text, data)
    errors = validate(template_text, output)
    if errors:
        print("VALIDASI GAGAL — output TIDAK ditulis:", file=sys.stderr)
        for err in errors:
            print("  - {}".format(err), file=sys.stderr)
        return 1

    if args.check_only:
        if output == template_text:
            print("CHECK-ONLY: output IDENTIK dengan template (tidak ada item baru).")
        else:
            import difflib
            diff = list(difflib.unified_diff(
                template_text.splitlines(), output.splitlines(), lineterm=""
            ))
            print("CHECK-ONLY: output BERBEDA dari template ({} baris diff).".format(len(diff)))
            for line in diff[:40]:
                print(line)
        print("Kartu baru disisipkan: {}".format(report["inserted"]))
        return 0

    out_path.write_text(output, encoding="utf-8")
    print("OK: {} ditulis ({} byte). Kartu baru: {}".format(
        out_path, len(output.encode("utf-8")), report["inserted"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
