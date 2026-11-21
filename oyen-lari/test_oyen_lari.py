#!/usr/bin/env python3
"""Uji Oyen Lari: string wajib + node --check + logika inti via harness Node.

Jalankan: python3 test_oyen_lari.py
Keluar 0 bila semua lolos.
"""
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
HTML = HERE / "index.html"
TMP = Path("/tmp/oyen_lari_test")

WAJIB = [
    "Oyen Lari", "localStorage", "oyenLari.rekor", "Kembali ke Game",
    "Harga menyusul", "Spasi", "500 m", "3 nyawa", "Suara",
    "lambat", "normal", "cepat", "Demo web",
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

// --- matematika murni ---
check("hitungLevel(0)=1", T.hitungLevel(0) === 1);
check("hitungLevel(499)=1", T.hitungLevel(499) === 1);
check("hitungLevel(500)=2", T.hitungLevel(500) === 2);
check("hitungLevel(1500)=4", T.hitungLevel(1500) === 4);
check("hitungSkor(100, 2)=150", T.hitungSkor(100, 2) === 150);
check("hitungSkor(0, 0)=0", T.hitungSkor(0, 0) === 0);

// --- kecepatan naik tiap level ---
const k1 = T.kecepatanSekarang();
T.setJarak(1000); // level 3
const k3 = T.kecepatanSekarang();
check("kecepatan naik saat level naik", k3 > k1);
check("setJarak(1000) -> level 3", T.status().level === 3);

// --- alur main: lompat + jarak bertambah ---
T.mulai();
check("status main setelah mulai", T.status().status === "main");
check("nyawa awal 3", T.status().nyawa === 3);
const y0 = T.status().oyenY;
T.lompat();
T.langkah(5);
check("lompat mengangkat Oyen", T.status().oyenY < y0);
T.langkah(120);
check("jarak bertambah saat berlari", T.status().jarak > 0);
check("skor = jarak + bonus ikan", T.status().skor === T.status().jarak + T.status().ikan * 25);

// --- koin ikan ---
const ikan0 = T.status().ikan;
T.tambahKoin();
check("koin menambah ikan & skor +25", T.status().ikan === ikan0 + 1 && T.status().skor === T.status().jarak + (ikan0 + 1) * 25);

// --- nyawa & game over + rekor tersimpan ---
T.tabrak(); T.tabrak();
check("nyawa berkurang jadi 1 setelah 2 tabrakan", T.status().nyawa === 1);
check("belum selesai di nyawa 1", T.status().status === "main");
const skorAkhir = T.status().skor;
T.tabrak();
check("game over saat nyawa 0", T.status().status === "selesai");
check("rekor tersimpan di localStorage", store["oyenLari.rekor"] === String(Math.max(skorAkhir, 0)) && T.status().rekor === skorAkhir);

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
    js_file = TMP / "oyen-lari.js"
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
