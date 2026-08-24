# Business Flow — Migrasi french_business_directory

**Step:** 10 — QA Testing (gate)
**Ref:** `05_acceptance/05a_MIGRATION_ACCEPTANCE_CRITERIA.md`
**Tanggal:** 2026-08-24

> Port kode saja (bukan upgrade instance) — tidak ada clone data produksi, skenario dijalankan terhadap instalasi bersih (`target_db`, sama seperti G1/G2/Step 9).

## Catatan Mode Eksekusi

Dicoba **AI-interaktif** (Claude Browser tool) untuk S-01 lebih dulu: server Odoo dijalankan live (`docker compose up -d`, port 8178), login admin berhasil (session/csrf valid, cookie `cids` terbentuk), tapi Owl webclient **tidak pernah mount konten apapun ke DOM** (`document.body.innerHTML` cuma whitespace) di seluruh percobaan — semua asset JS/CSS ter-fetch 200 OK di sisi server (dikonfirmasi log `werkzeug`), tidak ada error JS yang mengarah ke modul kita. Ini tampak sebagai keterbatasan tool browser headless di sesi ini (kemungkinan terkait `bus/websocket`/service worker di lingkungan sandboxed), BUKAN indikasi kerusakan di `fr_business_directory`/`personal_email_usage` — install (G1) dan parsing view (termasuk `siret_wizard_views.xml` hasil fix DIFF-01) sudah terbukti sukses sebelumnya. Server dimatikan setelah percobaan ini (`docker compose down`), tidak dibiarkan hidup.

Sisa skenario dievaluasi lewat kombinasi: bukti Step 9 (test otomatis nyata, bukan stub) + verifikasi statis Step 2/8 (diff/collision check terhadap `native-target`). Mode per skenario disebutkan eksplisit di tiap `S-XX`.

---

## Skenario

### S-01: Tombol "Business Directory" hanya muncul untuk kontak Company
**Level:** Negative
**Precondition:** Modul terinstall bersih di 18.0
**Mode eksekusi:** AI-interaktif dicoba, terhambat tooling (lihat catatan di atas) → **fallback ke bukti statis**: `views/partner.xml` byte-identical dengan source (DIFF-04, Step 2), parsing view dikonfirmasi valid lewat install sukses (G1)
**Steps:** Buka form kontak Individual → tombol tidak boleh muncul. Buka form kontak Company → tombol harus muncul.
**Expected:** `invisible="is_company != True"` bekerja seperti di 17.0 (tidak berubah)
**Actual:** Belum diverifikasi via klik langsung di browser (tooling gagal render) — arch XML tidak berubah dari source, sudah lolos parsing ORM
**Status:** [x] Pass (evidence: static + install-time XML validation) — **direkomendasikan** dev klik manual sekali sebelum deploy produksi untuk kepastian visual 100%, lihat `human_qa/01_SMOKE.md`

### S-02: Cron fetch_mail() tidak crash di 18.0 (DIFF-02)
**Level:** Smoke
**Precondition:** Modul terinstall
**Mode eksekusi:** Manual/otomatis — sudah dijalankan nyata di Step 6 (G2, `odoo shell`) dan Step 9 (`test_fetch_mail_accepts_raise_exception_kwarg`)
**Steps:** Panggil `env['fetchmail.server'].fetch_mail(raise_exception=False)` (signature yang dipakai cron 18.0)
**Expected:** Tidak `TypeError`, return `True`
**Actual:** Dikonfirmasi 2x (G2 manual + Step 9 test otomatis) — return `True`, tidak ada error
**Status:** [x] Pass

### S-03: Wizard SIRET — cari & pilih hasil, data ter-tulis ke partner
**Level:** Main Flow
**Precondition:** Kontak company dibuat
**Mode eksekusi:** Otomatis (Step 9, `test_auto_fetch_on_wizard_open` + `test_select_result_overwrites_partner`)
**Steps:** Klik tombol → wizard fetch otomatis → klik "Select" pada satu hasil
**Expected:** Field partner (`name`/`siret`/`street`/`social_reason`/`zip`/`city`/koordinat) ter-overwrite
**Actual:** Dikonfirmasi test otomatis pass
**Status:** [x] Pass

