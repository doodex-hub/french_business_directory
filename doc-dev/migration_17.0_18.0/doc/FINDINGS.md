# Findings — french_business_directory (migrasi 17.0 → 18.0)

**Modul:** french_business_directory (`fr_business_directory` + `personal_email_usage`)
**Migrasi:** 17.0 → 18.0
**Terakhir update:** 2026-08-31

---

## Ringkasan

| ID | Judul | Ditemukan di Step | Tag | Prioritas | Status |
|---|---|---|---|---|---|
| MF-01 | Soft-dependency ke model `res.country.department` (OCA, tidak di-connect) | 1 | `[PERLU-KEPUTUSAN]` | Sedang | 🟡 Ditunda — lanjut tanpa third-party folder, revisit di Step 2/9-10 |
| MF-02 | `_logger` dipakai tapi tidak diimpor (`siret_wizard.py`) | 1 (diwarisi backfill) | `[DIWARISI-SOURCE]` | Tinggi | 🟡 Default: dipertahankan identik |
| MF-03 | Param `limite_matching_etablissements` hilang di `fetch_previous_page` | 1 (diwarisi backfill) | `[DIWARISI-SOURCE]` | Sedang | 🟡 Default: dipertahankan identik |
| MF-04 | No-op senyap saat `partner_name` kosong di tengah paginasi | 1 (diwarisi backfill) | `[DIWARISI-SOURCE]` | Rendah | 🟡 Default: dipertahankan identik |
| MF-05 | Email yang di-skip tidak pernah ditandai processed → re-fetch tanpa henti | 1 (diwarisi backfill) | `[DIWARISI-SOURCE]` | **Tinggi** | ✅ CONFIRMED — dev setuju dipertahankan identik (2026-08-24) |
| MF-06 | Log ringkasan "succeeded" salah hitung | 1 (diwarisi backfill) | `[DIWARISI-SOURCE]` | Sedang | 🟡 Default: dipertahankan identik |
| MF-07 | `fetch_mail()` signature core berubah (`raise_exception` param baru) — override modul ini akan `TypeError` di cron 18.0 kalau tidak disesuaikan | 1, dikonfirmasi Step 2 | `[GAP-MIGRASI]` (**dikonfirmasi nyata**) | **Tinggi** | ✅ RESOLVED — fix diterapkan Step 6 (lihat `02_DIFF_ANALYSIS.md` DIFF-02) |
| MF-08 | `from odoo.tools import logging` gagal `ImportError` di 18.0 — `misc.py` menambahkan `__all__` yang menutup leak implisit stdlib `logging` | 6 (ditemukan lewat G1 dry run nyata, TIDAK terdeteksi Step 2/3 review statis) | `[GAP-MIGRASI]` (dikonfirmasi nyata) | **Tinggi (install-blocking)** | ✅ RESOLVED — fix diterapkan Step 6 (lihat `02_DIFF_ANALYSIS.md` DIFF-09) |
| MF-09 | `matching.etablissement` create() crash (`InvalidDatetimeFormat`) kalau key `date_fermeture` hilang total dari payload API (bukan cuma bernilai kosong) | 9 (ditemukan lewat test suite nyata, bug pre-existing 17.0, TIDAK disebabkan migrasi) | `[DIWARISI-SOURCE]` | Sedang (butuh kondisi API spesifik untuk terpicu) | 🟡 Dicatat, tidak diperbaiki (P1) |
| MF-10 | `matching.etablissement._compute_activite_principale` membaca `result_id.activite_principale` (nilai level siège/parent), BUKAN field `activite_principale` miliknya sendiri — beda dari yang tersirat di deskripsi BR-07 lama | 9 (ditemukan lewat penulisan test, dikonfirmasi baca kode + eksekusi nyata) | `[DIWARISI-SOURCE]` — koreksi pemahaman, bukan bug baru | Rendah (cuma klarifikasi, behavior tidak berubah dari 17.0) | 🟡 Dicatat, `01b_BASELINE_SPEC.md` BSL-007 dikoreksi |
| MF-11 | Test case `TC-FLAG-01` (`\Seen` flag sequencing vs `mark_read`, BSL-020) terdokumentasi di backfill lama tapi tidak pernah ter-port ke test suite migrasi ini — Step 9 dulu keliru menyimpulkan "source tidak punya test sama sekali" karena cuma cek `source-codebase`, tidak cek folder backfill terpisah (`french-business-directory-17`) | 9 (gap ditemukan lewat investigasi terpisah, 2026-08-31), ditutup sesi ini | `[DIWARISI-SOURCE]` — gap cakupan test, bukan bug produk | Rendah (cakupan test, BSL-020/MF-05 sendiri sudah lama dikonfirmasi lewat jalur lain) | ✅ RESOLVED — 2 method (`test_mark_read_true_reapplies_seen_flag`, `test_mark_read_false_does_not_reapply_seen_flag`) ditambahkan ke `personal_email_usage/tests/test_fetchmail.py`, dijalankan (`docker compose run` + `--test-enable`), 0 failed/error dari 26 test total |

