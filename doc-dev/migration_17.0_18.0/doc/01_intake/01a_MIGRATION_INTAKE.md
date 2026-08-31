# Migration Intake — french_business_directory

**Step:** 1 — Intake & Scope
**Versi:** 17.0 → 18.0
**Tanggal:** 2026-08-24
**Status:** Draft — menunggu review user

---

## 0. Folder Referensi — Dikonfirmasi Dev

- `native-target` (Community 18.0): `D:\Kuncoro\doodex\repo\odoo18` — dikonfirmasi dev, terverifikasi `odoo/release.py` → `version_info = (18, 0, 0, FINAL, 0, '')`.
- `native-source` (Community 17.0): `D:\Kuncoro\doodex\repo\odoo17` — dikonfirmasi dev, terverifikasi `odoo/release.py` → `version_info = (17, 0, 0, FINAL, 0, '')`.
- `native-target-enterprise` (18.0): `D:\Kuncoro\doodex\repo\enterprise18` — dikonfirmasi dev.
- `native-source-enterprise` (17.0): `D:\Kuncoro\doodex\repo\enterprise17` — dikonfirmasi dev.
- `third-party-source` / `third-party-target`: **belum di-connect** — lihat §2 (auto-scan menemukan indikasi kuat dependency OCA `res.country.department`, dev belum konfirmasi path OCA repo yang di-checkout).

### 0a. Konfirmasi Branch/Versi

- `source-codebase` — folder BARU, di-clone dari `origin/staging/17.0`, branch lokal `migration/17.0_source` — dikonfirmasi dev, path `D:\Kuncoro\doodex\repo\french-business-directory-migration-18-source`.
- `target-codebase` — folder existing (utama), branch lokal `migration/18.0_target` dibuat dari `origin/staging/17.0` — dikonfirmasi dev, path `D:\Kuncoro\doodex\repo\french-business-directory-migration-18` (repo ini).
- Dikonfirmasi dev: dua folder di atas adalah dua clone fisik terpisah (bukan symlink/alias satu folder).
- Versi Odoo semantik: **17.0 → 18.0** — dikonfirmasi eksplisit oleh dev (bukan cuma disimpulkan dari nama folder/branch).

### 0b. Gate `.claude/settings.json`

`Environment eksekusi = Claude Code CLI`, `cli-config` sudah di-bootstrap (`.claude/settings.json` sudah ada). Placeholder path diisi/dihapus sebagai berikut:

- `ABS_PATH_SOURCE_CODEBASE` → `D:\Kuncoro\doodex\repo\french-business-directory-migration-18-source`
- `ABS_PATH_MIGRATION_TOOL` → `D:\Kuncoro\doodex\repo\migration-tool-project\migration-tool`
- `ABS_PATH_NATIVE_TARGET_ENTERPRISE` → `D:\Kuncoro\doodex\repo\enterprise18` (dipakai, dev konfirmasi)
- `ABS_PATH_NATIVE_SOURCE_ENTERPRISE` → `D:\Kuncoro\doodex\repo\enterprise17` (dipakai, dev konfirmasi)
- `ABS_PATH_THIRD_PARTY_SOURCE` / `ABS_PATH_THIRD_PARTY_TARGET` → **belum diisi**, menunggu konfirmasi path OCA repo (lihat §2) — baris deny terkait belum bisa diaktifkan sampai path diketahui.

> Catatan: field ini akan disinkronkan ke `.claude/settings.json` sungguhan setelah path OCA dikonfirmasi (lihat "Ringkasan untuk Review" poin 1).

---

## Ringkasan untuk Review — Perlu Konfirmasi User

