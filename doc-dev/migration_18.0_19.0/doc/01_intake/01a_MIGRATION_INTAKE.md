# Migration Intake — french_business_directory

**Step:** 1 — Intake & Scope
**Versi:** 18.0 → 19.0
**Tanggal:** 2026-08-26
**Status:** ✔️ Disetujui — gate lulus

---

## 0. Folder Referensi — Dikonfirmasi Dev

- `native-target` + `native-target-enterprise` (SATU folder gabungan, 19.0): `D:\Kuncoro\doodex\repo\enterprise19.0` — dikonfirmasi dev (reuse dari project `advanced_sales_analysis` 18.0→19.0, pasangan versi sama). Diverifikasi lewat `ls`: struktur `odoo/addons/` berisi modul Community (`sale`) DAN Enterprise (`account_accountant`) di level yang sama → satu folder melayani dua peran sekaligus. **Bukan git repo** (hasil extract, bukan clone).
- `native-source` (Community 18.0): `D:\Kuncoro\doodex\repo\odoo18` — dikonfirmasi dev (reuse dari project sama).
- `native-source-enterprise` (18.0): **tidak dipakai** — modul tidak depend Enterprise (lihat §2), tidak perlu di-connect.
- `third-party-source` / `third-party-target` (OCA): **tidak dipakai** — dikonfirmasi dev eksplisit tidak ada dependency OCA/third-party lain di luar hasil scan manifest.

### 0a. Konfirmasi Branch/Versi

- `source-codebase` — folder BARU, di-clone dari `origin/migration/18.0` (`french_business_directory` repo), branch lokal tetap `migration/18.0` — path `D:\Kuncoro\doodex\repo\french-business-directory-migration-19-source`. Dikonfirmasi lewat `git branch --show-current`/`git log` (bukan ditanya ke dev, murni observasi hasil clone).
- `target-codebase` — folder existing (utama), branch lokal `migration/19.0_target` dibuat dari `origin/migration/18.0` (`git checkout -b migration/19.0_target origin/migration/18.0`) — path `D:\Kuncoro\doodex\repo\french-business-directory-migration-19` (repo ini). Nama branch target dikonfirmasi VERBATIM oleh dev di prompt awal sesi ("branch target migration/19.0_target, source copy dari migration/18.0").
- Dikonfirmasi: dua folder di atas adalah dua clone fisik terpisah (hasil `git clone` sibling folder baru, bukan symlink/alias).
- Versi Odoo semantik: **18.0 → 19.0** — dikonfirmasi eksplisit oleh dev di prompt awal ("migrasi 18 ke 19").

### 0b. Gate `.claude/settings.json`

`Environment eksekusi = Claude Code CLI`, `cli-config` sudah di-bootstrap dev sebelum sesi ini (varian Mode Git). Sebelum checkout, dicek `git show origin/migration/18.0:.claude/settings.json` — ternyata SUDAH template `migration-tool` yang sama (bukan config tool lama `doc-dev-backfill` seperti kejadian `advanced_sales_analysis`), cuma placeholder-nya sudah terisi path project 17.0→18.0. Placeholder untuk project INI diisi ulang (dengan persetujuan eksplisit dev — edit `.claude/settings.json` sempat diblokir classifier permission, dev mengonfirmasi lewat dialog terpisah):

- `ABS_PATH_SOURCE_CODEBASE` → `D:\Kuncoro\doodex\repo\french-business-directory-migration-19-source`
- `ABS_PATH_MIGRATION_TOOL` → `D:\Kuncoro\doodex\repo\migration-tool-project\migration-tool` (tidak berubah dari project sebelumnya)
- `ABS_PATH_NATIVE_TARGET` / `ABS_PATH_NATIVE_TARGET_ENTERPRISE` → `D:\Kuncoro\doodex\repo\enterprise19.0` (path SAMA untuk keduanya, sesuai struktur gabungan)
- `ABS_PATH_NATIVE_SOURCE` → `D:\Kuncoro\doodex\repo\odoo18`
- `ABS_PATH_NATIVE_SOURCE_ENTERPRISE` / `ABS_PATH_THIRD_PARTY_SOURCE` / `ABS_PATH_THIRD_PARTY_TARGET` → baris deny dihapus (tidak dipakai project ini)

---

## Ringkasan untuk Review — Perlu Konfirmasi User

