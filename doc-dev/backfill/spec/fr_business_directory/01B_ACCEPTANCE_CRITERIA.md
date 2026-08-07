# Acceptance Criteria — fr_business_directory

**Module:** `fr_business_directory`
**Ref:** `01A_FUNCTIONAL_SPEC.md`
**Last Updated:** 2026-08-07
**Status:** Backfill retroaktif

---

## AC-01 — Visibilitas tombol Business Directory

**AC-01-01** — ref `BR-01` `[HASIL-BACA]`
Given kontak dengan `is_company = True` dibuka di form view
When form partner dirender
Then tombol "Business Directory" tampil di sebelah field nama, memicu `siret_wizard()`.

**AC-01-02** — ref `BR-01` `[HASIL-BACA]`
Given kontak dengan `is_company = False` (Individual) dibuka di form view
When form partner dirender
Then tombol "Business Directory" TIDAK tampil.

---

## AC-02 — Auto-fetch saat wizard dibuka

**AC-02-01** — ref `BR-02` `[HASIL-BACA]`
Given partner dengan `name` terisi, tombol Business Directory diklik
When wizard `siret.wizard` terbuka (`default_get` dipanggil)
Then request GET dikirim ke `recherche-entreprises.api.gouv.fr/search` dengan `q=<nama partner
ter-encode>&page=1&per_page=25&limite_matching_etablissements=100`, dan `result_ids` terisi dari
response.

**AC-02-02** — ref `BR-02`, F-01 `[PERLU-KEPUTUSAN]`
Given API `recherche-entreprises.api.gouv.fr` mengembalikan error HTTP atau struktur response yang
tidak terduga (`siege` bukan dict)
When `_fetch_siret_data` menangani kondisi ini
Then kode SEHARUSNYA mencatat warning/error lewat `_logger` — TAPI SEKARANG raise `NameError`
karena `_logger` tidak pernah diimpor (lihat F-01 `FINDINGS.md`). Wizard tetap terbuka tapi
`result_ids` kosong/tidak lengkap, tanpa pesan error yang jelas ke user.

---

## AC-03 — Navigasi paginasi

**AC-03-01** — ref `BR-03` `[HASIL-BACA]`
Given wizard di halaman N, `N < total_pages`, `partner_name` terisi
When user klik "Next"
Then hasil lama di-`unlink()`, `page_number` bertambah 1, fetch API halaman baru, wizard tetap
terbuka menampilkan hasil halaman baru.

**AC-03-02** — ref `BR-03` `[HASIL-BACA]`
Given wizard di halaman terakhir (`page_number >= total_pages`)
When user klik "Next"
Then paginasi WRAP ke halaman 1 (bukan disabled) — lihat `models/siret_wizard.py:151-166`.

**AC-03-03** — ref `BR-03` `[HASIL-BACA]`
Given wizard di halaman 1
When user klik "Prev"
Then paginasi WRAP ke halaman terakhir (`total_pages`).

**AC-03-04** — ref `BR-03`, F-02 `[PERLU-KEPUTUSAN]`
Given user berada di halaman N via jalur "Next" vs jalur "Prev" (dari arah berlawanan)
When membandingkan hasil `matching_etablissements` untuk halaman N yang sama
Then hasil BISA berbeda karena `fetch_previous_page` tidak mengirim parameter
`limite_matching_etablissements` yang dikirim `fetch_next_page` — lihat F-02 `FINDINGS.md`.

**AC-03-05** — ref `BR-03`, F-03 `[PERLU-KEPUTUSAN]`
Given `partner_name` kosong/falsy (edge case), `page_number < total_pages`
When user klik "Next"
Then method mengembalikan `None` secara implisit — tidak ada fetch, tidak ada pesan error, wizard
diam tanpa perubahan terlihat (lihat F-03 `FINDINGS.md`).

---

## AC-04 — Select hasil pencarian menulis ke partner

**AC-04-01** — ref `BR-04` `[HASIL-BACA]`
Given user klik "Select" pada satu baris di tabel `siret.wizard.result` (level hasil, bukan
etablissement detail), setelah konfirmasi dialog "Are you sure want to overwrite the Data?"
When `select_siret()` dieksekusi
Then `res.partner` (dari `active_id`) di-`write()`: `name`, `siret`, `street`, `street2`,
`social_reason`, `zip`(`post_code`), `city`, `partner_latitude`, `partner_longitude` — data lama
di field-field ini TERTIMPA TOTAL tanpa merge.

**AC-04-02** — ref `BR-04` `[HASIL-BACA]`
Given user klik "Select" pada baris `matching.etablissement` (level detail, dalam form
`siret.wizard.result`)
When `select_siret()` (varian `MatchingEtablissement`) dieksekusi
Then `res.partner` ditulis dari data etablissement spesifik itu (`adresse` di-split manual by
`code_postal` untuk memisahkan jalan dari kode pos, `street2` selalu dikosongkan).

**AC-04-03** — ref `BR-05` `[PERLU-KEPUTUSAN]`
Given model `res.country.department` TIDAK terinstall di database (addon penyedianya tidak ada)
When `select_siret()` dieksekusi (baik varian result maupun etablissement)
Then field `country_department_id`/`state_id`/`country_id` pada partner TIDAK disentuh sama
sekali — field lain (nama, alamat, siret, dst) tetap terisi normal. Tidak ada pesan/indikasi ke user
bahwa sebagian data tidak terisi karena dependency opsional tidak ada (lihat F-05 `FINDINGS.md`).

**AC-04-04** — ref `BR-05` `[HASIL-BACA]`
Given model `res.country.department` terinstall DAN kode departemen dari hasil pencarian cocok
dengan record `res.country.department` yang ada
When `select_siret()` dieksekusi
Then `country_department_id`, `state_id` (dari `country_department.state_id`), dan `country_id`
(dari `country_department.country_id`) ikut terisi di partner.

---

## AC-05 — Tampilan status administratif

**AC-05-01** — ref `BR-06` `[HASIL-BACA]`
Given hasil pencarian punya `etat_administratif = 'A'`
When ditampilkan di tabel hasil
Then label "en activité" dengan badge hijau (`decoration-success`).

**AC-05-02** — ref `BR-06` `[HASIL-BACA]`
Given hasil pencarian punya `etat_administratif != 'A'` dan `date_fermeture` terisi
When ditampilkan di tabel etablissement (`etat_administratif_display`)
Then label "fermé le {{tanggal}}" dengan badge merah (`decoration-danger`).

---
