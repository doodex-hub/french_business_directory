# Spec Completeness Review — french_business_directory

**Step:** 4 — Spec Completeness Review (gate)
**Ref:** `03_spec/03_MIGRATION_SPEC.md`, source module 19.0 (`git ls-tree -r migration/19.0`), `FINDINGS.md`
**Tanggal:** 2026-09-24
**Status:** ✔️ Lulus gate

> Enumerasi = SEMUA file di `migration/19.0` di bawah kedua addon (`git ls-tree -r --name-only migration/19.0`), bukan hanya file yang "kelihatan relevan". `static/description/**` dikelompokkan (aset store, non-fungsional).

---

## Tabel Cakupan

### `fr_business_directory`

| Elemen source module | Ada di Migration Spec? | Status | Catatan |
|---|---|---|---|
| `__manifest__.py` | §2 baris manifest | ✅ Covered | version + entri ACL (DIFF-01/08) |
| `__init__.py`, `models/__init__.py` | §2 "tidak diubah" (implisit, import standar) | ✅ Covered | Tidak ada simbol versi-spesifik |
| `models/partner.py` | §2 "tidak diubah" | ✅ Covered | `social_reason`, `siret_wizard()` stabil (DIFF-10, kolisi nama 0) |
| `models/siret_wizard.py` — `SiretWizard` (default_get, `_fetch_siret_data`, fetch_next/prev) | §2 baris `siret_wizard.py` (hanya `select_siret` diubah) | ✅ Covered | `default_get(self, fields)` stabil (02 §0e); bug BSL-008..011 dipertahankan |
| `models/siret_wizard.py` — `SiretWizardResult.select_siret` | §2 | ✅ Covered | DIFF-02 (2 cabang) |
| `models/siret_wizard.py` — `MatchingEtablissement.select_siret`, computes, `_split_address` | §2 | ✅ Covered | DIFF-02 (2 cabang); compute tidak berubah |
| `security/ir.model.access.csv` | §2 | ✅ Covered | → `security/ir.access.csv` (DIFF-01) |
| `views/partner.xml` | §2 | ✅ Covered | DIFF-03 |
| `views/siret_wizard_views.xml` | §2 "tidak diubah" | ✅ Covered | `<list>`, `badge`, `confirm`, `special=cancel` stabil (DIFF-11) |
| `views/menu_item.xml` | §2 "tidak diubah" | ✅ Covered | `web_icon` stabil |
| `i18n/fr.po` | §2 "tidak diubah" | ✅ Covered | Hanya label field wizard (`Siret`, dst) — tidak merujuk `company_registry`; header "Odoo Server 17.0+e" dibiarkan (housekeeping) |
| `tests/__init__.py`, `tests/test_siret_wizard.py` | §2 baris test | ✅ Covered | DIFF-07/MF-06 |
| `README.md`, `LICENSE`, `googleaeed8a7b9ec156e7.html` (BSL-012) | §4 implisit (housekeeping dibawa apa adanya) | ✅ Covered | Tidak dimuat Odoo |
| `static/description/**` (banner, icon, index.html, screenshots) | §4 Di Luar Scope (MF-07) | ✅ Covered | Dibawa apa adanya dari `migration/19.0`; aset store 19.0 rilis tidak di-port |
| `controllers/`, `data/`, `report/`, `wizard/` folder | — | N/A | Tidak ada di modul (wizard ada di `models/`) |

### `personal_email_usage`

| Elemen source module | Ada di Migration Spec? | Status | Catatan |
|---|---|---|---|
| `__manifest__.py` | §2 | ✅ Covered | version (DIFF-08) |
| `__init__.py`, `models/__init__.py` | implisit | ✅ Covered | — |
| `models/mail.py` — imports | §2 | ✅ Covered | hapus `odoo.osv` (DIFF-04); import lain dibiarkan (masih ada di 20.0) |
| `models/mail.py` — `MailThread.message_new` | §2 "tidak disentuh" | ✅ Covered | Stabil (02 §0e, body identik 19↔20) |
| `models/mail.py` — `FetchmailServer` fields + `_fetch_mail` | §2 "tidak disentuh" | ✅ Covered | DIFF-06 stabil; `_cr` deprecated (DIFF-05/MF-05) |
| `security/ir.model.access.csv` (dead) | §2 | ✅ Covered | Tidak diubah (BSL-022) |
| `views/mail_views.xml` | §2 implisit + 02 §0e | ✅ Covered | xpath `attach` stabil |
| `tests/__init__.py`, `tests/test_fetchmail.py` | §2 | ✅ Covered | Tidak diubah |
| `README.md`, `LISEZMOI.md`, `LICENSE`, `googleaeed8a7b9ec156e7.html`, `static/description/**` | §4 | ✅ Covered | Housekeeping/aset store |

### Repo-level

| Elemen | Ada di Migration Spec? | Status | Catatan |
|---|---|---|---|
| `docker-env/docker-compose.yml` | §2 baris `docker-env/` | ✅ Covered | Diinstansiasi ulang untuk 20.0 (+ Dockerfile, requirements) |
| `CLAUDE.md`, `.claude/settings.json`, `.gitignore`, `README.md` | — | N/A | Infrastruktur project migrasi, bukan kode modul |

## Cek `FINDINGS.md` (wajib gate)

| MF | Status | Menghalangi gate? |
|---|---|---|
| MF-01, MF-02, MF-04, MF-06 | Keputusan AI terdokumentasi, strategi di 03 §2 | Tidak |
| MF-03 | Struktur diputuskan; bagian semantik `[PERLU-KEPUTUSAN]` → verifikasi Step 9 (`Form`) + Step 10 (visual). Implementasi default mempertahankan ekspresi 19.0 identik (tidak mengubah business rule) | Tidak — tidak ada opsi yang mengubah business rule tanpa persetujuan; default aman |
| MF-05 | Informasional | Tidak |
| MF-07 | Keputusan dev (tidak di-port) | Tidak |

## Verdict

- [x] ✅ Lulus — semua elemen Covered (0 gap), lanjut ke step 5
- [ ] ❌ Ditolak
