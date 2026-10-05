# Findings — french_business_directory (migrasi 18.0 → 19.0)

**Modul:** french_business_directory (`fr_business_directory`, `personal_email_usage`)
**Migrasi:** 18.0 → 19.0
**Terakhir update:** 2026-10-05

---

## Ringkasan

| ID | Judul | Ditemukan di Step | Tag | Prioritas | Status |
|---|---|---|---|---|---|
| MF-01 | `fetchmail.server.fetch_mail()` signature berubah lagi di 19.0 (parameter `raise_exception` dihapus) | Step 1/2 | `[GAP-MIGRASI]` | Tinggi (install-jalan-tapi-cron-crash) | Rekomendasi ditentukan, diterapkan Step 6 |
| MF-02 | `res.partner.siret` (l10n_fr) dihapus, dikonsolidasi ke `company_registry` generik | Step 1/2 | `[GAP-MIGRASI]` | Tinggi (fitur utama `fr_business_directory` — tombol "Select" akan gagal) | Rekomendasi ditentukan, diterapkan Step 6 |
| MF-03 | `fetchmail.server` — arsitektur internal 19.0 dirombak total, cron TIDAK LAGI memanggil `fetch_mail()` (public) — override modul jadi TIDAK PERNAH TERPANGGIL oleh cron. Ditemukan G1 (Step 9), TIDAK terdeteksi Step 2 review statis. | Step 9 (G1) | `[GAP-MIGRASI]` | **Kritis** (fitur inti `personal_email_usage` berhenti berfungsi via cron, silent — tidak error, cuma tidak jalan) | ✅ **RESOLVED** — user menyetujui rekomendasi AI 2026-08-26, fix diterapkan (override dipindah ke `_fetch_mail()`, `connect()`→`_connect__()`), menunggu G1 rerun untuk verifikasi |
| MF-04 | Carry-over dari project 17→18: 6 test penutup gap cakupan (`05_EMAIL_GAPS.md` S-10/S-11/S-12/S-14, TC-FLAG-01 mark_read) ditulis project 17→18 tanggal 2026-08-31 (SETELAH migrasi 18→19 ini selesai 2026-08-26) — belum ada di `test_fetchmail.py` project ini. Di-port + disesuaikan ke MF-03 (`_connect__`/`_fetch_mail`). Ditemukan sekaligus: `self._cr.commit()` di `mail.py:138` memicu `DeprecationWarning` 19.0 (bukan error, belum wajib fix). | Step 10/11 (carry-over pasca-UAT) | `[GAP-MIGRASI]` (test coverage) + `[NO-SPEC]` (deprecation warning) | Rendah (test coverage sudah lengkap 30/30 pass; deprecation belum breaking) | ✅ **RESOLVED** (porting+G1 rerun) — deprecation warning dicatat, belum diperbaiki (lihat detail) |
| MF-05 | Select setelah paginasi menimpa partner yang SALAH (= RMV-02 di 19→20) | Review 2026-10-05 | `[GAP-LAMA]` | **Kritis (data)** | ✅ FIXED di rilis 19.0.1.0.1 (2026-10-05) |
| MF-06 | Paket ketahanan API & paginasi: `_logger`, 429, alamat null, panggilan API ganda, judul dialog, param limite Prev, `print()` (= RMV-03..06) | Review 2026-10-05 | `[GAP-LAMA]` | Sedang | ✅ FIXED di rilis 19.0.1.0.1 (2026-10-05) |
| MF-07 | Rilis hotfix 19.0.1.0.1: ringkasan, bukti uji, item yang dibiarkan | Review 2026-10-05 | `[HASIL-BACA]` | — | ✅ Dirilis (bebaf14 → b7a8b4a) |

---

## Detail

