# Implementation Log — french_business_directory

**Step:** 6 — Code Migration
**Ref:** `03_spec/03_MIGRATION_SPEC.md`, `04_completeness/04_SPEC_COMPLETENESS_REVIEW.md`
**Tanggal:** 2026-08-26

---

## Applicability Check

Sama seperti migrasi 17.0→18.0 — kode tidak berubah struktur sejak saat itu, dikonfirmasi ulang `01a_MIGRATION_INTAKE.md` §2b:

| Fase | Relevan? | Bukti/alasan |
|---|---|---|
| B2 — Model Kompleks | ☐ Tidak | Tidak ada field JSON, relasi >2 level, atau dynamic model creation |
| C2 — Semantik XML & UX | ☐ Tidak | Tidak ada `attrs`/`states`/`domain`/`context` dinamis di view manapun |
| D1 — Controllers | ☐ Tidak | Tidak ada folder `controllers/` |
| D2 — Assets & CSS | ☐ Tidak | Tidak ada asset custom |
| E — JavaScript (Owl) | ☐ Tidak | Tidak ada file `.js` |
| F — Upgrade Template | ☐ Tidak | Otomatis N/A karena E N/A |

## Tabel Ringkas Status Fase

| Fase | Status | Tanggal |
|---|---|---|
| A1 (manifest version bump) | ✅ | 2026-08-26 |
| A5 (fix DIFF-01, DIFF-02 — breaking change API) | ✅ | 2026-08-26 |
| B1 (update test existing sesuai `03_MIGRATION_SPEC.md` §2) | ✅ | 2026-08-26 |
| B2, C2, D1, D2, E, F | N/A — dikonfirmasi Applicability Check | |
| G1 (install test, Mode C) | ✅ 4 run (1 gagal awal, 3 rerun perbaikan bertahap), run #4 final: 0 failed, 0 error(s) of 24 tests | 2026-08-26 |
| G2 (validasi akhir/runtime) | ✅ Tercakup dalam G1 run #4 (install + full regression suite) | 2026-08-26 |

---

## Entri

### [Fase A1] Manifest Bootstrap

- **Scope:** `fr_business_directory/__manifest__.py`, `personal_email_usage/__manifest__.py`
- **Item spec (ref):** `03_MIGRATION_SPEC.md` §2 baris "manifest version"
- **Aksi:**
  - `fr_business_directory/__manifest__.py`: `'version': '18.0.1.0.0'` → `'version': '19.0.1.0.0'`
  - `personal_email_usage/__manifest__.py`: `'version': '18.0.1.0.0'` → `'version': '19.0.1.0.0'`
- **Secara eksplisit TIDAK dilakukan:** tidak ada perubahan `depends`, `data`, `assets`, atau field manifest lain.

### [Fase A5] Fix DIFF-01 — `fetch_mail()` signature

- **Scope:** `personal_email_usage/models/mail.py`
- **Item spec (ref):** `03_MIGRATION_SPEC.md` §2 baris DIFF-01, `FINDINGS.md` MF-01
- **Aksi:**
  - Baris 61: `def fetch_mail(self, raise_exception=True):` → `def fetch_mail(self):` — docstring diupdate menjelaskan alasan (cron 19.0 memanggil tanpa argumen)
  - Baris 156: `return super(FetchmailServer, self.filtered(lambda s: s.server_type != 'imap')).fetch_mail(raise_exception=raise_exception)` → `.fetch_mail()` (argumen dihapus)
- **Behavior:** TIDAK berubah — override total untuk server IMAP tetap seperti semula (BSL-015..BSL-021 tidak tersentuh), delegasi penuh untuk non-IMAP tetap terjadi, cuma signature teknis yang disesuaikan.
- **Secara eksplisit TIDAK dilakukan:** tidak memperbaiki bug pre-existing BSL-020/BSL-021 di file yang sama.

### [Fase A5] Fix DIFF-02 — `siret` → `company_registry`

- **Scope:** `fr_business_directory/models/siret_wizard.py`
- **Item spec (ref):** `03_MIGRATION_SPEC.md` §2 baris DIFF-02, `FINDINGS.md` MF-02
- **Aksi:** Ganti key `'siret': self.siret,` → `'company_registry': self.siret,` di 4 lokasi (`replace_all`, dikonfirmasi semua 4 occurrence genuinely butuh perubahan yang sama — 2 di `siret.wizard.result.select_siret()` baris 260/275, 2 di `matching.etablissement.select_siret()` baris 354/369):
  - Baris 260 (`select_siret` result, cabang `if` model `res.country.department` ada)
  - Baris 275 (`select_siret` result, cabang `else`)
  - Baris 354 (`select_siret` etablissement, cabang `if`)
  - Baris 369 (`select_siret` etablissement, cabang `else`)
- **Behavior:** Value/logic assignment TIDAK berubah (tetap `self.siret`, field WIZARD sendiri — nama field wizard tidak diubah, cuma key target `res.partner` yang berubah). Field `matching.etablissement.siret`/`siret.wizard.result.siret` (definisi field wizard) TIDAK disentuh — masih dinamai `siret`, itu bukan bagian dari breaking change (breaking change ada di `res.partner`, bukan model wizard custom).
- **Secara eksplisit TIDAK dilakukan:** tidak me-rename field wizard `siret` sendiri (tidak perlu — cuma target `write()` yang berubah).

### [Fase B1] Update Test Existing