---

## Detail

### MF-01 — Soft-dependency ke model `res.country.department` (OCA, tidak di-connect)
**Ditemukan di:** Step 1 (2026-08-24)
**Tag:** `[PERLU-KEPUTUSAN]`
**Ref:** `BSL-006` (`01b_BASELINE_SPEC.md`), diwarisi `F-05` (`doc-dev-backfill/FINDINGS.md` di `french-business-directory-17`)
**Lokasi:** `fr_business_directory/models/siret_wizard.py:254-267`, `:346-364`
**Deskripsi:** Kode secara defensif cek `self.env['ir.model'].search([('model','=','res.country.department')])` sebelum mengisi `country_department_id`/`state_id`/`country_id` di `res.partner`. **Dikonfirmasi via pencarian menyeluruh (`rg`, bukan cuma `l10n_fr`) di seluruh `addons/` `native-source` (17.0 Community), `native-target` (18.0 Community), `native-source-enterprise` (17.0), DAN `native-target-enterprise` (18.0) — model `res.country.department` TIDAK ADA di keempatnya, nol hasil.** Ini pasti addon eksternal di luar keempat repo native yang sudah di-connect (kemungkinan besar OCA `l10n_fr_department`, repo `OCA/l10n-france`), tidak dideklarasikan di `depends` manifest manapun.
**Dampak:** Kalau addon penyedia model ini TIDAK terinstall di lingkungan produksi 17.0 sekarang, fitur pengisian department/state/country partner otomatis memang tidak pernah jalan (fallback aman, bukan bug) — tapi kita belum tahu status instalasinya di produksi, jadi belum bisa pastikan apakah fitur ini AKTIF dipakai atau tidak di produksi.
**Rekomendasi:** dev konfirmasi (a) apakah addon OCA ini terinstall di instance produksi sekarang, (b) kalau ya, sediakan `third-party-source`/`third-party-target` (path clone OCA repo checkout 17.0/18.0) supaya Step 2 bisa cek kompatibilitas model itu sendiri di 18.0.
**Catatan tambahan (2026-08-24):** backfill lama JUGA tidak pernah bisa memastikan ini — `04A_DEV_TESTING.md:84-86` mencatat AC terkait model ini `res.country.department TERSEDIA` **tidak dijalankan** (tidak ada di image `odoo:17.0` + tidak ada `EXTERNAL_ADDONS_PATHS`), dicatat sebagai limitasi tool, bukan hasil pass/fail. Tidak ada sumber manapun (kode maupun dokumen lama) yang bisa memastikan status instalasi di produksi.
**Keputusan pemilik modul:** Ditunda — dev pilih lanjut Step 1 tanpa `third-party-source`/`target` untuk sekarang, revisit kalau relevan di Step 2 (diff) atau Step 9/10 (testing, saat instance produksi nyata bisa dicek langsung).

---

### MF-02 — `_logger` dipakai tapi tidak diimpor (`siret_wizard.py`)
**Ditemukan di:** Step 1 (2026-08-24), diwarisi backfill 2026-08-07
**Tag:** `[DIWARISI-SOURCE]`
**Ref:** `BSL-008`, `F-01` (`doc-dev-backfill/FINDINGS.md`)
**Lokasi:** `fr_business_directory/models/siret_wizard.py:113,128`
**Deskripsi:** `_logger.warning`/`_logger.error` dipanggil tanpa `import logging`/`_logger = logging.getLogger(__name__)` — kalau jalur ini terpicu (respons API gouv.fr anomali, atau request gagal), Python raise `NameError` alih-alih log yang berguna.
**Dampak di 18.0:** Sama seperti 17.0 — dipertahankan identik per default `CLAUDE.md` (bug pre-existing, tidak diperbaiki kecuali diminta lain).
**Keputusan pemilik modul:** *(kosong — default: dipertahankan identik, kecuali dev eksplisit minta diperbaiki)*