### MF-01 — `fetchmail.server.fetch_mail()` signature berubah lagi di 19.0
**Ditemukan di:** Step 1/2 (2026-08-26)
**Tag:** `[GAP-MIGRASI]` — genuinely muncul karena perubahan platform 19.0, bukan bug source.
**Ref:** `BSL-023` (`01b_BASELINE_SPEC.md`), `DIFF-01` (`02_DIFF_ANALYSIS.md`)
**Lokasi:** `personal_email_usage/models/mail.py:61` (signature override), `:156` (pemanggilan `super()`)
**Deskripsi:** Migrasi 17→18 sebelumnya sudah mengadaptasi override `fetch_mail()` dari signature polos (17.0) menjadi `fetch_mail(self, raise_exception=True)` (18.0), karena core 18.0 cron memanggil `fetch_mail(raise_exception=False)`. Di 19.0, core `fetchmail.server.fetch_mail()` (`enterprise19.0/odoo/addons/mail/models/fetchmail.py:237`) BALIK ke signature TANPA parameter — `def fetch_mail(self):`, dan cron caller (`_fetch_mails()`) memanggil `.fetch_mail()` polos (dikonfirmasi: `enterprise19.0/odoo/addons/mail/models/fetchmail.py`, tidak ada lagi argumen `raise_exception` di titik panggilnya).
**Dampak:** Kalau signature override tidak disesuaikan, cron scheduler akan `TypeError: fetch_mail() takes 1 positional argument but 2 were given` (atau sebaliknya, tergantung arah ketidakcocokan) — untuk SEMUA server `fetchmail.server`, bukan cuma yang IMAP. Install-jalan-tapi-cron-crash, sama kelasnya dengan temuan serupa di migrasi 17→18 modul ini.
**Rekomendasi:** Ubah signature override kembali menjadi `def fetch_mail(self):` (tanpa parameter), dan ubah pemanggilan `super(FetchmailServer, self.filtered(...)).fetch_mail()` (tanpa argumen). Intent/behavior fungsional (override total untuk IMAP, delegasi penuh utuh untuk non-IMAP) TIDAK berubah — murni adaptasi signature teknis, risiko rendah, satu opsi jelas benar (tidak ada cara migrasi valid lain). Diterapkan langsung di Step 6 tanpa menunggu approval tambahan, sesuai `USAGE_GUIDE.md` "Eksekusi Berkelanjutan di CLI" (keputusan teknis dengan opsi jelas lebih aman).
**Keputusan pemilik modul:** *(tidak diperlukan — keputusan teknis risiko rendah, AI lanjutkan sesuai rekomendasi di atas, didokumentasikan di sini untuk visibilitas)*

---

### MF-02 — `res.partner.siret` dihapus di 19.0, dikonsolidasi ke `company_registry`
**Ditemukan di:** Step 1/2 (2026-08-26)
**Tag:** `[GAP-MIGRASI]`
**Ref:** `BSL-004`, `BSL-006` (`01b_BASELINE_SPEC.md`), `DIFF-02` (`02_DIFF_ANALYSIS.md`)
**Lokasi:** `fr_business_directory/models/siret_wizard.py:260` (`siret.wizard.result.select_siret`), `:354` (`matching.etablissement.select_siret`)
**Deskripsi:** Di 18.0, `l10n_fr` menyediakan field dedicated `res.partner.siret` (Char, size 14) — dikonfirmasi `odoo18/addons/l10n_fr/models/res_partner.py:10`. Di 19.0, field ini **dihapus total** dari `l10n_fr` (dikonfirmasi grep repo-wide `enterprise19.0/odoo/addons/l10n_fr/` — nol match untuk `siret` di kode Python; satu-satunya sisa adalah view yang me-relabel field GENERIK core `company_registry` jadi tampil sebagai "Siret": `enterprise19.0/odoo/addons/l10n_fr/views/res_partner_views.xml:13` — `<field name="company_registry" string="Siret" invisible="not l10n_fr_is_french" .../>`). Field `company_registry` (Char, `compute='_compute_company_registry', store=True, readonly=False` — computed-tapi-writable, pola umum Odoo) sudah ada sejak 18.0 di core `base` untuk keperluan umum (matching VAT/registry), sekarang dipakai ulang oleh `l10n_fr` 19.0 untuk menyimpan SIRET.
**Dampak:** Kode saat ini menulis `partner.write({'siret': self.siret, ...})` di dua tempat (`select_siret()` level result dan level etablissement) — field `siret` tidak dikenal di `res.partner` 19.0, `write()` akan error (field tidak ada di model). Ini melumpuhkan fitur INTI `fr_business_directory` (tombol "Select" untuk mengisi data partner dari hasil pencarian SIRET/SIREN).
**Rekomendasi:** Ganti key `'siret'` menjadi `'company_registry'` di KEDUA `partner.write({...})` call (baris 260 dan 354). Field internal wizard (`siret.wizard.result.siret`, `matching.etablissement.siret`) TIDAK perlu diganti nama — itu field wizard sendiri, cuma KEY TARGET saat menulis ke `res.partner` yang berubah. Value/logic (assignment dari SIRET API gouv.fr) tidak berubah. Risiko rendah, satu opsi jelas benar (field generik `company_registry` adalah satu-satunya tempat SIRET tersimpan di core 19.0, dikonfirmasi lewat pembacaan langsung `l10n_fr_account/views/report_invoice.xml` yang juga memakai `company_registry` untuk menampilkan "SIRET: ..." di laporan resmi). Diterapkan langsung di Step 6.
**Keputusan pemilik modul:** *(tidak diperlukan — keputusan teknis risiko rendah, AI lanjutkan sesuai rekomendasi di atas)*

