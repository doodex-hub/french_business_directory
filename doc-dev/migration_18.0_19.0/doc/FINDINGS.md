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

## Cara Pakai

Lihat `migration-tool/templates/FINDINGS.md` untuk penjelasan lengkap skema ID dan beda peran dari `ESCALATION`/`[GAP]`.
