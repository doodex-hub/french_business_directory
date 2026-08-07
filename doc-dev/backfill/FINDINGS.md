# Findings — french-business-directory-17 (fr_business_directory + personal_email_usage)

> Satu file konsolidasi untuk KEDUA addon di repo ini (konvensi multi-addon,
> `doc-dev-backfill/ai-doc/OVERVIEW.md` §3a) — tiap finding diberi prefix `[nama_addon]` di judul.
> Diisi terus sepanjang proses Step 01→07, bukan sekali jadi. Dokumen hidup: kalau pemilik modul
> memperbaiki kode sendiri berdasarkan finding di sini, update entry jadi `✅ RESOLVED` + tanggal +
> bukti test — jangan dihapus.

---

## Ringkasan

| ID | Addon | Judul | Tag | Prioritas |
|---|---|---|---|---|
| F-01 | fr_business_directory | `_logger` dipakai tapi tidak pernah diimpor/didefinisikan | `[PERLU-KEPUTUSAN]` | Tinggi |
| F-02 | fr_business_directory | Param `limite_matching_etablissements` hilang di fetch_previous_page | `[PERLU-KEPUTUSAN]` | Sedang |
| F-03 | fr_business_directory | No-op senyap saat `partner_name` kosong di tengah paginasi | `[PERLU-KEPUTUSAN]` | Rendah |
| F-04 | fr_business_directory | `print()` debug tertinggal di kode produksi | `[HASIL-BACA]` | Rendah |
| F-05 | fr_business_directory | Ketergantungan implisit ke model `res.country.department` (tidak di `depends`) | `[PERLU-KEPUTUSAN]` | Sedang |
| F-06 | fr_business_directory | File `googleaeed8a7b9ec156e7.html` ikut dibundle di root addon | `[HASIL-BACA]` | Rendah |
| F-07 | personal_email_usage | Email yang di-skip tidak pernah ditandai processed → re-fetch tanpa henti | `[PERLU-KEPUTUSAN]` | **Tinggi** |
| F-08 | personal_email_usage | Log ringkasan "succeeded" salah hitung (`count - failed`) | `[PERLU-KEPUTUSAN]` | Sedang |
| F-09 | personal_email_usage | `security/ir.model.access.csv` dead/orphan, referensi model yang tidak ada | `[HASIL-BACA]` | Rendah |
| F-10 | personal_email_usage | File `googleaeed8a7b9ec156e7.html` duplikat (lihat F-06) | `[HASIL-BACA]` | Rendah |
| F-11 | personal_email_usage | Override `fetch_mail()` tidak panggil `super()` untuk server IMAP — memutus chain `_inherit` lain | `[PERLU-KEPUTUSAN]` | Sedang |

---

## Detail

### F-01 [fr_business_directory] — `_logger` dipakai tapi tidak pernah diimpor/didefinisikan
**Tag:** `[PERLU-KEPUTUSAN]`
**Lokasi:** `fr_business_directory/models/siret_wizard.py:113`, `:128`
**Ref:** AC-02 (`_fetch_siret_data` error path)
**Deskripsi:** `siret_wizard.py` memanggil `_logger.warning(...)` (baris 113, kasus `siege` bukan
dict) dan `_logger.error(...)` (baris 128, blok `except requests.RequestException`) — tapi file ini
TIDAK PERNAH `import logging` maupun mendefinisikan `_logger = logging.getLogger(__name__)`. Import
di kepala file hanya `from odoo import fields, models, api, _`, `import requests`, `import urllib`.
**Dampak:** Begitu salah satu dari dua jalur ini benar-benar terpicu (struktur respons API
gouv.fr berubah, atau request gagal/timeout ke `recherche-entreprises.api.gouv.fr`), Python akan
raise `NameError: name '_logger' is not defined` — exception BARU yang menutupi akar masalah asli
(kegagalan API eksternal) yang justru sedang coba dicatat. Karena kode ini bergantung ke API pihak
ketiga di luar kendali modul, jalur error ini genuinely bisa terpicu di produksi (rate limit, API
down, perubahan skema respons).
**Rekomendasi:** tambahkan `import logging` + `_logger = logging.getLogger(__name__)` di kepala file.
**Keputusan pemilik modul:** *(kosong — diisi manusia)*

---

