# Test Plan — personal_email_usage

**Module:** `personal_email_usage`
**Ref:** `doc-dev/backfill/spec/personal_email_usage/01B_ACCEPTANCE_CRITERIA.md`
**Dibuat oleh:** BACKFILL (Step 03B, backfill)
**Last Updated:** 2026-08-07

> Modul ini bergantung ke protokol IMAP nyata (`imaplib`) — level LOGIC (skip-user, skip-non-kontak,
> dedup, flag sequencing, override `message_new`) diuji Unit dengan `unittest.mock.patch` pada
> `fetchmail.server.connect()` (mengganti koneksi IMAP asli dengan `MagicMock` yang mensimulasikan
> `select()`/`search()`/`fetch()`/`store()` — teknik yang sama validitasnya dengan stub Mode D,
> TAPI test tetap `TransactionCase` biasa, bukan stub terpisah di luar `tests/`, jadi ke-discover
> normal oleh Odoo test-runner). Level PIPELINE PENUH (server IMAP sungguhan) — lihat
> `PLAYBOOK.md` §"Mode B — testing incoming email" level 2 — BUTUH `greenmail`, dipertimbangkan di
> Step 07 kalau waktu/scope memungkinkan (kondisional, bukan wajib karena level logic sudah cukup
> untuk klaim "incoming email tercover" sesuai `CLAUDE_TEMPLATE.md`).

---

## Step 04 — Developer Testing (backfill)

| AC | Deskripsi singkat | Unit | Integration | API |
|---|---|---|---|---|
| AC-01-01 | Field `mark_read` muncul di form | | | |
| AC-02-01 | Server non-IMAP delegasi penuh ke core | ✓ | | |
| AC-03-01 | `mark_read=True` → di-set balik Seen | ✓ | | |
| AC-03-02 | `mark_read=False` + sukses → tetap Unseen, tercatat processed | ✓ | | |
| AC-03-03 | `mark_read=False` + skip → tetap Unseen, TIDAK tercatat (F-07) | ✓ | | |
| AC-04-01 | Skip email dari user internal | ✓ | | |
| AC-05-01 | Skip email dari bukan-kontak | ✓ | | |
| AC-05-02 | Proses email dari kontak terdaftar → `message_process()` | ✓ | | |
| AC-06-01 | `message_new` — partner existing dikembalikan | ✓ | | |
| AC-06-02 | `message_new` — sender tidak dikenal → `False` | ✓ | | |
| AC-06-03 | `message_new` — model selain res.partner → delegasi `super()` | ✓ | | |
| AC-07-01 | Log "succeeded" salah hitung (F-08) | ✓ | | |

**AC-01-01** (field muncul di form) tidak punya nilai tambah diuji lewat `TransactionCase` murni
(cuma baca XML view) — dicakup di Step 07 (desk-review/AI-interaktif, TIDAK ada Tour headless untuk
modul ini karena UI-nya hanya Technical Settings, bukan flow bisnis end-user, lihat `07_QA_TESTING.md`).

**Email (kondisional):** **Incoming** — Level logic (`message_process()`/skip-logic dipanggil
tidak-langsung lewat `fetch_mail()` yang di-mock koneksinya) sudah tercover penuh di Unit test di
atas, TIDAK butuh `mailpit`/`greenmail` untuk level ini. Level pipeline penuh (GreenMail sebagai
mailbox sumber sungguhan) — lihat catatan di atas, kondisional Step 07.

**Ringkasan:** 11 AC → Unit (mock `connect()`/`imaplib`, TransactionCase biasa), 0 → Integration
(tidak ada controller/route HTTP baru dari modul ini — `message_process()` dipanggil langsung
sebagai method, bukan lewat HTTP endpoint), API N/A (tidak expose API eksternal).

---

## Step 07 — QA Testing (level AI-interaktif + Smoke human-confirmed, TANPA UAT)

| AC | Deskripsi singkat | AI-interaktif (07 §3) | AI-Browser/Tour (07B) |
|---|---|---|---|
| AC-01-01 | Field `mark_read` tampil di Technical Settings | ✓ | |
| AC-02-01 – AC-07-01 | Sudah tercover penuh via Unit (mock IMAP) di Step 04 | ✓ (review hasil) | |

**Ringkasan:** BACKFILL pakai AI-interaktif (`07_QA_TESTING.md` §3) sebagai default — TIDAK ada
`07B_QA_AI_BROWSER.md`/Tour untuk modul ini (tidak ada flow UI end-user yang genuinely butuh
verifikasi visual browser; satu-satunya elemen UI adalah checkbox di Technical Settings, cukup
desk-review + baca hasil test Unit). Kalau dev mau level pipeline-penuh (GreenMail, real IMAP
round-trip), itu extra verification opsional di luar gate wajib Step 07 — dicatat sebagai catatan
terbuka, bukan blocker.

---

## Ringkasan Keseluruhan

| Step | Tipe | Jumlah AC |
|---|---|---|
| 04 | Unit | 11 |
| 04 | Integration | 0 |
| 04 | Smoke | 2 happy path (fetch sukses dari kontak, skip dari user internal) |
| 04 | API | N/A |
| 07 | AI-interaktif (`07` §3) | 1 (field visibility) + review hasil Unit |
| 07 | AI-Browser (`07B`) | N/A |
