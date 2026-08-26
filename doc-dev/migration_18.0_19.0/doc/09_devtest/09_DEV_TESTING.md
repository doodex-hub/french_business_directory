# Dev Testing — french_business_directory

**Step:** 9 — Dev Testing (gate)
**Ref:** `05_acceptance/05a_MIGRATION_ACCEPTANCE_CRITERIA.md`, `05_acceptance/05b_TEST_PLAN_MIGRATION.md`, `01_intake/01b_BASELINE_SPEC.md`
**Tanggal:** 2026-08-26
**Status:** 🔄 **Draft — G1 run #1 selesai, 1 blocker `[GAP-MIGRASI]` (MF-03) ditemukan, menunggu keputusan user sebelum fix + rerun**

---

## 9a. Audit Kesiapan Test

Semua 23 test existing (`test_siret_wizard.py` 14, `test_fetchmail.py` 9) sudah diaudit isinya sebagai bagian Step 5/6 (bukan stub — semua punya `assert*`/mock verifikasi nyata, lihat `05b_TEST_PLAN_MIGRATION.md`). `tests/__init__.py` kedua addon mengimpor file test dengan benar (dikonfirmasi dari log — 24 test benar-benar dieksekusi, bukan 0 akibat tag filter gagal/MSYS mangling).

## Baseline

- Test asli 17.0 tidak ada (modul tidak ada `tests/` di 17.0) — 23 test existing adalah hasil Step 9 project migrasi 17.0→18.0, sudah lulus 100% saat itu (28 test disebut commit gate, termasuk beberapa yang mungkin dihitung beda — 23 yang relevan project ini terverifikasi ada di kedua file).
- Applicability Check Fase E (Owl/JS): Tidak, N/A.

## Riwayat Percobaan G1

> **Mode eksekusi:** C (AI jalankan langsung, dikonfirmasi dev 2026-08-26 — Docker tersedia di sesi Claude Code CLI ini).

| # | Command | Hasil | Tanggal |
|---|---|---|---|
| 1 | `docker compose up --abort-on-container-exit` (`docker-env/docker-compose.yml`, image `odoo:19.0`, `--test-enable --test-tags=/fr_business_directory,/personal_email_usage`) | ❌ **1 failed, 6 error(s) of 24 tests** | 2026-08-26 |

## Hasil Detail Run #1

### `fr_business_directory` — 14/14 test AC-04-01 (fix DIFF-02) TERVERIFIKASI BENAR

Semua test PASS **kecuali 1**:

| Test | AC | Hasil | Catatan |
|---|---|---|---|
| `test_select_result_overwrites_partner` | AC-04-01 | ✅ Pass | **Konfirmasi langsung fix DIFF-02 benar** — assertion `self.partner.company_registry == '12345678900012'` lulus, membuktikan field target `company_registry` benar-benar menerima write dari wizard di 19.0 |
| `test_matching_etablissement_missing_date_fermeture_key_crashes` | — (MF-09, bug pre-existing dari project 17→18) | ❌ **Fail** — `AssertionError: Exception not raised` | **Temuan baru, low-priority** (bukan blocker): test ini meng-assert bahwa menulis string kosong `''` ke field `Date` (`date_fermeture`) crash di Postgres (bug pre-existing 17.0/18.0). Di 19.0, penulisan itu **TIDAK LAGI crash** — kemungkinan ORM 19.0 sekarang mengoersi `''`→`False`/NULL untuk field Date alih-alih meneruskan mentah ke Postgres. Ini PERBAIKAN behavior dari platform (bukan sesuatu yang kita ubah), bukan regresi fungsional — dicatat sebagai temuan, TIDAK memblokir gate (lihat "Kontribusi ke Knowledge Base" di bawah). Test perlu diupdate di rerun berikutnya (ubah `assertRaises` jadi assert sukses tanpa crash) SETELAH dikonfirmasi bukan false-negative environment-specific. |
| 12 test lain (AC-01 s/d AC-07 sisanya) | — | ✅ Pass | Semua behavior lain terkonfirmasi identik 18.0→19.0 |

### `personal_email_usage` — 6 error, SEMUA berakar SATU root cause (MF-03)

| Test | AC | Hasil | Catatan |
|---|---|---|---|
| `test_fetch_mail_accepts_no_args` | AC-08-03 | ❌ Error — `ValueError: Expected singleton: fetchmail.server()` | `fetch_mail()` 19.0 core WAJIB `ensure_one()` — override kita memanggil `super(...).fetch_mail()` pada recordset yang bisa KOSONG (0 server non-IMAP), yang sekarang jadi error, bukan no-op seperti 18.0. **Gejala dari MF-03**, lihat `FINDINGS.md`. |
| `test_skip_email_from_internal_user`, `test_skip_email_from_non_contact`, `test_process_email_from_known_contact`, `test_processed_email_recorded_in_processed_ids`, `test_skipped_email_never_marked_processed_preserved_bug` | AC-09-*, AC-11-01 | ❌ Error (5×) — `AttributeError: <class 'odoo.orm.models.fetchmail.server'> does not have the attribute 'connect'` | `connect()` di-rename `_connect__()` di core 19.0 — test mock `patch.object(type(self.imap_server), 'connect', ...)` gagal karena attribute itu tidak ada lagi. **Gejala dari MF-03.** |
| `test_message_new_returns_existing_partner`, `test_message_new_returns_false_for_unknown_sender` | AC-10-01/02 | ✅ Pass | `message_new()` (DIFF-06, tidak berubah) terkonfirmasi tetap benar — TIDAK terpengaruh MF-03 (method terpisah, tidak terkait `fetch_mail`) |

**Root cause tunggal untuk 6 error di atas:** lihat `FINDINGS.md` MF-03 — arsitektur `fetchmail.server` 19.0 dirombak total (cron tidak lagi memanggil `fetch_mail()`, method `connect()` di-rename `_connect__()`). Ini **TIDAK terdeteksi Step 2** (review statis cuma cek signature `fetch_mail()`, tidak cukup dalam untuk menangkap restrukturisasi method privat/cron entry point) — baru ketahuan di sini (G1), persis seperti tujuan checkpoint ini.

## Kontribusi ke Knowledge Base

- [x] Ada — dicatat sebagai kandidat baru di `migration-tool/migration-records/french_business_directory_18.0_19.0/SUMMARY.md`:
  - **CAND-03** — `fetchmail.server` arsitektur 19.0 dirombak total (`_fetch_mail()` baru, `connect()`→`_connect__()`, cron tidak lagi panggil `fetch_mail()`) — sangat mungkin general untuk modul migrasi manapun yang meng-override fetch email
  - **CAND-04** — Field `Date` di ORM 19.0 kemungkinan tidak lagi reject string kosong `''` (butuh verifikasi lebih lanjut sebelum diklaim sebagai perubahan pasti)

## Verdict

- [ ] ✅ Semua AC prioritas Unit/Integration pass — lanjut ke step 10
- [x] ❌ **Ada yang gagal — BLOCKED, menunggu keputusan user untuk MF-03** (lihat `FINDINGS.md` dan pertanyaan di respons chat). CAND-04 (test `date_fermeture`) tidak blocking, akan diselesaikan di rerun yang sama setelah MF-03 diputuskan.
