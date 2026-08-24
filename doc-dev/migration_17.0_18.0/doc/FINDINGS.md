# Findings — french_business_directory (migrasi 17.0 → 18.0)

**Modul:** french_business_directory (`fr_business_directory` + `personal_email_usage`)
**Migrasi:** 17.0 → 18.0
**Terakhir update:** 2026-08-24

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
| MF-07 | Override `fetch_mail()` tanpa `super()` untuk IMAP — perlu cek ulang kompatibilitas core 18.0 | 1 | `[GAP-MIGRASI]` (potensial) | Sedang | 🔴 Terbuka — cek di Step 2 |

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

### MF-07 — Override `fetch_mail()` tanpa `super()` untuk IMAP — perlu cek ulang kompatibilitas core 18.0
**Ditemukan di:** Step 1 (2026-08-24), diwarisi backfill 2026-08-07 (`F-11`), TAPI genuinely bisa jadi isu migrasi baru
**Tag:** `[GAP-MIGRASI]` (potensial — perlu dikonfirmasi di Step 2)
**Ref:** `BSL-023`, `F-11`
**Lokasi:** `personal_email_usage/models/mail.py:61-156`
**Deskripsi:** `fetch_mail()` di-override total untuk server IMAP (tanpa `super()`) — SENGAJA, intent tetap dipertahankan. TAPI implementasi ini menyalin ulang seluruh logic internal `fetchmail.server.fetch_mail()` core Odoo 17.0 (search/fetch/flag/route/commit) — kalau core 18.0 (`native-target`) mengubah signature/urutan operasi/API method ini, override ini bisa jadi tidak kompatibel meski intent tidak berubah.
**Rekomendasi:** Step 2 (Diff Analysis) WAJIB diff `mail/models/fetchmail.py` antara `native-source` (17.0) dan `native-target` (18.0) secara spesifik untuk method `fetch_mail`/`connect`/`message_process` yang dipakai override ini.
**Keputusan pemilik modul:** *(kosong — akan diisi setelah Step 2)*

---

## Cara Pakai

Lihat `migration-tool/templates/FINDINGS.md` untuk skema lengkap (perbedaan `[PERLU-KEPUTUSAN]`/`[DIWARISI-SOURCE]`/`[GAP-MIGRASI]`, dan kapan wajib update). Housekeeping murni tanpa dampak fungsional (F-04/F-06/F-09/F-10 dari backfill lama — `print()` debug, file Google verification, CSV orphan) TIDAK didaftarkan sebagai `MF-NNN` di sini karena tidak butuh keputusan apapun — sudah cukup tercatat sebagai `[MATCH]` di `01b_BASELINE_SPEC.md` §8 (BSL-011, BSL-012, BSL-022, BSL-024).
