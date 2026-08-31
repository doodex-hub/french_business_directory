# Functional Spec — fr_business_directory

**Module:** `fr_business_directory`
**Odoo Version:** 17.0
**Depends:** `base`, `contacts`, `l10n_fr`
**Last Updated:** 2026-08-07
**Status:** Backfill retroaktif — dibaca dari kode existing, bukan requirement baru
**Provenance:** lihat `doc-dev-backfill/templates/CLAUDE_TEMPLATE.md` §Provenance Tag

---

## Ringkasan untuk Review — Perlu Konfirmasi User

1. **F-01 (Tinggi):** `_logger` dipakai di `siret_wizard.py` tapi tidak pernah diimpor — jalur error
   API eksternal akan `NameError` bukan log yang berguna. Lihat `FINDINGS.md`.
2. **F-02 (Sedang):** parameter `limite_matching_etablissements` hilang di `fetch_previous_page` —
   data bisa beda antara Next vs Prev untuk halaman yang sama.
3. **F-05 (Sedang):** fitur pengisian departemen/state/country partner diam-diam tidak jalan kalau
   model `res.country.department` (addon di luar `depends`) tidak terinstall — tidak
   terdokumentasi sebagai soft-dependency.

---

## Latar Belakang & Tujuan

Modul menambahkan tombol pencarian cepat ("Business Directory") di form kontak Odoo (khusus
kontak berjenis perusahaan), yang membuka wizard untuk mencari data resmi perusahaan Perancis
(SIRET/SIREN) lewat API publik `recherche-entreprises.api.gouv.fr`, lalu mengisi field kontak
(alamat, kode pos, SIRET, koordinat, dst) dari hasil yang dipilih user. `[HASIL-BACA]`

---

## Scope

### Yang Termasuk (disimpulkan dari kode)

- Tombol "Business Directory" di form `res.partner` (hanya tampil kalau `is_company = True`). `[HASIL-BACA]`
- Wizard pencarian (`siret.wizard`) yang otomatis fetch hasil halaman 1 begitu dibuka, berdasar
  `partner.name` sebagai query. `[HASIL-BACA]`
- Paginasi hasil pencarian (Next/Prev) dengan wrap-around. `[HASIL-BACA]`
- Tabel hasil pencarian (`siret.wizard.result`) + sub-tabel "matching establishments"
  (`matching.etablissement`) untuk kasus satu nama perusahaan punya beberapa lokasi/etablissement. `[HASIL-BACA]`
- Aksi "Select" pada satu kandidat hasil → menulis data kandidat itu ke `res.partner` (overwrite,
  ada dialog konfirmasi di UI: `confirm="Are you sure want to overwrite the Data?"`). `[HASIL-BACA]`
- Field baru `social_reason` (Char, `tracking=True`) pada `res.partner` — nama badan usaha resmi,
  terpisah dari `name` (nama tampilan). `[HASIL-BACA]`

### Yang Tidak Termasuk

Tidak ada indikasi eksplisit dari kode soal scope yang sengaja dikeluarkan (tidak ada
comment/TODO yang menyebutkan pembatasan scope).

---

## User Stories (rekonstruksi)

> Ditulis dari sudut pandang kode, bukan wawancara user asli — beri label rekonstruksi.

### US-01 — Cari data resmi perusahaan dari nama kontak
Sebagai user Odoo yang mengelola kontak perusahaan, saya ingin mencari data resmi (SIRET, alamat,
status administratif) perusahaan itu langsung dari form kontak, tanpa harus membuka website
pemerintah Perancis secara manual, lalu mengisi field kontak dari hasil pencarian itu dengan satu
klik. `[HASIL-BACA]`

### US-02 — Navigasi hasil pencarian yang banyak
Sebagai user yang mencari nama perusahaan yang umum (banyak hasil), saya ingin bisa berpindah
halaman hasil pencarian (Next/Prev) tanpa membuka wizard baru. `[HASIL-BACA]`

### US-03 — Pilih etablissement yang tepat untuk perusahaan multi-lokasi
Sebagai user yang mencari perusahaan dengan beberapa cabang/etablissement, saya ingin melihat
semua etablissement yang cocok dan memilih salah satu (bukan cuma siège/kantor pusat) untuk mengisi
data kontak. `[HASIL-BACA]`

---

## Business Rules

> **Cek wajib tabrakan nama method vs Odoo core (dilakukan Step 01):** `ResPartner.siret_wizard()`
> adalah nama method BARU (bukan override) pada model `_inherit`-ed `res.partner` — tidak bentrok
> dengan method core manapun (dikonfirmasi: tidak ada `siret_wizard` di source Odoo core `base`/
> `contacts`). Aman.

