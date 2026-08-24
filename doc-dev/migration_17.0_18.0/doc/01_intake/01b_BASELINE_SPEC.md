# Baseline Spec — french_business_directory (fr_business_directory + personal_email_usage)

**Step:** 1 — Intake & Scope (pelengkap `01a_MIGRATION_INTAKE.md`)
**Tujuan:** dokumentasikan APA yang modul lakukan (behavior as-is) di 17.0 — bukan bagaimana diimplementasikan.
**Tanggal:** 2026-08-24
**Sumber:** Direkonsiliasi dari `FUNCTIONAL_SPEC.md`/`ACCEPTANCE_CRITERIA.md`/`FINDINGS.md` lama di `french-business-directory-17/doc-dev/backfill/` (hasil backfill 2026-08-07, branch `origin/17.0`) + cross-check baris-per-baris ke kode aktual di `source-codebase` (branch `migration/17.0_source`, dari `origin/staging/17.0`)

> Repo ini berisi DUA addon independen secara fungsional (`fr_business_directory`, `personal_email_usage`) — dipisah jadi Bagian A/B di bawah, penomoran `BSL-NNN` kontinu lintas keduanya.
>
> **Hasil cross-check:** semua klaim spec lama (BR-01..BR-08 tiap addon) dan semua temuan (F-01..F-11) COCOK dengan kode di `source-codebase` — tidak ditemukan penyimpangan antara branch `17.0` (dipakai backfill) dan `staging/17.0` (dipakai project migrasi ini) untuk kedua addon.

---

## Ringkasan untuk Review — Perlu Konfirmasi User

Tally provenance: 16 klaim `[MATCH]` (BR-01..BR-08 × 2 addon), 0 `[GAP]`, 0 `[NO-SPEC]` murni (semua berbasis spec lama yang sudah tervalidasi).

1. **BSL-006 `[MATCH]`** — Pengisian `country_department_id`/`state_id`/`country_id` partner BERSYARAT pada addon eksternal opsional (`res.country.department`) yang tidak terinstall di environment manapun yang bisa dicek (lihat `01a_MIGRATION_INTAKE.md` §2). Kalau addon itu tidak ada, field-field itu memang tidak pernah diisi — ini BUKAN bug, harus dipertahankan identik di 18.0.
2. **BSL-008 `[MATCH]` (F-01)** — `_logger` dipakai di `siret_wizard.py` tapi TIDAK PERNAH diimpor. Kalau respons API gouv.fr kehilangan `nom_complet`/`siret`, atau request API gagal — kode akan crash `NameError` alih-alih log yang berguna. **Bug pre-existing, WAJIB dipertahankan identik** (tidak diperbaiki) kecuali dev eksplisit minta lain.
3. **BSL-009 `[MATCH]` (F-02)** — parameter `limite_matching_etablissements` hilang di `fetch_previous_page` (ada di `fetch_next_page`) — data matching_etablissements bisa beda antara Next vs Prev untuk halaman yang sama. Pre-existing, dipertahankan.
4. **BSL-020 `[MATCH]` (F-07, prioritas TINGGI)** — email yang di-skip (dari user internal/bukan kontak) TIDAK PERNAH ditandai `processed_ids` → dengan `mark_read=False` (default), email itu di-fetch ULANG SELAMANYA tiap cron. Bug performa nyata, pre-existing, **dipertahankan identik** di 18.0 kecuali dev eksplisit minta diperbaiki.
5. **BSL-021 `[MATCH]` (F-08)** — log ringkasan "succeeded" dihitung `count - failed` padahal seharusnya `count` polos (beda semantik dari core Odoo) — angka log menyesatkan. Pre-existing, dipertahankan.
6. **BSL-023 `[MATCH]` (F-11)** — `fetch_mail()` di-override TOTAL untuk server IMAP, TIDAK memanggil `super()` — chain `_inherit` modul lain terputus untuk IMAP. SENGAJA (bukan bug), tapi WAJIB dicek ulang di Step 2 apakah signature/behavior `fetch_mail()` core berubah di 18.0 (bisa mempengaruhi cara override ini harus ditulis ulang demi kompatibilitas, walau intent-nya tetap sama).
7. Housekeeping tidak berdampak fungsional (boleh dibawa apa adanya, tidak wajib diperbaiki/dihapus kecuali dev minta): `print()` debug tertinggal (F-04), file `googleaeed8a7b9ec156e7.html` di kedua addon (F-06/F-10), `ir.model.access.csv` orphan di `personal_email_usage` yang tidak pernah di-load (F-09).

