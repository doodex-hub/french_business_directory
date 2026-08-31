# Dev Testing — personal_email_usage

**Step:** 04 — Developer Testing (backfill)
**Module:** `personal_email_usage`
**Spec ref:** `doc-dev/backfill/spec/personal_email_usage/01A_FUNCTIONAL_SPEC.md`
**Last Updated:** 2026-08-07

> Modul BELUM punya `tests/` sama sekali sebelum backfill ini — semua test di bawah BARU ditulis
> (`personal_email_usage/tests/test_fetchmail_server.py` + `test_message_new.py`, 21 test method).
> Dijalankan NYATA (Mode C). Level LOGIC diuji dengan mock `imaplib` (mengganti
> `fetchmail.server.connect()`) — TIDAK butuh `mailpit`/`greenmail` untuk klaim "incoming email
> tercover" (lihat `PLAYBOOK.md` §"Mode B — testing incoming email" level 1).

---

## 1. Smoke Test (happy path)

### Cara Eksekusi

Mode C (docker, real) — docker-env sama dengan `fr_business_directory` (satu instance untuk
seluruh repo, lihat `CLAUDE.md`).

### Checklist

| # | Area/fitur | Happy path / edge case | Cara | Status |
|---|---|---|---|---|
| 1 | Instalasi modul | `personal_email_usage` terinstal bersih di atas `odoo:17.0` + `mail` | Mode C | ✅ Pass |
| 2 | `fetch_mail()` sukses | Email dari kontak terdaftar diproses, `processed_message_ids` ter-update | Mode C | ✅ Pass |
| 3 | `fetch_mail()` skip | Email dari user internal di-skip, tidak diproses | Mode C | ✅ Pass |

---

## 2. Unit & Integration Test Specification

> **Lesson infrastruktur test yang WAJIB dibaca sebelum menulis test baru untuk `fetch_mail()`
> (ditemukan lewat eksekusi nyata, dicatat juga ke `records/` sebagai kandidat pengetahuan lintas
> modul — lihat §5):** `fetch_mail()` (baik override modul ini MAUPUN implementasi ASLI Odoo core
> di `mail/models/fetchmail.py`) memanggil `self._cr.commit()` untuk setiap email yang TIDAK
> di-skip — ini SENGAJA (semantik cron: commit progres per-email supaya satu email gagal tidak
> membatalkan yang sudah berhasil). TAPI panggilan commit SUNGGUHAN ini, kalau dieksekusi di dalam
> `TransactionCase` biasa, MENGHANCURKAN SAVEPOINT yang dipakai framework test Odoo untuk isolasi
> antar-test — begitu satu test mencapai baris commit ini, SEMUA test SETELAHNYA di kelas yang sama
> ikut gagal dengan error PostgreSQL yang membingungkan (`savepoint "test_N" does not exist` /
> `current transaction is aborted`), TERLEPAS apakah test-test itu sendiri benar. **Wajib**:
> `patch.object(self.cr, 'commit')` (no-op) di `setUp()` untuk SEMUA test class yang memanggil
> `fetch_mail()` lewat jalur non-skip — lihat implementasi di `TestFetchmailServerBase.setUp()`.
> **Dampak kalau lesson ini diabaikan:** percobaan pertama modul ini menghasilkan
> **2 failed, 6 error(s) of 25 tests** — 5 dari 6 error itu murni CASCADE dari satu test yang
> mencapai `self._cr.commit()` tanpa fix ini, BUKAN 5 bug independen.

### 2a. Model Fields

**File:** `models/mail.py`

Field `mark_read` (Boolean, default `False`) dan `processed_message_ids` (Text) — tidak ada
compute/constrain tersendiri, tercakup implisit lewat TC di bawah.

### 2b. `fetch_mail()` — flag handling & skip logic

#### TC-FETCH-01 — Passthrough server non-IMAP

| # | Tipe | Condition | Expected | Provenance |
|---|---|---|---|---|
| 01 | Unit | `server_type='pop'`, `fetch_mail()` dipanggil | `res.users.search`/`res.partner.search` (khusus logic IMAP modul ini) TIDAK PERNAH dipanggil | `[DIKONFIRMASI]` — dikonfirmasi nyata |

#### TC-FLAG-01 — `\Seen` flag sequencing vs `mark_read`

| # | Tipe | Condition | Expected | Provenance |
|---|---|---|---|---|
| 01 | Unit | `mark_read=True`, email dari kontak dikenal | `store(+FLAGS, \Seen)` dipanggil setelah fetch | `[DIKONFIRMASI]` |
| 02 | Unit | `mark_read=False` (default), email dari kontak dikenal, sukses diproses | `store(+FLAGS, \Seen)` TIDAK dipanggil; `store(-FLAGS, \Seen)` SELALU dipanggil | `[DIKONFIRMASI]` |

