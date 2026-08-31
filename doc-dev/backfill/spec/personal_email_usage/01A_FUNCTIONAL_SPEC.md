# Functional Spec — personal_email_usage

**Module:** `personal_email_usage`
**Odoo Version:** 17.0
**Depends:** `base`, `mail`
**Last Updated:** 2026-08-07
**Status:** Backfill retroaktif — dibaca dari kode existing, bukan requirement baru
**Provenance:** lihat `doc-dev-backfill/templates/CLAUDE_TEMPLATE.md` §Provenance Tag

---

## Ringkasan untuk Review — Perlu Konfirmasi User

1. **F-07 (TINGGI):** dengan konfigurasi default (`mark_read=False`), email dari user internal atau
   pengirim yang bukan kontak akan di-fetch ULANG SELAMANYA setiap cron `fetch_mail()` — beban IMAP
   dan log bertambah tanpa henti. Lihat `FINDINGS.md`.
2. **F-08 (Sedang):** log ringkasan "succeeded" salah hitung, menyesatkan monitoring operasional.
3. **F-11 (Sedang):** override `fetch_mail()` tidak memanggil `super()` untuk server IMAP — SENGAJA
   (sesuai tujuan modul), tapi memutus chain `_inherit` modul lain di masa depan. Perlu
   didokumentasikan eksplisit.

---

## Latar Belakang & Tujuan

Modul menambahkan kontrol lanjutan pada proses fetch email masuk (IMAP) milik Odoo core
(`fetchmail.server`): (1) pilihan menandai email yang di-fetch sebagai sudah dibaca atau tetap
belum dibaca di server, (2) melewati (skip) email yang dikirim oleh user internal Odoo sendiri,
(3) hanya memproses email dari pengirim yang sudah ada di daftar kontak (`res.partner`). `[HASIL-BACA]`

---

## Scope

### Yang Termasuk (disimpulkan dari kode)

- Field baru `mark_read` (Boolean, default `False`) dan `processed_message_ids` (Text) pada
  `fetchmail.server`. `[HASIL-BACA]`
- Override total `fetch_mail()` untuk server bertipe IMAP — logic fetch/parse/routing sendiri,
  TIDAK memanggil implementasi core Odoo untuk tipe server ini. `[HASIL-BACA]`
- Server bertipe LAIN (POP3, dll — bukan IMAP) tetap memakai implementasi core Odoo apa adanya
  (dipanggil via `super()`). `[HASIL-BACA]`
- Dedup pemrosesan lewat pencatatan `Message-ID` yang sudah diproses (`processed_message_ids`,
  disimpan sebagai string dipisah koma). `[HASIL-BACA]`
- Filter: skip kalau pengirim adalah user internal Odoo aktif (`res.users` dengan `share = False`).
  `[HASIL-BACA]`
- Filter: skip kalau pengirim BUKAN kontak (`res.partner`) yang sudah ada. `[HASIL-BACA]`
- Override `message_new()` pada `mail.thread` — kalau model target adalah `res.partner`, hanya
  kembalikan partner yang SUDAH ADA (match by email); TIDAK PERNAH membuat `res.partner` baru dari
  email masuk lewat jalur ini. `[HASIL-BACA]`
- UI: field `mark_read` ditambahkan di form `fetchmail.server` (Technical Settings, group
  `base.group_no_one`). `[HASIL-BACA]`

### Yang Tidak Termasuk

Tidak ada indikasi eksplisit dari kode soal scope yang sengaja dikeluarkan. Modul TIDAK menyentuh
sisi OUTGOING email sama sekali (tidak ada override composer/`ir_mail_server`) — murni INCOMING.

---

## User Stories (rekonstruksi)

### US-01 — Kontrol status baca email yang di-fetch
Sebagai admin sistem, saya ingin memilih apakah email yang berhasil diambil Odoo dari server IMAP
tetap ditandai "belum dibaca" di mailbox asli (supaya bisa dipantau juga lewat email client biasa)
atau langsung ditandai "sudah dibaca". `[HASIL-BACA]`

### US-02 — Hindari proses ulang email dari user internal
Sebagai admin sistem, saya tidak ingin email yang dikirim oleh sesama user internal Odoo (bukan
dari kontak eksternal) ikut diproses jadi lead/pesan di `mail.thread` — biasanya ini komunikasi
internal yang tidak relevan untuk di-thread-kan otomatis. `[HASIL-BACA]`

### US-03 — Hanya proses email dari kontak yang dikenal
Sebagai admin sistem, saya ingin mengurangi spam/email tidak relevan diproses otomatis dengan hanya
menerima email dari alamat yang sudah tercatat sebagai kontak (`res.partner`). `[HASIL-BACA]`

---

## Business Rules

