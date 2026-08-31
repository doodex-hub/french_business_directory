# Email Gaps — personal_email_usage

**Level:** Campuran (Detail + Negative) — semua terkait modul email (`personal_email_usage`), belum tercakup S-01..S-08.
**Estimasi waktu:** ~20 menit (semua skenario).
**Sumber:** analisis gap terhadap `models/mail.py`, `tests/test_fetchmail.py`, dan `LISEZMOI.md` (fitur yang dipasarkan) — dibuat 2026-08-31, di luar S-XX awal karena S-02/S-04/S-07 hanya menutup sebagian fitur modul ini.

## Kenapa file ini ada

`10_BUSINESS_FLOW_MIGRATION.md` menandai email module "Lulus" lewat S-02 (cron tidak crash), S-04 (kontak dikenal diproses), S-07 (tidak ada partner baru dari email). Tapi ketiganya cuma menguji jalur utama. Baca kode `mail.py` + `test_fetchmail.py` baris-per-baris menunjukkan beberapa cabang logic tidak disentuh sama sekali oleh test suite maupun QA manual manapun.

**PENTING — koreksi setelah cross-check dengan Step 9 (`09_DEV_TESTING.md`) dan `05a_MIGRATION_ACCEPTANCE_CRITERIA.md`:** tidak semua isi file ini "baru ditemukan". Dua kategori:

1. **Sudah diketahui & disclosure eksplisit oleh Step 9** (bukan gap tersembunyi — tim sudah sadar dan punya alasan): AC-01-01 (tombol UI, dilimpahkan ke Step 10), **AC-08-02 (delegasi POP3 — "kompleksitas mocking POP3 tidak sepadan untuk modul ini")**, AC-11-02 (log count salah, dianggap terlalu brittle untuk unit test). S-13 dan sebagian S-15 di bawah tumpang tindih dengan ini — dicantumkan di sini cuma supaya satu file ini lengkap sebagai checklist, BUKAN klaim temuan baru.
2. **Genuinely tidak pernah jadi acceptance criteria sama sekali** — tidak ada `BSL-XX` di `01b_BASELINE_SPEC.md`, tidak ada `AC-XX` di `05a_MIGRATION_ACCEPTANCE_CRITERIA.md`: **S-09, S-10, S-11, S-12, S-14**. Ini yang benar-benar gap baru, termasuk satu fitur yang DIPASARKAN di `LISEZMOI.md` ("Contrôle du Statut de Lecture" / `mark_read=True`) yang ternyata nol test DAN nol acceptance criteria menyentuhnya.

---

### S-09: `mark_read=True` benar-benar menandai email sebagai read di server IMAP
**Level:** Detail
**Kenapa gap:** Field `mark_read` (`mail.py` baris ~55) adalah fitur yang dipasarkan eksplisit di `LISEZMOI.md` ("Read Status Control"). Semua test di `test_fetchmail.py` pakai `imap_server` default (`mark_read=False` implisit). Tidak ada satu pun test/skenario QA yang set `mark_read=True` dan verifikasi `imap_server.store(num, '+FLAGS', '\\Seen')` benar-benar terpanggil.
**Precondition:** Server IMAP dengan `mark_read=True`
**Steps (otomatis, mock IMAP seperti test lain):**
```
1. Buat fetchmail.server dengan mark_read=True
2. Fetch mail dari kontak dikenal (conn mock)
3. Assert conn.store dipanggil dengan ('+FLAGS', '\\Seen') untuk message tsb
   (bukan cuma '-FLAGS', '\\Seen' yang selalu dipanggil di awal)
```
**Steps (manual UI, kalau mau verifikasi visual):**
```
1. Settings > Technical > Automation > Incoming Mail Servers, buka server, centang "Mark Emails as Read" (field ini groups="base.group_no_one" — perlu Developer mode aktif)
2. Kirim email test dari kontak dikenal, "Fetch Now"
3. Cek langsung di mailbox (webmail/IMAP client lain) — email itu harus berstatus "read", bukan "unread"
```
**Expected:** Email marked read di server ketika `mark_read=True`; tetap unread (default) ketika `mark_read=False`
**Status:** [x] ✅ Ditutup 2026-08-31 — lihat `FINDINGS.md` MF-11 (port `TC-FLAG-01` dari backfill). Dua method (`test_mark_read_true_reapplies_seen_flag`, `test_mark_read_false_does_not_reapply_seen_flag`) ditambahkan ke `personal_email_usage/tests/test_fetchmail.py`, persis menutup skenario "otomatis" di atas (assert `store(+FLAGS, \Seen)` dipanggil/tidak dipanggil). Steps "manual UI" di bawah TETAP belum dijalankan (sama kendala tooling seperti S-01/S-15).

