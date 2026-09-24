# Migration Spec (Teknis) — french_business_directory

**Step:** 3 — Migration Spec
**Versi:** 19.0 → 20.0
**Ref:** `02_diff/02_DIFF_ANALYSIS.md`, `FINDINGS.md`
**Tanggal:** 2026-09-24
**Status:** ✅ Selesai

> Memandu IMPLEMENTASI (Step 6). Dasar testing/AC tetap `01b_BASELINE_SPEC.md` + kode 19.0.

---

## 1. Ringkasan Strategi

Port mekanis untuk sebagian besar file (tidak ada JS/controller/report). Empat titik adaptasi wajib, semuanya install- atau fitur-blocking di 20.0:
1. **ACL** — konversi `ir.model.access.csv` → `security/ir.access.csv` mengikuti output konverter native (DIFF-01/MF-01).
2. **Target SIRET** — `company_registry` → `additional_identifiers['FR_SIRET']` di KEDUA `select_siret()`, dalam `write()` yang sama (DIFF-02/MF-02).
3. **View partner** — xpath baru ke field `name` tunggal 20.0, pertahankan field nama native via `$0`, tombol tetap `invisible="is_company != True"` (DIFF-03/MF-03).
4. **Import** — hapus `from odoo.osv import expression` (DIFF-04/MF-04).
Plus bump versi manifest (DIFF-08) dan penyesuaian test (DIFF-07/MF-06). Override `fetchmail`/`mail.thread` TIDAK disentuh (DIFF-06 stabil). Semua bug pre-existing dipertahankan.

## 2. Strategi per File/Simbol

| File/simbol | Ref DIFF | Strategi migrasi | Risiko | Ref BSL |
|---|---|---|---|---|
| `fr_business_directory/__manifest__.py` | DIFF-01, DIFF-08 | `version` → `20.0.1.0.0`; `data`: `security/ir.model.access.csv` → `security/ir.access.csv` (posisi pertama tetap). Key lain tidak disentuh. | Rendah | — |
| `fr_business_directory/security/ir.model.access.csv` → `ir.access.csv` | DIFF-01 | File baru: header `id,name,model_id,group_id/id,operation,domain`; baris: `access_siret_wizard,siret_wizard,siret.wizard,base.group_user,crud,` + 2 baris analog (`siret.wizard.result`, `matching.etablissement`). xmlid & name dipertahankan. File lama dihapus (`git rm`). | Rendah | Bagian A §2 |
| `fr_business_directory/models/siret_wizard.py` `SiretWizardResult.select_siret` + `MatchingEtablissement.select_siret` | DIFF-02 | Di tiap `partner.write({...})` (4 cabang: result×{dept ada, dept tidak}, etablissement×{dept ada, dept tidak}) ganti `'company_registry': self.siret` dengan `'additional_identifiers': <dict>`; dict dibangun helper modul-level baru `_fr_siret_identifiers(partner, siret)`: salin `partner.additional_identifiers or {}`, `pop('FR_SIRET')`, `pop('FR_SIREN')`, lalu set `FR_SIRET = siret` kalau truthy. Posisi key di dict write & field lain TIDAK berubah. Validasi/deduksi native berjalan otomatis di `write()`. | Sedang (deviasi edge-case MF-02 terdokumentasi) | BSL-004, BSL-006 |
| `fr_business_directory/views/partner.xml` | DIFF-03 | `<xpath expr="//h1/field[@name='name']" position="replace">` → `<div style="display: flex; align-items: center;white-space:nowrap">$0<button name="siret_wizard" ... invisible="is_company != True"/></div>`. Atribut tombol identik 19.0. `record`/`inherit_id`/`mode`/`priority` sama. Div tanpa `invisible` (MF-03: nama wajib tetap tampil untuk individu). | Sedang (semantik `is_company` — verifikasi Step 9/10) | BSL-001, BSL-025 |
| `fr_business_directory/models/partner.py`, `views/siret_wizard_views.xml`, `views/menu_item.xml`, `i18n/fr.po`, `static/**` | DIFF-10, DIFF-11 | Tidak diubah. | Rendah | BSL-001..014 |
| `personal_email_usage/__manifest__.py` | DIFF-08 | `version` → `20.0.1.0.0`. Baris `# 'security/ir.model.access.csv'` yang dikomentari dibiarkan. | Rendah | BSL-022 |
| `personal_email_usage/models/mail.py:11` | DIFF-04 | Hapus SATU baris `from odoo.osv import expression`. Import lain & seluruh `_fetch_mail`/`message_new` tidak disentuh. | Rendah | BSL-026 |
| `personal_email_usage/security/ir.model.access.csv` | DIFF-01 | Tidak diubah (dead file, tidak dimuat). | Rendah | BSL-022 |
| `fr_business_directory/tests/test_siret_wizard.py` | DIFF-07 | `test_select_result_overwrites_partner`: assert `_get_additional_identifier('FR_SIRET')`; data `_siege()['siret']` diganti SIRET valid Luhn HANYA kalau G1 membuktikan yang lama ditolak (docstring diperbarui). Test baru (Fase G2): MF-02 (SIRET tak valid → `ValidationError`; `FR_SIREN` terdeduksi; identifier lain tidak disentuh; select etablissement menulis `FR_SIRET`), MF-01 (ACL `ir.access` ada untuk 3 model, `crud`, `base.group_user`), MF-03 (arch view gabungan punya tombol + field nama; `Form` partner baru via context Contacts → nilai `is_company`). | Sedang | BSL-001, 004, 025 |
| `personal_email_usage/tests/test_fetchmail.py` | DIFF-06 | Tidak diubah (API stabil). | Rendah | BSL-015..023 |
| `docker-env/` | — | Instansiasi ulang untuk 20.0: build from source (`odoo20` mount read-only), Postgres 16, port unik 8196, `--http-interface=0.0.0.0`, `--without-demo=all`, `-i fr_business_directory,personal_email_usage --test-enable --test-tags=/fr_business_directory,/personal_email_usage`. Dockerfile+requirements disalin dari `advanced-sales-analysis-migration-20/docker-env` (layer cache sama, sudah terbukti jalan). | Rendah | — |

