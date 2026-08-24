# Migration Spec (Teknis) — french_business_directory

**Step:** 3 — Migration Spec
**Versi:** 17.0 → 18.0
**Ref:** `02_diff/02_DIFF_ANALYSIS.md`
**Tanggal:** 2026-08-24

> Dokumen ini memandu IMPLEMENTASI (step 6). Dasar testing/acceptance criteria tetap `01b_BASELINE_SPEC.md` (step 1) — bukan dokumen ini.

---

## 1. Ringkasan Strategi

Sebagian besar modul (kedua addon: `fr_business_directory`, `personal_email_usage`) di-port **1:1 tanpa perubahan** — tidak ada Owl/JS, controller, asset custom, atau view dinamis (`attrs`/`states`/`domain`/`context`) yang kena breaking change (dikonfirmasi `01a_MIGRATION_INTAKE.md` §2b). Dua titik butuh perubahan wajib demi kompatibilitas teknis (bukan perubahan business logic):

1. **DIFF-01** — `fr_business_directory/views/siret_wizard_views.xml`: ganti `<tree>`→`<list>` (2 tempat) + `mode="tree"`→`mode="list"` (1 tempat). Mekanis murni, install-blocking kalau tidak dikerjakan.
2. **DIFF-02** — `personal_email_usage/models/mail.py`: update signature override `fetch_mail(self)` → `fetch_mail(self, raise_exception=True)`, teruskan parameter ke `super()` call (path non-IMAP). Behavior internal path IMAP (log-only) dipertahankan identik.

Sisanya (manifest version bump, security ACL, skeleton) adalah langkah standar tiap migrasi, tanpa risiko spesifik modul ini.

## 2. Strategi per File/Simbol

| File/simbol | Ref `DIFF-NNN` | Strategi migrasi | Risiko | Ref `BSL-NNN` |
|---|---|---|---|---|
| `fr_business_directory/__manifest__.py` | — | Version bump `17.0.1.0.0` → `18.0.1.0.0` | Rendah | — |
| `personal_email_usage/__manifest__.py` | — | Version bump `17.0.1.0.0` → `18.0.1.0.0` | Rendah | — |
| `fr_business_directory/views/siret_wizard_views.xml` | DIFF-01 | `<tree string="Results" delete="False" create="false">` → `<list string="Results" delete="False" create="false">`; `mode="tree"` (pada `<field name="result_ids">`) → `mode="list"`; `<tree create="false" delete="false" editable="bottom" no_open="1">` → `<list create="false" delete="false" editable="bottom" no_open="1">` | **Tinggi (install-blocking kalau terlewat)** — mekanis, tidak ada perubahan field/logic | BSL-003, BSL-004 |
| `personal_email_usage/models/mail.py:6` — `from odoo.tools import logging` | DIFF-09 (ditemukan G1 dry run, Step 6) | Ganti `import logging` (stdlib langsung) — `odoo.tools.logging` bukan API resmi, cuma leak wildcard import yang ditutup di 18.0 (`misc.py` menambahkan `__all__`) | **Tinggi (install-blocking, dikonfirmasi nyata via G1)** | — |
| `personal_email_usage/models/mail.py` — `fetch_mail()` | DIFF-02 | Ubah signature jadi `def fetch_mail(self, raise_exception=True):`. Di baris terakhir (delegasi non-IMAP), ubah `super(FetchmailServer, self.filtered(...)).fetch_mail()` → `.fetch_mail(raise_exception=raise_exception)`. Path IMAP (di-override total) TIDAK diubah logic-nya — parameter `raise_exception` diterima tapi tidak dipakai untuk mengubah exception handling internal (tetap log-only, sesuai BSL-020/MF-05 yang sudah dikonfirmasi dipertahankan) | **Tinggi (functional-blocking di cron kalau terlewat)** | BSL-015, BSL-020 |
| `fr_business_directory/views/partner.xml` | DIFF-04 | Copy 1:1, tidak ada perubahan | Rendah | BSL-001 |
| `fr_business_directory/models/partner.py`, `models/siret_wizard.py` (selain fetch_mail) | DIFF-06, DIFF-07 | Copy 1:1 — tidak ada API Python yang dipakai modul ini yang berubah 17→18 (tidak ada `user_has_groups`, `_check_recursion`, `_name_search`, `create()` override, `search()` override) | Rendah | BSL-002, BSL-005 s/d BSL-014 |
| `personal_email_usage/models/mail.py` — `message_new()` | — | Copy 1:1 — `mail.thread.message_new()` tidak berubah signature 17→18 (dikonfirmasi tidak ada entry breaking-change terkait di knowledge base, dan pemakaian `tools.email_split`/`msg_dict` standar) | Rendah | BSL-019 |
| `security/ir.model.access.csv` (kedua addon) | — | Copy 1:1 — ACL wizard `fr_business_directory` (3 baris, `siret.wizard`/`siret.wizard.result`/`matching.etablissement`) sudah lengkap sejak 17.0, tidak perlu ACL baru. `personal_email_usage` ACL file tetap dibawa apa adanya sebagai dead file (dikomentari di manifest, lihat BSL-022) — TIDAK dihapus (P1 Full Module Fidelity) | Rendah | BSL-022 |
| `fr_business_directory/views/menu_item.xml` | — | Copy 1:1 — `<menuitem>` polos, tidak ada elemen yang terpengaruh perubahan 17→18 | Rendah | BSL-001 |
| `fr_business_directory/i18n/fr.po` | — | Copy 1:1 — file terjemahan, tidak ada string/label yang berubah di source (tidak ada rename field/view) | Rendah | — |
| `*/static/description/*`, `*/googleaeed8a7b9ec156e7.html`, `LICENSE`, `README.md` (kedua addon) | — | Copy 1:1 apa adanya (P1 Full Module Fidelity) — non-fungsional, tidak dibaca runtime Odoo | Rendah | BSL-012, BSL-024 |