---

### MF-03 — `fetchmail.server` arsitektur 19.0 dirombak total — override modul tidak lagi terpanggil cron
**Ditemukan di:** Step 9, checkpoint G1 (2026-08-26) — TIDAK terdeteksi Step 2 (review statis hanya cek signature `fetch_mail()`, tidak cukup dalam)
**Tag:** `[GAP-MIGRASI]` — genuinely muncul karena perubahan platform 19.0. **PERLU KEPUTUSAN USER** (bukan cuma diterapkan otomatis seperti MF-01/MF-02) — lihat alasan di bawah.
**Ref:** `DIFF-01` (revisi), `09_DEV_TESTING.md` (hasil G1)
**Lokasi:** `personal_email_usage/models/mail.py` (seluruh method `fetch_mail`, baris 61-156)
**Deskripsi:** G1 (install + jalankan 23 test existing via Docker `odoo:19.0`) menemukan 7 kegagalan (1 fail, 6 error) di `personal_email_usage`, semuanya berakar pada SATU perubahan arsitektur core yang jauh lebih dalam dari perkiraan `DIFF-01` (yang hanya mencatat perubahan signature parameter):

1. **`fetchmail.server.fetch_mail()` 19.0 sekarang HANYA wrapper tipis publik** (`enterprise19.0/odoo/addons/mail/models/fetchmail.py:237-242`): `self.ensure_one().check_access('write')` lalu delegasi ke `self.sudo()._fetch_mail()` (method BARU, private, `batch_limit=50`). `fetch_mail()` WAJIB dipanggil pada singleton (`ensure_one()`) — dipanggil pada recordset kosong ATAU >1 record akan `ValueError`.
2. **Cron TIDAK LAGI memanggil `fetch_mail()` sama sekali.** `_fetch_mails()` (entry point cron, `@api.model`) sekarang langsung memanggil `records.with_context(...)._fetch_mail(**kw)` — melewati `fetch_mail()` sepenuhnya. Override modul ini ada di `fetch_mail()` (method yang TIDAK LAGI dipanggil cron) — akibatnya **logic custom (filter user internal, filter non-kontak, dedup `processed_message_ids`, kontrol `mark_read`) TIDAK PERNAH JALAN lagi lewat cron terjadwal**, walau modul tetap ter-install tanpa error apapun (silent, bukan crash — jauh lebih berbahaya karena tidak kelihatan sampai ada yang sadar email tidak terfilter lagi).
3. **`_fetch_mail()` (worker baru) punya implementasi TOTAL BERBEDA** dari loop raw-imaplib modul ini: pakai `try_lock_for_update`, wrapper class `OdooIMAP4`/`OdooPOP3` dengan method `check_unread_messages()`/`retrieve_unread_messages()` (generator)/`handled_message()`/`disconnect()`, commit per-message via `ir.cron._commit_progress()`, `batch_limit` per cron run — bukan lagi `imap_server.search()`/`.fetch()`/`.store()` mentah yang dipakai modul ini.
4. **`connect()` di-rename jadi `_connect__()`** (private, `enterprise19.0/odoo/addons/mail/models/fetchmail.py:179`) — `server.connect()` yang dipanggil modul ini (`mail.py:69`) tidak ada lagi sebagai attribute publik, konsisten dengan error test `AttributeError: <class 'odoo.orm.models.fetchmail.server'> does not have the attribute 'connect'`.

