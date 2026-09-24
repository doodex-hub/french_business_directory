# Migration Intake — french_business_directory

**Step:** 1 — Intake & Scope
**Versi:** 19.0 → 20.0
**Tanggal:** 2026-09-24
**Status:** ✔️ Disetujui — gate lulus (konfirmasi dev via dialog intake 2026-09-24; baseline spec terisi)

---

## 0. Folder Referensi — Dikonfirmasi Dev

Semua path sudah disebut eksplisit oleh dev di prompt kickoff sesi ini (2026-09-24) dan di `CLAUDE.md` §Folder — tidak ditanya ulang, cukup diverifikasi lewat `ls`:

- `native-target` (Community 20.0): `D:\Kuncoro\doodex\repo\odoo20` — repo Community penuh, `odoo/release.py` `version_info = (20, 0, 0, FINAL, 0, '')`.
- `native-target-enterprise` (20.0): `D:\Kuncoro\doodex\repo\enterprise20` — addons-only, terpisah (bukan folder gabungan). Tidak wajib dianalisis (lihat §2: tidak ada dependency Enterprise), tetap tersedia jaga-jaga.
- `native-source` (Community 19.0): `D:\Kuncoro\doodex\repo\odoo19`; `native-source-enterprise`: `D:\Kuncoro\doodex\repo\enterprise19`.
- `third-party-source` / `third-party-target` (OCA): **tidak dipakai** — scan manifest hanya menemukan `base`/`contacts`/`l10n_fr`/`mail`; dependency opsional runtime `res.country.department` (BSL-006) sudah diketahui sejak project 17→18 dan tidak pernah ter-install di environment manapun (diputuskan tidak di-connect, sama seperti project sebelumnya).

### 0a. Konfirmasi Branch/Versi

- **Versi Odoo semantik: 19.0 → 20.0** — dikonfirmasi eksplisit dev di prompt kickoff ("Lakukan migrasi 19→20").
- **Source:** branch `migration/19.0` di repo yang SAMA (tidak ada `source-codebase` folder terpisah — kode 19.0 dibaca via `git show migration/19.0:<path>`). HEAD `35c4e25`. Dikonfirmasi dev di prompt kickoff ("Source branch: migration/19.0").
- **Target:** branch `migration/20.0` (dibuat saat conditioning dari `migration/19.0`), folder `D:\Kuncoro\doodex\repo\french-business-directory-migration-20` (repo ini, folder utama). Dikonfirmasi dev di prompt kickoff ("target branch: migration/20.0 (sudah dibuat saat conditioning)").
- Kode addon di `migration/20.0` saat intake = byte-identik dengan `migration/19.0` (dicek `git diff --stat migration/19.0 HEAD` — hanya `CLAUDE.md`/`.claude/settings.json`/skeleton `doc-dev` yang berbeda).

### 0b. Gate `.claude/settings.json`

`Environment eksekusi = Claude Code CLI`, varian Mode Git. `grep -c "{{" .claude/settings.json` = **0** — tidak ada placeholder literal tersisa. Deny `Edit` sudah terisi path nyata: `odoo19`, `enterprise19`, `odoo20`, `enterprise20`, `migration-tool/knowledge/**`, `migration-tool/templates/**`. Tidak ada baris `source-codebase`/`third-party-*` (tidak dipakai project ini). Gate terpenuhi, tidak ada perubahan yang dibutuhkan.

**Pre-flight Mode Git (2026-09-24):** dev konfirmasi GUI git client ditutup; `.git/index.lock` tidak ada; working tree bersih kecuali folder untracked `.claude/skills/` (skill Odoo `odoo-guidelines`/`odoo-review`/`odoo-security`/`odoo-web-guidelines` yang disalin dev) — **dev konfirmasi: biarkan untracked, tidak pernah di-stage**.

**Skill:** dev minta memakai skill di `migration-tool\.claude\skills` — folder itu tidak ada di `migration-tool`; set skill yang sama (Odoo Skill Library) sudah terpasang di `target-codebase/.claude/skills/` dan dipakai dari sana (dipakai terutama di Step 8 code review).

---

## Ringkasan untuk Review — Perlu Konfirmasi User