---

### S-10: Email dengan `Message-ID` yang sudah ada di `processed_message_ids` di-skip, tidak diproses ulang
**Level:** Detail
**Kenapa gap:** Ini fungsi UTAMA dari field `processed_message_ids` (cek `if message_id in processed_ids: continue`, `mail.py` baris ~90) — tapi tidak ada test yang menjalankan `fetch_mail()` DUA KALI dengan message_id yang sama untuk verifikasi panggilan kedua benar-benar skip. Test yang ada (`test_processed_email_recorded_in_processed_ids`) cuma cek ID tersimpan setelah SATU kali fetch, bukan bahwa fetch berikutnya benar-benar skip pemrosesan ulang.
**Precondition:** Server IMAP, satu partner dikenal
**Steps (otomatis):**
```
1. Fetch mail sekali dari known@example.com, message-id <dup@example.com> → tersimpan di processed_message_ids
2. Fetch mail LAGI dengan email yang sama (message-id sama, masih muncul di hasil UNSEEN mock)
3. Assert message_process TIDAK dipanggil kedua kalinya (mock_process.call_count tetap 1, bukan 2)
```
**Expected:** Email dengan message-id yang sudah tercatat tidak pernah diteruskan ke `message_process` lagi
**Status:** [x] ✅ Ditutup 2026-08-31 — `test_duplicate_message_id_skipped_on_repeat_fetch` ditambahkan ke `test_fetchmail.py`, dua kali panggil `fetch_mail()` dengan message-id sama, dikonfirmasi `message_process` cuma dipanggil sekali

---

