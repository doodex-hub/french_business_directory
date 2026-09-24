# Business Flow — Migrasi french_business_directory

**Step:** 10 — QA Testing (gate)
**Ref:** `05_acceptance/05a_MIGRATION_ACCEPTANCE_CRITERIA.md`, `FINDINGS.md` (MF-02, MF-03, RMV-01..04)
**Tanggal:** 2026-09-24 (slot diberikan dev: "mulai step 10")
**Status:** ✔️ Lulus (setelah paket perbaikan RMV-02/03/06 disetujui dev) — sisa terbuka: MF-03 workaround (sign-off Step 11), RMV-04/05 GAP-LAMA

**Environment:**
- **20.0 (target):** `docker-env/` — Odoo 20.0 from source, DB `fbd_qa_20` (install bersih, tanpa demo), port 8196, branch `migration/20.0`.
- **19.0 (Cross-Version Compare):** worktree sementara `migration/19.0` @ `35c4e25` + image `odoo:19.0`, DB `fbd_qa_19`, port 8197. Dibongkar setelah selesai (worktree dihapus, container `down -v`).
- **Engine AI-interaktif:** Playwright MCP (headless, CLI). API `recherche-entreprises.api.gouv.fr` **LIVE** (tidak di-mock).
- **Bukti:** screenshot di `evidence/`, query DB `res_partner`/`siret_wizard`, log server.

> Step 10 untuk UI dalam-modul: modul tanpa Owl/JS custom (Fase E N/A), jadi tidak ada tour Step 9. Skenario di sini menguji alur UI nyata + API live yang TIDAK bisa dicakup test otomatis (Step 9 me-mock `requests.get`).

## Checklist Skenario

- [x] Skenario dari AC risiko tinggi (AC-01-01/02 MF-03, AC-04-01/04/05 MF-02, AC-02/03 API live).
- [x] **Cross-Version Compare: DIJALANKAN** — kriteria "area risiko tinggi" terpenuhi (MF-02/MF-03 menyentuh fitur inti), dan temuan kritis S-06 butuh bukti apakah regresi atau bawaan 19.0. Prosedur `templates/CROSS_VERSION_COMPARE.md` (static-diff dulu → live kandidat → visual pass). Findings `RMV-01..04` di `FINDINGS.md`.
- [x] Spot-check integritas data: N/A (port kode saja, Step 7 N/A).
- [x] **Multi-dialog dari satu aksi:** ADA — wizard (`siret.wizard`) → dialog baris hasil (`siret.wizard.result`) → dialog konfirmasi Select, bertumpuk. Skenario "hanya satu dialog disentuh" = S-06 (Select dari dialog hasil setelah wizard di-reload paginasi) — **menemukan RMV-02**.

---

### S-01: Kontak baru dari aplikasi Contacts — tombol tampil sebaris dengan nama
**Level:** Smoke
**Precondition:** login admin, aplikasi Contacts.
**Mode eksekusi:** AI-interaktif (Playwright MCP)
**Steps:** Contacts → New.
**Expected:** field nama (placeholder "Name (company or person)") dan tombol "Business Directory" sebaris; tombol dengan ikon kaca pembesar.
**Actual:** layout benar (field + tombol sebaris, `evidence/s01-new-contact.png`). **Ikon rusak awalnya** ("-🔍", karena Font Awesome dihapus di 20.0 → RMV-01) → **difix** (`icon="search"`), diverifikasi ulang: "🔍 Business Directory" identik 19.0 (`evidence/s08-icons-fixed.png` vs `evidence/cvc19-new-contact.png`).
**Status:** [x] Pass (setelah fix RMV-01)
**Provenance:** [DIKONFIRMASI]

### S-02: Klik tombol pada kontak baru → wizard terbuka, hasil halaman 1 dari API live
**Level:** Smoke
**Precondition:** S-01, nama "LA POSTE" diketik (belum disimpan).
**Mode eksekusi:** AI-interaktif
**Steps:** klik "Business Directory".
**Expected:** record tersimpan otomatis, wizard "Search For Companies" terbuka dengan hasil halaman 1 (`q=LA POSTE&page=1&per_page=25&limite_matching_etablissements=100`).
**Actual:** percobaan 1: API membalas **HTTP 429 Too Many Requests** → `NameError: _logger` (bug bawaan BSL-008) → dialog "Oops" (`evidence/s01-after-click.png`) — lihat RMV-03. Record TETAP tersimpan (id 6). Percobaan 2: "10,000 Results Found", 1/400, 25 baris (`evidence/s02-wizard-open.png`).
**Status:** [x] Pass (alur benar; kegagalan percobaan 1 = GAP-LAMA RMV-03, identik 19.0)
**Provenance:** [DIKONFIRMASI]

