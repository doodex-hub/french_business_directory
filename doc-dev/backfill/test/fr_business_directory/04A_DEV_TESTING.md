# Dev Testing — fr_business_directory

**Step:** 04 — Developer Testing (backfill)
**Module:** `fr_business_directory`
**Spec ref:** `doc-dev/backfill/spec/fr_business_directory/01A_FUNCTIONAL_SPEC.md`
**Last Updated:** 2026-08-07

> Modul BELUM punya `tests/` sama sekali sebelum backfill ini — semua test di bawah BARU ditulis
> (`fr_business_directory/tests/test_siret_wizard.py`, 23 test method). Dijalankan NYATA (Mode C,
> AI menjalankan Docker sendiri dari CLI) — bukan desk-review.

---

## 1. Smoke Test (happy path)

### Cara Eksekusi

**Mode B/C (docker, real)** — `docker-env/docker-compose.yml` (satu instance untuk kedua addon di
repo ini, lihat `CLAUDE.md`), dijalankan via `docker compose up` dari Claude Code CLI, log dibaca
langsung dari `docker-env/logs/odoo.log` (mounted volume).

### Checklist

| # | Area/fitur | Happy path / edge case | Cara | Status |
|---|---|---|---|---|
| 1 | Instalasi modul | `fr_business_directory` terinstal bersih di atas `odoo:17.0` + `contacts`+`l10n_fr` (Core, tanpa Enterprise/3rd-party) | Mode C | ✅ Pass |
| 2 | Wizard buka + auto-fetch | Buka wizard dari partner company, hasil halaman 1 terisi dari API (mocked) | Mode C | ✅ Pass |
| 3 | Select hasil → partner | Pilih satu hasil, data ter-write ke `res.partner` | Mode C | ✅ Pass |

---

## 2. Unit & Integration Test Specification

### 2a. Model Fields

**File:** `models/partner.py`

Field `social_reason` (Char, `tracking=True`) — tidak ada logic tambahan untuk diuji terpisah
(field polos), tercakup implisit lewat TC-SELECT di bawah (di-write lewat `select_siret()`).

### 2b. Wizard fetch & pagination (`models/siret_wizard.py`)

#### TC-FETCH-01 — `default_get` auto-fetch halaman 1

| # | Tipe | Condition | Expected | Provenance |
|---|---|---|---|---|
| 01 | Unit | Buka wizard dari partner `is_company=True`, API (mocked) balas 1 hasil valid | `partner_name`, `result_count`, `total_pages`, `result_ids` (+`matching_etablissements`) terisi; URL request memuat `q=<nama>&page=1&per_page=25&limite_matching_etablissements=100` | `[DIKONFIRMASI]` — dijalankan nyata, lulus |

#### TC-PAGE-01 — Navigasi Next/Prev + wrap-around

| # | Tipe | Condition | Expected | Provenance |
|---|---|---|---|---|
| 01 | Unit | `page_number=1 < total_pages=3`, klik Next | `page_number` → 2, URL request memuat `page=2` DAN `limite_matching_etablissements=100` | `[DIKONFIRMASI]` |
| 02 | Unit | `page_number=3=total_pages=3`, klik Next | Wrap ke `page_number=1` (bukan disabled) | `[DIKONFIRMASI]` |
| 03 | Unit | `page_number=1`, klik Prev | Wrap ke `page_number=total_pages` | `[DIKONFIRMASI]` |
| 04 | Unit | Klik Prev (F-02) | URL request TIDAK memuat `limite_matching_etablissements` — beda dari Next (`FINDINGS.md` F-02) | `[PERLU-KEPUTUSAN]` — dikonfirmasi nyata via inspeksi `mock_get.call_args` |
| 05 | Unit | `partner_name` kosong, klik Next (F-03) | Method return `None`, TIDAK ada API call, `page_number` tidak berubah | `[PERLU-KEPUTUSAN]` — dikonfirmasi nyata |

#### TC-ERR-01 — Jalur error `_logger` tidak terdefinisi (F-01)

| # | Tipe | Condition | Expected | Provenance |
|---|---|---|---|---|
| 01 | Unit | `requests.get` raise `RequestException` | `NameError` (BUKAN log bersih) terlempar sampai ke caller | `[PERLU-KEPUTUSAN]` — dikonfirmasi nyata |
| 02 | Unit | `siege` adalah dict valid TAPI `nom_complet`/`siret` kosong | `NameError` terlempar (baris 113, koreksi trigger — lihat `FINDINGS.md` F-01) | `[PERLU-KEPUTUSAN]` — dikonfirmasi nyata, DIKOREKSI dari draf awal (semula dikira dipicu "siege bukan dict") |
| 03 | Unit | `siege` BUKAN dict sama sekali | TIDAK ada `NameError`/log — result di-skip senyap (`result_ids` kosong untuk result itu), gap TERPISAH dari F-01 | `[HASIL-BACA]` — dikonfirmasi nyata (AC-02-03) |

**Lesson dari dry run test ini (dicatat untuk sesi BACKFILL berikutnya):** draf awal test/`FINDINGS.md`
mengasumsikan `siege` bukan dict yang memicu `_logger.warning` (baris 113) — setelah dijalankan nyata
di Docker, hasilnya `AssertionError: NameError not raised`, membuktikan asumsi itu salah. Baca ulang
indentasi kode (line 112 `else` berpasangan dengan `if name and siret:` baris 57, BUKAN dengan
`if isinstance(siege, dict):` baris 51) mengungkap kondisi pemicu yang benar. **Jangan simpulkan
kondisi pemicu bug logging/exception hanya dari baca cepat — verifikasi lewat eksekusi nyata seperti
di sini**, terutama untuk percabangan `if/else` bertingkat.