---

### MF-03 — Param `limite_matching_etablissements` hilang di `fetch_previous_page`
**Ditemukan di:** Step 1 (2026-08-24), diwarisi backfill 2026-08-07
**Tag:** `[DIWARISI-SOURCE]`
**Ref:** `BSL-009`, `F-02`
**Lokasi:** `fr_business_directory/models/siret_wizard.py:177,195` (vs `:140` yang ada parameternya)
**Deskripsi:** Data `matching_etablissements` bisa beda untuk halaman yang sama tergantung arah navigasi (Next vs Prev).
**Keputusan pemilik modul:** *(kosong — default: dipertahankan identik)*

---

### MF-04 — No-op senyap saat `partner_name` kosong di tengah paginasi
**Ditemukan di:** Step 1 (2026-08-24), diwarisi backfill 2026-08-07
**Tag:** `[DIWARISI-SOURCE]`
**Ref:** `BSL-010`, `F-03`
**Lokasi:** `fr_business_directory/models/siret_wizard.py:134-150`, `:171-187`
**Deskripsi:** Tombol Next/Prev terlihat tidak berfungsi tanpa feedback kalau `partner_name` falsy — edge case jarang.
**Keputusan pemilik modul:** *(kosong — default: dipertahankan identik, prioritas rendah)*

---

### MF-05 — Email yang di-skip tidak pernah ditandai processed → re-fetch tanpa henti
**Ditemukan di:** Step 1 (2026-08-24), diwarisi backfill 2026-08-07
**Tag:** `[DIWARISI-SOURCE]`
**Ref:** `BSL-020`, `F-07`
**Lokasi:** `personal_email_usage/models/mail.py:64,75-77,93-96,98-107,120-121`
**Deskripsi:** Dengan `mark_read=False` (default), email dari user internal/bukan kontak di-fetch ulang SELAMANYA tiap cron — beban IMAP dan log bertambah tanpa henti.
**Dampak:** Bug performa/resource nyata, prioritas TINGGI.
**Keputusan pemilik modul:** ✅ Dikonfirmasi dev 2026-08-24 — dipertahankan identik di 18.0, tidak diperbaiki saat migrasi ini.

---

### MF-06 — Log ringkasan "succeeded" salah hitung
**Ditemukan di:** Step 1 (2026-08-24), diwarisi backfill 2026-08-07
**Tag:** `[DIWARISI-SOURCE]`
**Ref:** `BSL-021`, `F-08`
**Lokasi:** `personal_email_usage/models/mail.py:122-124,138-141`
**Deskripsi:** "succeeded" dihitung `count - failed`, padahal `count` hanya increment di jalur sukses — angka log selalu under-count/bisa negatif.
**Keputusan pemilik modul:** *(kosong — default: dipertahankan identik)*

---

### MF-07 — `fetch_mail()` signature core berubah — override modul akan `TypeError` di cron 18.0
**Ditemukan di:** Step 1 (2026-08-24, hipotesis), dikonfirmasi nyata Step 2 (2026-08-24)
**Tag:** `[GAP-MIGRASI]` — dikonfirmasi, bukan lagi potensial
**Ref:** `BSL-023`, `F-11` (asal usul override), `DIFF-02` (`02_DIFF_ANALYSIS.md`)
**Lokasi:** `personal_email_usage/models/mail.py:61` (override `def fetch_mail(self):`) vs `native-target` `mail/models/fetchmail.py:215` (`def fetch_mail(self, raise_exception=True):`)
**Deskripsi:** Dikonfirmasi langsung dari kode core: signature `fetch_mail()` berubah di 18.0, menambah parameter `raise_exception=True`. Cron entry point `_fetch_mails()` di 18.0 memanggil `.fetch_mail(raise_exception=False)` — override modul ini (`def fetch_mail(self):`, tanpa parameter apapun) akan `TypeError: fetch_mail() got an unexpected keyword argument 'raise_exception'` untuk SEMUA server (IMAP maupun POP) begitu cron pertama kali jalan di 18.0. Ini BUKAN cuma soal `super()` chain terputus (itu tetap benar, F-11) — ini genuinely install-jalan-tapi-cron-crash-total kalau override tidak diupdate.
**Dampak:** Modul tidak bisa fetch email SAMA SEKALI lewat cron di 18.0 tanpa fix ini (functional-blocking, bukan cuma risiko arsitektural jangka panjang seperti draft awal F-11).
**Rekomendasi:** Step 6 (Fase A/B, compat fix) WAJIB update signature override jadi `def fetch_mail(self, raise_exception=True):`, teruskan `raise_exception=raise_exception` ke `super()` call (path non-IMAP). Behavior internal path IMAP (log-only, tidak pernah raise) dipertahankan identik — parameter cukup diterima supaya tidak `TypeError`, tidak perlu mengubah exception handling internal modul ini.
**Keputusan pemilik modul:** *(kosong — fix ini bersifat kompatibilitas wajib (bukan pilihan), akan dieksekusi di Step 6 kecuali dev keberatan)*