## 2b. Risk Analysis Terstruktur

### Critical Migration Blockers
*(Mencegah instalasi atau operasi inti di 18.0)*

| # | Isu | Lokasi | Rujukan knowledge base |
|---|---|---|---|
| 1 | Manifest version harus `18.0.x.x.x` | `fr_business_directory/__manifest__.py`, `personal_email_usage/__manifest__.py` | `knowledge/version-diffs/17-to-18.md` |
| 2 | `<tree>`→`<list>` (DIFF-01) | `fr_business_directory/views/siret_wizard_views.xml:25,26,51` | `knowledge/version-diffs/17-to-18.md` §1 (PR `odoo/odoo#159909`) |

**Priority:** HIGH — perbaiki sebelum runtime testing apapun.

### Runtime/Functional Blockers (bukan install-blocking, tapi memutus fungsi inti)

| # | Isu | Lokasi | Priority |
|---|---|---|---|
| 1 | Signature `fetch_mail(raise_exception=True)` (DIFF-02) — tanpa fix, cron `_fetch_mails()` `TypeError` untuk SEMUA server | `personal_email_usage/models/mail.py:61` | **Tinggi** — modul tidak bisa fetch email sama sekali via cron di 18.0 tanpa ini |

### OWL Widget yang Butuh Rewrite/Review

Tidak ada — modul ini tidak punya komponen Owl/JS custom (dikonfirmasi `01a_MIGRATION_INTAKE.md` §2b, kedua addon).

### Controller & Route

Tidak ada — tidak ada `controllers/` di kedua addon.

### Assets & Dependency

Tidak ada asset custom (`assets: {}` kosong di `fr_business_directory`, tidak ada key `assets` di `personal_email_usage`). Dependency (`base`/`contacts`/`l10n_fr`/`mail`) semua stabil 17→18 (lihat `02_DIFF_ANALYSIS.md` §1).