Semua BR/F lain — cocok, low-risk, lihat detail di Bagian A/B.

---

## Provenance Tag

Semua klaim di dokumen ini bertag `[MATCH]` dengan rujukan `(ref: BR-NN)` atau `(ref: F-NN)` ke `french-business-directory-17/doc-dev/backfill/spec/{addon}/01A_FUNCTIONAL_SPEC.md` dan `FINDINGS.md` — dikonfirmasi cocok dengan kode `source-codebase` lewat pembacaan langsung baris-per-baris (lihat rujukan lokasi kode tiap klaim).

---

# Bagian A — `fr_business_directory`

## 1. Tujuan Modul

Menambahkan tombol pencarian cepat ("Business Directory") di form kontak Odoo (khusus kontak berjenis perusahaan), yang membuka wizard untuk mencari data resmi perusahaan Perancis (SIRET/SIREN) lewat API publik `recherche-entreprises.api.gouv.fr`, lalu mengisi field kontak (alamat, kode pos, SIRET, koordinat, dst) dari hasil yang dipilih user. `(ref: BR-latar belakang)`

## 2. Model & Tanggung Jawab

| Model | Tanggung Jawab |
|---|---|
| `res.partner` (`_inherit`) | Tambah field `social_reason`; method `siret_wizard()` untuk membuka wizard |
| `siret.wizard` (Transient) | Wizard utama — fetch hasil pencarian, paginasi |
| `siret.wizard.result` (Transient) | Satu baris hasil pencarian (satu nama perusahaan) |
| `matching.etablissement` (Transient) | Sub-baris etablissement/cabang untuk satu hasil (kalau perusahaan punya >1 lokasi) |

## 3. Field dengan Makna Bisnis

### `res.partner`
- `social_reason` (Char, `tracking=True`) — nama badan usaha resmi, terpisah dari `name` (nama tampilan)

### `siret.wizard`
- `partner_name`, `page_number` (default 1), `total_pages`, `result_count` (computed), `result_ids` (One2many ke `siret.wizard.result`)

### `siret.wizard.result` / `matching.etablissement`
- Data mentah dari API: `siret`, `social_reason`, alamat (`street`/`street2`/`city`/`post_code`/`department`/`region`), koordinat (`latitude`/`longitude`), tanggal (`date_creation`/`date_debut_activite`/`date_fermeture`), `etat_administratif` (+ `etat_administratif_display` computed di level etablissement), `activite_principale` (+ `computed_activite_principale` computed, hanya di level etablissement)

## 4. Business Workflow / State Transition

### Pencarian & Seleksi SIRET
- `[BSL-001]` `[MATCH]` (ref: BR-01) Tombol "Business Directory" (`siret_wizard()`) di form partner hanya muncul untuk kontak berjenis Company (`invisible="is_company != True"`). **Lokasi:** `views/partner.xml:13`
- `[BSL-002]` `[MATCH]` (ref: BR-02) `SiretWizard.default_get()` otomatis fetch halaman 1 (`per_page=25`, `limite_matching_etablissements=100`) dari `partner.name` begitu wizard dibuka. **Lokasi:** `models/siret_wizard.py:21-34`
- `[BSL-003]` `[MATCH]` (ref: BR-03) Paginasi wrap-around: Next di halaman terakhir → kembali ke halaman 1; Prev di halaman 1 → lompat ke halaman terakhir. Tiap navigasi `unlink()` hasil lama dulu sebelum fetch baru. **Lokasi:** `models/siret_wizard.py:131-205`
- `[BSL-004]` `[MATCH]` (ref: BR-04) Aksi "Select" (level result ATAU level etablissement) menulis SELALU overwrite ke `res.partner` yang sama (dari `active_id` context): `name`, `siret`, `street`(+`street2` di level result), `social_reason`, `zip`, `city`, `partner_latitude`, `partner_longitude` — tanpa merge/cek field existing, ada dialog konfirmasi UI (`confirm="Are you sure want to overwrite the Data?"`). **Lokasi:** `models/siret_wizard.py:250-285` (result), `:340-377` (etablissement)
- `[BSL-005]` `[MATCH]` (ref: BR-06) `etat_administratif` API (`'A'`=aktif) diterjemahkan ke label Perancis `'en activité'`/`'fermé le'`; level etablissement ada compute tambahan `etat_administratif_display` (gabung label+tanggal tutup). Ditampilkan widget `badge` (hijau/merah). **Lokasi:** `models/siret_wizard.py:379-385`, `views/siret_wizard_views.xml:57-60`