1. **Sifat migrasi, sync, aset store — semua dikonfirmasi dev (dialog intake 2026-09-24):** port kode saja (Step 7 di-skip); source `migration/19.0` beku (SYNC_POLICY tidak dipakai); aset store di branch rilis `19.0` (banner.gif ~23MB, icon.png baru, folder `assets` baru, `index.html` baru, fix key `images`) **TIDAK di-port** — baseline = `migration/19.0` HEAD apa adanya. Dicatat di `FINDINGS.md` MF-07 sebagai keputusan terpisah dev nanti.
2. **G1/Step 9 dijalankan AI (Mode C)** — dikonfirmasi dev. Docker Hub belum punya `odoo:20.0` (knowledge `19-to-20.md`) → build dari source `odoo20` di-mount read-only (pola yang sudah terbukti di project 19→20 lain).
3. **Tidak ada dependency Enterprise/OCA** — scan manifest: `base`, `contacts`, `l10n_fr`, `mail` (semua Community). Konsisten dengan dua project sebelumnya.
4. **Deadline/owner/dokumen pelengkap: belum relevan, dilewati** — diwarisi dari project 18→19 (single owner, tanpa deadline, tanpa dokumen pelengkap selain `doc-dev/` sendiri). Test lama = `fr_business_directory/tests/test_siret_wizard.py` (16 test) + `personal_email_usage/tests/test_fetchmail.py` (14 test) di dalam repo ini — lokasinya SAMA dengan source.
5. **Pre-scan native 20.0 menemukan 4 breaking change install-/fitur-blocking** (dicek dini di Step 1 karena menentukan scope; detail lengkap di `02_DIFF_ANALYSIS.md`):
   - `ir.model.access` (model + format CSV) **dihapus total**, diganti `ir.access` (`ir.access.csv`) → `fr_business_directory` gagal install kalau tidak dikonversi.
   - `res.partner.company_registry` **dihapus total dari base**, diganti JSON `additional_identifiers` (key `FR_SIRET`, dengan validasi Luhn) → tombol "Select" wizard (fitur inti) gagal.
   - `base.view_partner_form` 20.0 tidak lagi punya `<field id="company" name="name">` (form Contacts dirombak: satu field `name`, `is_company` jadi computed dari VAT) → view inherit gagal install + semantik visibilitas tombol berubah.
   - package `odoo.osv` **dihapus total** → `from odoo.osv import expression` (unused) di `personal_email_usage` → ImportError.

---

## 1. Modul & Scope

- **Modul yang dimigrasi:** `french_business_directory` (repo) — DUA addon independen:
  - `fr_business_directory` — quick-search SIRET/SIREN via API gouv.fr, isi field partner Perancis
  - `personal_email_usage` — kontrol lanjutan fetch email IMAP (`fetchmail.server`)
- Tidak saling depend (tidak ada `depends` silang, tidak ada referensi model/field lintas addon). Diinstal bersamaan di satu `docker-env/`.

## 2. Dependency Map (auto-scan)

| Dependency | Tipe | Versi tersedia di target (20.0)? | Catatan |
|---|---|---|---|
| `base` | Native Community | Ya | `company_registry` DIHAPUS, diganti `additional_identifiers` (DIFF-02); `ir.model.access`→`ir.access` (DIFF-01); form partner dirombak (DIFF-03) |
| `contacts` | Native Community | Ya | Action Contacts `context={'default_is_company': True}` (relevan untuk DIFF-03) |
| `l10n_fr` | Native Community | Ya | 20.0: `views/res_partner_views.xml` (relabel `company_registry`→"Siren/Siret") DIHAPUS; model `res.partner` tinggal `l10n_fr_is_french` |
| `mail` | Native Community | Ya | `fetchmail.py` 19→20 hampir identik (+`_rollback_progress()` di jalur error); `mail.thread.message_new/message_process` signature stabil |

Dependency opsional runtime: `res.country.department` (dicek via `ir.model.search`, BSL-006) — tidak terinstall, sama seperti project sebelumnya.

## 2b. Struktur & Fitur Modul (auto-scan)