---

### MF-08 — `from odoo.tools import logging` — `ImportError` di 18.0 (ditemukan G1 dry run)
**Ditemukan di:** Step 6, Checkpoint G1 percobaan #1 (2026-08-24) — **TIDAK terdeteksi di Step 2/3** (review statis manifest/kode tidak menangkap ini, murni ketahuan dari install nyata)
**Tag:** `[GAP-MIGRASI]` — dikonfirmasi
**Ref:** `DIFF-09` (`02_DIFF_ANALYSIS.md`)
**Lokasi:** `personal_email_usage/models/mail.py:6`
**Deskripsi:** `odoo/tools/misc.py` di 18.0 menambahkan `__all__` eksplisit yang tidak mencantumkan `logging` — menutup leak implisit stdlib `logging` yang di 17.0 (tanpa `__all__`) ikut ter-export lewat wildcard `from .misc import *` di `odoo/tools/__init__.py`. `odoo.tools.logging` bukan API resmi Odoo di versi manapun, cuma efek samping tidak disengaja.
**Dampak:** Install modul `personal_email_usage` gagal total (`ImportError`) di 18.0 tanpa fix ini.
**Rekomendasi:** ganti `from odoo.tools import logging` → `import logging` (stdlib langsung).
**Keputusan pemilik modul:** ✅ RESOLVED — fix diterapkan (compat mekanis, bukan perubahan business logic), diverifikasi ulang lewat G1 percobaan #2.

---

### MF-09 — `matching.etablissement` create() crash kalau `date_fermeture` hilang total dari payload
**Ditemukan di:** Step 9 (Dev Testing, 2026-08-24) — lewat penulisan test nyata, bukan review statis
**Tag:** `[DIWARISI-SOURCE]` — bug pre-existing 17.0, tidak disebabkan migrasi (kode ini tidak disentuh Step 6)
**Lokasi:** `fr_business_directory/models/siret_wizard.py` — `me.get('date_fermeture', '')` (baik jalur `matching_etablissements_data` maupun fallback siège)
**Deskripsi:** Kalau key `date_fermeture` SAMA SEKALI TIDAK ADA di dict payload (beda dari key ada tapi bernilai `null`/`False`), fallback `.get(..., '')` menghasilkan string kosong `''` yang ditulis ke field `date_fermeture` (`fields.Date`) — Postgres menolak dengan `InvalidDatetimeFormat: invalid input syntax for type date: ""`. Dikonfirmasi lewat test (`test_matching_etablissement_missing_date_fermeture_key_crashes`).
**Dampak:** Kalau API `recherche-entreprises.api.gouv.fr` pernah mengirim payload tanpa key ini sama sekali (belum dikonfirmasi apakah ini genuinely terjadi di produksi — API publik, bisa berubah kapan saja), `create()` akan crash, bukan silent-safe seperti yang mungkin diasumsikan.
**Keputusan pemilik modul:** Dicatat, TIDAK diperbaiki (P1 Full Fidelity — behavior identik 17.0). Kalau dev mau, bisa jadi kandidat perbaikan terpisah DI LUAR migrasi ini.

---

