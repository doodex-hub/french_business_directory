# Test Plan — fr_business_directory

**Module:** `fr_business_directory`
**Ref:** `doc-dev/backfill/spec/fr_business_directory/01B_ACCEPTANCE_CRITERIA.md`
**Dibuat oleh:** BACKFILL (Step 03B, backfill)
**Last Updated:** 2026-08-07

> Peta AC → tipe test pakai vocab Odoo intrinsik (`TransactionCase`/`HttpCase`/Tour) — `cicd/`
> tidak tersedia/tidak dijangkau sesi ini, dipakai vocab bawaan Odoo (lihat `PLAYBOOK.md` §0).
> Panggilan HTTP ke `recherche-entreprises.api.gouv.fr` di-mock (`unittest.mock.patch`) di level Unit
> — modul ini TIDAK mengekspos API-nya sendiri (hanya KONSUMEN API eksternal), jadi kolom API =
> N/A untuk seluruh AC.

---

## Step 04 — Developer Testing (backfill)

| AC | Deskripsi singkat | Unit | Integration | API |
|---|---|---|---|---|
| AC-01-01/02 | Visibilitas tombol Business Directory | | | |
| AC-02-01 | Auto-fetch halaman 1 saat wizard dibuka | ✓ | | |
| AC-02-02 | `_logger` NameError di jalur error (F-01) | ✓ | | |
| AC-03-01/02/03 | Paginasi wrap-around Next/Prev | ✓ | | |
| AC-03-04 | Param API tidak konsisten Next vs Prev (F-02) | ✓ | | |
| AC-03-05 | No-op senyap `partner_name` kosong (F-03) | ✓ | | |
| AC-04-01/02 | Select hasil → write ke partner | ✓ | | |
| AC-04-03 | `res.country.department` tidak ada → field dilewati (F-05) | ✓ | | |
| AC-04-04 | `res.country.department` ada → field terisi | — | — | — |
| AC-05-01/02 | Badge status administratif | ✓ (compute) | | |

**AC-01-01/02** (visibilitas tombol, atribut `invisible` di XML view) dan bagian visual AC-05
(tampilan badge di UI) tidak punya nilai tambah diuji lewat `TransactionCase`/`HttpCase` murni
(cuma baca atribut XML statis) — dicakup di Step 07 lewat Tour headless (Mode E), lihat
`07_QA_TESTING.md`.

**AC-04-04** (`res.country.department` TERSEDIA) **tidak bisa dijalankan di environment ini** —
model itu berasal dari addon di luar `depends` resmi (F-05) yang TIDAK terpasang di image
`odoo:17.0` maupun `EXTERNAL_ADDONS_PATHS` (kosong, lihat `CLAUDE.md`) — dicatat sebagai limitasi
tool di `FINDINGS.md`, bukan diklaim "Pass" dari asumsi.

**Ringkasan:** 7 AC → Unit (mock `requests.get`, tanpa server hidup — cukup `TransactionCase`
karena tidak ada endpoint HTTP milik modul ini yang diuji), 0 → Integration (`HttpCase`, tidak
relevan — modul tidak menambah controller/route), API N/A (modul konsumen, bukan penyedia API).

---

## Step 07 — QA Testing (level AI-interaktif + Smoke human-confirmed, TANPA UAT)

| AC | Deskripsi singkat | AI-interaktif (07 §3) | AI-Browser/Tour (07B) |
|---|---|---|---|
| AC-01-01/02 | Visibilitas tombol sesuai `is_company` | ✓ | ✓ |
| AC-02-01 | Wizard auto-fetch saat dibuka | ✓ | ✓ |
| AC-03-01/02/03 | Navigasi paginasi (termasuk wrap) | ✓ | ✓ |
| AC-04-01 | Select hasil + dialog konfirmasi overwrite (skenario "satu dialog") | ✓ | ✓ |
| AC-05-01/02 | Badge status administratif tampil benar | ✓ | ✓ |

**Ringkasan:** BACKFILL pakai AI-interaktif (`07_QA_TESTING.md` §3) sebagai default. AI-Browser
(`07B`) di CLI ini berarti **Tour headless (Mode E)** — lihat `PLAYBOOK.md` §Mode E — karena
`mcp__Claude_Browser__*` diketahui macet dari CLI (§Definisi Environment). Skenario dialog
konfirmasi "Are you sure want to overwrite the Data?" WAJIB masuk sebagai skenario tersendiri
(hanya SATU dialog yang pernah muncul di flow ini — tidak ada dialog kedua yang bersaing, jadi cek
wajib "hanya satu dialog disentuh" di `CLAUDE_TEMPLATE.md` tidak relevan untuk modul ini, dicatat
eksplisit sebagai N/A, bukan dilewati diam-diam).

---

## Ringkasan Keseluruhan

| Step | Tipe | Jumlah AC |
|---|---|---|
| 04 | Unit | 7 |
| 04 | Integration | 0 |
| 04 | Smoke | 2 happy path (wizard buka + fetch, select siret) |
| 04 | API | N/A (konsumen eksternal, bukan penyedia) |
| 07 | AI-interaktif (`07` §3) | 5 |
| 07 | AI-Browser/Tour (`07B`) | 5 |
