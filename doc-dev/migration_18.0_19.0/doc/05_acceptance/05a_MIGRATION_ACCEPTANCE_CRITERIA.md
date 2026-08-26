# Migration Acceptance Criteria — french_business_directory

**Step:** 5 — Acceptance Criteria & Test Plan
**Ref:** `01_intake/01b_BASELINE_SPEC.md` dan kode 18.0 yang berjalan — bukan `03_spec/03_MIGRATION_SPEC.md`
**Tanggal:** 2026-08-26

> AC ini identik dengan `doc-dev/migration_17.0_18.0/doc/05_acceptance/05a_MIGRATION_ACCEPTANCE_CRITERIA.md` (ID dipertahankan sama untuk traceability lintas project), KECUALI 2 perubahan wajib karena breaking change 19.0: **AC-04-01** (field target `company_registry`, bukan lagi `siret`) dan **AC-08-03** (signature `fetch_mail()` TANPA parameter, bukan lagi `raise_exception=...`).

---

# Bagian A — `fr_business_directory`

## AC-01 — Tombol & Buka Wizard

**AC-01-01** (verifies `BSL-001`)
Given kontak dengan `is_company = True`
When form partner dibuka
Then tombol "Business Directory" tampil di header; kontak Individual (`is_company = False`) tidak menampilkan tombol ini

## AC-02 — Auto-Fetch Saat Wizard Dibuka

**AC-02-01** (verifies `BSL-002`)
Given partner company bernama X, tombol "Business Directory" diklik
When wizard `siret.wizard` terbuka
Then request otomatis terkirim ke `recherche-entreprises.api.gouv.fr` dengan `q=X&page=1&per_page=25&limite_matching_etablissements=100`, hasil halaman 1 langsung terisi tanpa input tambahan

## AC-03 — Paginasi

**AC-03-01** (verifies `BSL-003`)
Given wizard di halaman terakhir
When tombol "Next" diklik
Then kembali ke halaman 1 (wrap-around), hasil lama di-unlink sebelum hasil baru muncul

**AC-03-02** (verifies `BSL-003`)
Given wizard di halaman 1
When tombol "Prev" diklik
Then lompat ke halaman terakhir (wrap-around)

**AC-03-03** `[PRESERVE-BUG]` (verifies `BSL-009`)
Given navigasi via "Prev"
When request API dikirim
Then parameter `limite_matching_etablissements` **TIDAK** disertakan (beda dari "Next"). Bug pre-existing, wajib direplikasi identik.

**AC-03-04** `[PRESERVE-BUG]` (verifies `BSL-010`)
Given `partner_name` kosong (falsy) saat tombol Next/Prev diklik dalam kondisi navigasi valid
When method dipanggil
Then method return `None` implisit tanpa pesan/error. Preserve identik.

## AC-04 — Select Hasil Pencarian

**AC-04-01** `[COMPAT-FIX WAJIB]` (verifies `BSL-004`, `DIFF-02`, `MF-02`)
Given user klik "Select" pada satu baris hasil (level `siret.wizard.result` ATAU `matching.etablissement`)
When dialog konfirmasi "Are you sure want to overwrite the Data?" disetujui
Then `res.partner` terkait (`active_id`) di-overwrite: `name`, **`company_registry`** (BUKAN lagi `siret` — field ini dihapus di 19.0, dikonsolidasi ke `company_registry` generik, lihat DIFF-02), `street`(+`street2` di level result), `social_reason`, `zip`, `city`, `partner_latitude`, `partner_longitude` — tanpa merge, field lama langsung tertimpa. **Perubahan dari AC-04-01 versi 17.0→18.0:** nama field target berubah, value/logic assignment TIDAK berubah (tetap dari data SIRET API gouv.fr).

**AC-04-02** (verifies `BSL-006`)
Given model `res.country.department` TERSEDIA di environment (addon eksternal terinstall)
When "Select" dijalankan
Then `country_department_id`/`state_id`/`country_id` partner ikut terisi dari lookup departemen

**AC-04-03** (verifies `BSL-006`)
Given model `res.country.department` **TIDAK** tersedia (kondisi environment test standar)
When "Select" dijalankan
Then `country_department_id`/`state_id`/`country_id` **TIDAK** disentuh sama sekali (bukan error) — field lain tetap ter-write normal.

## AC-05 — Status & Tampilan

**AC-05-01** (verifies `BSL-005`)
Given hasil dengan `etat_administratif = 'A'`
When ditampilkan di tabel hasil
Then label "en activité", badge hijau

**AC-05-02** (verifies `BSL-005`)
Given hasil dengan `etat_administratif != 'A'`
When ditampilkan (level etablissement)
Then label "fermé le {{date_fermeture}}", badge merah

**AC-05-03** (verifies `BSL-007`)
Given `activite_principale` (level siège/`siret.wizard.result`) berakhiran huruf `A`/`B`/`Z`/`D`
When `computed_activite_principale` (level `matching.etablissement`) dihitung
Then diterjemahkan ke label Perancis sesuai 4 kasus; kode lain ditampilkan mentah

## AC-06 — Field & Tracking