**Dampak:** Kalau tidak diperbaiki, modul akan install BERSIH (tidak ada error saat `-i`), TAPI fitur inti (filter email otomatis lewat cron) berhenti bekerja SAMA SEKALI di 19.0 — regresi silent yang cuma ketahuan dari test run (G1) atau observasi produksi (email dari user internal/non-kontak mulai diproses lagi seolah modul tidak pernah ada).

**Kenapa ini BUKAN sekadar "AI pilih & lanjut" seperti MF-01/MF-02:** MF-01/MF-02 adalah rename/adaptasi signature 1:1, satu opsi jelas benar tanpa ambiguitas. MF-03 melibatkan RESTRUKTURISASI method mana yang di-override (target override pindah dari `fetch_mail()` ke `_fetch_mail()`) dan REIMPLEMENTASI logic IMAP terhadap API internal baru (`_connect__()`, wrapper `OdooIMAP4`, generator `retrieve_unread_messages()`) — bukan lagi port mekanis, tapi rewrite substansial yang menyentuh cara kerja inti fitur. ada risiko nyata behavior tidak 100% identik (mis. titik commit per-message, interaksi dengan `try_lock_for_update`/locking multi-worker, `batch_limit` yang tidak ada di versi lama) kalau dikerjakan tergesa tanpa persetujuan eksplisit.

**Rekomendasi (opsi yang direkomendasikan AI, menunggu konfirmasi user):**
1. **Override `_fetch_mail()` (BUKAN `fetch_mail()`)** — hapus override `fetch_mail()` sepenuhnya (biarkan wrapper tipis core 19.0 berjalan apa adanya, otomatis memanggil override kita lewat `self.sudo()._fetch_mail()`).
2. Di override `_fetch_mail()` baru: pertahankan SPLIT yang sama seperti sekarang — untuk server IMAP jalankan logic custom (skip user internal/non-kontak, dedup `processed_message_ids`, kontrol `mark_read`), untuk server lain delegasikan ke `super()._fetch_mail(batch_limit=batch_limit)`.
3. Untuk implementasi IMAP custom: PALING AMAN adalah TETAP pakai raw imaplib manual seperti sekarang (bukan ikut arsitektur wrapper `OdooIMAP4` baru — itu perubahan gaya/style, bukan wajib kompatibilitas), cukup ganti `server.connect()` → `server._connect__()` (satu-satunya perubahan wajib di titik ini, method lama sudah private-renamed, bukan dihapus fungsinya).
**Risiko rekomendasi ini:** Rendah-Sedang — mempertahankan implementasi manual existing (perilaku sudah terbukti benar & diuji 23 test), cuma pindah "titik pasang" override dan satu rename method koneksi. Tidak ikut arsitektur baru sepenuhnya (tidak pakai `try_lock_for_update`/batching baru) — ini KONSISTEN dengan prinsip "port kode saja, jangan refactor demi mengikuti gaya baru kecuali wajib kompatibilitas".
**Keputusan pemilik modul:** ✅ **Disetujui 2026-08-26** — terapkan rekomendasi AI (override `_fetch_mail()`, pertahankan raw-imaplib existing, ganti `connect()`→`_connect__()`). Diterapkan di `personal_email_usage/models/mail.py`: method di-rename `fetch_mail(self)` → `_fetch_mail(self, batch_limit=50)`, `server.connect()` → `server._connect__()`, delegasi akhir jadi `super(...)._fetch_mail(batch_limit=batch_limit)` (aman dipanggil pada recordset kosong — beda dari `fetch_mail()` yang butuh `ensure_one()`). Test terkait diupdate (`test_fetch_mail_accepts_no_args` menguji `_fetch_mail()` langsung, assert `None` bukan `True`; 5 test IMAP lain di-patch `_connect__` bukan `connect`).

