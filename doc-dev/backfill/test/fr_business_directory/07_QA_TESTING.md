# QA Testing — fr_business_directory

**Step:** 07 — QA Testing (backfill, TANPA UAT — BACKFILL berhenti di sini)
**Ref:** `doc-dev/backfill/spec/fr_business_directory/01A_FUNCTIONAL_SPEC.md`,
`doc-dev/backfill/spec/fr_business_directory/01B_ACCEPTANCE_CRITERIA.md`, `03B_TEST_PLAN.md`
**Tanggal:** 2026-08-07

---

## 1. Area / AC yang Harus Dicakup

- [x] AC-01 — Visibilitas tombol Business Directory (`is_company`)
- [x] AC-02 — Auto-fetch saat wizard dibuka + jalur error `_logger` (F-01)
- [x] AC-03 — Navigasi paginasi + wrap-around
- [x] AC-04 — Select hasil → write ke partner (termasuk dialog konfirmasi overwrite)
- [x] AC-05 — Tampilan badge status administratif

**Cek "hanya satu dialog disentuh"** (`CLAUDE_TEMPLATE.md`) — **N/A untuk modul ini**: hanya SATU
dialog yang bisa terpicu dari alur ini (wizard SIRET sendiri, `target: 'new'`), dan di dalamnya
hanya SATU dialog konfirmasi (`confirm="Are you sure want to overwrite the Data?"` pada tombol
Select) — tidak ada dialog KEDUA yang independen bisa terpicu bersamaan dari aksi yang sama. Dicatat
eksplisit sebagai N/A, bukan dilewati diam-diam.

---

## 2. Format Skenario

```
### S-{{NN}}: {{Nama Skenario}}
**Precondition:** {{kondisi awal}}
**Mode eksekusi:** {{Mode B (docker) / AI-in-the-loop (browser) / Desk-review — WAJIB diisi}}
**Steps:** ...
**Expected:** {{...}}
**Actual:** {{diisi saat eksekusi}}
**Status:** ☐ Pass / ☐ Fail
**Provenance:** ...
```

---

## 3. Skenario

### S-01: Tombol Business Directory hanya tampil untuk kontak Company
**Precondition:** Dua kontak — satu `is_company=True`, satu `is_company=False`.
**Mode eksekusi:** Desk-review (baca `views/partner.xml:11-14`, `invisible="is_company != True"`
diterapkan di `<div>` pembungkus field nama+tombol) — **TIDAK dijalankan lewat Tour headless
(Mode E)** sesi ini, lihat catatan §7 di bawah untuk alasan eksplisit.
**Steps:**
1. Baca XML view: atribut `invisible` pada `<div>` yang membungkus field `name`+tombol
   `siret_wizard`.
2. Bandingkan dengan behavior Odoo standar: `invisible="..."` domain dievaluasi di klien terhadap
   record value saat ini.
**Expected:** Untuk `is_company=True`, `invisible` evaluate `False` → tombol tampil. Untuk
`is_company=False`, evaluate `True` → tombol tersembunyi.
**Actual:** Sesuai expected — atribut domain XML valid dan konsisten dengan BR-01
(`01A_FUNCTIONAL_SPEC.md`). Tidak ada ambiguitas ditemukan.
**Status:** ✔️ Pass (desk-review)
**Provenance:** `[HASIL-BACA]`

### S-02: Wizard auto-fetch saat dibuka dari partner
**Precondition:** Partner company dengan `name` terisi.
**Mode eksekusi:** Sudah dibuktikan penuh via Unit test nyata (`test_default_get_auto_fetches_first_page`,
Step 04, Mode C) — di sini di-review ulang sebagai konfirmasi cakupan QA, bukan dieksekusi ulang.
**Steps:** (lihat `04A_DEV_TESTING.md` TC-FETCH-01)
**Expected:** Wizard terbuka dengan `result_ids` terisi dari API (mocked di Unit; API asli
`recherche-entreprises.api.gouv.fr` di produksi).
**Actual:** Pass — dikonfirmasi via test run Docker nyata (`0 failed, 0 error(s)`, lihat
`04A_DEV_TESTING.md` §3).
**Status:** ✔️ Pass (via Unit test Step 04, direview ulang di sini)
**Provenance:** `[DIKONFIRMASI]`

