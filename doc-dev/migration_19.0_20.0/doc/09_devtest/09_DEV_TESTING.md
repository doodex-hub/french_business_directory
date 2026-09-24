# Dev Testing — french_business_directory

**Step:** 9 — Dev Testing (gate)
**Ref:** `05_acceptance/05a_MIGRATION_ACCEPTANCE_CRITERIA.md`, `05_acceptance/05b_TEST_PLAN_MIGRATION.md`, `01_intake/01b_BASELINE_SPEC.md`
**Tanggal:** 2026-09-24
**Status:** ✔️ Lulus gate

---

**Eksekusi resmi:** Mode C, lewat wrapper `docker-env/run-test.sh` (instansiasi `templates/run-test.sh.template`, diadaptasi 20.0 — lihat header file):

```bash
./run-test.sh odoo fbd_test_20 fr_business_directory,personal_email_usage
```

Environment: Odoo 20.0 from source (`D:\Kuncoro\doodex\repo\odoo20`, `version_info (20,0,0,FINAL)`), Python 3.12, Postgres 16, DB fresh (`down -v`), tanpa demo data (default 20.0), branch `migration/20.0` @ `96dc1db`.

## 9a. Audit Kesiapan Test

1. **Registrasi:** `fr_business_directory/tests/__init__.py` mengimpor `test_siret_wizard` + `test_migration_20`; `personal_email_usage/tests/__init__.py` mengimpor `test_fetchmail`. Semua file `test_*.py` terdaftar. Semua class ber-tag `post_install, -at_install`.
2. **Isi method** (audit `ast` di container, 2026-09-24): **40 method, 0 stub**, tiap method punya ≥1 `assert*`/`skipTest`. (Koreksi hitungan dokumen sebelumnya: test lama = 16 `fr_business_directory` + 14 `personal_email_usage` = 30, bukan 15+15.)

| AC | Deskripsi | File test | Status | Catatan |
|---|---|---|---|---|
| AC-00-01 | Install bersih | run log | ✅ Lengkap | 0 ERROR/CRITICAL |
| AC-00-02 | ACL ir.access | `test_ir_access_rows_converted`, `test_internal_user_can_use_wizard_models` | ✅ Lengkap | |
| AC-01-01 | Tombol + nama | `test_partner_form_arch_has_name_and_button` | ✅ Lengkap | arch gabungan |
| AC-01-02 | `is_company` form baru | `test_new_partner_form_contacts_context_is_company` | ✅ Lengkap (characterization) | MF-03 |
| AC-01-03 | Action | `test_siret_wizard_action` | ✅ Lengkap | |
| AC-02-01 | Auto-fetch | `test_auto_fetch_on_wizard_open` | ✅ Lengkap | |
| AC-03-01..04 | Paginasi + bug | 5 test `test_pagination_*`, `test_*_limite_*`, `test_empty_partner_name_is_noop` | ✅ Lengkap | |
| AC-04-01 | Select → FR_SIRET | `test_select_result_overwrites_partner`, `test_select_etablissement_writes_fr_siret`, `test_select_empty_siret_clears_fr_siret` | ✅ Lengkap | |
| AC-04-02 | Departemen tersedia | `test_select_department_field_filled_when_model_present` | ⚠️ Skip (by design) | model `res.country.department` tidak terinstall di environment manapun — sama seperti 17→18/18→19 |
| AC-04-03 | Departemen tidak ada | `test_select_department_field_untouched_when_model_absent` | ✅ Lengkap | |
| AC-04-04 | SIRET invalid | `test_select_invalid_siret_raises_validation_error` | ✅ Lengkap | MF-02 (a) |
| AC-04-05 | Identifier lain + SIREN | `test_select_keeps_other_identifiers_and_deduces_siren` | ✅ Lengkap | MF-02 (b) |
| AC-05-01..03 | Status & activite | 4 test | ✅ Lengkap | |
| AC-05-04 | Etablissement dari siège | `test_result_without_etablissements_uses_siege` | ✅ Lengkap | |
| AC-06-01 | tracking | `test_social_reason_field_tracked` | ✅ Lengkap | |
| AC-07-01 | NameError preserved | `test_logger_undefined_nameerror_preserved_bug` | ✅ Lengkap | |
| AC-07-02 | Tidak ada kolisi | — | Statis | `02` §0e + `08` §D (0 match) |
| AC-07-03 | date_fermeture hilang | `test_matching_etablissement_missing_date_fermeture_key_no_longer_crashes` | ✅ Lengkap | |
| AC-08-01..03 | Routing/entry point | `test_fetch_mail_accepts_no_args`, `test_process_email_from_known_contact`, `test_one_server_connect_failure_does_not_block_other_servers` | ✅ Lengkap | |
| AC-09-01..03 | Filter pengirim | 3 test | ✅ Lengkap | |
| AC-10-01/02 | message_new | 2 test | ✅ Lengkap | |
| AC-10-03 | message_new model lain | — | ❌ Tidak ada test | Risiko rendah: body override tidak berubah 19→20 dan `super()` dipanggil apa adanya (desk review `08` §C); sama dengan cakupan 18→19 |
| AC-11-01 | skip tidak processed | 2 test | ✅ Lengkap | |
| AC-11-02 | log count-failed | — | ❌ Tidak ada test (log) | Baca kode — baris tidak berubah; sama dengan cakupan 18→19 |
| AC-11-03/04 | mark_read | 2 test | ✅ Lengkap | |
| AC-11-05 | dedup/batch/server/attach | 4 test | ✅ Lengkap | |