## 5. Server-Side Logic dengan Side Effect

- `[BSL-006]` `[MATCH]` (ref: BR-05) **write (select_siret):** sebelum mengisi `country_department_id`/`state_id`/`country_id`, kode cek `self.env['ir.model'].search([('model','=','res.country.department')])`. Kalau model ADA (dari addon eksternal di luar `depends`), field itu diisi dari lookup `res.country.department` (by kode departemen). Kalau TIDAK ada, field-field itu SAMA SEKALI tidak disentuh (bukan error). **Lokasi:** `models/siret_wizard.py:254-267` (result), `:346-364` (etablissement)
- `[BSL-007]` `[MATCH]` (ref: BR-07) `_compute_activite_principale` (`matching.etablissement`) menerjemahkan HURUF TERAKHIR kode `activite_principale` ke label Perancis untuk 4 kasus (`A`,`B`,`Z`,`D`) — kode lain ditampilkan mentah, tidak lengkap by design/oversight (tidak ada indikasi disengaja). **Koreksi (Step 9, MF-10):** sumber kode yang diterjemahkan adalah `result_id.activite_principale` (field level siège/`siret.wizard.result`, `@api.depends('result_id.activite_principale')`), BUKAN field `activite_principale` milik `matching.etablissement` itu sendiri — semua etablissement dalam satu hasil pencarian yang sama menampilkan translasi identik berdasar siège, terlepas kode individual masing-masing etablissement. **Lokasi:** `models/siret_wizard.py:310-324`

## 6. Client-Side Behavior (Views)

- Form `res.partner`: button `siret_wizard` (stat button, icon `fa-search`) menggantikan posisi field `name` untuk company — replace via `<field id="company" name="name" position="replace">`.
- Wizard `siret.wizard`: form dialog (`target: new`), tabel hasil dengan badge status.
- Tidak ada komponen Owl/JS custom (tidak ada `static/src/`, `assets: {}` kosong di manifest).

## 7. Dependency Eksternal

### Eksplisit (manifest)
- `depends: ['base', 'contacts', 'l10n_fr']`

### Implisit/Inferred
- `[BSL-006]` — soft-dependency ke addon eksternal (belum dikonfirmasi mana persis, kemungkinan OCA `l10n_fr_department`) yang menyediakan model `res.country.department` + field `country_department_id` pada `res.partner`.
- API eksternal: `https://recherche-entreprises.api.gouv.fr` (HTTP publik, tanpa API key, lewat `requests`).

## 8. Quirk / Behavior Non-Obvious (WAJIB dipertahankan, bukan diperbaiki)