### S-11: Exception saat `message_process()` tidak menghentikan cron — email lain tetap diproses
**Level:** Negative
**Kenapa gap:** Blok `try/except` di sekitar `message_process` (`mail.py` baris ~131-138) menangkap exception per-email dan increment `failed`, lalu lanjut ke email berikutnya. Tidak ada test yang membuat `message_process` raise exception untuk verifikasi: (a) cron tidak crash total, (b) email berikutnya di batch yang sama tetap diproses, (c) email yang gagal itu TIDAK masuk `processed_message_ids` (jadi akan di-retry cron berikutnya).
**Precondition:** 2 email UNSEEN dari kontak dikenal dalam satu batch fetch
**Steps (otomatis):**
```
1. Mock message_process: raise Exception untuk email #1, return 999 untuk email #2
2. Jalankan fetch_mail()
3. Assert: tidak ada exception yang menembus ke pemanggil, message_process dipanggil 2x (email #2 tetap diproses meski #1 gagal), message-id email #1 TIDAK ada di processed_message_ids, message-id email #2 ADA
```
**Expected:** Satu email gagal tidak menghentikan batch; kegagalan tidak ditandai processed (akan di-retry)
**Status:** [x] ✅ Ditutup 2026-08-31 — `test_message_process_exception_does_not_abort_batch` ditambahkan, 2 email dalam satu fetch (email #1 raise, email #2 sukses), dikonfirmasi keduanya diproses (`call_count == 2`), email #1 TIDAK masuk `processed_message_ids`, email #2 masuk

---

### S-12: Kegagalan koneksi/search IMAP (mis. auth salah) tidak crash cron, server lain tetap jalan
**Level:** Negative
**Kenapa gap:** Try/except terluar (`mail.py` baris ~76 s.d. akhir loop) menangani kegagalan `server.connect()` atau `imap_server.search()` — tidak ada test yang membuat `connect()` sendiri raise exception (beda dari test yang ada, yang semua asumsi connect() sukses lalu mock method IMAP-nya). Juga belum ada test dengan LEBIH DARI SATU server IMAP dalam satu pemanggilan `fetch_mail()` untuk verifikasi satu server gagal tidak menghentikan pemrosesan server lain (`for server in self.filtered(...)` — loop per server).
**Precondition:** 2 fetchmail.server bertipe IMAP
**Steps (otomatis):**
```
1. Server A: connect() raise exception (mis. simulasi auth gagal)
2. Server B: connect() sukses, ada email dari kontak dikenal
3. Panggil fetch_mail() pada recordset gabungan (server A + B)
4. Assert: tidak ada exception menembus ke pemanggil, message_process TETAP dipanggil untuk email di server B
```
**Expected:** Kegagalan satu server IMAP tidak menghalangi server IMAP lain diproses dalam batch yang sama
**Status:** [x] ✅ Ditutup 2026-08-31 — `test_one_server_connect_failure_does_not_block_other_servers` ditambahkan, server A `connect()` raise, server B sukses dengan email dari kontak dikenal, dikonfirmasi `message_process` tetap terpanggil untuk email server B (log nyata: "General failure ... Test IMAP" lalu "Fetched 1 email(s) ... Test IMAP B; 1 succeeded")

---

### S-13: Server non-IMAP (mis. POP3) tetap diproses lewat `fetch_mail()` bawaan Odoo, tidak lewat override
**Level:** Detail
**Kenapa gap — KOREKSI, ini BUKAN temuan baru:** ini persis `AC-08-02` di `05a_MIGRATION_ACCEPTANCE_CRITERIA.md`, sudah eksplisit ditandai `⚠️ POP tidak dicover` di `09_DEV_TESTING.md` dengan alasan "kompleksitas mocking POP3 tidak sepadan untuk modul ini", dan sudah diverifikasi lewat inspeksi kode statis (Step 8). Dicantumkan di sini murni supaya checklist ini lengkap — kalau mau override keputusan Step 9 (misal karena sekarang ada waktu), jalankan langkah di bawah; kalau tidak, biarkan status Step 9 yang berlaku.
**Precondition:** 1 server IMAP + 1 server POP3 dalam satu recordset
**Steps (otomatis):**
```
1. Buat fetchmail.server kedua dengan server_type='pop', mock/patch method fetch_mail milik parent class (native mail.fetchmail.server) untuk server ini
2. Panggil fetch_mail() pada gabungan kedua server
3. Assert: parent fetch_mail() (native, non-IMAP path) terpanggil untuk server POP3, logic filtering (mark_read/skip user/skip non-contact) TIDAK diterapkan padanya
```
**Expected:** Server POP3 tidak tersentuh logic filtering modul ini — perilaku sama seperti sebelum modul diinstall
**Status:** Belum dites otomatis — diverifikasi via code review Step 8, keputusan sadar AC-08-02 (`05a_MIGRATION_ACCEPTANCE_CRITERIA.md`), kompleksitas mock POP3 dianggap tidak sepadan untuk modul ini. Bukan gap yang terlewat.

---

### S-14: `strip_attachments`/`save_original` (field `attach`/`original` bawaan Odoo) tetap diteruskan dengan benar ke `message_process`
**Level:** Detail
**Kenapa gap:** `mail.py` baris ~127-128 meneruskan `save_original=server.original, strip_attachments=(not server.attach)` — nilai ini tidak pernah diverifikasi di test manapun (semua test mock `message_process` tanpa assert kwargs selain arg pertama/model).
**Precondition:** Server dengan `attach=True` (lampiran disimpan) vs `attach=False` (lampiran di-strip)
**Steps (otomatis):**
```
1. Set server.attach = False, fetch email dari kontak dikenal
2. Assert mock_process dipanggil dengan strip_attachments=True
3. Ulangi dengan server.attach = True → assert strip_attachments=False
```
**Expected:** Flag lampiran/original mengikuti konfigurasi form server persis seperti sebelum modul ini menambahkan filtering
**Status:** [x] ✅ Ditutup 2026-08-31 — `test_attach_and_original_flags_forwarded_to_message_process` ditambahkan, `attach=False` → `strip_attachments=True` dan sebaliknya, dikonfirmasi via `call_args.kwargs`. (`save_original`/`server.original` tidak diuji terpisah — sama pola kode, kwarg sejenis, dianggap cukup terwakili)

---

### S-15 (manual UI, rekomendasi sebelum rilis besar): Verifikasi visual field "Mark Emails as Read" muncul & berfungsi di form
**Level:** Detail — pelengkap S-09, bukan pengganti
**Kenapa gap:** beda dari S-13 di atas — field `mark_read` sendiri TIDAK ADA di AC-01 (yang cuma soal tombol Business Directory) atau AC manapun. Jadi ini genuinely belum pernah jadi acceptance criteria, bukan cuma "dilimpahkan ke Step 10" seperti AC-01-01. `views/mail_views.xml` menambahkan field `mark_read` dengan `groups="base.group_no_one"` (hanya tampil kalau Developer Mode aktif) — belum pernah diklik/dicentang langsung di browser sungguhan (kendala tooling browser yang sama seperti S-01, lihat catatan di `10_BUSINESS_FLOW_MIGRATION.md`).
**Precondition:** Developer mode aktif
**Steps:**
```
1. Aktifkan Developer Mode
2. Settings > Technical > Automation > Incoming Mail Servers > buka satu server IMAP
3. Field "Mark Emails as Read" harus muncul persis setelah field "Keep Attachments" (posisi xpath: after attach)
4. Centang, Save — reload halaman, pastikan nilai tersimpan (bukan cuma di-render, benar-benar persisten)
```
**Expected:** Field muncul di posisi benar, toggle tersimpan setelah reload
**Status:** ⚠️ **Sebagian dites 2026-08-31 via Playwright MCP** (bukan "kendala tooling" generik — detail konkret di bawah):

- **Langkah 1-3 (Pass, terverifikasi visual nyata):** Developer mode aktif, navigasi Settings → Technical → Incoming Mail Servers → New berhasil lewat Playwright MCP (headless, DOM-based, render sukses — beda dari percobaan S-01 sebelumnya yang gagal total karena webclient tidak mount). Field **"Mark Emails as Read" dikonfirmasi ADA**, posisinya PERSIS setelah "Keep Attachments" di tab Advanced (sesuai xpath `after attach`), checkbox bisa dicentang (state `checked` terkonfirmasi di accessibility snapshot & screenshot).
- **Langkah 4 (Fail — BUKAN karena modul, kemungkinan bug Odoo build ini):** tombol "Save manually" (`button.o_form_button_save`) TIDAK PERNAH benar-benar menyimpan record, walau dicoba 7 cara berbeda: klik via accessibility role locator (×3), `element.click()` langsung via JS, dispatch manual urutan penuh `pointerdown/mousedown/pointerup/mouseup/click` dengan koordinat asli, hotkey `Alt+S` (sesuai `data-hotkey="s"` di DOM), dan percobaan ulang di form baru yang benar-benar bersih. **Dikonfirmasi ganda:**
  1. Event `click` genuinely diterima elemen (dibuktikan lewat listener sementara yang di-attach manual — `window.__clickReceived = true`).
  2. TIDAK ADA request `call_kw/fetchmail.server/create` atau `web_save` apapun yang terkirim ke server (dicek `browser_network_requests` berkali-kali).
  3. TIDAK ADA error/exception/notification/invalid-field apapun di console, DOM (`.o_notification`, `.o_field_invalid`), maupun `unhandledrejection`/`window.onerror` (listener sementara dipasang, tetap kosong).
  4. Dikonfirmasi server-side via `odoo shell` langsung: `env['fetchmail.server'].search([('name','like','S-15')])` → recordset KOSONG — record genuinely tidak pernah tersimpan.
  5. Mencoba navigasi keluar memicu dialog native "unsaved changes" browser — membuktikan form memang masih dianggap dirty oleh Odoo sendiri, konsisten dengan save yang tidak pernah sukses.
- **Kesimpulan:** klik terkirim & diterima DOM, tapi tidak memicu RPC/error apapun — mengarah ke kemungkinan bug di build Odoo `18.0-20260817` (nightly/dev snapshot) itu sendiri, BUKAN masalah kode `personal_email_usage`, bukan juga masalah render Playwright MCP (render & interaksi field lain semuanya berhasil normal). Belum dikonfirmasi apakah ini reproduce di build Odoo 18.0 stable lain.
- **Langkah 4 TETAP belum diverifikasi** (persistence setelah reload) — butuh investigasi lebih lanjut (kandidat: coba build Odoo 18.0 berbeda, atau observasi manual dev sendiri di browser non-headless untuk exclude Playwright sepenuhnya) sebelum bisa dianggap selesai.

---

## Ringkasan

| # | Skenario | Level | Kenapa belum tercakup S-01..S-08 |
|---|---|---|---|
| S-09 | `mark_read=True` → email ditandai read di server | Detail | ✅ **Ditutup 2026-08-31** (MF-11) — sebelumnya fitur dipasarkan di `LISEZMOI.md` tanpa test |
| S-10 | Message-ID duplikat di-skip, tidak diproses ulang | Detail | ✅ **Ditutup 2026-08-31** — sebelumnya cuma dites "tersimpan", bukan "efektif mencegah reproses" |
| S-11 | Exception di `message_process()` tidak menghentikan batch | Negative | ✅ **Ditutup 2026-08-31** — sebelumnya try/except per-email tidak pernah dipicu di test |
| S-12 | Kegagalan koneksi satu server tidak hentikan server lain | Negative | ✅ **Ditutup 2026-08-31** — sebelumnya semua test asumsi `connect()` sukses, belum ada multi-server |
| S-13 | Server POP3 tetap lewat jalur native, tidak kena filtering | Detail | **BUKAN gap yang terlewat** — persis `AC-08-02`, keputusan sadar Step 8/9, kompleksitas mock POP3 dianggap tidak sepadan |
| S-14 | `strip_attachments`/`save_original` diteruskan benar | Detail | ✅ **Ditutup 2026-08-31** (`strip_attachments` saja — `save_original` dianggap cukup terwakili) |
| S-15 | Field "Mark Emails as Read" tampil & tersimpan di UI | Detail | ⚠️ **Sebagian ditutup 2026-08-31** — field ADA & posisi benar (Playwright MCP, terverifikasi visual nyata). Persistence (Save) TIDAK bisa diverifikasi — klik terkirim tapi save tidak pernah jalan, kemungkinan bug Odoo build ini, BUKAN masalah modul/Playwright — lihat detail lengkap di bawah |

**Status akhir (2026-08-31):** S-09, S-10, S-11, S-12, S-14 semua ditutup — semuanya PASS saat dieksekusi nyata (tidak ada satupun yang mengungkap bug baru; `personal_email_usage` sekarang 16 test, naik dari 10 di Step 9 awal). S-13 diklarifikasi (bukan gap baru, keputusan sadar Step 9). **S-15 SEBAGIAN ditutup** — field `mark_read` dikonfirmasi ADA & posisi benar via Playwright MCP (render sungguhan, bukan lagi kendala tooling seperti S-01), TAPI verifikasi persistence (Save) menemukan kemungkinan bug nyata di build Odoo `18.0-20260817` sendiri (klik terkirim, tidak ada RPC/error, save tidak pernah sukses) — lihat `FINDINGS.md` MF-13 untuk detail lengkap.

**Catatan:** semua skenario yang ditutup PASS tanpa mengungkap bug baru — murni menutup gap cakupan test, bukan menemukan regresi. Kalau S-13/S-15 nanti dijalankan dan ternyata gagal, catat sebagai finding baru (format `MF-NNN` di `FINDINGS.md`, ref ke S-XX ini) dan evaluasi apakah mengganjal Step 11 (UAT) yang sudah diterima.