### S-03: MF-03 workaround — company TANPA VAT yang sudah tersimpan tetap bisa membuka wizard
**Level:** Main Flow
**Precondition:** partner LA POSTE (id 6) tersimpan, tanpa VAT, tanpa parent (`is_company = False` di 20.0).
**Mode eksekusi:** AI-interaktif
**Steps:** buka partner → klik tombol.
**Expected:** tombol tampil dan wizard terbuka (skenario yang dinilai dev bisa jadi blocker).
**Actual:** tombol tampil di record tersimpan, wizard terbuka berulang kali (S-02 percobaan 2, S-07). **Workaround MF-03 bekerja live.**
**Status:** [x] Pass — MF-03 tetap OPEN (sisa gap: individu tanpa parent juga melihat tombol; sign-off Step 11)
**Provenance:** [DIKONFIRMASI]

### S-04: Paginasi Next / Prev / wrap-around (API live)
**Level:** Main Flow
**Mode eksekusi:** AI-interaktif
**Steps:** Next (1→2), Prev (2→1), Prev di halaman 1 (→400), Next di halaman 400 (→1).
**Expected:** BSL-003 — hasil lama di-unlink, halaman berganti, wrap-around; BSL-009 — Prev tanpa `limite_matching_etablissements`.
**Actual:** semua transisi benar (1→2 "4 DU POINT DU JOUR", 2→1, 1→400, 400→1). Log: `unlink` hasil lama sebelum fetch; URL Prev = `...&page=1&per_page=25` TANPA `limite_matching_etablissements` (BSL-009 terbukti live). 2 dari ±6 panggilan kena 429 → NameError (RMV-03); transaksi gagal di-rollback, halaman tetap (data aman). Judul dialog berubah "Odoo" setelah paginasi — identik 19.0 (RMV-04).
**Status:** [x] Pass
**Provenance:** [DIKONFIRMASI]

### S-05: Tampilan hasil & etablissement — badge status, terjemahan activité, ikon panah
**Level:** Detail
**Mode eksekusi:** AI-interaktif
**Steps:** buka baris hasil pertama (siège La Poste).
**Expected:** "100 Results Found", kolom Siret/Core Business/Address/Date/Status, badge hijau "en activité", terjemahan kode `Z`; panah "← Prev" / "Next →" seperti 19.0.
**Actual:** sesuai (`evidence/s04-result-form.png`): badge hijau "en activité", "Administration publique (tutelle)… (53.10Z)". Panah: rusak awalnya ("-- Prev", "Next" tanpa panah — RMV-01) → difix (`arrow_back`/`arrow_forward`), identik 19.0 (`evidence/s08-wizard-fixed2.png` vs `evidence/cvc19-wizard.png`). Catatan: "None FRM DE VALSERY" (`numero_voie` kosong → "None") muncul juga di 19.0 (RMV-04).
**Status:** [x] Pass (setelah fix RMV-01)
**Provenance:** [DIKONFIRMASI]

### S-06: Select setelah paginasi — partner mana yang tertimpa? (skenario multi-dialog)
**Level:** Negative
**Precondition:** wizard dibuka dari partner LA POSTE (id 6), lalu dipaginasi minimal sekali.
**Mode eksekusi:** AI-interaktif + query DB, di 20.0 DAN 19.0 (Cross-Version Compare)
**Steps:** Next/Prev → buka baris hasil → Select → Ok.
**Expected:** partner id 6 yang ditimpa (BSL-004: partner dari `active_id` = kontak asal).
**Actual:** **partner yang ditimpa = partner dengan id SAMA dengan id wizard**, bukan partner asal. 20.0: wizard 1 → partner 1 ("My Company", partner perusahaan sendiri: nama/alamat/SIRET tertimpa). 19.0: wizard 1 → partner 1, wizard 2 → partner 2 (OdooBot) — **identik**. Penyebab: `fetch_next_page`/`fetch_previous_page` mengembalikan action tanpa `context`, dialog di-reload dengan `active_id` = id wizard sendiri. Tanpa paginasi → partner benar (S-07). **RMV-02 — GAP-LAMA, dampak korupsi data.**
**Status:** [x] Pass (setelah fix RMV-02 disetujui dev) — run pertama FAIL (GAP-LAMA, identik 19.0); rerun 2026-09-24 10:11 dengan data demo `rmv02_demo_setup.py`: kontak asal id 6 ter-update, korban id 7 utuh (`evidence/s09-rmv02-fixed-asal.png`)
**Provenance:** [DIKONFIRMASI]

