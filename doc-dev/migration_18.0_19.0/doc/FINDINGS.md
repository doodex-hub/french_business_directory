# Findings — french_business_directory (migrasi 18.0 → 19.0)

**Modul:** french_business_directory (`fr_business_directory`, `personal_email_usage`)
**Migrasi:** 18.0 → 19.0
**Terakhir update:** 2026-08-26

---

## Ringkasan

| ID | Judul | Ditemukan di Step | Tag | Prioritas | Status |
|---|---|---|---|---|---|
| MF-01 | `fetchmail.server.fetch_mail()` signature berubah lagi di 19.0 (parameter `raise_exception` dihapus) | Step 1/2 | `[GAP-MIGRASI]` | Tinggi (install-jalan-tapi-cron-crash) | Rekomendasi ditentukan, diterapkan Step 6 |
| MF-02 | `res.partner.siret` (l10n_fr) dihapus, dikonsolidasi ke `company_registry` generik | Step 1/2 | `[GAP-MIGRASI]` | Tinggi (fitur utama `fr_business_directory` — tombol "Select" akan gagal) | Rekomendasi ditentukan, diterapkan Step 6 |
| MF-03 | `fetchmail.server` — arsitektur internal 19.0 dirombak total, cron TIDAK LAGI memanggil `fetch_mail()` (public) — override modul jadi TIDAK PERNAH TERPANGGIL oleh cron. Ditemukan G1 (Step 9), TIDAK terdeteksi Step 2 review statis. | Step 9 (G1) | `[GAP-MIGRASI]`, **PERLU KEPUTUSAN USER** | **Kritis** (fitur inti `personal_email_usage` berhenti berfungsi via cron, silent — tidak error, cuma tidak jalan) | ⏳ **Menunggu keputusan user** — lihat ESCALATION di bawah |

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
**Keputusan pemilik modul:** *(menunggu — lihat pertanyaan yang diajukan AI di respons chat)*

---

## Cara Pakai

Lihat `migration-tool/templates/FINDINGS.md` untuk penjelasan lengkap skema ID dan beda peran dari `ESCALATION`/`[GAP]`.