### F-02 [fr_business_directory] — Param `limite_matching_etablissements` hilang di `fetch_previous_page`
**Tag:** `[PERLU-KEPUTUSAN]`
**Lokasi:** `fr_business_directory/models/siret_wizard.py:140` (ada) vs `:177`, `:195` (tidak ada)
**Ref:** AC-03 (navigasi halaman wizard)
**Deskripsi:** URL yang dibangun `fetch_next_page` menyertakan
`&limite_matching_etablissements=100`; DUA URL yang dibangun `fetch_previous_page` (baik saat
`page_number > 1` maupun saat wrap ke halaman terakhir) TIDAK menyertakan parameter ini.
**Dampak:** Jumlah/struktur `matching_etablissements` yang dikembalikan API bisa berbeda untuk
halaman yang SAMA tergantung arah navigasi (Next vs Prev) — user yang klik Prev lalu Next lagi ke
halaman yang sama bisa melihat data establishment yang berbeda. Kemungkinan bug ketidaksengajaan
(copy-paste tidak lengkap), bukan by-design.
**Rekomendasi:** samakan parameter query di ketiga tempat pemanggilan API.
**Keputusan pemilik modul:** *(kosong — diisi manusia)*

---

### F-03 [fr_business_directory] — No-op senyap saat `partner_name` kosong di tengah paginasi
**Tag:** `[PERLU-KEPUTUSAN]`
**Lokasi:** `fr_business_directory/models/siret_wizard.py:134-150` (`fetch_next_page`), `:171-187` (`fetch_previous_page`)
**Ref:** AC-03
**Deskripsi:** Struktur kedua method: `if self.page_number < self.total_pages: if self.partner_name:
... return {...}` — kalau kondisi luar True tapi `self.partner_name` falsy, tidak ada `else`/`return`
di cabang itu, method mengembalikan `None` secara implisit.
**Dampak:** Kalau `partner_name` kosong (seharusnya jarang karena diisi `default_get` dari
`partner.name`, tapi bisa terjadi kalau partner tidak punya nama), tombol Next/Prev di wizard tidak
melakukan apa-apa tanpa pesan/feedback ke user — terlihat seperti tombol tidak berfungsi.
**Rekomendasi:** opsional — bisa dibiarkan (edge case jarang) atau ditambah pesan `UserError` kalau
pemilik modul mau perilaku lebih eksplisit.
**Keputusan pemilik modul:** *(kosong — diisi manusia)*

---

### F-04 [fr_business_directory] — `print()` debug tertinggal di kode produksi
**Tag:** `[HASIL-BACA]`
**Lokasi:** `fr_business_directory/models/siret_wizard.py:141, 157, 178, 192, 196`
**Deskripsi:** Lima pemanggilan `print(api_url)`/`print(self.page_count)` tersisa di
`fetch_next_page`/`fetch_previous_page` — kemungkinan sisa debugging yang tidak dibersihkan sebelum
commit.
**Dampak:** Tidak fungsional (tidak memengaruhi behavior), hanya noise ke stdout container/log
server. Housekeeping saja.
**Keputusan pemilik modul:** *(kosong — diisi manusia)*

---

### F-05 [fr_business_directory] — Ketergantungan implisit ke model `res.country.department` (tidak di `depends`)
**Tag:** `[PERLU-KEPUTUSAN]`
**Lokasi:** `fr_business_directory/models/siret_wizard.py:254-257` (`SiretWizardResult.select_siret`), `:346-349` (`MatchingEtablissement.select_siret`)
**Ref:** AC-04 (isi data partner dari hasil pencarian)
**Deskripsi:** Kode secara defensif mengecek `self.env['ir.model'].search([('model', '=',
'res.country.department')])` sebelum memakai field `country_department_id`/`state_id`/`country_id`
pada `res.partner`. Model `res.country.department` BUKAN bagian dari `base`/`contacts`/`l10n_fr`
(dependency yang dideklarasikan `__manifest__.py`) — kemunculan cek defensif ini menyiratkan
developer sudah tahu model ini kadang tidak ada (kemungkinan berasal dari addon Perancis
tambahan/OCA yang terpisah, tidak dideklarasikan).
**Dampak:** Kalau addon penyedia `res.country.department` TIDAK terinstall (skenario paling mungkin
di instalasi vanilla `fr_business_directory` + dependency resminya saja), pengisian
department/state/country partner otomatis SENYAP tidak jalan sama sekali (fallback branch aman,
tidak crash) — tapi ini fitur yang hilang tanpa pemberitahuan apapun ke user/admin, dan tidak
terdokumentasi di README modul addon apa yang sebenarnya dibutuhkan untuk fitur penuh ini.
**Rekomendasi:** dokumentasikan soft-dependency ini di README, atau evaluasi apakah perlu masuk
`depends` resmi kalau memang selalu diharapkan tersedia di deployment Doodex.
**Keputusan pemilik modul:** *(kosong — diisi manusia)*

