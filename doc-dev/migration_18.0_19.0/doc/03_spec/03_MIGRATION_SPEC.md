# Migration Spec (Teknis) — french_business_directory

**Step:** 3 — Migration Spec
**Versi:** 18.0 → 19.0
**Ref:** `02_diff/02_DIFF_ANALYSIS.md`
**Tanggal:** 2026-08-26

> Dokumen ini memandu IMPLEMENTASI (step 6). Dasar testing/acceptance criteria adalah `01b_BASELINE_SPEC.md` + kode 18.0 (lihat step 5), bukan dokumen ini.

---

## 1. Ringkasan Strategi

Migrasi ini adalah port kode mekanis hampir murni — **2 fix wajib** (signature `fetch_mail()`, rename field `siret`→`company_registry`), sisanya port 1:1 tanpa perubahan. Tidak ada OWL/JS custom, tidak ada controller, tidak ada asset custom, view sudah dalam sintaks `<list>`/ekspresi-inline yang kompatibel sejak migrasi 17→18 sebelumnya (lihat Applicability Check `01a_MIGRATION_INTAKE.md` §2b — semua fase D1/D2/E/F/B2/C2 N/A). Manifest `version` perlu diupdate dari `18.0.1.0.0` ke `19.0.1.0.0` di kedua addon.

## 2. Strategi per File/Simbol

| File/simbol | Ref `DIFF-NNN` | Strategi migrasi | Risiko | Ref `BSL-NNN` |
|---|---|---|---|---|
| `personal_email_usage/models/mail.py:61` (signature `fetch_mail`) | DIFF-01 | Ubah `def fetch_mail(self, raise_exception=True):` → `def fetch_mail(self):` | Rendah — fix mekanis, preseden identik dari migrasi 17→18 modul ini sendiri | BSL-023 |
| `personal_email_usage/models/mail.py:156` (pemanggilan `super()`) | DIFF-01 | Ubah `return super(FetchmailServer, self.filtered(lambda s: s.server_type != 'imap')).fetch_mail(raise_exception=raise_exception)` → hapus argumen `raise_exception=raise_exception`, jadi `.fetch_mail()` | Rendah | BSL-023 |
| `fr_business_directory/models/siret_wizard.py:260` (`siret.wizard.result.select_siret`, dalam blok `if`) | DIFF-02 | Ganti key `'siret': self.siret` → `'company_registry': self.siret` di dict `partner.write({...})` | Rendah — cuma rename key, value/logic sama | BSL-004, BSL-006 |
| `fr_business_directory/models/siret_wizard.py:260` (blok `else`, tanpa `country_department_id`) | DIFF-02 | Sama — ganti key `'siret'`→`'company_registry'` di cabang `else` juga (baris `~274-280`) | Rendah | BSL-004 |
| `fr_business_directory/models/siret_wizard.py:354` (`matching.etablissement.select_siret`, blok `if`) | DIFF-02 | Sama — ganti key `'siret'`→`'company_registry'` | Rendah | BSL-004, BSL-006 |
| `fr_business_directory/models/siret_wizard.py:354` (blok `else`) | DIFF-02 | Sama — ganti key `'siret'`→`'company_registry'` di cabang `else` juga (baris `~366-372`) | Rendah | BSL-004 |
| `fr_business_directory/__manifest__.py`, `personal_email_usage/__manifest__.py` | — (housekeeping wajib, bukan DIFF) | Update `'version': '18.0.1.0.0'` → `'19.0.1.0.0'` | Tidak ada | — |
| `fr_business_directory/tests/test_siret_wizard.py:130` (`test_select_result_overwrites_partner`) | DIFF-02 | Ganti assertion `self.assertEqual(self.partner.siret, ...)` → `self.assertEqual(self.partner.company_registry, ...)` (ditemukan Step 4 completeness review) | Rendah | BSL-004 |
| `personal_email_usage/tests/test_fetchmail.py:51-54` (`test_fetch_mail_accepts_raise_exception_kwarg`) | DIFF-01 | Tulis ulang jadi `test_fetch_mail_accepts_no_args` — panggil `fetch_mail()` TANPA argumen (cara cron 19.0 memanggil), bukan lagi `fetch_mail(raise_exception=False)` (ditemukan Step 4 completeness review) | Rendah | BSL-023 |
| Semua file lain (models/views/security tidak disebut di atas) | DIFF-03..DIFF-09 | Port apa adanya, tanpa perubahan — dikonfirmasi tidak ada breaking change | Tidak ada | — |

## 2b. Risk Analysis Terstruktur

### Critical Migration Blockers
*(Mencegah instalasi atau operasi inti di 19.0)*

