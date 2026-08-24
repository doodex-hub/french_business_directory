# Test Plan (Migrasi) — french_business_directory

**Step:** 5 — Acceptance Criteria & Test Plan
**Ref:** `05_acceptance/05a_MIGRATION_ACCEPTANCE_CRITERIA.md`
**Tanggal:** 2026-08-24

> Tidak ada komponen Owl/JS di modul ini (`01a_MIGRATION_INTAKE.md` §2b) — kolom "Tour" selalu N/A.

---

## Step 9 — Dev Testing

> Eksekusi: otomatis/background — `odoo-bin -i fr_business_directory,personal_email_usage --test-enable --test-tags /fr_business_directory,/personal_email_usage --stop-after-init`.

| AC | Deskripsi | Unit | Integration | Tour |
|---|---|---|---|---|
| AC-01-01 | Tombol muncul hanya untuk company | — | ✓ (render form, cek visibility) | N/A |
| AC-02-01 | Auto-fetch saat wizard dibuka | ✓ (mock `requests.get`) | ✓ | N/A |
| AC-03-01/02 | Paginasi wrap-around | ✓ | — | N/A |
| AC-03-03 | `[PRESERVE-BUG]` param hilang di Prev | ✓ (assert URL tidak mengandung param) | — | N/A |
| AC-03-04 | `[PRESERVE-BUG]` no-op partner_name kosong | ✓ | — | N/A |
| AC-04-01 | Select overwrite partner | ✓ | ✓ | N/A |
| AC-04-02 | Select isi department (kalau model ada) | — | ⚠️ Butuh `third-party-*` (MF-01) — SKIP kalau tidak tersedia, catat sebagai "tidak dijalankan" bukan "pass" | N/A |
| AC-04-03 | Select TIDAK isi department (model tidak ada) | ✓ (kondisi default environment test) | ✓ | N/A |
| AC-05-01/02 | Badge status administratif | ✓ | — | N/A |
| AC-05-03 | Terjemahan kode aktivitas | ✓ | — | N/A |
| AC-06-01 | `social_reason` tracking | ✓ | — | N/A |
| AC-07-01 | `[PRESERVE-BUG]` NameError `_logger` | ✓ (mock response tanpa `nom_complet`, assert `NameError` raised) | — | N/A |
| AC-07-02 | Tidak ada method collision | ✓ (install test bersih, lihat G1) | — | N/A |
| AC-08-01/02 | Routing fetch per tipe server | ✓ (mock IMAP/POP connection) | ✓ | N/A |
| AC-08-03 | `[COMPAT-FIX]` `fetch_mail(raise_exception=...)` tidak `TypeError` | ✓ (panggil dengan & tanpa kwarg) | ✓ (jalankan `_fetch_mails()` cron method langsung) | N/A |
| AC-09-01/02/03 | Filter pengirim (internal/non-kontak/valid) | ✓ | ✓ | N/A |
| AC-10-01/02/03 | `message_new()` blokir auto-create | ✓ | ✓ | N/A |
| AC-11-01 | `[PRESERVE-BUG]` re-fetch tanpa henti | ✓ (assert `processed_ids` tidak bertambah di jalur skip, 2 siklus cron berturut menemukan email sama) | — | N/A |
| AC-11-02 | `[PRESERVE-BUG]` log salah hitung | ✓ (assert isi log message) | — | N/A |

**Catatan audit kesiapan test (9a):** source module TIDAK punya folder `tests/` sama sekali di 17.0 (dikonfirmasi `01a_MIGRATION_INTAKE.md` — tidak ada `tests/` di listing file source). Semua unit/integration test di atas adalah **test BARU** yang perlu ditulis di Step 6/9 dari nol (bukan port test lama) — tidak ada risiko "stub kosong seperti `totp_enhancement`" karena memang belum ada apapun untuk diaudit.

## Step 10 — QA Testing

| AC | Deskripsi | Manual | AI-interaktif | AI+tool eksternal |
|---|---|---|---|---|
| AC-01-01, AC-02-01, AC-03-*, AC-04-* | Alur wizard SIRET end-to-end (buka form → klik tombol → cari → paginasi → select) | ✓ | ✓ (Claude in Chrome, kalau tersedia) | — |
| AC-04-02 | Select dengan `res.country.department` tersedia | ✓ (kalau QA punya akses instance dengan addon OCA terinstall — lihat MF-01) | — | — |
| AC-05-*, AC-06-01 | Tampilan badge, tracking chatter | ✓ | ✓ | — |
| AC-08-*, AC-09-*, AC-10-* | Fetch email end-to-end (perlu mailbox IMAP test nyata) | ✓ (QA setup mailbox test) | — | ✓ (script Python simulasi IMAP kalau QA tidak punya akses mailbox nyata) |
| AC-11-01 | Verifikasi re-fetch tanpa henti (regresi, bukan bug baru) | ✓ (jalankan cron 2x manual, screenshot log) | — | — |

## Step 11 — UAT

| Kelompok fitur | AC tercakup | UAT |
|---|---|---|
| Pencarian & isi data perusahaan Perancis (SIRET) | AC-01 s/d AC-07 | Business user cari & isi data kontak company nyata, bandingkan hasil dengan instance 17.0 produksi |
| Kontrol fetch email lanjutan | AC-08 s/d AC-11 | Admin sistem verifikasi email fetch tetap berjalan sesuai konfigurasi `mark_read` yang sama seperti 17.0 |

## Ringkasan

| Step | Role | Tipe | Eksekusi | Jumlah AC |
|---|---|---|---|---|
| 9 | Developer | Unit/Integration (tidak ada Tour — tidak ada Owl/JS) | Otomatis/background | 21 AC, 1 kondisional (AC-04-02, butuh third-party) |
| 10 | QA | Manual/AI-interaktif/AI+tool eksternal | Campuran per skenario | 21 AC |
| 11 | PM/FA/User | UAT | Manual (selalu) | 2 kelompok fitur |