### S-07: Select tanpa paginasi — SIRET cabang La Poste (MF-02, kasus checksum khusus)
**Level:** Main Flow
**Precondition:** wizard fresh dari partner id 6, tanpa paginasi.
**Mode eksekusi:** AI-interaktif + query DB
**Steps:** buka baris 2 (MORTEAU) → Select etablissement → dialog "Are you sure want to overwrite the Data?" → Ok.
**Expected:** partner 6 ditimpa: nama, alamat, kode pos, kota, SIRET (`FR_SIRET`), SIREN terdeduksi.
**Actual:** partner 6: `27 GRANDE RUE`, `25500`, `MORTEAU`, `additional_identifiers = {"FR_SIRET": "48331597400012", "FR_SIREN": "483315974"}`. Form partner menampilkan field **SIRET** dan **SIREN** walau negara kosong (`evidence/s08-icons-fixed.png`). Select cabang La Poste `35600000024221` (aturan checksum khusus) juga diterima validator (S-06, tercatat di partner 1). Tidak ada ValidationError untuk SIRET resmi.
**Status:** [x] Pass
**Provenance:** [DIKONFIRMASI]

### S-08: Incoming Mail Server — field "Mark Emails as Read"
**Level:** Detail
**Mode eksekusi:** AI-interaktif
**Steps:** Settings → Technical → Incoming Mail Servers → New (`?debug=1`) → tab Advanced.
**Expected:** BSL/`mail_views.xml` — `mark_read` setelah "Keep Attachments", default tidak dicentang, hanya mode developer.
**Actual:** label berurutan "Keep Attachments", "Mark Emails as Read", "Keep Original"; checkbox tidak dicentang (`evidence/s07-fetchmail-form.png`).
**Status:** [x] Pass
**Provenance:** [DIKONFIRMASI]

### S-09: Tanpa mode developer, "Mark Emails as Read" tidak tampil
**Level:** Negative
**Mode eksekusi:** AI-interaktif
**Steps:** form yang sama dengan `?debug=0`.
**Expected:** field tersembunyi (`groups="base.group_no_one"`).
**Actual:** `mark_read` tidak ada di DOM (tab Advanced native juga tersembunyi).
**Status:** [x] Pass
**Provenance:** [DIKONFIRMASI]

### S-10: Fetchmail cron/filter email (level pipeline)
**Level:** Detail
**Mode eksekusi:** — (tidak dieksekusi live)
**Expected:** filter user internal / non-kontak / dedup / mark_read di cron.
**Actual:** tidak dijalankan dengan mailbox sungguhan (GreenMail) — dicover 14 test IMAP-mock Step 9 (`test_fetchmail.py`, PASS) dan entry point cron 20.0 terverifikasi statis (02 §0e).
**Status:** [x] Pass
**Provenance:** [HASIL-BACA — ref: Step 9, AC-08..AC-11]

### S-11: API membalas 429 → modul menunggu & mencoba ulang, tanpa "Oops" (setelah fix RMV-03/06)
**Level:** Main Flow
**Precondition:** paket perbaikan RMV-02/03/06 (disetujui dev 2026-09-24), data demo `rmv02_demo_setup.py`.
**Mode eksekusi:** AI-interaktif + log server + query DB
**Steps:** buka wizard dari kontak LA POSTE → Next.
**Expected:** saat disimpan wizard TIDAK memanggil API ulang; kalau API membalas 429, modul menunggu `Retry-After` lalu mencoba ulang; halaman 2 tampil tanpa traceback.
**Actual:** `web_save` 7 ms tanpa panggilan API, `total_pages=400` tersimpan, 25 hasil (tanpa record yatim). API membalas 429 → log `Directory API rate limited (429), retrying in 4.0s` → percobaan ulang sukses → halaman 2 tampil, **tanpa dialog "Oops"**. Pesan `UserError` Inggris untuk 429 berkepanjangan dicover test (`test_429_persisting_shows_english_busy_message`) — tidak dipaksakan live karena 429 tidak bisa dipicu sesuka hati.
**Status:** [x] Pass
**Provenance:** [DIKONFIRMASI] (pesan UserError: [HASIL-BACA — ref: Step 9 test])