1. **Dependency OCA belum di-connect** — dua wizard di `fr_business_directory` (`siret.wizard.result.select_siret`, `matching.etablissement.select_siret`) menulis field `country_department_id` ke `res.partner` dan membaca model `res.country.department`, keduanya **tidak ada** di `native-source`/`native-target` Community maupun `native-source-enterprise` (dicek langsung, tidak ketemu). Ini soft-dependency ke addon eksternal (kemungkinan besar OCA `l10n_fr_department` dari repo `OCA/l10n-france`) yang sengaja dibuat opsional lewat cek `self.env['ir.model'].search(...)` sebelum dipakai — kalau addon itu tidak terinstall, field-field itu memang tidak pernah diisi (bukan error, sudah diverifikasi dari kode). **Perlu dev konfirmasi:** apakah addon OCA ini terinstall di environment produksi 17.0 sekarang, dan apakah perlu ikut disediakan (`third-party-source`/`third-party-target`) untuk pengujian migrasi — atau cukup dianggap tetap opsional di 18.0 juga.
2. **Reuse spec lama dikonfirmasi** — `01b_BASELINE_SPEC.md` disusun dari `doc-dev/backfill/spec/*/01A_FUNCTIONAL_SPEC.md` (functional spec + acceptance criteria hasil backfill 2026-08-07, awalnya dari `french-business-directory-17` — sekarang disalin ke dalam repo ini, lihat catatan §4), di-cross-check baris-per-baris ke kode aktual di `source-codebase` (`origin/staging/17.0`) — semua klaim **cocok** (`[MATCH]`), tidak ada penyimpangan ditemukan antara `staging/17.0` dan `17.0` yang dipakai backfill.
3. **Dua bug pre-existing di 17.0 yang WAJIB dipertahankan (bukan diperbaiki)** di 18.0, sudah tercatat sebagai temuan backfill lama: (a) `personal_email_usage` — email dari user internal/non-kontak di-fetch ulang selamanya tiap cron kalau `mark_read=False` (default) karena `processed_message_ids` tidak diisi di jalur skip; (b) log ringkasan "succeeded" salah hitung. Lihat BSL-020, BSL-021 di `01b_BASELINE_SPEC.md`.
4. **Tidak ada dependency Enterprise** — dikonfirmasi dari `__manifest__.py` kedua addon (`base`/`contacts`/`l10n_fr`/`mail` saja) DAN dari scan `native-source-enterprise`/`native-target-enterprise` (model/field yang dipakai modul tidak ditemukan di source Enterprise) — `native-target-enterprise` tetap sudah di-connect sesuai kebijakan "selalu tanya", tapi tidak ada temuan yang membutuhkannya secara aktif di step 2.
5. Tidak ada dokumen pelengkap LAIN selain spec backfill di atas (PRD/Excel/Confluence/vendor) — dikonfirmasi dev.
6. Deadline: tidak ada deadline khusus (default, dikonfirmasi dev secara implisit — belum ada yang disebutkan).
7. Owner tiap step: single owner (dev sendiri) — default, belum ada pembagian role disebutkan.

---

## 1. Modul & Scope

- **Modul yang dimigrasi:** `french_business_directory` (repo) — berisi DUA addon independen:
  - `fr_business_directory` — quick-search SIRET/SIREN via API gouv.fr, isi field partner Perancis
  - `personal_email_usage` — kontrol lanjutan fetch email IMAP (`fetchmail.server`)
- Kedua addon **genuinely tidak berhubungan secara fungsional** (produk berbeda, kebetulan di-bundle di repo yang sama) — tidak ada `depends` silang satu ke yang lain, tidak ada referensi model/field lintas addon.

## 2. Dependency Map (auto-scan)

| Dependency | Tipe | Versi tersedia di target? | Catatan |
|---|---|---|---|
| `base` | Native Community | Ya (18.0) | — |
| `contacts` | Native Community | Ya (18.0) | — |
| `l10n_fr` | Native Community | Ya (18.0) — perlu dicek detail field `siret` di step 2 diff | menyediakan field `siret` di `res.partner` |
| `mail` | Native Community | Ya (18.0) | `fetchmail.server`, `mail.thread` |

Dependency opsional yang dicek runtime (tidak terlihat di manifest):

- `res.country.department` (model) + `country_department_id` (field `res.partner`) — dicek via `self.env['ir.model'].search([('model','=','res.country.department')])` sebelum dipakai di `fr_business_directory/models/siret_wizard.py` (`select_siret` di `siret.wizard.result` dan `matching.etablissement`). **Tidak ditemukan** di `native-source`/`native-target` Community maupun `native-source-enterprise` — kemungkinan besar OCA (`l10n_fr_department`). Belum ada `third-party-source`/`third-party-target` di-connect — lihat "Ringkasan untuk Review" poin 1.

## 2b. Struktur & Fitur Modul (auto-scan)

### `fr_business_directory`

