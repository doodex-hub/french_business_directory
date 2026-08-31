# Acceptance Criteria — personal_email_usage

**Module:** `personal_email_usage`
**Ref:** `01A_FUNCTIONAL_SPEC.md`
**Last Updated:** 2026-08-07
**Status:** Backfill retroaktif

---

## AC-01 — Field kontrol baru

**AC-01-01** — ref `BR-01` `[HASIL-BACA]`
Given `fetchmail.server` record apapun
When form Incoming Mail Server dibuka (Settings → Technical → Email, `base.group_no_one`)
Then field `mark_read` (checkbox, default OFF) muncul setelah field `attach`.

---

## AC-02 — Server bukan-IMAP tidak terpengaruh

**AC-02-01** — ref `BR-02` `[HASIL-BACA]`
Given `fetchmail.server` dengan `server_type != 'imap'` (mis. `pop`)
When `fetch_mail()` dipanggil (manual atau cron)
Then perilaku SAMA PERSIS dengan Odoo core (`super().fetch_mail()` dipanggil apa adanya) — field
`mark_read`/filter user-internal/filter kontak TIDAK berlaku untuk server tipe ini.

---

## AC-03 — Status baca (Seen/Unseen) sesuai `mark_read`

**AC-03-01** — ref `BR-03` `[HASIL-BACA]`
Given `mark_read = True`, email UNSEEN baru masuk di server IMAP
When cron `fetch_mail()` jalan dan email berhasil diproses (`message_process` sukses)
Then email tersebut ditandai `\Seen` (dibaca) di server setelah fetch.

**AC-03-02** — ref `BR-03` `[HASIL-BACA]`
Given `mark_read = False` (default), email UNSEEN baru masuk, DAN pengirim adalah kontak terdaftar
When cron `fetch_mail()` jalan dan email berhasil diproses
Then email tetap UNSEEN di server (flag `\Seen` dihapus, tidak diset ulang) — TAPI `message_id`
tercatat di `processed_message_ids`, sehingga TIDAK diproses ulang di cron berikutnya walau statusnya
tetap UNSEEN.

**AC-03-03** — ref `BR-03`, F-07 `[PERLU-KEPUTUSAN]`
Given `mark_read = False` (default), email dari user internal Odoo ATAU dari alamat yang bukan
kontak terdaftar
When cron `fetch_mail()` jalan (skip terjadi di BR-04/BR-05)
Then email tetap UNSEEN (sama seperti AC-03-02) TAPI `message_id` TIDAK tercatat di
`processed_message_ids` — akibatnya email yang SAMA muncul lagi di search `(UNSEEN)` cron
BERIKUTNYA, di-fetch ulang, di-skip lagi, SELAMANYA (lihat F-07 `FINDINGS.md` untuk dampak
resource/log).

---

## AC-04 — Filter user internal

**AC-04-01** — ref `BR-04` `[HASIL-BACA]`
Given email masuk dari alamat yang cocok dengan `res.users.login` (user dengan `share = False`)
When `fetch_mail()` memproses email itu
Then `message_process()` TIDAK dipanggil, counter `skipped` bertambah 1, log info "Skipped email
from user: {{email}}" tercatat.

---

## AC-05 — Filter kontak terdaftar

**AC-05-01** — ref `BR-05` `[HASIL-BACA]`
Given email masuk dari alamat yang BUKAN user internal DAN TIDAK cocok `res.partner.email` manapun
When `fetch_mail()` memproses email itu
Then `message_process()` TIDAK dipanggil, counter `skipped` bertambah 1, log info "Skipped email
from non-contact: {{email}}" tercatat.

**AC-05-02** — ref `BR-05` `[HASIL-BACA]`
Given email masuk dari alamat yang BUKAN user internal DAN cocok `res.partner.email`
When `fetch_mail()` memproses email itu
Then `message_process()` DIPANGGIL dengan payload RFC822 mentah + context
`fetchmail_cron_running=True`.

---

## AC-06 — `message_new()` tidak membuat partner baru dari email

**AC-06-01** — ref `BR-07` `[HASIL-BACA]`
Given alias `mail.alias` yang menargetkan model `res.partner`, email masuk dari alamat yang cocok
`res.partner.email` yang SUDAH ADA
When `message_new()` dipanggil (dari `message_process`, `self._name == 'res.partner'`)
Then partner yang SUDAH ADA itu dikembalikan — TIDAK ada record `res.partner` baru dibuat.

**AC-06-02** — ref `BR-07` `[HASIL-BACA]`
Given alias `mail.alias` yang menargetkan model `res.partner`, email masuk dari alamat yang TIDAK
cocok `res.partner.email` manapun
When `message_new()` dipanggil
Then `False` dikembalikan — pembuatan `res.partner` baru dari email ini DIBATALKAN (bukan fallback
ke perilaku core `super()`).

**AC-06-03** — ref `BR-07` `[HASIL-BACA]`
Given `mail.thread.message_new()` dipanggil untuk model SELAIN `res.partner` (mis. `crm.lead`,
`project.task`)
When method dieksekusi
Then delegasi penuh ke `super().message_new(...)` — perilaku core Odoo standar, tidak berubah sama
sekali oleh modul ini.

---

## AC-07 — Log ringkasan siklus fetch

**AC-07-01** — ref `BR-08`, F-08 `[PERLU-KEPUTUSAN]`
Given satu siklus `fetch_mail()` selesai dengan `count=3` sukses, `failed=1`, `skipped=2`
When baris log ringkasan dicetak
Then log SEKARANG menampilkan "succeeded" = `2` (yaitu `count - failed` = `3 - 1`), padahal jumlah
sukses SEBENARNYA adalah `3` (`count`) — angka di log menyesatkan (lihat F-08 `FINDINGS.md`).

---