| Fitur | Ada di modul? | Lokasi/bukti | Fase step 6 |
|---|---|---|---|
| Controllers (route custom) | Tidak | tidak ada `controllers/` di kedua addon | D1 → N/A |
| Assets/CSS/JS custom | Tidak | `fr_business_directory` `'assets': {}` kosong; tidak ada `static/src/` di kedua addon | D2, E, F → N/A |
| Komponen Owl/JavaScript custom | Tidak | tidak ada file `.js` | E, F → N/A |
| Field JSON / relasi berantai >2 level / dynamic model | Ya (baru, sisi target) | 20.0: tulis ke `res.partner.additional_identifiers` (Json) — kebutuhan adaptasi DIFF-02. Kode 19.0 sendiri: tidak ada | B2 |
| View `attrs=`/`states=`/dinamis | Tidak (sudah inline expression sejak 17→18) | `views/partner.xml`, `views/siret_wizard_views.xml`, `views/mail_views.xml` | C2 (cek ringan) |

## 3. Sifat Migrasi

- [x] Port kode saja (belum ada data produksi — instalasi baru di versi target) — dikonfirmasi dev 2026-09-24
- [ ] Upgrade instance

## 4. Baseline Spec / Characterization Test (gate)

- [x] `FUNCTIONAL_SPEC.md` lama: tidak ada di repo. Baseline sebelumnya = `doc-dev/migration_18.0_19.0/doc/01_intake/01b_BASELINE_SPEC.md` (BSL-001..024, semua tervalidasi 18→19) — dipakai sebagai draft, di-cross-check ulang baris-per-baris ke kode 19.0 aktual.
- [x] Test lama: ADA, lokasi SAMA dengan source (`*/tests/*.py` di branch `migration/19.0`) — 30 test (16+14), lulus 30/30 di G1 final project 18→19 (`FINDINGS.md` 18→19 MF-04). Asal-usul: backfill 17.0 (`doc-dev/backfill/`) → project 17→18 → 18→19.
- [x] `01b_BASELINE_SPEC.md` terisi — lihat file itu (BSL-001..BSL-030).

### 4a. Dokumen Pelengkap Lain

- [x] Tidak ada dokumen pelengkap di luar repo — diwarisi dari konfirmasi dev project 18→19 (2026-08-26), dev tidak menyebut dokumen baru di kickoff sesi ini. Dokumen internal yang dibaca: `doc-dev/migration_18.0_19.0/doc/{01_intake,FINDINGS.md}`, `doc-dev/migration_17.0_18.0/`, `migration-tool/migration-records/french_business_directory_18.0_19.0/SUMMARY.md`.

## 4b. Source Masih Aktif Dikembangkan?

- [x] Tidak — `migration/19.0` dibekukan (dikonfirmasi dev 2026-09-24).

## 5. Scope Boundary

- **Yang harus tetap identik:** seluruh BSL-001..BSL-030 (`01b_BASELINE_SPEC.md`), termasuk bug pre-existing yang dipertahankan (BSL-008/009/010/011/020/021).
- **Yang sengaja diubah (wajib kompatibilitas 20.0, bukan pilihan):** konversi ACL ke `ir.access.csv`; target tulis SIRET `company_registry`→`additional_identifiers['FR_SIRET']`; struktur xpath view partner; hapus import `odoo.osv` yang tidak dipakai; versi manifest `20.0.1.0.0`. Keputusan desain di dalamnya dicatat di `FINDINGS.md` MF-01..MF-06.
- **Yang sengaja TIDAK di-port:** aset store branch rilis `19.0` (MF-07, keputusan dev).

## 6. Constraint

- Deadline: belum relevan, dilewati (tidak ada deadline khusus).
- Owner tiap step: single owner (dev sendiri, `kuncoro@doodex.net`).
- **Constraint operasional dari dev (kickoff 2026-09-24):** jalan terus Step 1→9 tanpa henti; **STOP WAJIB sebelum Step 10** (QA browser live) — lapor "siap Step 10, menunggu slot" karena Step 10 dibatasi slot lintas-repo (maks. 2 repo kecil bersamaan atau 1 repo besar sendirian; kontensi browser-tool/Docker, MF-46).