1. **Sifat migrasi & source paralel dikonfirmasi dev:** port kode saja (tanpa data produksi, Step 7 di-skip); source (`migration/18.0`) dibekukan selama migrasi berjalan.
2. **Tidak ada dependency Enterprise/OCA** — dikonfirmasi dev eksplisit, konsisten dengan scan manifest (`base`/`contacts`/`l10n_fr`/`mail` saja, semua Community).
3. **Tidak ada deadline khusus, single owner** (dev sendiri), **tidak ada dokumen pelengkap lain** — semua dikonfirmasi dev di intake awal.
4. **Baseline spec 18.0 = hasil validasi ulang baseline 17.0→18.0** — direkonsiliasi dari `doc-dev/migration_17.0_18.0/doc/01_intake/01b_BASELINE_SPEC.md` (BSL-001..BSL-024, semua `[MATCH]`), di-cross-check baris-per-baris LANGSUNG ke kode aktual di `source-codebase` (branch `migration/18.0`) project ini — **1 perubahan ditemukan** dibanding baseline 17.0→18.0: `fetch_mail()` sekarang bersignature `fetch_mail(self, raise_exception=True)` (bukan lagi `fetch_mail(self)` polos) — ini ADALAH hasil migrasi 17→18 sebelumnya (BSL-023 sudah mengantisipasi ini), bukan penyimpangan baru. Semua klaim BSL lain **cocok tanpa perubahan**. Lihat `01b_BASELINE_SPEC.md`.
5. **2 breaking change signifikan ditemukan dari verifikasi langsung `native-source` (odoo18) vs `native-target` (enterprise19.0), WAJIB ditangani di Step 2/3/6** (detail lengkap: `02_DIFF_ANALYSIS.md`):
   - **`fetchmail.server.fetch_mail()` signature berubah LAGI** — 18.0: `fetch_mail(self, raise_exception=True)` → 19.0: `fetch_mail(self)` (parameter `raise_exception` **dihapus total**, bukan cuma dijadikan optional). Override `personal_email_usage/models/mail.py` (baris 61, 156) memanggil `super(...).fetch_mail(raise_exception=raise_exception)` — akan `TypeError` di 19.0 kalau tidak disesuaikan.
   - **`res.partner.siret` (field dedicated dari `l10n_fr`) dihapus total di 19.0** — dikonsolidasi ke field generik core `company_registry` (Char, sudah ada sejak 18.0 untuk keperluan lain, cuma sekarang dipakai ulang oleh `l10n_fr` untuk SIRET, label view di-override jadi "Siret"). `fr_business_directory/models/siret_wizard.py` — `select_siret()` di `siret.wizard.result` (baris 260) DAN `matching.etablissement` (baris 354) menulis `partner.write({'siret': ...})` — field `siret` **tidak akan ditemukan** di `res.partner` 19.0, akan gagal `ValueError`/field tidak dikenal.

---

## 1. Modul & Scope

- **Modul yang dimigrasi:** `french_business_directory` (repo) — berisi DUA addon independen:
  - `fr_business_directory` — quick-search SIRET/SIREN via API gouv.fr, isi field partner Perancis
  - `personal_email_usage` — kontrol lanjutan fetch email IMAP (`fetchmail.server`)
- Kedua addon genuinely tidak berhubungan secara fungsional (tidak ada `depends` silang, tidak ada referensi model/field lintas addon) — sama seperti project 17.0→18.0.

## 2. Dependency Map (auto-scan)

| Dependency | Tipe | Versi tersedia di target (19.0)? | Catatan |
|---|---|---|---|
| `base` | Native Community | Ya | `company_registry` field generik dipakai ulang oleh `l10n_fr` untuk SIRET — lihat §5 |
| `contacts` | Native Community | Ya | — |
| `l10n_fr` | Native Community | Ya — **field `siret` dihapus**, konsolidasi ke `company_registry` | Breaking, lihat `02_DIFF_ANALYSIS.md` |
| `mail` | Native Community | Ya — **`fetchmail.server.fetch_mail()` signature berubah** | Breaking, lihat `02_DIFF_ANALYSIS.md` |

Dependency opsional yang dicek runtime (tidak terlihat di manifest):

- `res.country.department` (model) + `country_department_id` (field `res.partner`) — dicek via `self.env['ir.model'].search(...)` di `fr_business_directory/models/siret_wizard.py`. Sama seperti 17.0→18.0: **tidak ditemukan** di `native-source`/`native-target`, soft-dependency opsional ke addon eksternal (kemungkinan OCA `l10n_fr_department`) yang sengaja dibuat opsional. Dikonfirmasi dev: tidak perlu `third-party-*` di-connect, tetap dianggap opsional di 19.0 juga.

## 2b. Struktur & Fitur Modul (auto-scan)

Identik dengan hasil scan project 17.0→18.0 (kode tidak berubah struktur sejak itu) — dikonfirmasi ulang lewat pembacaan langsung kode `source-codebase` (branch `migration/18.0`):