---

## Paket perbaikan pasca-Step 10 (disetujui dev 2026-09-24)

RMV-02, RMV-03, RMV-06 diperbaiki atas persetujuan eksplisit dev (deviasi disengaja dari 19.0), pesan user dalam bahasa Inggris. Detail & bukti: `FINDINGS.md` §"Paket perbaikan pasca-Step 10". `run-test.sh`: **0 failed, 0 error of 53**. S-06 dan S-11 di-rerun live → Pass.

## Loop-back yang dilakukan di Step 10

| Temuan | Klasifikasi | Tindakan | Bukti |
|---|---|---|---|
| RMV-01 ikon Font Awesome rusak (tombol, Prev, Next) | REGRESI | ✅ Difix di target: `partner.xml` `icon="search"`, `siret_wizard_views.xml` `icon="arrow_back"` + `<i class="oi" data-icon="arrow_forward"/>`; test baru `test_no_font_awesome_icons_rmv01` | Visual identik 19.0; `run-test.sh` 0 failed, 0 error of 44 |
| RMV-02 Select setelah paginasi menimpa partner id = id wizard | GAP-LAMA | ✅ Difix (disetujui dev) — action paginasi membawa context | S-06 rerun Pass |
| RMV-03 API 429 memicu NameError BSL-008 (sering) | GAP-LAMA | ✅ Difix (disetujui dev) — `_logger`, retry 429, UserError Inggris | S-11 Pass |
| RMV-05 `TypeError` bila `libelle_voie` null | GAP-LAMA | Dicatat, belum diputuskan | demo CARREFOUR hal. 2 |
| RMV-06 API dipanggil 2x pada Next pertama | GAP-LAMA | ✅ Difix (disetujui dev) — `default_get` + `force_save` | S-11 Pass |
| RMV-04 "None" di alamat, judul dialog "Odoo" | GAP-LAMA (kosmetik) | Dicatat | S-04, S-05 |

## Ringkasan per Level

| Level | Skenario | Jumlah |
|---|---|---|
| Smoke | S-01, S-02 | 2 |
| Main Flow | S-03, S-04, S-07, S-11 | 4 |
| Detail | S-05, S-08, S-10 | 3 |
| Negative | S-06, S-09 | 2 |

## Rekap Provenance

| Provenance | Jumlah | Skenario |
|---|---|---|
| `[DIKONFIRMASI]` | 10 | S-01..S-09, S-11 |
| `[HASIL-BACA]` | 1 | S-10 (ref Step 9) |
| `[HASIL-BACA-MURNI]` | 0 | — |
| `[PERLU-KEPUTUSAN]` | 0 (S-06 dieksekusi, keputusan fix di FINDINGS RMV-02) | — |

## Human QA Checklists

Digenerate di `human_qa/` (00_README + 01_SMOKE + 02_MAIN_FLOW + 03_DETAIL + 04_NEGATIVE).

## Verdict

- [x] ✅ **Lulus** (2026-09-24, setelah paket perbaikan) — semua skenario live Pass (S-01..S-09, S-11) + S-10 `[HASIL-BACA — ref Step 9]`. RMV-01 (regresi) difix; RMV-02/03/06 (bug bawaan) difix atas persetujuan dev, pesan Inggris; `run-test.sh` 0 failed of 53. **Masih terbuka untuk Step 11:** MF-03 workaround (sign-off aturan tombol), RMV-04/RMV-05 (GAP-LAMA, belum diputuskan).
- [ ] ⚠️ Lulus Bersyarat — (status sebelum paket perbaikan) semua regresi migrasi sudah difix dan terverifikasi live (RMV-01); fitur inti berjalan di 20.0 dengan API live (S-01..S-05, S-07..S-09 Pass). **Satu skenario Negative FAIL karena bug bawaan 19.0 (RMV-02: Select setelah paginasi menimpa partner yang salah — korupsi data)**. Bukan regresi migrasi, tapi dampaknya tinggi → **butuh keputusan dev sebelum Step 11**: (a) terima sebagai known issue (port apa adanya), atau (b) izinkan fix minimal (action paginasi membawa `context` asal). Juga MF-03 (workaround, OPEN) dan RMV-03 (429 → NameError) menunggu keputusan.
- [ ] ❌ Ada kegagalan regresi