- `[BSL-008]` `[MATCH]` (ref: F-01) `_logger` dipakai (`siret_wizard.py:113,128`) tapi TIDAK PERNAH diimpor/didefinisikan (tidak ada `import logging`). Terpicu kalau `siege` adalah dict valid tapi `nom_complet`/`siret` kosong (baris 113), atau `requests.RequestException` (baris 128, network/API error) — Python akan raise `NameError` yang menutupi akar masalah (API gouv.fr bermasalah). **Tambahan:** kalau `siege` BUKAN dict sama sekali, result itu di-skip TANPA log apapun (silent data loss, beda dari NameError di atas tapi root cause sama).
- `[BSL-009]` `[MATCH]` (ref: F-02) `fetch_previous_page` (kedua cabang, baris 177 & 195) TIDAK menyertakan `&limite_matching_etablissements=100` di URL API, padahal `fetch_next_page` (baris 140) menyertakannya — kemungkinan copy-paste tidak lengkap, bukan by-design.
- `[BSL-010]` `[MATCH]` (ref: F-03) `fetch_next_page`/`fetch_previous_page`: kalau `self.partner_name` falsy di tengah kondisi navigasi valid, method return `None` implisit (tidak ada `else`/pesan) — tombol terlihat tidak berfungsi tanpa feedback.
- `[BSL-011]` `[MATCH]` (ref: F-04) Lima `print(api_url)`/`print(self.page_count)` debug tertinggal (`siret_wizard.py:141,157,178,192,196`) — noise stdout, tidak fungsional.
- `[BSL-012]` `[MATCH]` (ref: F-06) File `googleaeed8a7b9ec156e7.html` (verifikasi Google Search Console, tidak terkait Odoo) ikut ter-bundle di root addon — housekeeping, tidak dibaca Odoo.
- `[BSL-013]` `[MATCH]` (ref: BR-08) `social_reason` (`tracking=True`) — perubahan tercatat di chatter `res.partner` seperti field ter-tracking lain. **Lokasi:** `models/partner.py:6`
- `[BSL-014]` `[MATCH]` Method `siret_wizard()` di `res.partner` adalah method BARU (bukan override) — tidak bentrok dengan method core `base`/`contacts` manapun (diverifikasi: tidak ada `siret_wizard` di source Odoo core).

---

# Bagian B — `personal_email_usage`

## 1. Tujuan Modul

Menambahkan kontrol lanjutan pada proses fetch email masuk (IMAP) `fetchmail.server`: (1) pilihan menandai email yang di-fetch sebagai sudah/belum dibaca di server, (2) skip email dari user internal Odoo, (3) hanya proses email dari pengirim yang sudah jadi kontak (`res.partner`). Modul TIDAK menyentuh sisi outgoing email sama sekali.

## 2. Model & Tanggung Jawab

| Model | Tanggung Jawab |
|---|---|
| `fetchmail.server` (`_inherit`) | Tambah field kontrol (`mark_read`, `processed_message_ids`); override total `fetch_mail()` untuk server IMAP |
| `mail.thread` (`_inherit`, AbstractModel) | Override `message_new()` — blokir auto-create `res.partner` baru dari email masuk |

## 3. Field dengan Makna Bisnis

### `fetchmail.server`
- `mark_read` (Boolean, default `False`) — tandai email fetched sebagai read/unread di server
- `processed_message_ids` (Text) — daftar `Message-ID` yang sudah diproses, disimpan sebagai string dipisah koma, untuk dedup

## 4. Business Workflow / State Transition

- `[BSL-015]` `[MATCH]` (ref: BR-02) `fetch_mail()` di-override TOTAL untuk `server_type == 'imap'` (search `(UNSEEN)`, fetch, parse, route) — TIDAK memanggil `super()` untuk grup ini. Server BUKAN IMAP tetap didelegasikan penuh ke `super().fetch_mail()`. **Lokasi:** `models/mail.py:61-156`
- `[BSL-016]` `[MATCH]` (ref: BR-04) Skip (tanpa proses) kalau pengirim (`from_email`) cocok `res.users` dengan `share=False` (user internal aktif). **Lokasi:** `models/mail.py:87-96`
- `[BSL-017]` `[MATCH]` (ref: BR-05) Kalau bukan user internal, cek balik apakah pengirim ada di `res.partner` (`email =ilike from_email`) — kalau tidak ketemu, JUGA di-skip. **Lokasi:** `models/mail.py:98-107`
- `[BSL-018]` `[MATCH]` (ref: BR-06) Email yang lolos filter diteruskan ke `mail.thread.message_process()` standar dengan context `fetchmail_cron_running=True, default_fetchmail_server_id=server.id`. **Lokasi:** `models/mail.py:109-129`
- `[BSL-019]` `[MATCH]` (ref: BR-07) `message_new()` di-extend: kalau model target `res.partner`, HANYA kembalikan partner existing (match by email); kalau tidak ketemu, kembalikan `False` (TIDAK PERNAH buat `res.partner` baru dari email masuk). Model lain → delegasi penuh ke `super()`. **Lokasi:** `models/mail.py:22-43`

## 5. Server-Side Logic dengan Side Effect