> **Cek wajib tabrakan/override method vs Odoo core (Step 01):** DUA method di modul ini
> mendefinisikan ulang method pada model `_inherit` — didetailkan di BR-02 dan BR-07 di bawah, dan
> di tabel Override/Collision Check `04A_DEV_TESTING.md` §2f.

### BR-01 — Field kontrol baru pada `fetchmail.server`
`mark_read` (Boolean, default `False`) dan `processed_message_ids` (Text, dedup state) ditambahkan
ke `fetchmail.server`. `[HASIL-BACA]`
**Lokasi kode:** `models/mail.py:52-59`

### BR-02 — `fetch_mail()` di-override TOTAL untuk server IMAP, delegasi ke core untuk server lain
Untuk `self.filtered(lambda s: s.server_type == 'imap')`, TIDAK ADA pemanggilan
`super().fetch_mail()` sama sekali — seluruh proses search/fetch/flag/route/commit ditulis ulang.
Untuk server yang BUKAN IMAP, baris terakhir method memanggil
`super(FetchmailServer, self.filtered(lambda s: s.server_type != 'imap')).fetch_mail()` — delegasi
penuh ke implementasi core Odoo. `[HASIL-BACA]` — SENGAJA (bukan lupa `super()`, ini tujuan utama
modul), tapi lihat F-11 di `FINDINGS.md` untuk risiko arsitektural jangka panjang.
**Lokasi kode:** `models/mail.py:61-156`

### BR-03 — Status baca (\Seen) dipaksa ulang sesuai `mark_read`, TIDAK peduli hasil pemrosesan
Segera setelah `fetch(num, '(RFC822)')`, flag `\Seen` SELALU dihapus dulu (`-FLAGS`, baris 75) —
lalu HANYA ditambahkan balik (`+FLAGS`, baris 76-77) kalau `server.mark_read = True`. Ini terjadi
SEBELUM keputusan skip/proses email itu diambil — berlaku untuk SEMUA email yang di-fetch, termasuk
yang nanti di-skip. `[PERLU-KEPUTUSAN]` — lihat F-07 di `FINDINGS.md`: kombinasi ini dengan
`processed_message_ids` yang tidak diisi di jalur skip menyebabkan re-fetch tanpa henti kalau
`mark_read=False` (nilai default).
**Lokasi kode:** `models/mail.py:74-77`

### BR-04 — Skip email dari user internal Odoo
Kalau alamat pengirim (`from_email`) cocok dengan `res.users` yang `share = False` (user internal,
bukan portal/publik), email itu di-skip (`continue`, dihitung `skipped`, di-log `_logger.info`) —
TIDAK diproses lewat `message_process()` sama sekali. `[HASIL-BACA]` — lihat BR-03/F-07 untuk celah
dedup pada jalur skip ini.
**Lokasi kode:** `models/mail.py:87-96`

### BR-05 — Skip email dari pengirim yang bukan kontak terdaftar
Kalau pengirim BUKAN user internal, dicek balik apakah alamatnya cocok dengan `res.partner` yang
ada (`email =ilike from_email`). Kalau tidak ketemu, email itu JUGA di-skip (`continue`, dihitung
`skipped`). `[HASIL-BACA]` — lihat BR-03/F-07 untuk celah dedup yang sama.
**Lokasi kode:** `models/mail.py:98-107`

### BR-06 — Email yang lolos filter diproses lewat `message_process()` standar
Email yang bukan dari user internal DAN pengirimnya kontak terdaftar diteruskan ke
`self.env['mail.thread'].with_context(fetchmail_cron_running=True,
default_fetchmail_server_id=server.id).message_process(...)` — jalur pemrosesan RFC2822 standar
Odoo core, dengan context yang sama seperti core (`save_original`/`strip_attachments` dari
konfigurasi server). `[HASIL-BACA]`
**Lokasi kode:** `models/mail.py:109-129`

### BR-07 — `message_new()` di-extend (bukan override total) — blokir auto-create `res.partner` dari email
Kalau model target `mail.thread` yang menangani alias adalah `res.partner`
(`self._name == 'res.partner'`): cari partner existing by email (`=ilike`); kalau ketemu,
KEMBALIKAN partner itu (bukan buat baru); kalau TIDAK ketemu, kembalikan `False` (skip pembuatan
record baru sama sekali, TIDAK memanggil `super()`). Untuk model LAIN (bukan `res.partner`),
delegasi penuh ke `super().message_new(...)` — perilaku core Odoo standar tidak berubah.
`[HASIL-BACA]`
**Lokasi kode:** `models/mail.py:22-43`

### BR-08 — Ringkasan log per siklus fetch
Tiap server selesai diproses, satu baris log info dicetak: jumlah total fetched (`count`),
"succeeded" (dihitung `count - failed`), `failed`, `skipped`. `[PERLU-KEPUTUSAN]` — lihat F-08 di
`FINDINGS.md`: nilai "succeeded" salah hitung.
**Lokasi kode:** `models/mail.py:138-141`

---
