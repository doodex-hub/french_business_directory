# QA Testing — personal_email_usage

**Step:** 07 — QA Testing (backfill, TANPA UAT — BACKFILL berhenti di sini)
**Ref:** `doc-dev/backfill/spec/personal_email_usage/01A_FUNCTIONAL_SPEC.md`,
`doc-dev/backfill/spec/personal_email_usage/01B_ACCEPTANCE_CRITERIA.md`, `03B_TEST_PLAN.md`
**Tanggal:** 2026-08-07

---

## 1. Area / AC yang Harus Dicakup

- [x] AC-01 — Field `mark_read` muncul di Technical Settings
- [x] AC-02 — Server non-IMAP tidak terpengaruh
- [x] AC-03 — Flag `\Seen` sesuai `mark_read`
- [x] AC-04/AC-05 — Filter user internal & non-kontak (F-07)
- [x] AC-06 — `message_new()` override
- [x] AC-07 — Log ringkasan (F-08)

**Cek "hanya satu dialog disentuh"** — **N/A**: modul ini tidak punya dialog/wizard UI sama sekali
(satu-satunya elemen UI adalah satu checkbox di form Technical Settings existing Odoo, tidak ada
popup/wizard baru).

---

## 2. Format Skenario

Sama seperti `fr_business_directory/07_QA_TESTING.md` §2 — tidak diulang di sini.

---

## 3. Skenario

### S-01: Field `mark_read` tampil di Incoming Mail Server (Technical Settings)
**Precondition:** User dengan akses `base.group_no_one` (Developer mode/Technical Settings aktif).
**Mode eksekusi:** Desk-review (baca `views/mail_views.xml:8-10`, `xpath` menyisipkan field
`mark_read` setelah field `attach`, `groups="base.group_no_one"`).
**Steps:**
1. Baca XML: `inherit_id="mail.view_email_server_form"`, xpath target
   `//field[@name='attach']`, posisi `after`.
2. Bandingkan dengan konvensi Odoo standar untuk field baru di Technical Settings.
**Expected:** Field muncul HANYA untuk user dengan Developer mode aktif, tepat setelah field
"Keep Attachments" di form Incoming Mail Server.
**Actual:** Sesuai expected — xpath valid secara statis, mengikuti konvensi Odoo yang benar (tidak
ada indikasi field akan gagal render atau salah posisi).
**Status:** ✔️ Pass (desk-review)
**Provenance:** `[HASIL-BACA]`

### S-02: Review cakupan Unit test untuk seluruh logic `fetch_mail()`/`message_new()`
**Precondition:** —
**Mode eksekusi:** Review hasil eksekusi nyata Step 04 (bukan eksekusi baru) — modul ini TIDAK
punya elemen UI end-user (form Technical Settings saja, lihat S-01), sehingga AI-interaktif Step 07
untuk modul ini berupa REVIEW kelengkapan Unit test terhadap AC, bukan skenario UI baru.
**Steps:**
1. Cocokkan tiap AC (`01B_ACCEPTANCE_CRITERIA.md`) ke TC yang sesuai di `04A_DEV_TESTING.md`.
2. Pastikan semua AC punya minimal 1 TC yang PERNAH dijalankan nyata (bukan cuma ditulis).
**Expected:** Semua AC (AC-02 s.d. AC-07) punya TC yang dieksekusi nyata dan Pass.
**Actual:** Terkonfirmasi — 12 TC (21 test method) semuanya PASS di run terakhir (`0 failed, 0
error(s) of 26`, gabungan dengan `fr_business_directory`, lihat `04A_DEV_TESTING.md` §3). Tidak ada
AC yang hanya "diklaim" tanpa eksekusi.
**Status:** ✔️ Pass
**Provenance:** `[DIKONFIRMASI]`

---

## 4. Status Sub-file & Rekap Eksekusi

| File | Isi | Status | Dieksekusi? | Mode |
|---|---|---|---|---|
| §3 di file ini | 2 skenario (desk-review + review Unit test) | ✅ Selesai | Ya | Desk-review + review Unit test Step 04 |
| `07B_QA_AI_BROWSER.md` | N/A — tidak ada flow UI end-user yang butuh verifikasi visual browser | N/A | Tidak | — |

**Keterbatasan eksekusi:** Level pipeline PENUH incoming email (GreenMail, `fetchmail.server`
sungguhan polling mailbox eksternal) **TIDAK dijalankan** — lihat `03B_TEST_PLAN.md` (kondisional,
tidak wajib untuk klaim "incoming email tercover" karena level logic sudah tercover penuh via Unit
test nyata). Dicatat eksplisit sebagai keterbatasan, bukan diklaim "pipeline penuh sudah dites".

---

## 5. Rekap Findings

| Tag | Jumlah |
|---|---|
| `[PERLU-KEPUTUSAN]` | 3 (F-07, F-08, F-11 — lihat `FINDINGS.md`) |
| `[DIKONFIRMASI]` | — (belum ada keputusan pemilik modul) |
| `[HASIL-BACA]` (tanpa masalah, termasuk housekeeping F-09/F-10) | BR-01, BR-04, BR-06 (parsial), BR-07 |

**Verdict:** Backfill dokumentasi selesai sampai Step 07 (QA Testing). **Tidak ada sign-off.**
Keputusan atas item `[PERLU-KEPUTUSAN]` di `FINDINGS.md` ada di tangan pemilik modul — **F-07
(prioritas TINGGI)** sangat direkomendasikan untuk direview segera karena berdampak resource/log
di produksi dengan konfigurasi DEFAULT modul (`mark_read=False`).

---

## 6. Bug / Perlu Perbaikan

> Semua skenario §3 Pass. Bug/gap (F-07, F-08, F-09, F-10, F-11) adalah temuan dari membuktikan
> perilaku kode sekarang, detail lengkap di `FINDINGS.md`.

| Ditemukan di | Scenario | Ringkasan masalah | Status perbaikan |
|---|---|---|---|
| Tidak ada | — | — | — |