**AC-06-01** (verifies `BSL-013`)
Given `social_reason` partner diubah (manual atau via wizard select)
When perubahan disimpan
Then tercatat di chatter `res.partner` (tracked field)

## AC-07 — Quirk Pre-Existing (WAJIB dipertahankan)

**AC-07-01** `[PRESERVE-BUG]` (verifies `BSL-008`)
Given respons API kehilangan `nom_complet`/`siret` pada satu hasil, ATAU request API gagal (`RequestException`)
When `_fetch_siret_data` mencoba log warning/error
Then `NameError: name '_logger' is not defined` terjadi (crash), BUKAN log yang berhasil — preserve identik.

**AC-07-02** (verifies `BSL-014`)
Given method `siret_wizard()` baru di `res.partner`
When modul di-install bersama modul lain manapun
Then tidak ada method collision dengan core `base`/`contacts`

---

# Bagian B — `personal_email_usage`

## AC-08 — Routing Fetch per Tipe Server

**AC-08-01** (verifies `BSL-015`)
Given server `fetchmail.server` dengan `server_type = 'imap'`
When `fetch_mail()` dipanggil (manual atau cron)
Then logic custom modul yang jalan, TIDAK memanggil `super().fetch_mail()` untuk server ini

**AC-08-02** (verifies `BSL-015`)
Given server dengan `server_type` BUKAN `'imap'`
When `fetch_mail()` dipanggil
Then didelegasikan penuh ke `super().fetch_mail()` — behavior identik core Odoo 19.0 untuk tipe server ini

**AC-08-03** `[COMPAT-FIX WAJIB]` (verifies `DIFF-01`, `MF-01`) — **DIUBAH TOTAL dari versi 17.0→18.0**
Given cron `_fetch_mails()` native 19.0 memanggil `.fetch_mail()` **TANPA argumen** (bukan lagi `raise_exception=False` seperti 18.0)
When cron dijalankan terhadap server manapun (IMAP atau bukan)
Then **TIDAK** terjadi `TypeError` — override modul menerima pemanggilan tanpa argumen, signature `fetch_mail(self)` (bukan lagi `fetch_mail(self, raise_exception=True)`). **Perubahan dari AC-08-03 versi 17.0→18.0:** arah kompatibilitas terbalik — 17→18 menambah parameter, 18→19 menghapusnya. AC BARU untuk pasangan versi ini, murni kompatibilitas teknis, bukan behavior 18.0.

## AC-09 — Filter Pengirim

**AC-09-01** (verifies `BSL-016`)
Given email masuk dari alamat yang match `res.users` dengan `share = False`
When diproses cron IMAP
Then email di-skip, dihitung `skipped`, TIDAK diproses `message_process`

**AC-09-02** (verifies `BSL-017`)
Given email masuk dari alamat yang BUKAN user internal DAN tidak match `res.partner` manapun
When diproses cron IMAP
Then email JUGA di-skip

**AC-09-03** (verifies `BSL-018`)
Given email masuk dari alamat yang BUKAN user internal DAN match `res.partner` existing
When diproses cron IMAP
Then diteruskan ke `message_process()` standar dengan context yang benar

## AC-10 — Blokir Auto-Create Partner

**AC-10-01** (verifies `BSL-019`)
Given email masuk dialiaskan ke model `res.partner`, pengirim match partner existing
When `message_new()` dipanggil
Then partner existing dikembalikan (bukan buat baru)

**AC-10-02** (verifies `BSL-019`)
Given email masuk dialiaskan ke `res.partner`, pengirim TIDAK match partner manapun
When `message_new()` dipanggil
Then `False` dikembalikan — TIDAK ADA `res.partner` baru dibuat

**AC-10-03** (verifies `BSL-019`)
Given model target BUKAN `res.partner`
When `message_new()` dipanggil
Then didelegasikan penuh ke `super()` — behavior core standar tidak berubah

## AC-11 — Quirk Pre-Existing (WAJIB dipertahankan)

**AC-11-01** `[PRESERVE-BUG, prioritas TINGGI]` (verifies `BSL-020`)
Given `mark_read = False` (default), email di-skip (user internal ATAU bukan kontak)
When cron jalan lagi di siklus BERIKUTNYA
Then email yang sama muncul lagi di search `(UNSEEN)` — TIDAK PERNAH masuk `processed_ids` lewat jalur skip, di-fetch ulang SELAMANYA. Preserve identik.

**AC-11-02** `[PRESERVE-BUG]` (verifies `BSL-021`)
Given siklus fetch selesai dengan beberapa email gagal diproses
When log ringkasan dicetak
Then "succeeded" dihitung `count - failed` (bukan `count` polos). Preserve identik.

---

## Ringkasan Traceability

Sama seperti project 17.0→18.0: 24 `BSL-NNN` → 21 AC di atas (mencakup semua kecuali item housekeeping murni — BSL-011, BSL-012/022/024). **2 AC diubah isinya** dibanding versi 17.0→18.0 (AC-04-01, AC-08-03) untuk mengakomodasi breaking change 19.0 — ID tetap sama untuk traceability, isi kondisi/hasil yang berubah.
