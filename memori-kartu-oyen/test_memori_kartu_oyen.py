#!/usr/bin/env python3
"""Uji Memori Kartu Oyen: string wajib + node --check + logika acak/pasangan/bintang.

Jalankan: python3 test_memori_kartu_oyen.py
Keluar 0 bila semua lolos.
"""
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
HTML = HERE / "index.html"
TMP = Path("/tmp/memori_kartu_oyen_test")

WAJIB = [
    "Memori Kartu Oyen", "localStorage", "oyenMemori.terbaik.", "Kembali ke Game",
    "Harga menyusul", "4 &times; 3", "4 &times; 4", "6 &times; 4", "Demo web",
    "Langkah", "Waktu", "Pasangan",
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
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
let pass = 0, fail = 0;
function check(nama, kond) {
  if (kond) { pass++; console.log("PASS: " + nama); }
  else { fail++; console.log("FAIL: " + nama); }
}
const T = global.OYEN_TEST;
check("OYEN_TEST tersedia", !!T);

// --- acak dek: tiap ukuran tepat 2x tiap gambar ---
for (const uk of [12, 16, 24]) {
  const dek = T.acakDek(uk);
  const hitung = {};
  dek.forEach(g => { hitung[g] = (hitung[g] || 0) + 1; });
  const nilai = Object.values(hitung);
  check("acakDek(" + uk + "): " + (uk / 2) + " pasangan, tiap gambar tepat 2x",
    dek.length === uk && nilai.length === uk / 2 && nilai.every(v => v === 2));
}
// --- acak benar-benar mengacak (10 dek berbeda urutannya) ---
const seen = new Set();
for (let i = 0; i < 10; i++) seen.add(T.acakDek(24).join(","));
check("acakDek menghasilkan urutan bervariasi", seen.size > 1);

// --- pasangan & bintang ---
check("hitungPasangan(12)=6", T.hitungPasangan(12) === 6);
check("hitungPasangan(24)=12", T.hitungPasangan(24) === 12);
check("bintang 6 langkah/6 pasangan = 3", T.hitungBintang(6, 6) === 3);
check("bintang 9 langkah/6 pasangan = 3", T.hitungBintang(9, 6) === 3);
check("bintang 10 langkah/6 pasangan = 2", T.hitungBintang(10, 6) === 2);
check("bintang 15 langkah/6 pasangan = 2", T.hitungBintang(15, 6) === 2);
check("bintang 16 langkah/6 pasangan = 1", T.hitungBintang(16, 6) === 1);
check("formatWaktu(65000)=1:05", T.formatWaktu(65000) === "1:05");
check("formatWaktu(5000)=0:05", T.formatWaktu(5000) === "0:05");

// --- simulasi main penuh papan 4x3 ---
T.setUkuran(12);
check("papan 12 kartu setelah setUkuran(12)", T.status().dekPanjang === 12 && T.status().totalPasangan === 6);
await T.cocokSemua();
await sleep(300);
check("game selesai setelah semua pasangan cocok", T.status().selesai === true);
check("pasangan 6/6", T.status().pasangan === 6);
check("langkah = 6 (sempurna, tanpa salah)", T.status().langkah === 6);
const tb12 = JSON.parse(store["oyenMemori.terbaik.12"]);
check("skor terbaik 12 tersimpan (6 langkah)", tb12 && tb12.langkah === 6 && tb12.bintang === 3);

// --- papan 4x4 juga bisa selesai ---
T.setUkuran(16);
await T.cocokSemua();
await sleep(300);
check("papan 16 selesai, langkah 8", T.status().selesai === true && T.status().langkah === 8);
const tb16 = JSON.parse(store["oyenMemori.terbaik.16"]);
check("skor terbaik 16 tersimpan (8 langkah)", tb16 && tb16.langkah === 8);

console.log("RINGKASAN lolos=" + pass + " gagal=" + fail);
process.exit(fail ? 1 : 0);
})();
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
    js_file = TMP / "memori.js"
    js_file.write_text(js, encoding="utf-8")
    r = subprocess.run(["node", "--check", str(js_file)], capture_output=True, text=True)
    check("node --check pada JS yang diekstrak", r.returncode == 0)
    if r.returncode != 0:
        print(r.stderr)

    harness_file = TMP / "harness.js"
    harness_file.write_text(HARNESS + "\n" + js + "\n" + TESTS, encoding="utf-8")
    r = subprocess.run(["node", str(harness_file)], capture_output=True, text=True, timeout=90)
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