### BR-01 — Tombol Business Directory hanya untuk kontak perusahaan
Tombol "Business Directory" (`siret_wizard()`) di form partner hanya `invisible="is_company !=
True"` — hanya muncul untuk kontak berjenis Company, tidak untuk kontak Individual. `[HASIL-BACA]`
**Lokasi kode:** `views/partner.xml:13`

### BR-02 — Auto-fetch halaman 1 saat wizard dibuka
`SiretWizard.default_get()` otomatis memanggil API pencarian (`per_page=25`,
`limite_matching_etablissements=100`) menggunakan `partner.name` (dari `active_id` di context) begitu
wizard dibuka — user tidak perlu mengetik ulang nama pencarian. `[HASIL-BACA]`
**Lokasi kode:** `models/siret_wizard.py:21-34`

### BR-03 — Paginasi wrap-around
`fetch_next_page()`: kalau sudah di halaman terakhir (`page_number >= total_pages`), klik Next
kembali ke halaman 1 (bukan disabled/no-op). `fetch_previous_page()`: kalau sudah di halaman 1,
klik Prev lompat ke halaman terakhir (`total_pages`). Tiap navigasi menghapus (`unlink()`) hasil
lama sebelum fetch hasil halaman baru. `[HASIL-BACA]` — **lihat F-02 di `FINDINGS.md`: parameter
query API tidak konsisten antara Next dan Prev.**
**Lokasi kode:** `models/siret_wizard.py:131-205`

### BR-04 — Select hasil pencarian menulis (overwrite) data ke partner
Baik dari level "hasil" (`siret.wizard.result.select_siret()`) maupun level "etablissement" spesifik
(`matching.etablissement.select_siret()`), aksi Select menulis ke `res.partner` yang sama
(`active_id` dari context): `name`, `siret`, `street`(+`street2` di level result), `social_reason`,
`zip`, `city`, `partner_latitude`, `partner_longitude` — SELALU overwrite tanpa merge/cek field
existing. `[HASIL-BACA]`
**Lokasi kode:** `models/siret_wizard.py:250-285` (result), `:340-377` (etablissement)

### BR-05 — Pengisian department/state/country BERSYARAT pada ketersediaan model eksternal
Sebelum mengisi `country_department_id`/`state_id`/`country_id`, kode cek dulu
`self.env['ir.model'].search([('model', '=', 'res.country.department')])`. Kalau model itu ADA
(disediakan addon di luar `depends` resmi modul ini), field-field itu ikut diisi dari hasil lookup
`res.country.department` berdasar kode departemen (`department`/2-digit awal `code_postal`). Kalau
model TIDAK ada, field-field itu SAMA SEKALI tidak disentuh (bukan error). `[PERLU-KEPUTUSAN]` —
lihat F-05 di `FINDINGS.md`.
**Lokasi kode:** `models/siret_wizard.py:254-267` (result), `:346-364` (etablissement)

### BR-06 — Status administratif ditampilkan dengan badge + tanggal tutup
`etat_administratif` API (`'A'` = aktif) diterjemahkan ke label Perancis `'en activité'`/`'fermé
le'`. Untuk level etablissement, ada field compute tambahan `etat_administratif_display` yang
menggabungkan label + tanggal tutup (`date_fermeture`) kalau statusnya tertutup. Ditampilkan dengan
widget `badge` (hijau kalau aktif, merah kalau tidak) di tabel hasil. `[HASIL-BACA]`
**Lokasi kode:** `models/siret_wizard.py:379-385`, `views/siret_wizard_views.xml:57-60`

### BR-07 — Kode aktivitas utama (NAF/APE) diterjemahkan sebagian ke label Perancis
`_compute_activite_principale` pada `matching.etablissement` menerjemahkan HURUF TERAKHIR kode
`activite_principale` ke label deskriptif Perancis untuk 4 kasus (`A`, `B`, `Z`, `D`) — kode lain
ditampilkan mentah (kode asli tanpa terjemahan). `[HASIL-BACA]` — cakupan terjemahan tidak lengkap
untuk seluruh kemungkinan kode NAF/APE (tidak ada indikasi ini disengaja/bug, kemungkinan cuma
belum diperluas).
**Lokasi kode:** `models/siret_wizard.py:310-324`

### BR-08 — Field `social_reason` di-tracking di chatter partner
`social_reason` (`tracking=True`) — perubahan nilainya akan tercatat di log chatter `res.partner`
seperti field ter-tracking Odoo lainnya. `[HASIL-BACA]`
**Lokasi kode:** `models/partner.py:6`

---
