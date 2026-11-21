#!/usr/bin/env python3
"""Uji Kuis Cerita Nabi: string wajib + node --check + validasi 50 soal + simulasi main.

Jalankan: python3 test_kuis_cerita_nabi.py
Keluar 0 bila semua lolos.
"""
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
HTML = HERE / "index.html"
TMP = Path("/tmp/kuis_cerita_nabi_test")

WAJIB = [
    "Kuis Cerita Nabi", "localStorage", "kuisNabi.terbaik.", "Kembali ke Game",
    "Harga menyusul", "Nabi Nuh", "Nabi Yunus", "Nabi Yusuf", "Nabi Musa",
    "Nabi Ibrahim", "Demo web",
]
DILARANG = ["Rp149.000", "Rp19.900", "Rp49.900", "Rp99.900", "http://", "https://cdn",
            "fonts.googleapis", "<script src="]

HARNESS = r"""
const store = {};
global.localStorage = {
  getItem: k => (k in store ? store[k] : null),
  setItem: (k, v) => { store[k] = String(v); },
  removeItem: k => { delete store[k]; },
};
function makeClassList() {
  const s = new Set();
  return {
    add: (...c) => c.forEach(x => s.add(x)),
    remove: (...c) => c.forEach(x => s.delete(x)),
    toggle: (c, f) => { if (f === undefined) f = !s.has(c); f ? s.add(c) : s.delete(c); return f; },
    contains: c => s.has(c),
  };
}
function makeCtx() {
  const grad = { addColorStop() {} };
  return new Proxy({}, {
    get(t, p) {
      if (p === "createLinearGradient" || p === "createRadialGradient") return () => grad;
      if (p === "measureText") return () => ({ width: 0 });
      return (...a) => {};
    },
    set() { return true; },
  });
}
function makeEl(id) {
  const el = {
    id: id || "", style: {}, children: [], _handlers: {},
    classList: makeClassList(), textContent: "", disabled: false, _innerHTML: "",
    addEventListener(ev, fn) { (this._handlers[ev] = this._handlers[ev] || []).push(fn); },
    removeEventListener() {},
    appendChild(c) { this.children.push(c); return c; },
    querySelectorAll() { return this.children.slice(); },
    querySelector() { return null; },
    getContext() { return makeCtx(); },
    setAttribute(k, v) { this["attr_" + k] = v; },
    getAttribute(k) { return this["attr_" + k]; },
    click() { (this._handlers.click || []).forEach(f => f({ preventDefault() {} })); },
  };
  Object.defineProperty(el, "innerHTML", {
    get() { return this._innerHTML; },
    set(v) { this._innerHTML = v; if (v === "") this.children = []; },
  });
  return el;
}
const els = {};
global.document = {
  getElementById(id) { return els[id] || (els[id] = makeEl(id)); },
  createElement(tag) { return makeEl(""); },
  querySelectorAll() { return []; },
  querySelector() { return null; },
  addEventListener() {},
  hidden: false,
};
global.window = global;
global.requestAnimationFrame = () => 0;
global.cancelAnimationFrame = () => {};
"""