---

### MF-04 — Carry-over test gap dari project 17→18 (S-10/S-11/S-12/S-14/TC-FLAG-01) + deprecation warning `_cr.commit()`
**Ditemukan di:** Step 10/11 carry-over, 2026-08-31 (dikerjakan dari sesi project migrasi 17→18, direkonsiliasi ke sini)
**Tag:** `[GAP-MIGRASI]` (test coverage) + `[NO-SPEC]` (deprecation warning, informasional)
**Ref:** `french-business-directory-migration-18/doc-dev/migration_17.0_18.0/doc/10_qa/human_qa/05_EMAIL_GAPS.md` (S-10, S-11, S-12, S-14), `FINDINGS.md` project 17→18 MF-11/MF-12, [[MF-03]] (rename `_connect__`/`_fetch_mail` yang jadi acuan adaptasi)
**Lokasi:** `personal_email_usage/tests/test_fetchmail.py`

**Kronologi:** migrasi 18.0→19.0 ini (project ini) selesai penuh 2026-08-26, termasuk Step 9-11. Setelah itu, project migrasi 17.0→18.0 (repo terpisah) menutup 4 gap cakupan test yang ditemukan lewat review manual Step 10 QA (S-10 duplicate message-id, S-11 exception di satu email tidak menghentikan batch, S-12 kegagalan connect satu server tidak memblokir server lain, S-14 flag `attach`/`strip_attachments`) plus 2 test `TC-FLAG-01` (mark_read true/false) yang diporting dari backfill 17.0 — total 6 method test baru, ditulis 2026-08-31. Project 19.0 ini (selesai lebih dulu, 2026-08-26) otomatis TIDAK punya 6 test itu.

**Tindakan:** 6 method di-port ke `test_fetchmail.py` project ini, disesuaikan ke arsitektur [[MF-03]]:
- `patch.object(type(...), 'connect', ...)` → `patch.object(type(...), '_connect__', ...)` (5 test).
- `test_one_server_connect_failure_does_not_block_other_servers` (S-12): versi 17→18 memanggil `(server_a + server_b).fetch_mail()` pada recordset 2-record. Di 19.0 `fetch_mail()` adalah wrapper publik core yang mewajibkan `ensure_one()` ([[MF-03]] poin 1) — recordset multi-record akan `ValueError`. Diubah panggil `_fetch_mail()` langsung (aman dipanggil non-singleton, konsisten dengan cara core sendiri memanggilnya dari cron).
- Test lain tetap panggil `.fetch_mail()` (wrapper publik) pada 1 record — valid karena `ensure_one()` otomatis lolos.

**Verifikasi:** G1 rerun penuh (`docker compose up`, `--test-tags=/fr_business_directory,/personal_email_usage`, `image: odoo:19.0`) — hasil `odoo.tests.result: 0 failed, 0 error(s) of 30 tests when loading database 'target_db_19'` (24 test lama + 6 test baru, semua lolos).

**Temuan tambahan (bukan bug, informasional):** log G1 menunjukkan `DeprecationWarning` di `personal_email_usage/models/mail.py:138` (`self._cr.commit()`) — "Deprecated since 19.0, use self.env.cr directly". Ini WARNING, bukan error — test tetap lolos, tidak ada perilaku yang berubah. Belum diperbaiki di sesi ini (di luar scope carry-over test-gap; port kode 19.0 sendiri sudah selesai & disetujui via [[MF-03]], mengubah `self._cr` → `self.env.cr` di titik ini adalah perubahan gaya kecil, bukan wajib kompatibilitas — TIDAK dilakukan tanpa persetujuan eksplisit sesuai prinsip "jangan refactor demi mengikuti gaya baru kecuali wajib"). Catat sebagai kandidat carry-over ringan ke migrasi 19.0→20.0 berikutnya kalau `self._cr` benar-benar dihapus (bukan cuma deprecated) di versi itu.