### S-03: Navigasi paginasi Next/Prev + wrap-around
**Precondition:** Wizard dengan `total_pages > 1`.
**Mode eksekusi:** Sudah dibuktikan penuh via Unit test nyata (Step 04, TC-PAGE-01) — direview di
sini.
**Steps:** (lihat `04A_DEV_TESTING.md` TC-PAGE-01)
**Expected:** Next/Prev wrap-around bekerja sesuai BR-03; F-02 (param API tidak konsisten) dan F-03
(no-op senyap) terbukti nyata, tercatat di `FINDINGS.md`.
**Actual:** Pass (logic terbukti benar SESUAI kode existing, termasuk dua gap F-02/F-03 yang
terdokumentasi sebagai temuan, bukan dianggap "Fail" test — test yang mendokumentasikan bug
ditandai Pass karena berhasil MEMBUKTIKAN perilaku sekarang, sesuai prinsip provenance
`[PERLU-KEPUTUSAN]`).
**Status:** ✔️ Pass (via Unit test Step 04)
**Provenance:** `[DIKONFIRMASI]`/`[PERLU-KEPUTUSAN]` (campuran, lihat F-02/F-03)

### S-04: Select hasil pencarian + dialog konfirmasi overwrite
**Precondition:** Wizard dengan minimal 1 hasil di `result_ids`.
**Mode eksekusi:** Desk-review (alur dialog) + Unit test nyata (efek `write()`, Step 04
TC-SELECT-01).
**Steps:**
1. (Desk-review) Baca `views/siret_wizard_views.xml:61-63` — tombol "Select" punya atribut
   `confirm="Are you sure want to overwrite the Data?"`, mekanisme dialog konfirmasi BAWAAN Odoo
   (bukan wizard/dialog custom terpisah).
2. (Unit, sudah dijalankan) Panggil `select_siret()` langsung (setelah dialog dikonfirmasi secara
   konseptual — dialog `confirm` HANYA gate di level UI klien, tidak ada logic tambahan di server
   selain menjalankan action seperti biasa setelah user klik "Ok").
**Expected:** User diberi kesempatan membatalkan sebelum data partner tertimpa; setelah konfirmasi,
`write()` berjalan seperti diuji di Unit test.
**Actual:** Sesuai expected. Dialog konfirmasi memakai mekanisme native Odoo (`confirm` attribute)
— tidak ada risiko dialog custom bertumpuk/bersaing (selaras dengan catatan §1 "hanya satu dialog").
**Status:** ✔️ Pass
**Provenance:** `[HASIL-BACA]` (dialog) + `[DIKONFIRMASI]` (efek write, dari Unit test nyata)

### S-05: Badge status administratif tampil sesuai data
**Precondition:** Hasil pencarian dengan `etat_administratif` bervariasi (aktif/tutup).
**Mode eksekusi:** Desk-review (baca `views/siret_wizard_views.xml:57-60`, widget `badge` +
`decoration-success`/`decoration-danger`) + Unit test nyata untuk logic compute (Step 04
TC-...compute display, lihat `04A_DEV_TESTING.md` §2d).
**Expected:** Aktif → badge hijau; tutup → badge merah + tanggal.
**Actual:** Sesuai expected — logic compute terbukti benar via Unit test, binding widget `badge` ke
decoration domain di XML view valid secara statis (pola standar Odoo, tidak ada indikasi
salah-tulis).
**Status:** ✔️ Pass
**Provenance:** `[HASIL-BACA]` (visual) + `[DIKONFIRMASI]` (compute logic)

---

## 4. Status Sub-file & Rekap Eksekusi

| File | Isi | Status | Dieksekusi? | Mode |
|---|---|---|---|---|
| §3 di file ini | 5 skenario (AI-interaktif/desk-review + review Unit test) | ✅ Selesai | Ya | Desk-review + review Unit test Step 04 |
| `07B_QA_AI_BROWSER.md` | N/A untuk sesi ini | N/A | Tidak | — |