TESTS = r"""
let pass = 0, fail = 0;
function check(nama, kond) {
  if (kond) { pass++; console.log("PASS: " + nama); }
  else { fail++; console.log("FAIL: " + nama); }
}
const T = global.OYEN_TEST;
check("OYEN_TEST tersedia", !!T);
const PAKET = T.paket;

// --- struktur data soal ---
check("tepat 5 paket", PAKET.length === 5);
check("id paket sesuai urutan tugas", PAKET.map(p => p.id).join(",") === "nuh,yunus,yusuf,musa,ibrahim");
let strukturOk = true, totalSoal = 0;
const semuaTeks = new Set();
for (const p of PAKET) {
  if (p.soal.length !== 10) { strukturOk = false; console.log("  paket " + p.id + " punya " + p.soal.length + " soal"); }
  const teksPaket = new Set();
  for (const s of p.soal) {
    totalSoal++;
    if (!s.t || s.p.length !== 4 || s.j < 0 || s.j > 3 || !s.e || s.e.length < 10) strukturOk = false;
    if (new Set(s.p).size !== 4) { strukturOk = false; console.log("  pilihan ganda di paket " + p.id); }
    if (teksPaket.has(s.t)) { strukturOk = false; console.log("  soal ganda: " + s.t); }
    teksPaket.add(s.t);
    if (semuaTeks.has(s.t)) { strukturOk = false; console.log("  soal sama di 2 paket: " + s.t); }
    semuaTeks.add(s.t);
  }
}
check("tiap paket 10 soal, tiap soal 4 pilihan + kunci valid + penjelasan", strukturOk);
check("total 50 soal", totalSoal === 50);

// --- bintang ---
check("bintang 10 benar = 3", T.hitungBintang(10) === 3);
check("bintang 9 benar = 3", T.hitungBintang(9) === 3);
check("bintang 8 benar = 2", T.hitungBintang(8) === 2);
check("bintang 7 benar = 2", T.hitungBintang(7) === 2);
check("bintang 5 benar = 1", T.hitungBintang(5) === 1);
check("bintang 4 benar = 0", T.hitungBintang(4) === 0);

// --- simulasi: jawab semua benar di paket Nuh ---
T.mulaiPaket("nuh");
for (let i = 0; i < 10; i++) { T.jawabBenar(); T.lanjut(); }
check("skor 100 setelah 10 jawaban benar", T.status().skor === 100);
check("benar 10/10", T.status().benar === 10);
const tbNuh = JSON.parse(store["kuisNabi.terbaik.nuh"]);
check("skor terbaik Nuh tersimpan (100)", tbNuh && tbNuh.skor === 100 && tbNuh.benar === 10);

// --- simulasi: satu jawaban salah di paket Yunus ---
T.mulaiPaket("yunus");
const s0 = T.soalAktif();
const salah = (s0.j + 1) % 4;
T.jawab(salah);
check("jawaban salah tidak menambah skor", T.status().skor === 0 && T.status().benar === 0);
T.lanjut();
T.jawabBenar();
check("jawaban benar setelahnya menambah 10", T.status().skor === 10 && T.status().benar === 1);

// --- skor terbaik tidak turun bila main lebih buruk ---
T.mulaiPaket("nuh");
for (let i = 0; i < 10; i++) { const s = T.soalAktif(); T.jawab((s.j + 1) % 4); T.lanjut(); }
const tbNuh2 = JSON.parse(store["kuisNabi.terbaik.nuh"]);
check("skor terbaik Nuh tetap 100 setelah main buruk", tbNuh2 && tbNuh2.skor === 100);

console.log("RINGKASAN lolos=" + pass + " gagal=" + fail);
process.exit(fail ? 1 : 0);
"""


def main() -> int:
    lolos = gagal = 0

    def check(nama, kond):
        nonlocal lolos, gagal
        if kond:
            lolos += 1
            print(f"PASS: {nama}")
        else:
            gagal += 1
            print(f"FAIL: {nama}")

    html = HTML.read_text(encoding="utf-8")
    for s in WAJIB:
        check(f"string wajib ada: {s!r}", s in html)
    for s in DILARANG:
        check(f"string terlarang tidak ada: {s!r}", s not in html)

    m = re.search(r"<script>(.*?)</script>", html, re.S)
    check("ada satu blok <script>", m is not None)
    if not m:
        print(f"RINGKASAN lolos={lolos} gagal={gagal}")
        return 1
    js = m.group(1)

    TMP.mkdir(parents=True, exist_ok=True)
    js_file = TMP / "kuis.js"
    js_file.write_text(js, encoding="utf-8")
    r = subprocess.run(["node", "--check", str(js_file)], capture_output=True, text=True)
    check("node --check pada JS yang diekstrak", r.returncode == 0)
    if r.returncode != 0:
        print(r.stderr)

    harness_file = TMP / "harness.js"
    harness_file.write_text(HARNESS + "\n" + js + "\n" + TESTS, encoding="utf-8")
    r = subprocess.run(["node", str(harness_file)], capture_output=True, text=True, timeout=60)
    print(r.stdout, end="")
    if r.stderr:
        print(r.stderr, end="")
    m2 = re.search(r"RINGKASAN lolos=(\d+) gagal=(\d+)", r.stdout)
    if m2:
        lolos += int(m2.group(1))
        gagal += int(m2.group(2))
    else:
        gagal += 1
        print("FAIL: harness Node tidak menghasilkan ringkasan")
    check("harness Node keluar 0", r.returncode == 0)

    print(f"RINGKASAN TOTAL lolos={lolos} gagal={gagal}")
    return 0 if gagal == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