| Fitur | Ada? | Lokasi/bukti | Fase step 6 relevan |
|---|---|---|---|
| Controllers (route custom) | Tidak | — | N/A — D1 |
| Assets/CSS/JS custom | Tidak | `assets: {}` kosong di manifest, tidak ada `static/src/` | N/A — D2, E, F |
| Komponen Owl/JavaScript custom | Tidak | tidak ada file `.js` | N/A — E, F |
| Field JSON, relasi berantai (>2 level), dynamic model creation | Tidak | semua `self.env[...]` pakai string literal; relasi terdalam `siret.wizard.result` → `matching.etablissement` (2 level) | N/A — B2 |
| View pakai `attrs=`/`states=`/`domain=`/`context=` dinamis | Tidak | grep XML tidak menemukan pola ini — view sudah pakai sintaks atribut langsung (`invisible="is_company != True"`), gaya 17.0 yang sudah kompatibel 18.0 | N/A — C2 |

### `personal_email_usage`

| Fitur | Ada? | Lokasi/bukti | Fase step 6 relevan |
|---|---|---|---|
| Controllers (route custom) | Tidak | — | N/A — D1 |
| Assets/CSS/JS custom | Tidak | tidak ada `static/src/`, tidak ada key `assets` di manifest | N/A — D2, E, F |
| Komponen Owl/JavaScript custom | Tidak | tidak ada file `.js` | N/A — E, F |
| Field JSON, relasi berantai (>2 level), dynamic model creation | Tidak | tidak ditemukan | N/A — B2 |
| View pakai `attrs=`/`states=`/`domain=`/`context=` dinamis | Tidak | `views/mail_views.xml` cuma `xpath`+`field` sederhana | N/A — C2 |

Semua kolom "Ada?" = Tidak untuk kedua addon → Fase D1/D2/E/F/B2/C2 langsung dinyatakan **N/A** di Applicability Check step 6, tanpa perlu dikerjakan satu-satu.

## 3. Sifat Migrasi

- [x] Port kode saja (belum ada data produksi — instalasi baru di versi target)
- [ ] Upgrade instance

## 4. Baseline Spec / Characterization Test (gate)

- Modul punya `FUNCTIONAL_SPEC.md` lama? **Ya** — hasil backfill 2026-08-07, disalin ke `doc-dev/backfill/spec/{fr_business_directory,personal_email_usage}/01A_FUNCTIONAL_SPEC.md` (+ `01B_ACCEPTANCE_CRITERIA.md`) di repo ini (2026-08-31 — awalnya dirujuk eksternal dari folder terpisah `french-business-directory-17`, dipindahkan supaya repo ini self-contained, tidak bergantung path eksternal di disk dev; remote `french-business-directory-17` tidak related secara git ke repo ini). Dev eksplisit setuju dipakai sebagai dasar.
- Proses: baca spec lama → cross-check tiap klaim (BR-01..BR-08 tiap addon) ke kode aktual di `source-codebase` (`origin/staging/17.0`) satu per satu → **semua klaim cocok**, tidak ada penyimpangan (spec backfill dibuat dari branch `17.0`, source-codebase project ini dari `staging/17.0` — isi kode identik untuk kedua addon berdasarkan pembacaan langsung).
- `01b_BASELINE_SPEC.md` sudah diisi — lihat file di folder yang sama.

### 4a. Dokumen Pelengkap Lain

- Ditanya eksplisit ke dev: selain kode `source-codebase` dan spec backfill di atas, apakah ada dokumen pelengkap lain (PRD, Excel/Notion/Confluence, vendor docs)?
- **Dikonfirmasi tidak ada** dokumen pelengkap lain di luar yang sudah disebutkan.

## 4b. Source Masih Aktif Dikembangkan?

- [x] Tidak — source module dibekukan selama migrasi berjalan
- [ ] Ya

## 5. Scope Boundary

- **Yang harus tetap identik pasca migrasi:** seluruh business rule BR-01..BR-08 (`fr_business_directory`) dan BR-01..BR-08 (`personal_email_usage`) di `01b_BASELINE_SPEC.md`, termasuk dua bug pre-existing yang wajib dipertahankan (re-fetch tanpa henti pada email skip, log "succeeded" salah hitung).
- **Yang sengaja diubah/di-drop:** tidak ada — port kode saja, tidak ada perubahan scope yang disepakati di intake ini.

## 6. Constraint

- Deadline: tidak ada deadline khusus.
- Owner tiap step: single owner (dev sendiri).