**Keterbatasan eksekusi (WAJIB diisi):** Tour headless (Mode E, default AI-Browser di CLI) **TIDAK
dijalankan** sesi ini — lihat rasional eksplisit di §7 di bawah. S-01/S-04/S-05 (elemen visual/dialog)
diverifikasi lewat desk-review kode XML statis, BUKAN eksekusi visual browser sungguhan — lebih
lemah sebagai bukti dibanding Tour nyata, dicatat eksplisit di sini, bukan disamarkan sebagai
"sudah dites visual".

---

## 5. Rekap Findings

| Tag | Jumlah |
|---|---|
| `[PERLU-KEPUTUSAN]` | 3 (F-01, F-02, F-03, F-05 — lihat `FINDINGS.md`) |
| `[DIKONFIRMASI]` | — (belum ada keputusan pemilik modul, semua masih `[PERLU-KEPUTUSAN]`/`[HASIL-BACA]`) |
| `[HASIL-BACA]` (tanpa masalah) | BR-01, BR-04, BR-06, BR-07, BR-08 |

**Verdict:** Backfill dokumentasi selesai sampai Step 07 (QA Testing). **Tidak ada sign-off** — ini
bukan release gate. Keputusan atas item `[PERLU-KEPUTUSAN]` di `FINDINGS.md` ada di tangan pemilik
modul.

---

## 6. Bug / Perlu Perbaikan

> Semua skenario §3 Pass — TIDAK ADA skenario Fail. Bug/gap yang ditemukan (F-01 s.d. F-06) adalah
> temuan dari MEMBUKTIKAN perilaku kode SEKARANG (sesuai prinsip provenance), bukan skenario QA yang
> gagal dieksekusi — detail lengkap tetap satu tempat di `FINDINGS.md`.

| Ditemukan di | Scenario | Ringkasan masalah | Status perbaikan |
|---|---|---|---|
| Tidak ada | — | — | — |

---

## 7. Rasional: Tour Headless (Mode E) TIDAK dijalankan sesi ini

`PLAYBOOK.md` §Mode E menjadikan Tour headless default AI-Browser di CLI. Untuk modul ini,
diputuskan TIDAK dijalankan sesi ini dengan alasan eksplisit (bukan diam-diam dilewati):

1. Kelima AC yang tersisa (AC-01–AC-05) SUDAH masing-masing punya bukti yang kuat: 4 dari 5 sudah
   dibuktikan `[DIKONFIRMASI]` lewat Unit test NYATA (bukan mock murni tanpa eksekusi — dijalankan
   di Docker sungguhan, lihat `04A_DEV_TESTING.md`); sisanya (visibilitas tombol, binding badge)
   adalah pembacaan atribut XML statis yang risiko salah-baca-nya rendah (tidak ada logic
   JS/OWL custom di modul ini yang butuh eksekusi browser nyata untuk dibuktikan — beda dari kasus
   `purchase_product_optional` yang punya dialog CUSTOM dengan state OWL kompleks).
2. Wizard `siret.wizard` bergantung ke API eksternal (`recherche-entreprises.api.gouv.fr`) yang
   TIDAK dikontrol dari Tour test tanpa infra mock tambahan (Tour headless via `HttpCase` tidak
   bisa mem-mock `requests.get` Python dengan cara yang sama seperti `TransactionCase` — perlu
   pendekatan berbeda, mis. `httpretty`/mock server, di luar scope resep Mode E yang ada saat ini)
   — membangun Tour yang genuinely bermakna (bukan cuma "wizard terbuka lalu macet nunggu API
   asli") butuh investasi tambahan yang belum sepadan dengan nilai marginal di atas Unit test yang
   sudah ada.
3. **Bukan klaim "sudah cukup selamanya"** — kalau pemilik modul kelak menambah komponen JS/OWL
   custom (bukan sekadar `<button>`/`confirm` bawaan seperti sekarang), Tour headless jadi wajib
   dipertimbangkan ulang di sesi berikutnya, sesuai §Mode E.
