# Spec Completeness Review — french_business_directory

**Step:** 4 — Spec Completeness Review (gate)
**Ref:** `03_spec/03_MIGRATION_SPEC.md`, `source-codebase` (branch `migration/18.0`)
**Tanggal:** 2026-08-26

> Tujuan: pastikan `03_MIGRATION_SPEC.md` mencakup 100% elemen source module — bukan review kualitas kode (itu step 8).

---

## Tabel Cakupan

### `fr_business_directory`

| Elemen source module | Ada di Migration Spec? | Status | Catatan |
|---|---|---|---|
| `__manifest__.py` | Ya — §2 (version bump) | ✅ Covered | |
| `models/partner.py` (`res.partner` inherit, `social_reason`, `siret_wizard()`) | Ya — §2 baris "Semua file lain" | ✅ Covered | Tidak ada perubahan wajib |
| `models/siret_wizard.py` (`siret.wizard`, `siret.wizard.result`, `matching.etablissement`) | Ya — §2 baris DIFF-02 (4 lokasi `write()`) | ✅ Covered | |
| `views/partner.xml` | Ya — DIFF-03 (`02_DIFF_ANALYSIS.md`), §2 "Semua file lain" | ✅ Covered | Tidak ada perubahan wajib |
| `views/siret_wizard_views.xml` | Ya — DIFF-04, §2 "Semua file lain" | ✅ Covered | |
| `views/menu_item.xml` | Ya — §2 "Semua file lain" | ✅ Covered | |
| `security/ir.model.access.csv` | Ya — §2 "Semua file lain" | ✅ Covered | |
| `i18n/fr.po` | Ya — §2 "Semua file lain" (tidak ada perubahan bahasa) | ✅ Covered | Field label tidak berubah, tidak perlu update terjemahan |
| `static/description/*` (banner, icon, screenshot, index.html) | Ya — §2 "Semua file lain" | ✅ Covered | Housekeeping, tidak ada perubahan |
| `tests/test_siret_wizard.py` | **Tidak eksplisit di §2** | ❌ Gap | Test `test_select_result_overwrites_partner` (baris 130) meng-assert `self.partner.siret` — akan gagal di 19.0 karena field `siret` tidak ada. WAJIB diupdate ke `self.partner.company_registry` sebagai bagian Step 6, ditambahkan ke `03_MIGRATION_SPEC.md` §2 |
| `googleaeed8a7b9ec156e7.html`, `LICENSE`, `README.md` | Ya — housekeeping, tidak fungsional | ✅ Covered | |

### `personal_email_usage`

| Elemen source module | Ada di Migration Spec? | Status | Catatan |
|---|---|---|---|
| `__manifest__.py` | Ya — §2 (version bump) | ✅ Covered | |
| `models/mail.py` (`fetchmail.server`, `mail.thread` inherit) | Ya — §2 baris DIFF-01 (2 lokasi) | ✅ Covered | |
| `views/mail_views.xml` | Ya — DIFF-05, §2 "Semua file lain" | ✅ Covered | |
| `security/ir.model.access.csv` (dead file, BSL-022) | Ya — §2 "Semua file lain" | ✅ Covered | Dibawa apa adanya |
| `static/description/*` | Ya — §2 "Semua file lain" | ✅ Covered | |
| `tests/test_fetchmail.py` | **Tidak eksplisit di §2** | ❌ Gap | Test `test_fetch_mail_accepts_raise_exception_kwarg` (baris 51-54) secara eksplisit menguji signature 18.0 (`fetch_mail(raise_exception=False)`) — akan `TypeError` di 19.0 karena parameter itu dihapus. WAJIB ditulis ulang untuk menguji signature 19.0 (`fetch_mail()` tanpa argumen, sesuai cara cron 19.0 memanggil), sebagai bagian Step 6 |
| `googleaeed8a7b9ec156e7.html`, `LICENSE`, `LISEZMOI.md`, `README.md` | Ya — housekeeping | ✅ Covered | |

## Update Terhadap `03_MIGRATION_SPEC.md`

2 gap di atas (test files) ditambahkan sebagai baris baru di `03_spec/03_MIGRATION_SPEC.md` §2 sebelum Step 6 dimulai:

| File/simbol | Ref `DIFF-NNN` | Strategi migrasi | Risiko |
|---|---|---|---|
| `fr_business_directory/tests/test_siret_wizard.py:130` | DIFF-02 | Ganti assertion `self.partner.siret` → `self.partner.company_registry` | Rendah |
| `personal_email_usage/tests/test_fetchmail.py:51-54` | DIFF-01 | Tulis ulang `test_fetch_mail_accepts_raise_exception_kwarg` → `test_fetch_mail_accepts_no_args`, panggil `fetch_mail()` tanpa argumen (sesuai cara cron 19.0 memanggil) | Rendah |

## Verdict

- [x] ✅ Lulus — semua elemen Covered (2 gap test file ditemukan dan sudah ditambahkan ke migration spec di atas sebelum gate ditutup), lanjut ke step 5
- [ ] ❌ Ditolak