### 2c. Select hasil → write partner (`select_siret`)

#### TC-SELECT-01

| # | Tipe | Condition | Expected | Provenance |
|---|---|---|---|---|
| 01 | Unit | Select dari `siret.wizard.result`, `res.country.department` TIDAK terinstal (kondisi nyata di image `odoo:17.0`) | `name`/`siret`/`street`/`zip`/`city`/`social_reason` ter-write; `state_id`/`country_id` TETAP kosong (F-05) | `[PERLU-KEPUTUSAN]` — dikonfirmasi nyata |
| 02 | Unit | Select dari `matching.etablissement`, alamat gabungan `"10 rue de la Paix 75002 Paris"` | `_split_address` memisahkan jadi `street="10 rue de la Paix"`, `zip="75002"` | `[HASIL-BACA]` — dikonfirmasi nyata |

**AC-04-04** (`res.country.department` TERSEDIA) **tidak dijalankan** — model itu tidak ada di
`odoo:17.0` + `depends` resmi modul, dan tidak ada `EXTERNAL_ADDONS_PATHS` yang menyediakannya (lihat
`CLAUDE.md`). Dicatat sebagai limitasi tool, bukan "Pass" dari asumsi.

### 2d. Compute fields — status & aktivitas (`matching.etablissement`)

| # | Tipe | Condition | Expected | Provenance |
|---|---|---|---|---|
| 01 | Unit | `etat_administratif='en activité'` | Display = `'en activité'` | `[HASIL-BACA]` |
| 02 | Unit | `etat_administratif='fermé le'`, `date_fermeture` terisi | Display gabung status+tanggal | `[HASIL-BACA]` |
| 03 | Unit | `activite_principale` (di parent result) berakhiran `'A'` | Diterjemahkan ke label Perancis + kode asli dalam kurung | `[HASIL-BACA]` |
| 04 | Unit | `activite_principale` berakhiran huruf TIDAK dipetakan (mis. `'C'`) | Ditampilkan mentah, tanpa terjemahan (BR-07, bukan bug) | `[HASIL-BACA]` |

### 2e. Test Matrix Summary

| Area | Unit | Integration | Provenance |
|---|---|---|---|
| Fetch/pagination | ✓ (8 test) | | Mixed |
| Error handling (F-01) | ✓ (3 test) | | `[PERLU-KEPUTUSAN]`/`[HASIL-BACA]` |
| Select→partner | ✓ (2 test) | | Mixed |
| Compute display | ✓ (4 test) | | `[HASIL-BACA]` |

### 2f. Override/Collision Check terhadap Odoo Core

| # | Method | Model | Kelas yang mendefinisikan (`__mro__`) | Override total Odoo core? | Provenance |
|---|---|---|---|---|---|
| 01 | `siret_wizard` | `res.partner` (`_inherit`) | Hanya `fr_business_directory` (method BARU, tidak ada di core `base`/`contacts`) | ☑ Tidak (aman — nama tidak bentrok) | `[DIKONFIRMASI]` — dicek grep source `odoo:17.0` image |

### 2g. Incoming Email — N/A untuk modul ini (tidak menyentuh email sama sekali).

---

## 3. Hasil Eksekusi Real (Mode C, Docker)

**Environment:** `docker-env/docker-compose.yml` — `odoo:17.0` + `postgres:15`, install
`fr_business_directory,personal_email_usage` bersamaan (repo multi-addon, satu docker-env untuk
semuanya).

**Hasil (log lengkap: `docker-env/logs/odoo.log`, run terakhir 2026-08-07 07:50):**
```
odoo.tests.stats: fr_business_directory: 23 tests 0.32s 458 queries
odoo.tests.result: 0 failed, 0 error(s) of 26 tests when loading database 'french_business_directory_17_test'
```
(26 = 23 dari `fr_business_directory` + hasil gabungan dengan `personal_email_usage`, lihat
`test/personal_email_usage/04A_DEV_TESTING.md`.)

**Riwayat 3 percobaan sampai lulus (dicatat transparan, bukan disembunyikan):**
1. Percobaan #1 (25 test, tanpa 2 test yang ditambah belakangan): **2 failed, 6 error(s)** — 1
   kegagalan genuinely di modul ini (`test_fetch_siret_data_unexpected_siege_shape_raises_nameerror_F01`,
   asumsi trigger F-01 salah — lihat catatan lesson §2b di atas); sisanya cascade dari modul
   `personal_email_usage` (lihat detail root cause di `test/personal_email_usage/04A_DEV_TESTING.md`).
2. Percobaan #2: fix test siege+F-01 diterapkan, fix `personal_email_usage` diterapkan → **1 failed,
   0 error(s) of 26** — sisa kegagalan murni di `personal_email_usage` (F-08 test, lihat dokumen itu).
3. Percobaan #3 (final): **0 failed, 0 error(s) of 26 tests** — PASS PENUH.

---

## 4. Ringkasan

- **Unit:** 23 TC (`fr_business_directory/tests/test_siret_wizard.py`) — jalankan
  `odoo -i fr_business_directory --test-enable --test-tags=/fr_business_directory --stop-after-init`
- **Integration:** 0 (modul tidak menambah controller/HTTP route)
- **Smoke:** 3/3 Pass