---

### F-06 [fr_business_directory] — File `googleaeed8a7b9ec156e7.html` ikut dibundle di root addon
**Tag:** `[HASIL-BACA]`
**Lokasi:** `fr_business_directory/googleaeed8a7b9ec156e7.html`
**Deskripsi:** File verifikasi Google Search Console (biasanya untuk domain website, tidak
berhubungan dengan modul Odoo) ikut ter-commit di root folder addon. File identik juga ada di
`personal_email_usage/` (lihat F-10) — kemungkinan tidak sengaja ikut ter-copy saat scaffolding
kedua addon dari template yang sama.
**Dampak:** Tidak fungsional (Odoo tidak membaca file ini), housekeeping saja — file tidak
seharusnya ikut dalam source addon.
**Keputusan pemilik modul:** *(kosong — diisi manusia)*

---

### F-07 [personal_email_usage] — Email yang di-skip tidak pernah ditandai processed → re-fetch tanpa henti
**Tag:** `[PERLU-KEPUTUSAN]`
**Lokasi:** `personal_email_usage/models/mail.py:64` (`processed_ids` dibaca dari state lama),
`:75` (`-FLAGS \Seen` tanpa syarat setelah fetch), `:93-96` (skip sender = internal user), `:98-107`
(skip sender = bukan kontak), `:121` (`processed_ids.add()` HANYA di jalur sukses)
**Ref:** AC-05/AC-06 (filter user internal, validasi kontak)
**Deskripsi:** Tiap email yang di-`fetch()` langsung di-un-seen (`imap_server.store(num, '-FLAGS',
'\\Seen')`, baris 75) TANPA MELIHAT apakah nanti email itu akan diproses atau di-skip. `message_id`
HANYA ditambahkan ke `processed_ids` di jalur SUKSES (`if res_id: processed_ids.add(message_id)`,
baris 120-121) — dua jalur SKIP (pengirim = user internal Odoo, baris 93-96; pengirim bukan kontak
terdaftar, baris 98-107) TIDAK PERNAH menambahkan `message_id` ke `processed_ids`.

Field `mark_read` (kontrol utama fitur modul ini) **default `False`**. Kalau `mark_read=False`:
email yang di-skip TETAP berstatus UNSEEN di server DAN TIDAK tercatat di `processed_ids` — search
`(UNSEEN)` di eksekusi cron BERIKUTNYA akan menemukan email yang SAMA lagi, mengulang seluruh siklus
fetch→cek-user→skip→log SELAMANYA, untuk SETIAP email yang pernah dikirim oleh user internal atau
alamat yang bukan kontak.
**Dampak:** Ini bug performa/resource riil, bukan kosmetik — beban IMAP (fetch ulang RFC822 body
PENUH tiap cron tick, tanpa batas waktu) bertambah terus seiring email internal yang terakumulasi di
mailbox, log "Skipped email from..." bertambah tanpa henti, `fetch_mail()` makin lambat dari waktu
ke waktu. Dengan konfigurasi DEFAULT (`mark_read=False`), setiap deployment modul ini akan mengalami
gejala ini kalau mailbox yang di-poll juga menerima email dari user internal/non-kontak (skenario
umum untuk mailbox shared/support).
**Rekomendasi:** tandai email yang di-skip juga sebagai processed (tambah `message_id` ke
`processed_ids` di kedua jalur skip), ATAU re-apply `\Seen` untuk email yang di-skip terlepas dari
`mark_read` (supaya tidak masuk `(UNSEEN)` search lagi) — pilih salah satu, keduanya menutup celah
ini.
**Keputusan pemilik modul:** *(kosong — diisi manusia)*

---

### F-08 [personal_email_usage] — Log ringkasan "succeeded" salah hitung
**Tag:** `[PERLU-KEPUTUSAN]`
**Lokasi:** `personal_email_usage/models/mail.py:122-124` (increment `count`/`failed`), `:138-141` (log)
**Deskripsi:** `count` HANYA diincrement di jalur sukses (`if res_id: ... count += 1`, baris 122);
`failed` diincrement TERPISAH di jalur gagal (`else: failed += 1`, baris 124, dan blok `except`,
baris 129) — dua counter INDEPENDEN, tidak tumpang tindih (bukan `count` = total lalu `failed`
sebagian darinya). Baris log (139-141) menghitung kolom "succeeded" sebagai `(count - failed)`,
padahal seharusnya cukup `count` polos.
**Dampak:** Angka "succeeded" di log SELALU under-count dari nilai sebenarnya (dan bisa NEGATIF
kalau `failed > count`) — siapapun yang memonitor log ini untuk kebutuhan operasional/alerting akan
mendapat angka yang menyesatkan.
**Rekomendasi:** ganti `(count - failed)` jadi `count` di baris log.
**Keputusan pemilik modul:** *(kosong — diisi manusia)*