### MF-10 — `_compute_activite_principale` (matching.etablissement) sumbernya `result_id.activite_principale`, bukan field sendiri
**Ditemukan di:** Step 9 (Dev Testing, 2026-08-24)
**Tag:** `[DIWARISI-SOURCE]` — koreksi pemahaman terhadap `01b_BASELINE_SPEC.md` BSL-007/BR-07 lama, bukan bug baru
**Lokasi:** `fr_business_directory/models/siret_wizard.py` — `_compute_activite_principale` di `matching.etablissement`, `@api.depends('result_id.activite_principale')`
**Deskripsi:** Field `activite_principale` yang dipakai untuk translasi label Perancis adalah milik `siret.wizard.result` (level siège/perusahaan), diakses via `record.result_id.activite_principale` — BUKAN field `activite_principale` milik `matching.etablissement` itu sendiri (yang datanya per-etablissement dari `me.get('activite_principale', '')`). Artinya SEMUA etablissement dalam satu hasil pencarian yang sama akan menampilkan translasi yang SAMA (berdasar siège), terlepas kode `activite_principale` masing-masing etablissement individual.
**Dampak:** Behavior tidak berubah dari 17.0 (kode ini tidak disentuh migrasi) — ini murni klarifikasi pemahaman yang sebelumnya kurang presisi di spec lama (BR-07 backfill menyiratkan translasi berdasar kode etablissement itu sendiri). Dikoreksi di `01b_BASELINE_SPEC.md` BSL-007.
**Keputusan pemilik modul:** Tidak perlu keputusan — behavior dipertahankan, cuma dokumentasi yang diperjelas.

---

### MF-11 — `TC-FLAG-01` (backfill) tidak pernah ter-port ke test suite migrasi
**Ditemukan di:** Step 9, gap ditemukan lewat investigasi terpisah (2026-08-31) — ditutup sesi yang sama
**Tag:** `[DIWARISI-SOURCE]` — gap cakupan test, bukan bug produk baru
**Ref:** `BSL-020` (`01b_BASELINE_SPEC.md`), `F-07`/`BR-03` (backfill), `TC-FLAG-01` (`french-business-directory-17/doc-dev/backfill/test/personal_email_usage/04A_DEV_TESTING.md:66-71`)
**Lokasi:** `personal_email_usage/tests/test_fetchmail.py` (baru), `personal_email_usage/models/mail.py:75-77` (mekanisme `\Seen` yang diverifikasi)
**Deskripsi:** `09_DEV_TESTING.md` (Step 9, 2026-08-24) menyimpulkan "source module tidak pernah punya test sama sekali" berdasarkan cek `source-codebase` saja — klaim itu benar untuk `source-codebase` (branch `migration/17.0_source`), TAPI folder terpisah `french-business-directory-17` (hasil backfill 2026-08-07, tidak dipakai sebagai `source-codebase` project ini — lihat keputusan Step 1 "Clone baru bersih") justru punya dokumentasi test case lengkap (`TC-FLAG-01`, `TC-SKIP-01`, `TC-LOG-01`) yang tidak pernah ikut disurvei. `TC-FLAG-01` spesifik menguji mekanisme `\Seen` flag (`mark_read=True` → `+FLAGS \Seen` dipanggil; `mark_read=False` → tidak) yang jadi dasar bug BSL-020/MF-05 — sudah didokumentasikan benar di baseline spec, tapi belum ada bukti test otomatis untuk mekanisme flag itu sendiri (test lama yang ada cuma menguji sisi `processed_message_ids`, bukan sisi `\Seen`).
**Dampak:** Murni gap cakupan test — BSL-020/MF-05 sudah dikonfirmasi lewat pembacaan kode + Step 8 review, jadi tidak ada risiko fungsional baru. Tapi tanpa test ini, regresi di masa depan pada mekanisme `\Seen` (mis. saat modul lain ikut disentuh) tidak akan tertangkap otomatis.
**Rekomendasi:** Port `TC-FLAG-01` #01 dan #02 sebagai test otomatis.
**Keputusan pemilik modul:** ✅ Diterapkan 2026-08-31 — 2 method ditambahkan ke `test_fetchmail.py` (`test_mark_read_true_reapplies_seen_flag`, `test_mark_read_false_does_not_reapply_seen_flag`), dijalankan via `docker compose run --rm odoo_target odoo ... --test-enable --test-tags /fr_business_directory,/personal_email_usage`, hasil: 0 failed, 0 error dari 26 test (`personal_email_usage`: 12 test, naik dari 10).

---

## Cara Pakai

Lihat `migration-tool/templates/FINDINGS.md` untuk skema lengkap (perbedaan `[PERLU-KEPUTUSAN]`/`[DIWARISI-SOURCE]`/`[GAP-MIGRASI]`, dan kapan wajib update). Housekeeping murni tanpa dampak fungsional (F-04/F-06/F-09/F-10 dari backfill lama — `print()` debug, file Google verification, CSV orphan) TIDAK didaftarkan sebagai `MF-NNN` di sini karena tidak butuh keputusan apapun — sudah cukup tercatat sebagai `[MATCH]` di `01b_BASELINE_SPEC.md` §8 (BSL-011, BSL-012, BSL-022, BSL-024).