| # | Isu | Lokasi | Rujukan knowledge base |
|---|---|---|---|
| 1 | Manifest version — harus `19.0.x` | `fr_business_directory/__manifest__.py`, `personal_email_usage/__manifest__.py` | — |
| 2 | `fetch_mail()` signature — cron akan `TypeError` kalau tidak diadaptasi | `personal_email_usage/models/mail.py:61,156` | `migration-tool/knowledge/version-diffs/18-to-19.md` §1a (setelah curation) |
| 3 | `res.partner.siret` tidak ada lagi — tombol "Select" akan gagal `write()` | `fr_business_directory/models/siret_wizard.py:260,354` | `migration-tool/knowledge/dependency-compat/l10n_fr/18-to-19.md` (setelah curation) |

**Priority:** HIGH — perbaiki sebelum runtime testing apapun (item 2 & 3 blocking fungsional, bukan cuma install).

### OWL Widget yang Butuh Rewrite/Review

N/A — tidak ada komponen Owl/JS custom di modul ini (dikonfirmasi `01a_MIGRATION_INTAKE.md` §2b).

### Controller & Route

N/A — tidak ada controller custom.

### Assets & Dependency

N/A — `assets: {}` kosong di kedua manifest, tidak ada `static/src/`.

### Kompatibilitas Data Model

| # | Isu | Lokasi | Priority | Ref `BSL-NNN` |
|---|---|---|---|---|
| 1 | Field target `write()` berubah nama (`siret`→`company_registry`) — bukan perubahan model CUSTOM modul ini, tapi target write ke model core | `siret_wizard.py:260,354` | HIGH | BSL-004, BSL-006 |

### Risiko Integrasi

| # | Isu | Lokasi | Priority |
|---|---|---|---|
| 1 | Soft-dependency opsional `res.country.department` — behavior sudah defensif, tidak ada risiko baru dari migrasi | `siret_wizard.py:254,346` | Rendah |

### Urutan Prioritas Testing

1. Install & startup — manifest version, dependency (`base`/`contacts`/`l10n_fr`/`mail`, semua tersedia 19.0)
2. Core user flow `fr_business_directory` — buka wizard dari form partner company, search SIRET, pilih hasil ("Select"), verifikasi `company_registry` (bukan lagi `siret`) terisi benar di partner
3. Core user flow `personal_email_usage` — fetch IMAP jalan tanpa `TypeError`, filter user-internal/non-kontak tetap berfungsi, `mark_read` tetap berfungsi
4. Persistensi data — `social_reason` tracking di chatter, `processed_message_ids` tersimpan
5. Bug pre-existing tetap identik (BSL-008, BSL-009, BSL-020, BSL-021) — verifikasi TIDAK diperbaiki tanpa sengaja

### View List (dulu Tree) Checklist

N/A — sudah `<list>` sejak migrasi 17→18, tidak ada `<tree>` tersisa di modul ini (dikonfirmasi grep).

### Estimasi Effort

| Area | Effort | Catatan |
|---|---|---|
| Fix DIFF-01 (`fetch_mail` signature) | Sangat kecil (2 baris) | Preseden identik sudah pernah dikerjakan di migrasi 17→18 |
| Fix DIFF-02 (`siret`→`company_registry`) | Kecil (4 baris, 2 file lokasi) | Cuma rename key dict |
| Manifest version bump | Trivial (2 baris) | — |
| Testing (Step 9/10) | Sedang | Perlu environment executable (Docker) untuk verifikasi runtime, terutama G1 install test dan flow "Select" |

## 3. Data Migration (ringkas)

**N/A — port kode saja, tidak ada data produksi** (dikonfirmasi intake §3). Catatan untuk masa depan kalau modul ini SUATU HARI upgrade instance dengan data produksi: kolom DB `siret` (kalau pernah tersimpan di deployment 18.0 manapun) TIDAK otomatis pindah ke `company_registry` — ini murni perubahan level KODE modul custom (target field `write()`), bukan migrasi kolom yang ditangani ORM core `l10n_fr` sendiri (beda dengan kasus `sale.order.line.tax_id`→`tax_ids` yang ditangani ORM core karena rename field terjadi DI DALAM modul `sale` itu sendiri). Kalau ada data produksi di masa depan, field `company_registry` partner yang sudah ada isinya (dari mekanisme core lain) TIDAK akan tertimpa oleh migrasi ini kecuali user menjalankan ulang wizard "Select".

## 4. Scope

### Termasuk
- Fix DIFF-01, DIFF-02 (wajib untuk kompatibilitas 19.0)
- Manifest version bump kedua addon
- Port seluruh kode lain apa adanya (tanpa perubahan)

### Di Luar Scope (sengaja, disetujui di intake)
- Tidak memperbaiki bug pre-existing (BSL-008, BSL-009, BSL-020, BSL-021)
- Tidak menyediakan `third-party-*` untuk `res.country.department` — tetap soft-dependency opsional
- Tidak ada Step 7 (Data Migration) — port kode saja