- **Scope:** `fr_business_directory/tests/test_siret_wizard.py`, `personal_email_usage/tests/test_fetchmail.py`
- **Item spec (ref):** `03_MIGRATION_SPEC.md` §2 (2 baris ditambahkan Step 4 gate)
- **Aksi:**
  - `test_siret_wizard.py::test_select_result_overwrites_partner` — assertion `self.assertEqual(self.partner.siret, ...)` → `self.assertEqual(self.partner.company_registry, ...)`, docstring ditambah catatan penjelasan
  - `test_fetchmail.py::test_fetch_mail_accepts_raise_exception_kwarg` → ditulis ulang jadi `test_fetch_mail_accepts_no_args`, memanggil `fetch_mail()` tanpa argumen (bukan lagi `fetch_mail(raise_exception=False)`)
- **21 test lain** di kedua file di-reuse APA ADANYA (tidak disentuh) — akan jadi regression check di Step 9 bahwa behavior lain benar-benar tidak berubah.

### [Fase A5, revisi setelah G1 run #1] Fix MF-03 — pindahkan override ke `_fetch_mail()`

- **Scope:** `personal_email_usage/models/mail.py`, `personal_email_usage/tests/test_fetchmail.py`
- **Item spec (ref):** `FINDINGS.md` MF-03, `09_DEV_TESTING.md` (G1 run #1)
- **Ditemukan:** G1 run #1 (Step 9) — 6 dari 9 test `test_fetchmail.py` error. Root cause: cron 19.0 (`_fetch_mails()`) memanggil `_fetch_mail()` (privat) langsung, TIDAK LAGI memanggil `fetch_mail()` (publik, yang di-override modul sejak fix DIFF-01 awal). `connect()` juga di-rename `_connect__()`.
- **Keputusan:** dieskalasi ke user (bukan diputuskan sepihak AI — beda dari DIFF-01/DIFF-02 yang rendah risiko) karena melibatkan pindah titik override, bukan cuma rename signature. User menyetujui rekomendasi AI 2026-08-26.
- **Aksi:**
  - `def fetch_mail(self):` → `def _fetch_mail(self, batch_limit=50):` (method di-rename, docstring dijelaskan alasan)
  - `server.connect()` → `server._connect__()`
  - `return super(FetchmailServer, ...).fetch_mail()` → `return super(FetchmailServer, ...)._fetch_mail(batch_limit=batch_limit)`
  - `test_fetch_mail_accepts_no_args`: sekarang memanggil `self.env['fetchmail.server']._fetch_mail()` langsung dan assert `assertIsNone(result)` (bukan `assertTrue`, karena `_fetch_mail()` return `None`/`Exception`, bukan `True`/`False` seperti `fetch_mail()` versi 18.0)
  - 5 test lain (`test_skip_email_from_internal_user` dkk): `patch.object(type(self.imap_server), 'connect', ...)` → `patch.object(type(self.imap_server), '_connect__', ...)`, pemanggilan `self.imap_server.fetch_mail()` TIDAK diubah (tetap lewat entry point publik core 19.0, yang sekarang secara benar mendelegasikan ke `_fetch_mail()` override kita lewat `self.sudo()._fetch_mail()`)
- **Behavior:** TIDAK berubah dari intent asli (BSL-015..BSL-021) — override total untuk IMAP (raw imaplib, TIDAK diganti ke wrapper `OdooIMAP4` baru — keputusan sengaja, lihat MF-03), delegasi penuh untuk non-IMAP. Perbedaan teknis: delegasi ke non-IMAP sekarang AMAN dipanggil pada recordset kosong (tidak ada lagi crash `ensure_one()` seperti sebelumnya di Fase A5 pertama).
- **Secara eksplisit TIDAK dilakukan:** tidak mengadopsi arsitektur `OdooIMAP4`/`retrieve_unread_messages()`/`try_lock_for_update`/`batch_limit` baru untuk logic IMAP kita — itu perubahan gaya/robustness opsional, bukan wajib untuk kompatibilitas (P1 fidelity, "jangan refactor kecuali wajib").

---

## Ringkasan Perubahan File (final, setelah G1)

| File | Jenis perubahan |
|---|---|
| `fr_business_directory/__manifest__.py` | Version bump |
| `fr_business_directory/models/siret_wizard.py` | Fix DIFF-02 (4 lokasi) |
| `fr_business_directory/tests/test_siret_wizard.py` | Update 2 test: `test_select_result_overwrites_partner` (assertion field), `test_matching_etablissement_missing_date_fermeture_key_no_longer_crashes` (CAND-04, ditemukan G1) |
| `personal_email_usage/__manifest__.py` | Version bump |
| `personal_email_usage/models/mail.py` | Fix DIFF-01/MF-03 (override dipindah `fetch_mail()`→`_fetch_mail()`, `connect()`→`_connect__()`, ditemukan+diperbaiki setelah G1) |
| `personal_email_usage/tests/test_fetchmail.py` | Update 7 test: 1 ditulis ulang total (`test_fetch_mail_accepts_no_args`), 5 ganti target patch (`connect`→`_connect__`), 1 tambah commit-mock |
| `docker-env/docker-compose.yml` | Update image/nama/port untuk 19.0, tambah `--test-enable` |

Semua file lain di kedua addon (views, security, i18n, static, README, dll) **tidak disentuh** — port apa adanya, dikonfirmasi tidak ada breaking change (`02_DIFF_ANALYSIS.md` DIFF-03..DIFF-09).
