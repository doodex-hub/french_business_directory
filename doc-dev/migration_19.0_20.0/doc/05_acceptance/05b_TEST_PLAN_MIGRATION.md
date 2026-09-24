# Test Plan (Migrasi) — french_business_directory

**Step:** 5 — Acceptance Criteria & Test Plan
**Ref:** `05_acceptance/05a_MIGRATION_ACCEPTANCE_CRITERIA.md`
**Tanggal:** 2026-09-24
**Status:** ✅ Selesai

---

## Step 9 — Dev Testing

> Eksekusi: Mode C (AI jalankan) — `docker compose up` di `docker-env/` (Odoo 20.0 from source), `-i fr_business_directory,personal_email_usage --test-enable --test-tags=/fr_business_directory,/personal_email_usage --without-demo=all --stop-after-init`. `docker compose down -v` sebelum tiap rerun. Tour: N/A (tidak ada Owl/JS — Fase E N/A), jadi tidak butuh Chrome; `Form` (`odoo.tests.Form`) dipakai untuk mensimulasikan onchange form partner (AC-01-02).
>
> Nama test = nama method di file; audit isi (bukan stub) dilakukan di Step 9a. File: `F` = `fr_business_directory/tests/test_siret_wizard.py`, `P` = `personal_email_usage/tests/test_fetchmail.py`, `N` = test baru Fase G2 (`fr_business_directory/tests/test_migration_20.py`).

| AC | Deskripsi | Unit | Integration | Tour |
|---|---|---|---|---|
| AC-00-01 | Install bersih | — | G1 log (install tanpa ERROR) | N/A |
| AC-00-02 | ACL `ir.access` crud | N `test_ir_access_rows_converted` | — | N/A |
| AC-01-01 | Tombol + field nama di view | N `test_partner_form_arch_has_name_and_button` | — | N/A |
| AC-01-02 | `is_company` form baru via Contacts | N `test_new_partner_form_contacts_context_is_company` | — | N/A |
| AC-01-03 | Action `siret_wizard()` | N `test_siret_wizard_action` | — | N/A |
| AC-02-01 | Auto-fetch | F `test_auto_fetch_on_wizard_open` | — | N/A |
| AC-03-01..04 | Paginasi & bug | F `test_pagination_wraparound_next/prev`, `test_prev_page_missing_limite_param_preserved_bug`, `test_next_page_has_limite_param`, `test_empty_partner_name_is_noop` | — | N/A |
| AC-04-01 | Select result → `FR_SIRET` | F `test_select_result_overwrites_partner` (diadaptasi) | — | N/A |
| AC-04-01 | Select etablissement → `FR_SIRET` | N `test_select_etablissement_writes_fr_siret` | — | N/A |
| AC-04-02/03 | Departemen | F `test_select_department_field_filled_when_model_present` (skip), `test_select_department_field_untouched_when_model_absent` | — | N/A |
| AC-04-04 | SIRET tak valid → ValidationError | N `test_select_invalid_siret_raises_validation_error` | — | N/A |
| AC-04-05 | `FR_SIREN` deduksi + identifier lain utuh | N `test_select_keeps_other_identifiers_and_deduces_siren` | — | N/A |
| AC-05-01..03 | Status/activite | F `test_status_label_active/closed`, `test_activite_principale_translation_*` | — | N/A |
| AC-05-04 | Etablissement dari siège | N `test_result_without_etablissements_uses_siege` | — | N/A |
| AC-06-01 | tracking | F `test_social_reason_field_tracked` | — | N/A |
| AC-07-01 | NameError preserved | F `test_logger_undefined_nameerror_preserved_bug` | — | N/A |
| AC-07-02 | Tidak ada kolisi | 02 §0e (statis) | — | N/A |
| AC-07-03 | date_fermeture hilang | F `test_matching_etablissement_missing_date_fermeture_key_no_longer_crashes` | — | N/A |
| AC-08-01/02/03 | Routing & entry point | P `test_fetch_mail_accepts_no_args`, `test_process_email_from_known_contact`, `test_one_server_connect_failure_does_not_block_other_servers` | — | N/A |
| AC-09-01..03 | Filter pengirim | P `test_skip_email_from_internal_user`, `test_skip_email_from_non_contact`, `test_process_email_from_known_contact` | — | N/A |
| AC-10-01/02 | message_new | P `test_message_new_returns_existing_partner`, `test_message_new_returns_false_for_unknown_sender` | — | N/A |
| AC-10-03 | message_new model lain → super | — (tidak ada test; dicover pembacaan kode + body identik) | — | N/A |
| AC-11-01 | skip tidak processed | P `test_skipped_email_never_marked_processed_preserved_bug`, `test_processed_email_recorded_in_processed_ids` | — | N/A |
| AC-11-02 | log count-failed | — (log, dicek baca kode; test existing tidak meng-assert log) | — | N/A |
| AC-11-03/04 | mark_read | P `test_mark_read_true_reapplies_seen_flag`, `test_mark_read_false_does_not_reapply_seen_flag` | — | N/A |
| AC-11-05 | dedup/batch/server/attach | P `test_duplicate_message_id_skipped_on_repeat_fetch`, `test_message_process_exception_does_not_abort_batch`, `test_one_server_connect_failure_does_not_block_other_servers`, `test_attach_and_original_flags_forwarded_to_message_process` | — | N/A |

**Email nyata (USAGE_GUIDE "Testing email nyata"):** level logic (`_fetch_mail` dengan IMAP mock + `message_new` langsung) sudah WAJIB & ada (15 test P). Level pipeline penuh (GreenMail IMAP sungguhan) — opsional, ditunda ke Step 10 kalau dev menginginkan (sama seperti project 18→19).

## Step 10 — QA Testing (belum dijalankan — STOP wajib, menunggu slot dev)

| AC | Deskripsi | Manual | AI-interaktif (Playwright MCP) | AI+tool eksternal |
|---|---|---|---|---|
| AC-01-01/02 | Tombol tampil sebaris dengan nama untuk company; individu tanpa tombol; perilaku partner baru tanpa VAT (MF-03) | Opsional | ✅ Utama | — |
| AC-02-01, AC-03-01/02 | Wizard terbuka + paginasi dengan API gouv.fr LIVE | Opsional | ✅ | — |
| AC-04-01/05 | Select → SIRET tampil di identifier partner form 20.0 | — | ✅ | — |
| AC-05-01/02 | Badge hijau/merah | — | ✅ | — |
| AC-08..11 | Fetchmail form (`mark_read` di mode developer), tombol "Fetch Now" | — | ✅ (form saja) | GreenMail opsional |

## Step 11 — UAT

| Kelompok fitur | AC tercakup | UAT |
|---|---|---|
| Business Directory (tombol, wizard, select) | AC-01..AC-07 | Manual business user |
| Personal Email Usage (filter, mark_read) | AC-08..AC-11 | Manual business user |

## Ringkasan

| Step | Role | Tipe | Eksekusi | Jumlah AC |
|---|---|---|---|---|
| 9 | Developer (AI, Mode C) | Unit/Integration (+ `Form`) | Otomatis | 33 (2 dicover statis: AC-07-02, AC-10-03/AC-11-02 baca kode) |
| 10 | QA | AI-interaktif (Playwright MCP) | Setelah slot diberikan dev | 10 |
| 11 | Dev/User | UAT | Manual | semua kelompok |