### `fr_business_directory`

| Fitur | Ada? | Fase step 6 relevan |
|---|---|---|
| Controllers (route custom) | Tidak | N/A — D1 |
| Assets/CSS/JS custom | Tidak (`assets: {}` kosong, tidak ada `static/src/`) | N/A — D2, E, F |
| Komponen Owl/JavaScript custom | Tidak | N/A — E, F |
| Field JSON, relasi berantai (>2 level), dynamic model creation | Tidak (relasi terdalam 2 level: `siret.wizard.result` → `matching.etablissement`) | N/A — B2 |
| View pakai `attrs=`/`states=`/domain dinamis | Tidak (sudah pakai ekspresi inline `invisible="is_company != True"`, gaya 18.0-compatible) | N/A — C2 |

### `personal_email_usage`

| Fitur | Ada? | Fase step 6 relevan |
|---|---|---|
| Controllers (route custom) | Tidak | N/A — D1 |
| Assets/CSS/JS custom | Tidak | N/A — D2, E, F |
| Komponen Owl/JavaScript custom | Tidak | N/A — E, F |
| Field JSON, relasi berantai, dynamic model creation | Tidak | N/A — B2 |
| View pakai `attrs=`/`states=`/domain dinamis | Tidak (`views/mail_views.xml` cuma `xpath`+`field`) | N/A — C2 |

Semua kolom "Ada?" = Tidak untuk kedua addon → Fase D1/D2/E/F/B2/C2 langsung **N/A** di Applicability Check step 6.

## 3. Sifat Migrasi

- [x] Port kode saja (belum ada data produksi — instalasi baru di versi target)
- [ ] Upgrade instance

## 4. Baseline Spec / Characterization Test (gate)

- Modul punya `01b_BASELINE_SPEC.md` dari project migrasi sebelumnya (17.0→18.0)? **Ya** — `doc-dev/migration_17.0_18.0/doc/01_intake/01b_BASELINE_SPEC.md`, sudah tervalidasi penuh (16 klaim `[MATCH]`, 0 gap) terhadap kode `source-codebase` 17.0→18.0 saat itu.
- Proses: baca baseline 17.0→18.0 sebagai draft awal → cross-check tiap klaim (BSL-001..BSL-024) ke kode aktual `source-codebase` project INI (branch `migration/18.0`, hasil migrasi 17→18 yang sudah selesai) satu per satu → **semua klaim cocok**, KECUALI BSL-023 (`fetch_mail()` override) yang perlu update deskripsi teknis (signature sekarang `fetch_mail(self, raise_exception=True)`, bukan lagi polos — ini justru KONFIRMASI bahwa fix migrasi 17→18 sudah diterapkan dengan benar, behavior/intent tidak berubah).
- `01b_BASELINE_SPEC.md` (versi 18.0→19.0) sudah diisi — lihat file di folder yang sama.

### 4a. Dokumen Pelengkap Lain

- Ditanya eksplisit ke dev: selain kode `source-codebase`, apakah ada dokumen pelengkap lain?
- **Dikonfirmasi tidak ada** dokumen pelengkap lain di luar baseline spec yang sudah disebutkan.

## 4b. Source Masih Aktif Dikembangkan?

- [x] Tidak — source module dibekukan selama migrasi berjalan (dikonfirmasi dev)
- [ ] Ya

## 5. Scope Boundary

- **Yang harus tetap identik pasca migrasi:** seluruh business rule BSL-001..BSL-024 di `01b_BASELINE_SPEC.md`, termasuk bug pre-existing yang wajib dipertahankan (BSL-008 `_logger` tidak diimpor, BSL-009 parameter hilang di `fetch_previous_page`, BSL-020 re-fetch tanpa henti pada email skip, BSL-021 log "succeeded" salah hitung).
- **Yang WAJIB diubah demi kompatibilitas 19.0 (bukan perubahan scope, murni port teknis):**
  1. `personal_email_usage/models/mail.py` — sesuaikan override `fetch_mail()` dengan signature 19.0 (`fetch_mail(self)`, tanpa `raise_exception`).
  2. `fr_business_directory/models/siret_wizard.py` — ganti key `'siret'` menjadi `'company_registry'` di kedua `partner.write({...})` (`select_siret()` di `siret.wizard.result` dan `matching.etablissement`) — value/logic penulisan TIDAK berubah, cuma nama field target di `res.partner`.
- **Yang sengaja diubah/di-drop selain itu:** tidak ada.

## 6. Constraint

- Deadline: tidak ada deadline khusus (dikonfirmasi dev).
- Owner tiap step: single owner (dev sendiri) — dikonfirmasi dev.