## 2b. Risk Analysis Terstruktur

### Critical Migration Blockers

| # | Isu | Lokasi | Rujukan |
|---|---|---|---|
| 1 | Manifest version harus `20.0.x` | kedua `__manifest__.py` | DIFF-08 |
| 2 | `ir.model.access` tidak ada | `fr_business_directory/security/` | DIFF-01, `19-to-20.md` |
| 3 | xpath `field[@id='company']` tidak ketemu | `fr_business_directory/views/partner.xml` | DIFF-03 |
| 4 | `odoo.osv` ImportError | `personal_email_usage/models/mail.py:11` | DIFF-04 |
| 5 | `company_registry` tidak ada (runtime, saat "Select") | `siret_wizard.py:260,275,354,369` | DIFF-02 |

**Priority:** HIGH — semua sebelum G1.

### OWL Widget / Controller & Route / Assets
N/A — tidak ada JS, controller, maupun assets (01a §2b).

### Kompatibilitas Data Model

| # | Isu | Lokasi | Priority | Ref BSL |
|---|---|---|---|---|
| 1 | SIRET disimpan di JSON tervalidasi, bukan Char bebas | `select_siret` ×2 | High | BSL-004 |
| 2 | `is_company` computed (bukan input user) | `partner.xml` visibilitas tombol | High (verifikasi) | BSL-001, BSL-025 |

### Risiko Integrasi

| # | Isu | Lokasi | Priority |
|---|---|---|---|
| 1 | Cron fetchmail tetap memanggil override (riwayat silent regression MF-03 18→19) | `mail.py _fetch_mail` | Medium — dikunci test existing + G1 |
| 2 | API gouv.fr live (tidak dimock) hanya di Step 10 | `siret_wizard.py` | Low (di luar kendali modul) |

### Urutan Prioritas Testing

1. Install & startup kedua addon bersamaan (G1) — manifest, ACL `ir.access`, view inherit, import.
2. Flow inti `fr_business_directory`: buka wizard → hasil → Select → partner terisi (`FR_SIRET`).
3. Fetchmail override via `_fetch_mail` (15 test existing).
4. Semantik `is_company`/visibilitas tombol (`Form`).
5. Regresi bug yang dipertahankan (PRESERVE-BUG tests).

### View List (dulu Tree) Checklist
Sudah `<list>` sejak 17→18 — tidak ada perubahan.

## 3. Data Migration

Tidak ada — port kode saja (Step 7 N/A). Catatan untuk kalau suatu saat jadi upgrade instance: konversi `company_registry` → `additional_identifiers` ditangani script upgrade native Odoo, bukan modul ini.

## 4. Scope

### Termasuk
- Semua kode kedua addon, test, `docker-env/`.

### Di Luar Scope (disetujui di intake)
- Aset store branch rilis `19.0` (MF-07).
- Perbaikan bug pre-existing (BSL-008/009/010/011/020/021) dan deprecation `_cr`/`_context` (MF-05).
- Perubahan business rule visibilitas tombol (MF-03 opsi `invisible="parent_id"`) — hanya kalau dev memutuskan.