#### TC-SKIP-01 — Filter user internal & non-kontak (F-07)

| # | Tipe | Condition | Expected | Provenance |
|---|---|---|---|---|
| 01 | Unit | Sender = user internal (`share=False`) | `message_process` TIDAK dipanggil; `message_id` TIDAK masuk `processed_message_ids` (F-07) | `[PERLU-KEPUTUSAN]` — dikonfirmasi nyata |
| 02 | Unit | Sender = bukan kontak terdaftar | Sama seperti di atas, TIDAK masuk `processed_message_ids` (F-07) | `[PERLU-KEPUTUSAN]` — dikonfirmasi nyata |
| 03 | Unit | Sender = kontak terdaftar | `message_id` MASUK `processed_message_ids` | `[HASIL-BACA]` — dikonfirmasi nyata |
| 04 | Unit | `message_id` SUDAH ada di `processed_message_ids` sebelum fetch | `message_process` TIDAK dipanggil ulang (dedup jalan untuk kasus yang SUDAH tercatat) | `[HASIL-BACA]` — dikonfirmasi nyata |

#### TC-LOG-01 — Log ringkasan "succeeded" salah hitung (F-08)

| # | Tipe | Condition | Expected | Provenance |
|---|---|---|---|---|
| 01 | Unit | 1 email sukses, 1 email gagal (`message_process` raise) | Log SEKARANG mencatat `succeeded=0` (`count-failed`=`1-1`), padahal SEHARUSNYA `1` (F-08) | `[PERLU-KEPUTUSAN]` — dikonfirmasi nyata, di-assert langsung ke argumen `_logger.info(...)` (bukan `assertLogs`, lihat lesson di bawah) |

**Lesson teknik test kedua (dicatat untuk sesi berikutnya):** draf awal TC-LOG-01 pakai
`self.assertLogs(...)`, yang gagal dengan `"no logs of level INFO or higher triggered"` walau kode
sudah genuinely memanggil `_logger.info(...)` — kemungkinan interaksi `assertLogs` dengan konfigurasi
logging Odoo (level/propagation) yang tidak sepenuhnya predictable dari luar. **Fix:** `patch()`
langsung objek `_logger` modul (`patch('odoo.addons.personal_email_usage.models.mail._logger')`) dan
inspeksi `mock_logger.info.call_args_list` — tidak bergantung pada plumbing logging Odoo sama sekali,
lebih robust untuk kasus serupa di modul lain.

### 2c. `message_new()` override — AC-06

#### TC-MSGNEW-01

| # | Tipe | Condition | Expected | Provenance |
|---|---|---|---|---|
| 01 | Unit | Model=`res.partner`, sender cocok partner existing | Partner existing dikembalikan, TIDAK ada partner baru dibuat | `[HASIL-BACA]` — dikonfirmasi nyata |
| 02 | Unit | Model=`res.partner`, sender TIDAK cocok partner manapun | `False` dikembalikan | `[HASIL-BACA]` — dikonfirmasi nyata |
| 03 | Unit | Model selain `res.partner` (`mail.thread` abstrak) | `res.partner.search` TIDAK dipanggil — delegasi ke `super()` (lihat lesson savepoint di bawah) | `[HASIL-BACA]` — dikonfirmasi nyata |

**Lesson teknik test ketiga:** memanggil `message_new()` langsung di model ABSTRAK `mail.thread`
membuat `super()` core mencoba `self.create()` ke tabel yang TIDAK ADA (`relation "mail_thread" does
not exist`) — bare `try/except Exception` di Python menangkap exception-nya TAPI TIDAK memulihkan
transaksi PostgreSQL yang sudah ter-abort, tetap mencemari test setelahnya (gejala SAMA dengan lesson
`self._cr.commit()` di atas, akar masalah beda). **Fix:** bungkus panggilan berisiko dengan
`self.env.cr.savepoint()` (primitive Odoo sendiri untuk isolasi kegagalan level-DB), bukan cuma
`try/except` Python biasa.

### 2d. Test Matrix Summary

| Area | Unit | Integration | Provenance |
|---|---|---|---|
| Passthrough non-IMAP | ✓ (1 test) | | `[DIKONFIRMASI]` |
| Flag sequencing | ✓ (2 test) | | `[DIKONFIRMASI]` |
| Skip logic (F-07) | ✓ (4 test) | | Mixed |
| Log bug (F-08) | ✓ (1 test) | | `[PERLU-KEPUTUSAN]` |
| `message_new` (AC-06) | ✓ (3 test) | | `[HASIL-BACA]` |

### 2f. Override/Collision Check terhadap Odoo Core