---

### F-09 [personal_email_usage] — `security/ir.model.access.csv` dead/orphan
**Tag:** `[HASIL-BACA]`
**Lokasi:** `personal_email_usage/security/ir.model.access.csv:2`, `personal_email_usage/__manifest__.py` (baris `data`)
**Deskripsi:** CSV mereferensikan `model_personal_email_usage_personal_email_usage` (model
`personal_email_usage.personal_email_usage`) yang TIDAK ADA di `models/mail.py` — kemungkinan sisa
scaffold boilerplate generator modul (yang biasanya membuat model placeholder senama modul) sebelum
developer pivot ke extend `mail.thread`/`fetchmail.server` murni tanpa model baru. Baris `data` di
manifest yang memuat file ini SUDAH dikomentari (`# 'security/ir.model.access.csv',`), jadi file ini
tidak pernah benar-benar di-load — tidak menyebabkan error install.
**Dampak:** Tidak ada dampak fungsional (tidak dimuat). Housekeeping — file bisa dihapus karena
tidak dipakai dan mereferensikan model yang tidak ada.
**Keputusan pemilik modul:** *(kosong — diisi manusia)*

---

### F-10 [personal_email_usage] — File `googleaeed8a7b9ec156e7.html` duplikat
**Tag:** `[HASIL-BACA]`
**Lokasi:** `personal_email_usage/googleaeed8a7b9ec156e7.html`
**Deskripsi:** Sama persis dengan F-06 (`fr_business_directory`) — file verifikasi Google Search
Console yang tidak berhubungan dengan Odoo, ikut dibundle di root addon ini juga (isi file identik).
**Dampak:** Housekeeping saja, lihat F-06.
**Keputusan pemilik modul:** *(kosong — diisi manusia)*

---

### F-11 [personal_email_usage] — Override `fetch_mail()` tidak panggil `super()` untuk server IMAP
**Tag:** `[PERLU-KEPUTUSAN]`
**Lokasi:** `personal_email_usage/models/mail.py:61-156`
**Ref:** Cek wajib Step 01 — tabrakan/override method Odoo core (`CLAUDE_TEMPLATE.md`)
**Deskripsi:** `FetchmailServer.fetch_mail()` (`_inherit = 'fetchmail.server'`) menulis ULANG total
logic untuk server bertipe IMAP (`self.filtered(lambda s: s.server_type == 'imap')`) — TIDAK
memanggil `super().fetch_mail()` untuk grup server ini sama sekali. `super()` HANYA dipanggil di
baris terakhir (156) untuk server yang BUKAN IMAP (`self.filtered(lambda s: s.server_type !=
'imap')`). Ini SESUAI dengan tujuan modul (deskripsi manifest: kontrol lanjutan atas fetch IMAP) —
bukan kesalahan tak sengaja seperti kasus tabrakan nama method yang genuinely accidental — tapi
tetap berarti CHAIN `_inherit` Odoo core (dan modul LAIN manapun yang juga `_inherit` ke
`fetchmail.server.fetch_mail` lewat mekanisme cooperative-override) TERPUTUS TOTAL untuk server tipe
IMAP.
**Dampak:** Kalau di masa depan ada modul lain terinstall bersamaan (custom Doodex lain, atau
addon Enterprise `google_gmail`/`microsoft_outlook` yang juga override `fetch_mail` untuk jenis
server tertentu) yang mengandalkan `super()` chain untuk fitur TAMBAHAN pada IMAP fetch — fitur itu
TIDAK akan pernah jalan, karena chain berhenti di modul ini tanpa pesan/warning apapun. Saat ini
(dependency modul cuma `base`, `mail`) belum ada konflik nyata, tapi ini risiko arsitektural untuk
instalasi masa depan.
**Rekomendasi:** dokumentasikan eksplisit di README/komentar kode bahwa override ini SENGAJA total
untuk IMAP (bukan lupa `super()`), supaya developer lain yang menambah modul terkait fetchmail tahu
untuk tidak mengandalkan cooperative-override pada path IMAP.
**Keputusan pemilik modul:** *(kosong — diisi manusia)*

---

## Limitasi Tool (kalau ada)

- *(diisi setelah Step 04/07 — kalau ada gap yang genuinely tidak bisa dipastikan tanpa
  instrumentasi tambahan ke kode bisnis)*