---

### MF-05 — Select setelah paginasi menimpa partner yang SALAH (= RMV-02 di migrasi 19→20)
**Ditemukan di:** Review kode rilis 2026-10-05 (sesi review → fix → publish), setelah RMV-02 terbukti live di 20.0
**Tag:** `[GAP-LAMA]` — diwarisi dari 17.0, bukan regresi migrasi
**Prioritas:** **Kritis (korupsi data)**
**Lokasi:** `fr_business_directory/models/siret_wizard.py` — `fetch_next_page`, `fetch_previous_page`
**Deskripsi:** action yang dikembalikan Next/Prev (reload dialog dengan `res_id` wizard) tidak membawa `context` asal. Dialog hasil reload memakai `active_id` = id wizard, sehingga tombol Select menulis ke `res.partner` ber-id sama dengan id wizard (kontak lain milik orang lain), bukan kontak asal.
**Bukti:** skrip uji sebelum fix menunjukkan action tanpa `active_id` (id yang dipakai ≠ kontak asal) di 18.0 dan 19.0, dan sudah benar di 20.0. Catatan jujur: korupsi data end-to-end belum direproduksi live di 18/19 sebelum fix — klik Next pada "CARREFOUR" di kode lama justru crash `TypeError` (lihat MF-06), sehingga jalur Select-setelah-Next tidak tercapai di UI; mekanisme terbukti live di 20.0 (RMV-02) dengan kode yang identik.
**Status:** ✅ FIXED di rilis 19.0.1.0.1 — action membawa `'context': dict(self.env.context)` dan `name`. Verifikasi UI nyata (Playwright, API gouv.fr asli): Next ke halaman 2 → buka hasil → Select; hanya kontak asal yang berubah, tidak ada kontak lain ter-update.
**Keputusan pemilik modul:** Disetujui dev 2026-10-05 ("jika di 20 sudah di-fix, 18 dan 19 juga di-fix").

---

### MF-06 — Paket ketahanan API & paginasi (= RMV-03/04/05/06 di migrasi 19→20; MF-02/MF-03 (17→18))
**Ditemukan di:** Review kode rilis 2026-10-05; direproduksi dengan skrip uji sebelum fix di 18.0 dan 19.0 (kode identik)
**Tag:** `[GAP-LAMA]` (diwarisi dari 17.0)
**Prioritas:** Sedang
**Lokasi:** `fr_business_directory/models/siret_wizard.py`, `views/siret_wizard_views.xml`
**Deskripsi dan bukti sebelum fix:**
- `_logger` tidak didefinisikan → `NameError` (dialog "Oops") saat API gagal atau struktur `siege` anomali.
- HTTP 429 dari API gouv.fr tidak ditangani (jatuh ke `NameError` di atas).
- `libelle_voie: null` → `TypeError` (live: klik Next pada "CARREFOUR" crash di log server); `numero_voie` kosong tampil "None"; `_split_address` tidak aman untuk alamat/kode pos kosong.
- Next pertama memanggil API 2× (create wizard memicu `default_get` yang query ulang).
- Judul dialog menjadi "Odoo" setelah Next/Prev.
- Prev tidak mengirim `limite_matching_etablissements=100` (hasil Prev ≠ Next) dan `print()` debug tertinggal di 5 tempat (F-02, F-04 backfill).
**Status:** ✅ FIXED di rilis 19.0.1.0.1 — port dari 20.0: `_logger`, retry 429 (Retry-After, maks 2×, ≤5 dtk) + `UserError` berbahasa Inggris, helper `_street_line()` dan penjaga `_split_address`, `default_get` hanya query saat dialog dibuka + `force_save`, `name` pada action paginasi, parameter limite pada Prev, `print()` dihapus. Penyimpanan SIRET tidak diubah (field versi ini dipertahankan).
**Keputusan pemilik modul:** Disetujui dev 2026-10-05.

---