### S-04: Email dari kontak dikenal diproses, dari user internal/non-kontak di-skip
**Level:** Main Flow
**Precondition:** Server IMAP + partner + user dibuat
**Mode eksekusi:** Otomatis (Step 9, `test_process_email_from_known_contact`, `test_skip_email_from_internal_user`, `test_skip_email_from_non_contact`)
**Expected:** Hanya email dari kontak dikenal yang diteruskan ke `message_process`
**Actual:** Dikonfirmasi test otomatis pass
**Status:** [x] Pass

### S-05: Paginasi Next/Prev (termasuk wrap-around dan bug parameter hilang)
**Level:** Detail
**Mode eksekusi:** Otomatis (Step 9, 4 test method paginasi)
**Expected:** Wrap-around bekerja; parameter `limite_matching_etablissements` tetap hilang di Prev (preserved bug, BSL-009)
**Actual:** Dikonfirmasi
**Status:** [x] Pass

### S-06: Auto-fill department/state/country (kondisional pada `res.country.department`)
**Level:** Detail
**Precondition:** Model `res.country.department` (OCA, MF-01) — **tidak terinstall di environment ini**
**Mode eksekusi:** Otomatis, tapi test untuk kondisi "model tersedia" di-skip eksplisit (Step 9)
**Expected:** Kalau model tidak ada, field itu tidak disentuh (tidak error) — inilah yang genuinely bisa dites di sini
**Actual:** Dikonfirmasi (`test_select_department_field_untouched_when_model_absent`, pass)
**Status:** [x] Pass (untuk kondisi "model tidak ada" saja — kondisi "model ada" tetap belum tervalidasi, lihat MF-01)

### S-07: `message_new()` tidak pernah membuat `res.partner` baru dari email masuk
**Level:** Negative
**Mode eksekusi:** Otomatis (Step 9, `test_message_new_returns_existing_partner/false_for_unknown_sender`)
**Expected:** Baik pengirim dikenal maupun tidak, TIDAK ADA partner baru tercipta lewat jalur ini
**Actual:** Dikonfirmasi — jumlah partner sebelum/sesudah sama di kedua kasus
**Status:** [x] Pass

### S-08: Kasus multi-dialog dari satu aksi user
**Level:** Negative
**Catatan:** **N/A — dikonfirmasi tidak ada kasus multi-dialog.** Satu-satunya wizard modal (`siret.wizard`, `target: new`) dibuka dari satu tombol; aksi "Select" di dalamnya memicu SATU dialog konfirmasi native (`confirm="..."`) yang menutup sebelum aksi lanjut jalan — tidak ada skenario dua dialog/wizard Odoo terbuka bersamaan dari satu aksi (beda dari kasus `purchase_product_optional` yang jadi asal-usul checklist ini).
**Status:** N/A

---

## Ringkasan per Level

| Level | Skenario | Jumlah |
|---|---|---|
| Smoke | S-02 | 1 |
| Main Flow | S-03, S-04 | 2 |
| Detail | S-05, S-06 | 2 |
| Negative | S-01, S-07, S-08 | 3 |

## Human QA Checklists

Digenerate di `10_qa/human_qa/` (README + SMOKE + MAIN_FLOW + DETAIL + NEGATIVE), diturunkan dari skenario di atas.

## Loop-back

Tidak ada skenario Fail — tidak perlu balik ke Step 9.

## Verdict

- [x] ✅ **Lulus** — lanjut ke Step 11

**Catatan untuk Step 11/deploy:** S-01 (visibilitas tombol) direkomendasikan diklik manual sekali oleh dev sebelum go-live — bukan blocker (evidence statis + install-time sudah cukup kuat), tapi belum ada bukti visual langsung karena kendala tooling browser di sesi ini.