- `[BSL-020]` `[MATCH]` (ref: F-07, **prioritas TINGGI**) Tiap email yang di-`fetch()` langsung di-un-seen (`-FLAGS \Seen`, baris 75) TANPA MELIHAT apakah nanti akan diproses/skip; flag `+FLAGS \Seen` HANYA ditambah balik kalau `mark_read=True`. `message_id` HANYA masuk `processed_ids` di jalur SUKSES — dua jalur skip (user internal, bukan kontak) TIDAK PERNAH menambahkannya. **Efek:** dengan `mark_read=False` (default), email yang di-skip tetap UNSEEN dan tidak tercatat processed → search `(UNSEEN)` cron berikutnya menemukan email SAMA lagi → re-fetch SELAMANYA untuk tiap email dari user internal/non-kontak. **Beda dari core Odoo** (`mail/models/fetchmail.py`) yang selalu `+FLAGS \Seen` tanpa syarat setelah fetch (berhasil/gagal) — modul ini sengaja jadi kondisional (`mark_read`) untuk fitur "biarkan unread", tapi jalur skip tidak ikut disesuaikan. **Lokasi:** `models/mail.py:64,75-77,93-96,98-107,120-121`
- `[BSL-021]` `[MATCH]` (ref: F-08) Log ringkasan per siklus fetch menghitung "succeeded" sebagai `count - failed` (baris 139), padahal `count` HANYA increment di jalur sukses (beda semantik dari core Odoo, di mana `count` increment tanpa syarat) — angka "succeeded" di log SELALU under-count, bisa negatif. **Lokasi:** `models/mail.py:122-124,138-141`

## 6. Client-Side Behavior (Views)

- Field `mark_read` ditambahkan di form `fetchmail.server` (Technical Settings, `groups="base.group_no_one"`), posisi setelah field `attach`. Tidak ada JS/Owl custom.

## 7. Dependency Eksternal

### Eksplisit (manifest)
- `depends: ['base', 'mail']`

### Implisit/Inferred
- Tidak ada — semua model yang di-`_inherit` (`fetchmail.server`, `mail.thread`) berasal dari `mail` yang sudah dideklarasikan.

## 8. Quirk / Behavior Non-Obvious (WAJIB dipertahankan, bukan diperbaiki)

- `[BSL-022]` `[MATCH]` (ref: F-09) `security/ir.model.access.csv` mereferensikan model `personal_email_usage.personal_email_usage` yang TIDAK ADA di kode — tapi baris `data` yang memuatnya SUDAH dikomentari di manifest, jadi file ini tidak pernah benar-benar dimuat, tidak ada dampak fungsional. Boleh dibawa apa adanya ke 18.0 (dead file) atau dihapus — tidak mengubah behavior baik cara.
- `[BSL-023]` `[MATCH]` (ref: F-11) Override `fetch_mail()` TIDAK memanggil `super()` untuk server IMAP — SENGAJA (sesuai tujuan modul), tapi memutus chain `_inherit` modul lain (mis. addon Enterprise `google_gmail`/`microsoft_outlook` kalau ada) untuk path IMAP. **Perlu dicek ulang di Step 2:** apakah signature/urutan operasi `fetch_mail()` core berubah di 18.0 (native-target) yang mempengaruhi cara override total ini harus ditulis ulang demi kompatibilitas — intent (total override untuk IMAP) tetap dipertahankan, implementasi teknisnya yang mungkin perlu menyesuaikan API core baru.
- `[BSL-024]` `[MATCH]` (ref: F-10) File `googleaeed8a7b9ec156e7.html` duplikat dari `fr_business_directory` (lihat BSL-012) — housekeeping, tidak fungsional.

---

## Cara Pakai

ID `BSL-NNN` di atas dipakai sebagai rujukan wajib di `03_MIGRATION_SPEC.md` (strategi teknis) dan `05a_MIGRATION_ACCEPTANCE_CRITERIA.md` (tiap AC sebut `BSL-NNN` yang diverifikasi). Bug pre-existing (BSL-008, BSL-009, BSL-010, BSL-020, BSL-021) **tidak diperbaiki** di migrasi ini kecuali dev eksplisit meminta lain — dipertahankan identik sesuai aturan `CLAUDE.md` "Source of Truth & Forbidden Actions".