### MF-07 — Rilis hotfix 19.0.1.0.1 (2026-10-05): ringkasan, bukti uji, yang dibiarkan
**Ditemukan di:** Sesi review → fix → publish 2026-10-05 (bukan sesi migrasi)
**Tag:** `[HASIL-BACA]` — catatan rilis
**Perubahan kode (hanya `fr_business_directory`):** `siret_wizard.py`, `siret_wizard_views.xml` (`force_save` pada read-only field wizard), `__manifest__.py` → `19.0.1.0.1`. `personal_email_usage` tidak berubah (diff terhadap rilis lama kosong).
**Bukti uji (skrip `odoo shell` yang sama sebelum dan sesudah fix, DB baru, API dimock; tidak ada Python host):**
| Uji | Sebelum | Sesudah |
|---|---|---|
| Alur normal (buka, pilih SIRET) | OK | OK (tidak berubah) |
| Next/Prev membawa context asal | tidak | ya |
| API mati | `NameError _logger` | `UserError` jelas |
| HTTP 429 sekali lalu 200 | `NameError` | pulih lewat retry |
| Alamat null | `TypeError` | `''` / `'RUE X'` |
| Panggilan API saat save wizard | 1 | 0 |
| Prev memakai `limite_matching_etablissements` | tidak | ya |
| Judul dialog setelah paginasi | kosong | "Search For Companies" |
UI nyata (Playwright + API asli, kontak "CARREFOUR"): Next → halaman 2 → Select hanya mengubah kontak asal. Upgrade modul tanpa error; log server bersih setelah restart.
**Belum teruji:** suite test dari branch migrasi tidak dijalankan; lingkungan Enterprise tidak diuji; korupsi data MF-05 tidak direproduksi end-to-end sebelum fix (lihat MF-05).
**Dibiarkan (keputusan dev 2026-10-05, setelah rekomendasi + pertimbangan risiko):**
- Next/Prev no-op senyap saat `partner_name` kosong (F-03 backfill / MF-04 17→18) — dialog hanya dibuka dari partner bernama; aman.
- Soft-dependency `res.country.department` (OCA) tidak di `depends` — kode sudah menjaga lewat cek `ir.model`; aman.
- `position="replace"` pada field nama di form partner (18.0/19.0; di 20.0 sudah memakai `$0`) — berfungsi; rapuh bila modul lain mengubah field yang sama.
- `personal_email_usage`: email non-kontak yang di-skip tidak pernah ditandai processed → diunduh ulang tiap cron, dan `processed_message_ids` tumbuh tanpa batas (F-07 backfill / MF-05 17→18, keputusan dev 2026-08-24 "dipertahankan identik"). Data aman; beban naik seiring jumlah email non-kontak. Kandidat rilis tersendiri bila mailbox produksi besar.
- **[baru, dicatat saja]** loop IMAP `personal_email_usage` mengabaikan `batch_limit` dan memproses semua email UNSEEN dalam satu cron — risiko timeout hanya pada mailbox besar.
- **[baru, dicatat saja]** filter pengirim memakai `=ilike` dengan alamat mentah: `_` dan `%` bertindak sebagai wildcard (pola yang sama dipakai Odoo core); filter hanya melihat header `From` (tanpa cek SPF/DKIM), jadi pengirim yang memalsukan `From` sebuah kontak bisa masuk ke chatter kontak itu — keterbatasan desain, bergantung pada mail server untuk menolak email palsu.
- Housekeeping `personal_email_usage` (import tak terpakai, CSV security yatim, `application: True`) dan deprecation warning `self._cr.commit()`.
**Catatan audit operasional:** tidak ada data tersimpan yang perlu diperbaiki — wizard bersifat transient; perubahan hanya perilaku ke depan. Kontak yang pernah tertimpa lewat bug MF-05 (bila ada) tidak bisa dikenali otomatis dari DB.
**Hash:** staging/19.0.1.0.1 724de03 → c07f567; 19.0.1.0.1 (rilis) bebaf14 → b7a8b4a. Branch hotfix: `hotfix/19.0.1.0.1-siret-wizard`.

---

## Cara Pakai

Lihat `migration-tool/templates/FINDINGS.md` untuk penjelasan lengkap skema ID dan beda peran dari `ESCALATION`/`[GAP]`.