| # | Method | Model | Kelas yang mendefinisikan (`__mro__`) | Override total Odoo core? | Provenance |
|---|---|---|---|---|---|
| 01 | `fetch_mail` | `fetchmail.server` (`_inherit`) | `personal_email_usage.FetchmailServer` mendefinisikan ulang total untuk `server_type='imap'`; `mail.FetchmailServer` (core) HANYA dipanggil (`super()`) untuk server bukan-IMAP | ☑ Ya untuk IMAP (SENGAJA, tujuan utama modul — lihat F-11 `FINDINGS.md` untuk risiko arsitektural ke modul LAIN yang mungkin extend method ini di masa depan) | `[DIKONFIRMASI]` — dikonfirmasi baca source `mail/models/fetchmail.py` + eksekusi nyata TC-FETCH-01 |
| 02 | `message_new` | `mail.thread` (`_inherit`) | `personal_email_usage.MailThread` — HANYA short-circuit untuk `_name=='res.partner'`, delegasi `super()` untuk model lain | ☑ Tidak untuk model lain (aman, dikonfirmasi TC-MSGNEW-03); untuk `res.partner` SENGAJA menggantikan pembuatan record baru (BR-07) | `[HASIL-BACA]` — dikonfirmasi nyata |

### 2g. Incoming Email — `message_process()` Test

Level logic tercover PENUH lewat TC-SKIP-01 poin 03 (sender dikenal → `message_process` benar-benar
dipanggil dengan raw RFC822 dari `fetch_mail()`, bukan dipanggil langsung terisolasi — pilihan desain
test ini SENGAJA supaya integrasi `fetch_mail()`↔`message_new()` ikut terbukti dalam satu jalur,
bukan dua test terpisah yang masing-masing mock separuh). Level pipeline penuh (GreenMail,
`fetchmail.server` polling mailbox eksternal sungguhan) — **tidak dijalankan**, lihat
`03B_TEST_PLAN.md` (kondisional, tidak wajib untuk klaim "incoming email tercover").

---

## 3. Hasil Eksekusi Real (Mode C, Docker)

**Hasil (log lengkap: `docker-env/logs/odoo.log`, run terakhir 2026-08-07 07:50):**
```
odoo.tests.stats: personal_email_usage: 21 tests 0.50s 663 queries
odoo.tests.result: 0 failed, 0 error(s) of 26 tests when loading database 'french_business_directory_17_test'
```

**Riwayat 3 percobaan sampai lulus:**
1. Percobaan #1: **2 failed, 6 error(s) of 25 tests** — root cause: `test_mark_read_false_...`
   (test PERTAMA yang mencapai jalur commit) memicu `self._cr.commit()` sungguhan di dalam
   `TransactionCase`, menghancurkan savepoint framework, meng-cascade jadi 5 `ERROR` tambahan di
   test-test SETELAHNYA (yang kodenya sendiri sebenarnya benar) + 1 `ERROR` terpisah dari
   `test_message_new_delegates_to_super_for_non_partner_models` (akar masalah beda: INSERT ke tabel
   abstrak `mail_thread` yang tidak ada) + 1 `FAIL` asli (`test_succeeded_count_in_log_is_wrong_F08`,
   gagal karena transaksi SUDAH tercemar sebelum test ini sempat jalan bersih).
2. Percobaan #2 (setelah fix `patch.object(self.cr, 'commit')` + `self.env.cr.savepoint()`):
   **1 failed, 0 error(s) of 26** — SEMUA cascade hilang, sisa 1 kegagalan ASLI:
   `assertLogs` tidak menangkap log (lihat lesson TC-LOG-01 di atas).
3. Percobaan #3 (setelah fix mock `_logger` langsung): **0 failed, 0 error(s) of 26 tests** — PASS
   PENUH.

---

## 4. Ringkasan

- **Unit:** 12 TC / 21 test method (`personal_email_usage/tests/test_fetchmail_server.py` +
  `test_message_new.py`) — jalankan
  `odoo -i personal_email_usage --test-enable --test-tags=/personal_email_usage --stop-after-init`
- **Integration:** 0 (tidak ada controller/HTTP route baru; `message_process()` diuji sebagai
  pemanggilan method langsung, bukan lewat HTTP)
- **Smoke:** 3/3 Pass

---

## 5. Kandidat `records/` (kontribusi ke Knowledge Base BACKFILL — lihat §5 `07_QA_TESTING.md`)

Dua lesson teknik test di atas (§2b: `self._cr.commit()` vs `TransactionCase` savepoint; §2c:
`self.env.cr.savepoint()` untuk isolasi kegagalan DB-level) GENUINELY lintas-modul — method Odoo
manapun yang secara sengaja `self._cr.commit()` di tengah eksekusi (pola cron umum) akan berulang
kali menjebak sesi BACKFILL berikutnya kalau tidak didokumentasikan sekali di sini. Dicatat ke
`records/french-business-directory-17/SUMMARY.md`.