### Kompatibilitas Data Model

| # | Isu | Lokasi | Priority | Ref `BSL-NNN` |
|---|---|---|---|---|
| 1 | `country_department_id`/`res.country.department` — soft-dependency eksternal, tidak ditemukan di native manapun (17/18, Community/Enterprise) | `fr_business_directory/models/siret_wizard.py:254-267,346-364` | Rendah (kode sudah defensif, tidak crash) | BSL-006 |

### Risiko Integrasi

Tidak ada — modul tidak berintegrasi dengan sistem eksternal selain API publik `recherche-entreprises.api.gouv.fr` (HTTP biasa via `requests`, tidak terpengaruh perubahan versi Odoo).

### Urutan Prioritas Testing

1. Install & startup — manifest version, `<tree>`→`<list>` (DIFF-01), ACL wizard
2. Core user flow — buka form partner company → klik "Business Directory" → wizard fetch hasil → paginasi → Select → data ter-write ke partner (BSL-001 s/d BSL-006)
3. Cron `fetch_mail()` — jalankan manual/cron, pastikan tidak `TypeError` (DIFF-02), pastikan filter user-internal/non-kontak tetap jalan (BSL-015 s/d BSL-019)
4. Persistensi data — `social_reason`, `mark_read`, `processed_message_ids` tersimpan benar
5. Widget backend (Owl) — N/A, tidak ada

### View List (dulu Tree) Checklist

| # | Apa | Di mana | Perubahan |
|---|---|---|---|
| 1 | Inline tree di form (`siret.wizard.result_ids`) | `fr_business_directory/views/siret_wizard_views.xml:25-26` | `mode="tree"`→`mode="list"`, `<tree>`→`<list>` |
| 2 | Inline tree di form (`matching_etablissements`) | `fr_business_directory/views/siret_wizard_views.xml:51` | `<tree>`→`<list>` |
| 3 | Standalone list view / `view_mode` action | — | N/A — tidak ada `ir.actions.act_window` dengan `view_mode` eksplisit di kedua addon |

### Estimasi Effort

| Area | Effort | Catatan |
|---|---|---|
| Fase A (fondasi/install) | Sangat rendah | Manifest bump + 3 tag `<tree>`→`<list>` + ACL sudah lengkap |
| Fase A5 (Python API compat) | Rendah | 1 signature fix (`fetch_mail`) |
| Fase B (Python models) | Sangat rendah | Copy 1:1, tidak ada perubahan API yang relevan |
| Fase C (XML views) | Sangat rendah | Copy 1:1 setelah A2, tidak ada `attrs`/dynamic lain |
| Fase D/E/F | **N/A** | Tidak ada controller/asset/Owl |
| Fase G1/G2 | Rendah | Modul kecil, 2 addon, alur test singkat |

## 3. Data Migration (ringkas)

N/A — sifat migrasi ini **port kode saja** (tidak ada data produksi, `01a_MIGRATION_INTAKE.md` §3). Tidak ada field/model yang berubah struktur data antara 17.0 dan 18.0 untuk kedua addon.

## 4. Scope

### Termasuk
- Port penuh `fr_business_directory` (models, views, security, i18n) dan `personal_email_usage` (models, views, security) ke 18.0
- Fix DIFF-01 (`<tree>`→`<list>`) dan DIFF-02 (`fetch_mail` signature) — kompatibilitas wajib
- Preservasi identik semua bug pre-existing yang sudah dikonfirmasi di `FINDINGS.md` (MF-02, MF-03, MF-04, MF-05, MF-06)

### Di Luar Scope (sengaja, disetujui di intake)
- Perbaikan bug pre-existing (MF-02/03/04/05/06) — TIDAK diperbaiki di migrasi ini
- Koneksi `third-party-source`/`target` untuk OCA `res.country.department` — ditunda (MF-01)
- Data migration — N/A, port kode saja