**Verdict audit:** ✅ Semua AC prioritas tinggi (AC-00, AC-01-01/02, AC-04-01/04/05, AC-08-03, AC-11-01) berstatus Lengkap. Dua AC tanpa test (AC-10-03, AC-11-02) bukan prioritas tinggi, kodenya tidak diubah, gap-nya warisan sejak project sebelumnya — didisclose di sini, tidak memblokir.

## Baseline

- `01a` §4: test lama ADA di lokasi SAMA dengan source (`migration/19.0` `*/tests/*.py`), 30 method — lulus 30/30 di G1 final project 18→19 (Odoo 19.0, `FINDINGS.md` 18→19 MF-04). Tidak ada test lama di lokasi lain yang belum ter-port (6 test carry-over 17→18 sudah di-port di MF-04 18→19).
- Di 20.0: 28 dari 30 test lama PASS tanpa perubahan; 2 butuh adaptasi data/assertion (MF-06 — dummy SIRET gagal Luhn, `company_registry` tidak ada) → PASS.
- Applicability Check Fase E (Owl/JS): **Tidak** — tidak ada tour test yang dibutuhkan.

## Hasil Unit, Integration & Tour Test (target-codebase)

**Run resmi (wrapper):** `odoo.tests.result: 0 failed, 0 error(s) of 42 tests when loading database 'fbd_test_20'` — exit code 0, 42 baris `Starting <Class>.test_*`.
**Rincian 42:** 40 test modul (26 `fr_business_directory` + 14 `personal_email_usage`, 1 di antaranya skip by design) + 2 suite JS native `odoo.addons.web.tests.test_js` (`WebSuite.test_unit_desktop`, `MobileWebSuite.test_unit_mobile`) yang ikut terpilih lewat tag modul dan selesai <10 ms (modul tidak punya test JS) — bukan test modul, dicatat supaya hitungan tidak disalahbaca.
**Log:** 0 ERROR/CRITICAL. WARNING: `markdown2 is not installed` (environment), `DeprecationWarning` `self._context`/`self._cr` (MF-05, pre-existing, sengaja dipertahankan).

| AC | Unit | Integration | Tour | Pass/Fail | Catatan |
|---|---|---|---|---|---|
| AC-00-01/02 | ✅ | install G1 | N/A | Pass | |
| AC-01-01..03 | ✅ | `Form` | N/A | Pass | AC-01-02 = characterization MF-03 |
| AC-02, AC-03 | ✅ | — | N/A | Pass | |
| AC-04-01/03/04/05 | ✅ | — | N/A | Pass | AC-04-02 skip by design |
| AC-05, AC-06, AC-07 | ✅ | — | N/A | Pass | |
| AC-08..AC-11 (kecuali AC-10-03, AC-11-02) | ✅ | IMAP mock | N/A | Pass | |

**Riwayat loop test→fix→test:** lihat `06c_IMPLEMENTATION_LOG.md` "Riwayat Percobaan G1" #1-#7 (4 fail diekspektasikan/diperbaiki, 1 characterization dikunci) + run resmi wrapper di atas.

**Email nyata (GreenMail pipeline penuh):** tidak dijalankan di Step 9 (level logic sudah lengkap, 14 test IMAP mock + `message_new`). Opsional untuk Step 10 — konsisten keputusan project 18→19.

## Kontribusi ke Knowledge Base

- [x] Ada — `migration-records/french_business_directory_19.0_20.0/SUMMARY.md` CAND-02 (lanjutan: nilai `is_company` teramati) dan CAND-05 (`$0`). Tambahan kecil untuk template: `run-test.sh.template` perlu varian 20.0 (odoo-bin from source, tanpa `--without-demo=all`, `down -v`, pola `Starting <Class>.test_`) → CAND-06.

## Verdict

- [x] ✅ Semua AC prioritas Unit/Integration pass — **siap Step 10**, TETAPI Step 10 (QA browser live) **TIDAK dimulai**: STOP wajib dari dev (slot Step 10 lintas-repo). Menunggu dev memberi giliran.
- Keputusan dev yang masih terbuka (tidak memblokir Step 9, wajib sebelum Step 11): **MF-03** (visibilitas tombol untuk company tanpa VAT), konfirmasi opsi MF-02 (validasi SIRET native).

## Rerun setelah MF-03 workaround (2026-09-24)

`./run-test.sh odoo fbd_test_20 fr_business_directory,personal_email_usage` → **0 failed, 0 error(s) of 43 tests** (41 test modul + 2 suite JS native), 43 baris `Starting <Class>.test_*`. Test baru: `test_button_visibility_workaround_mf03`. Gate Step 9 tetap LULUS; MF-03 tetap OPEN (workaround).
